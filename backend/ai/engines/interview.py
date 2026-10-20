"""
ai/engines/interview.py

AI Discovery Interview Engine

Drives the conversational onboarding experience.
Maintains conversation state, extracts structured data from natural dialogue,
and writes findings to the identity_profile and onboarding_interview_state tables.

Flow:
    1. User sends a message
    2. Engine loads conversation history from DB
    3. Builds prompt with current phase context
    4. Gets AI response
    5. Extracts any newly surfaced data points
    6. Updates onboarding_interview_state
    7. If interview is complete AND data quality passes, writes to identity_profile
       + advances onboarding status
    8. If interview completion signal fires but data quality fails, returns
       needs_more_depth=True — the frontend keeps the conversation open and
       injects a Coach PO-voiced prompt to go deeper

The extraction happens silently -- the user just has a conversation.

Interview phases (v2):
    tension     -- surface what's not working (where are they stuck / disappointed?)
    real_goal   -- find the true goal beneath the stated one
    crystallise -- synthesise and confirm the goal + identity anchor
    summary     -- wrap up, signal completion

Timezone is collected separately via the frontend (browser Intl API) -- not during
the interview. Asking for it mid-conversation breaks the emotional flow.

Quality gate:
    Three signals must be present before the interview is treated as complete:
    - personal_vision: the real goal beneath the stated one
    - identity_anchor: who they said they'd become
    - resistance_triggers: what has stopped them before

    If any of these are missing when the completion phrase fires, the engine
    returns needs_more_depth=True instead of is_complete=True. The AI
    continues the conversation — no user-visible error, no broken experience.
"""

import json
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai.base import BaseAIEngine
from ai.prompts.system_prompts import get_prompt
from ai.utils.safety_filter import SafetyLevel, safety_filter
from core.security import sanitize_input

logger = structlog.get_logger()

# Phases in order -- the interview moves through these naturally
# v2: 3-phase psychological funnel (tension -> real goal -> crystallise)
# Timezone removed -- collected by frontend via Intl.DateTimeFormat()
INTERVIEW_PHASES = [
    "tension",       # What's not working? Where is the real pain?
    "real_goal",     # What do they actually want? What's stopped them?
    "crystallise",   # Synthesise the goal. Lock in the identity anchor.
    "summary",       # Wrap up, signal completion.
]

# The three fields that must be present for a quality interview.
# These map directly to the three phases of the funnel:
#   tension -> resistance_triggers
#   real_goal -> personal_vision
#   crystallise -> identity_anchor
REQUIRED_QUALITY_FIELDS = ["personal_vision", "identity_anchor", "resistance_triggers"]

# Minimum string length for a field to count as meaningfully populated.
# Guards against one-word extractions like {"identity_anchor": "leader"}.
QUALITY_MIN_LENGTH = 10

# Coverage gate (20 Oct 2026). The fields the coach and task generator read
# (context_builder.format_for_prompt), checked in code before the interview may
# conclude. Fill rates across 50 profiles with a goal: life_direction 43,
# motivation_style 34, obstacle (resistance_triggers or weaknesses) 46,
# core_values 11. Time is asked separately (identity_profiles.daily_minutes).
ESSENTIAL_FIELDS = ["life_direction", "motivation_style", "obstacle", "core_values"]

# What to explore for each missing field. Injected into one interview turn as
# an instruction, so the question comes in the coach's own voice.
COVERAGE_HINTS = {
    "life_direction": (
        "where their life is right now: their work, their days, what a normal week "
        "looks like and how this goal fits into it"
    ),
    "motivation_style": (
        "what actually moves them when they do follow through: going after something "
        "they want, getting away from something they fear, living up to something they "
        "believe in, or proving something to themselves"
    ),
    "obstacle": (
        "what usually gets in the way when they try, in their own words: the moment "
        "it tends to fall apart"
    ),
    "core_values": (
        "what this goal is really in service of: the two or three things that matter "
        "most to them underneath it"
    ),
}

MAX_COVERAGE_QUESTIONS = 3   # extra questions in total, then conclude anyway
MAX_DEPTH_PROMPTS = 2        # quality-gate prompts before concluding anyway

VALID_MOTIVATION_STYLES = {"aspiration_driven", "fear_driven", "values_driven", "achievement_driven"}

COMPLETION_PHRASE = "let's define your one goal"

# Message injected by the engine when the completion phrase fires but quality
# fails. Written in Coach PO's voice — not a system error message.
# "needs_more_depth" in the response signals the frontend to display this
# instead of routing away.
DEPTH_PROMPT_MESSAGE = (
    "We're getting close — but I want to make sure I have what I need to build "
    "something that's actually yours. Let me ask you one more thing. "
    "When you imagine the version of you who's already solved this — "
    "what's different about how they show up in the world? Not what they've achieved. "
    "Who they are."
)


class InterviewEngine(BaseAIEngine):
    """
    Manages the AI discovery interview.
    Stateful -- loads and saves conversation from the database.
    """

    engine_name = "interview"
    default_temperature = 0.8  # warmer, more conversational

    async def process_message(
        self,
        user_id: UUID | str,
        user_message: str,
        db: AsyncSession,
    ) -> dict:
        """
        Process a user message in the interview flow.

        Returns:
            {
                message: str,           -- AI response to show user
                phase: str,             -- current interview phase
                is_complete: bool,      -- True when interview is complete AND quality passes
                needs_more_depth: bool, -- True when completion fired but quality gate failed
                extracted: dict,        -- data extracted so far
            }
        """
        uid = str(user_id)

        # Safety check first
        safety_level = safety_filter.classify(user_message)
        if safety_level in (SafetyLevel.CRISIS, SafetyLevel.DISTRESS):
            safe_response = safety_filter.get_safe_response(safety_level)
            await safety_filter.log_safety_flag(
                user_id=uid,
                source_type="interview_message",
                source_id=uid,
                level=safety_level,
                excerpt=user_message[:200],
                ai_response=safe_response,
                db=db,
            )
            return {
                "message": safe_response,
                "phase": "paused",
                "is_complete": False,
                "needs_more_depth": False,
                "extracted": {},
            }

        # Prompt injection check
        if safety_filter.detect_prompt_injection(user_message):
            return {
                "message": "Let's keep going. Tell me more about where you are right now.",
                "phase": "error",
                "is_complete": False,
                "needs_more_depth": False,
                "extracted": {},
            }

        # Clean input
        clean_message = sanitize_input(user_message)

        # Load interview state
        state = await self._load_state(uid, db)
        messages = state.get("messages", [])
        current_phase = state.get("current_phase", "tension")
        extracted = state.get("extracted_data", {})

        # Advance onboarding status if this is the first message
        await self._ensure_interview_started(uid, db)

        # Add user message to history
        messages.append({"role": "user", "content": clean_message})

        # Build the prompt
        system_prompt = get_prompt("interview")

        # Coverage gate: near the end, if an essential field is still empty,
        # this turn explores it (one area, one question). Capped, so the user
        # is never kept in the interview.
        coverage = dict(extracted.get("_coverage") or {})
        coverage.setdefault("asked", 0)
        coverage.setdefault("fields", [])
        coverage.setdefault("depth_prompts", 0)
        missing = self._missing_essentials(extracted)
        user_turns = sum(1 for m in messages if m.get("role") == "user")
        near_end = current_phase in ("crystallise", "summary") or user_turns >= 7
        # Each area is asked about once; if the answer didn't fill it, move on.
        unasked = [f for f in missing if f not in coverage["fields"]]
        coverage_field = None
        if unasked and near_end and coverage["asked"] < MAX_COVERAGE_QUESTIONS:
            coverage_field = unasked[0]

        # Keep last 20 messages for context
        context_messages = messages[-20:] if len(messages) > 20 else messages

        async def respond(field: str | None) -> str:
            prompt = system_prompt + (self._coverage_instruction(field) if field else "")
            return await self._complete(
                messages=[{"role": "system", "content": prompt}, *context_messages],
                user_id=uid,
                temperature=0.8,
                max_tokens=300,  # shorter responses -- the prompt enforces 2-4 sentences
            )

        ai_response = await respond(coverage_field)

        # The model may still try to conclude. If essentials are missing and the
        # cap allows, ask it again for the coverage question instead.
        if COMPLETION_PHRASE in ai_response.lower() and coverage["asked"] < MAX_COVERAGE_QUESTIONS:
            field = coverage_field or (unasked[0] if unasked else None)
            if field:
                retry = await respond(field)
                if COMPLETION_PHRASE not in retry.lower():
                    ai_response = retry
                    coverage_field = field
                else:
                    coverage_field = None  # it insists; let it conclude (never trap the user)

        if coverage_field and COMPLETION_PHRASE not in ai_response.lower():
            coverage["asked"] += 1
            coverage["fields"].append(coverage_field)
            logger.info("interview_coverage_question", user_id=uid, field=coverage_field,
                        asked=coverage["asked"], missing=missing)

        # Add AI response to history
        messages.append({"role": "assistant", "content": ai_response})

        # Extract structured data from this exchange
        new_extractions = await self._extract_data(
            messages=messages,
            current_extracted=extracted,
            user_id=uid,
        )
        extracted = self._merge_extractions(extracted, new_extractions)
        extracted["_coverage"] = coverage

        # Determine if phase should advance
        next_phase = self._determine_phase(current_phase, ai_response, extracted, messages)

        # Check completion signal and quality
        completion_result = self._check_completion(ai_response, extracted)
        is_complete = completion_result["is_complete"]
        needs_more_depth = completion_result["needs_more_depth"]
        missing_fields = completion_result["missing_fields"]

        # Never trap the user: after MAX_DEPTH_PROMPTS quality-gate prompts the
        # interview concludes with what it has.
        if needs_more_depth and coverage["depth_prompts"] >= MAX_DEPTH_PROMPTS:
            logger.warning("interview_quality_gate_capped", user_id=uid, missing_fields=missing_fields)
            is_complete, needs_more_depth = True, False
        elif needs_more_depth:
            coverage["depth_prompts"] += 1

        if is_complete:
            still_missing = self._missing_essentials(extracted)
            logger.info("interview_completed_coverage", user_id=uid,
                        missing_essentials=still_missing, coverage_questions=coverage["asked"])

        # If completion fired but quality failed, inject the depth prompt.
        # The AI response is replaced with Coach PO's voice asking for more.
        # We stay in crystallise phase and keep the conversation open.
        if needs_more_depth:
            logger.info(
                "interview_quality_gate_failed",
                user_id=uid,
                missing_fields=missing_fields,
                message_count=len(messages),
            )
            ai_response = DEPTH_PROMPT_MESSAGE
            messages[-1] = {"role": "assistant", "content": ai_response}
            next_phase = "crystallise"  # Don't advance past crystallise

        # Save state
        await self._save_state(
            user_id=uid,
            messages=messages,
            current_phase=next_phase,
            extracted_data=extracted,
            is_complete=is_complete,
            db=db,
        )

        # If complete and quality passed, write to identity profile
        if is_complete:
            await self._finalize_profile(uid, extracted, db)

        return {
            "message": ai_response,
            "phase": next_phase,
            "is_complete": is_complete,
            "needs_more_depth": needs_more_depth,
            "extracted": extracted,
        }

    async def _extract_data(
        self,
        messages: list,
        current_extracted: dict,
        user_id: str,
    ) -> dict:
        """
        Read the whole conversation so far and return the current best reading
        of each profile field (merged by _merge_extractions).

        Changed 20 Oct 2026. It used to see only the latest exchange and was told
        to extract only what was "explicitly stated", so short answers produced
        almost nothing. In the reviewer account's interview, "No proper routine
        and structure" and "I'm busy" became the trigger "previous attempts to
        change fitness and health", and life direction, values and motivation
        were never filled.
        """
        transcript = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'Coach'}: {m.get('content', '')}"
            for m in messages[-24:]
        )
        known = {k: v for k, v in (current_extracted or {}).items() if not k.startswith("_")}
        extraction_prompt = f"""You keep a person's profile up to date from their coaching interview.
Read the whole conversation and return your best current reading of each field.

Rules:
- Short answers count. "I'm busy" is a resistance trigger. "Fit, healthy, sharp and confident" tells you what they value.
- Use their own words where you can.
- If a later answer refines an earlier one, use the later one.
- Infer motivation_style and core_values when the conversation gives reasonable signal, even if they never named them.
- Leave a field out only when there is genuinely no signal. Never invent facts they didn't give you.

Return ONLY a JSON object with any of these fields:
{{
  "life_direction": "where they are in life right now -- their current situation, in a sentence",
  "personal_vision": "where they want to be -- their real goal beneath the stated one",
  "identity_anchor": "who they will be when this is solved, ideally their own final wording",
  "core_values": ["2-4 values the goal serves, expressed or clearly implied"],
  "self_reported_strengths": ["strengths they mentioned"],
  "self_reported_weaknesses": ["weaknesses or fears they revealed"],
  "resistance_triggers": ["what has stopped them before, in their words"],
  "motivation_style": "one of: aspiration_driven, fear_driven, values_driven, achievement_driven",
  "lifestyle_context": {{"workStyle": "remote|office|hybrid", "familyStatus": "..."}}
}}

Profile so far: {json.dumps(known, indent=2)}

Conversation:
{transcript}
"""
        try:
            raw = await self._complete(
                messages=[{"role": "user", "content": extraction_prompt}],
                user_id=user_id,
                temperature=0.1,
                max_tokens=700,
            )
            return self._parse_json(raw, fallback={})
        except Exception as e:
            logger.warning("extraction_failed", error=str(e))
            return {}

    @staticmethod
    def _merge_extractions(current: dict, new: dict) -> dict:
        """
        The extractor reads the whole conversation, so a non-empty new value
        replaces the old one. Empty or invalid values never erase what exists.
        motivation_style must be one of the four allowed values (checked here,
        not trusted to the prompt).
        """
        merged = dict(current or {})
        for key, value in (new or {}).items():
            if key.startswith("_"):
                continue
            if key == "motivation_style":
                value = (value or "").strip().lower() if isinstance(value, str) else None
                if value not in VALID_MOTIVATION_STYLES:
                    continue
            if isinstance(value, str):
                if value.strip():
                    merged[key] = value.strip()
            elif isinstance(value, list):
                items = [str(v).strip() for v in value if isinstance(v, (str, int, float)) and str(v).strip()]
                if items:
                    merged[key] = items[:8]
            elif isinstance(value, dict):
                if value:
                    merged[key] = value
        return merged

    @staticmethod
    def _missing_essentials(extracted: dict) -> list[str]:
        """Essential fields still empty, in ESSENTIAL_FIELDS order."""
        def filled(v) -> bool:
            if isinstance(v, str):
                return len(v.strip()) >= 3
            if isinstance(v, list):
                return any(str(x).strip() for x in v)
            return bool(v)

        missing = []
        for field in ESSENTIAL_FIELDS:
            if field == "obstacle":
                ok = filled(extracted.get("resistance_triggers")) or filled(extracted.get("self_reported_weaknesses"))
            else:
                ok = filled(extracted.get(field))
            if not ok:
                missing.append(field)
        return missing

    @staticmethod
    def _coverage_instruction(field: str) -> str:
        return (
            "\n\nFOR THIS TURN ONLY (from the system, never mention it): before this "
            "conversation can conclude, you still need to understand "
            f"{COVERAGE_HINTS[field]}. Reflect briefly on what they just said, then ask "
            "ONE natural question that explores this, in your usual voice. It must feel "
            "like the next step in the conversation, not a form or a checklist. Do not "
            "conclude the interview in this message and do not use the closing line."
        )

    def _determine_phase(
        self,
        current_phase: str,
        ai_response: str,
        extracted: dict,
        messages: list,
    ) -> str:
        """
        Determine if the conversation has moved to a new phase.

        v2 logic: phases advance based on data coverage + message count signals.
        The AI is trusted to drive the conversation -- we just track where it is.
        """
        phase_index = INTERVIEW_PHASES.index(current_phase) if current_phase in INTERVIEW_PHASES else 0

        # Count user messages so far (rough turn count)
        user_turn_count = sum(1 for m in messages if m.get("role") == "user")

        # Phase advancement criteria
        phase_ready = {
            # Tension phase: done when they've shared what's not working
            "tension": (
                bool(extracted.get("life_direction")) or
                bool(extracted.get("self_reported_weaknesses")) or
                user_turn_count >= 3
            ),
            # Real goal phase: done when we have their true goal + what's stopped them
            "real_goal": (
                bool(extracted.get("personal_vision")) and
                bool(extracted.get("resistance_triggers")) or
                user_turn_count >= 6
            ),
            # Crystallise phase: done when we have the identity anchor
            "crystallise": (
                bool(extracted.get("identity_anchor")) or
                user_turn_count >= 9
            ),
            # Summary: always terminal
            "summary": False,
        }

        if phase_ready.get(current_phase, False) and phase_index < len(INTERVIEW_PHASES) - 1:
            return INTERVIEW_PHASES[phase_index + 1]

        return current_phase

    def _check_completion(self, ai_response: str, extracted: dict) -> dict:
        """
        Check whether the interview is genuinely complete.

        Two conditions must both be true for is_complete=True:
        1. The AI has produced the completion phrase
        2. The three phase-specific quality fields are present and substantive

        If (1) is true but (2) fails, returns needs_more_depth=True so the
        frontend keeps the conversation open with a Coach PO-voiced prompt.

        A field is considered substantive if it is:
        - A non-empty string longer than QUALITY_MIN_LENGTH characters, OR
        - A non-empty list with at least one element

        This guards against one-word extractions being treated as valid data.
        """
        completion_signal = COMPLETION_PHRASE in ai_response.lower()

        if not completion_signal:
            return {
                "is_complete": False,
                "needs_more_depth": False,
                "missing_fields": [],
            }

        # Completion phrase fired — now check data quality
        missing_fields = []
        for field in REQUIRED_QUALITY_FIELDS:
            value = extracted.get(field)
            if value is None:
                missing_fields.append(field)
            elif isinstance(value, str) and len(value.strip()) < QUALITY_MIN_LENGTH:
                missing_fields.append(field)
            elif isinstance(value, list) and len(value) == 0:
                missing_fields.append(field)

        if missing_fields:
            # Completion signalled but quality insufficient
            return {
                "is_complete": False,
                "needs_more_depth": True,
                "missing_fields": missing_fields,
            }

        # All good
        return {
            "is_complete": True,
            "needs_more_depth": False,
            "missing_fields": [],
        }

    # Keep the old method name as a thin wrapper for any callers that reference it directly
    def _is_interview_complete(self, ai_response: str, extracted: dict) -> bool:
        """Legacy wrapper — use _check_completion for full quality gate result."""
        return self._check_completion(ai_response, extracted)["is_complete"]

    async def _load_state(self, user_id: str, db: AsyncSession) -> dict:
        """Load interview state from database."""
        result = await db.execute(
            text("""
                SELECT current_phase, messages, extracted_data, is_complete
                FROM onboarding_interview_state
                WHERE user_id = :user_id
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return {"current_phase": "tension", "messages": [], "extracted_data": {}}

        return {
            "current_phase": row.current_phase,
            "messages": row.messages or [],
            "extracted_data": row.extracted_data or {},
            "is_complete": row.is_complete,
        }

    async def _save_state(
        self,
        user_id: str,
        messages: list,
        current_phase: str,
        extracted_data: dict,
        is_complete: bool,
        db: AsyncSession,
    ) -> None:
        """Save interview state to database."""
        await db.execute(
            text("""
                UPDATE onboarding_interview_state
                SET current_phase = :phase,
                    messages = CAST(:messages AS jsonb),
                    extracted_data = CAST(:extracted AS jsonb),
                    is_complete = :is_complete,
                    completed_at = CASE WHEN :is_complete THEN NOW() ELSE completed_at END
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id,
                "phase": current_phase,
                "messages": json.dumps(messages),
                "extracted": json.dumps(extracted_data),
                "is_complete": is_complete,
            },
        )

    async def _ensure_interview_started(self, user_id: str, db: AsyncSession) -> None:
        """Advance onboarding status to interview_started on first message."""
        await db.execute(
            text("""
                UPDATE users
                SET onboarding_status = 'interview_started'
                WHERE id = :user_id AND onboarding_status = 'created'
            """),
            {"user_id": user_id},
        )

    async def _finalize_profile(
        self, user_id: str, extracted: dict, db: AsyncSession
    ) -> None:
        """
        Write extracted data to identity_profile and advance onboarding status.
        Called once when interview is complete AND quality gate has passed.
        """
        await db.execute(
            text("""
                UPDATE identity_profiles SET
                    life_direction = COALESCE(:life_direction, life_direction),
                    personal_vision = COALESCE(:personal_vision, personal_vision),
                    core_values = COALESCE(:core_values, core_values),
                    self_reported_strengths = COALESCE(:strengths, self_reported_strengths),
                    self_reported_weaknesses = COALESCE(:weaknesses, self_reported_weaknesses),
                    lifestyle_context = COALESCE(:lifestyle_context, lifestyle_context),
                    resistance_triggers = COALESCE(:resistance_triggers, resistance_triggers),
                    motivation_style = COALESCE(:motivation_style, motivation_style),
                    last_ai_update = NOW()
                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id,
                "life_direction": extracted.get("life_direction"),
                "personal_vision": extracted.get("personal_vision"),
                "core_values": extracted.get("core_values"),
                "strengths": extracted.get("self_reported_strengths"),
                "weaknesses": extracted.get("self_reported_weaknesses"),
                "lifestyle_context": json.dumps(extracted.get("lifestyle_context")) if extracted.get("lifestyle_context") else None,
                "resistance_triggers": extracted.get("resistance_triggers"),
                "motivation_style": extracted.get("motivation_style"),
            },
        )

        # Store identity anchor -- this becomes the user's bio seed
        if extracted.get("identity_anchor"):
            await db.execute(
                text("UPDATE users SET bio = :bio WHERE id = :user_id"),
                {
                    "user_id": user_id,
                    "bio": extracted["identity_anchor"],
                },
            )

        # Advance onboarding status
        await db.execute(
            text("UPDATE users SET onboarding_status = 'interview_complete' WHERE id = :user_id"),
            {"user_id": user_id},
        )

        logger.info("interview_finalized", user_id=user_id)
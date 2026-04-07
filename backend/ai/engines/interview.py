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

        # Keep last 20 messages for context
        context_messages = messages[-20:] if len(messages) > 20 else messages

        prompt_messages = [
            {"role": "system", "content": system_prompt},
            *context_messages,
        ]

        # Get AI response
        ai_response = await self._complete(
            messages=prompt_messages,
            user_id=uid,
            temperature=0.8,
            max_tokens=300,  # shorter responses -- the prompt enforces 2-4 sentences
        )

        # Add AI response to history
        messages.append({"role": "assistant", "content": ai_response})

        # Extract structured data from this exchange
        new_extractions = await self._extract_data(
            user_message=clean_message,
            ai_response=ai_response,
            current_extracted=extracted,
            current_phase=current_phase,
            db=db,
            user_id=uid,
        )
        extracted.update(new_extractions)

        # Determine if phase should advance
        next_phase = self._determine_phase(current_phase, ai_response, extracted, messages)

        # Check completion signal and quality
        completion_result = self._check_completion(ai_response, extracted)
        is_complete = completion_result["is_complete"]
        needs_more_depth = completion_result["needs_more_depth"]
        missing_fields = completion_result["missing_fields"]

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
        user_message: str,
        ai_response: str,
        current_extracted: dict,
        current_phase: str,
        db: AsyncSession,
        user_id: str,
    ) -> dict:
        """
        Silently extract structured profile data from a conversation turn.
        Uses a separate AI call with lower temperature for accuracy.
        """
        extraction_prompt = f"""Extract any new profile information from this conversation exchange.
Only extract what was explicitly stated or clearly implied by the user.
Return ONLY a JSON object with any of these fields that were discussed:
{{
  "life_direction": "where they are in life right now -- their current situation",
  "personal_vision": "where they want to be -- their real goal beneath the stated one",
  "identity_anchor": "how they described themselves when this is solved -- their identity statement",
  "core_values": ["values they expressed or implied"],
  "self_reported_strengths": ["strengths they mentioned"],
  "self_reported_weaknesses": ["weaknesses, fears, or resistance patterns they revealed"],
  "resistance_triggers": ["what has stopped them before -- specific patterns"],
  "motivation_style": "aspiration_driven|fear_driven|values_driven|achievement_driven",
  "lifestyle_context": {{"workStyle": "remote|office|hybrid", "familyStatus": "..."}},
  "peak_performance_time": "early_morning|late_morning|afternoon|evening"
}}

Conversation turn:
User: {user_message}
AI: {ai_response}

Already extracted: {json.dumps(current_extracted, indent=2)}

Return only NEW or UPDATED fields. Return empty object {{}} if nothing new was stated.
Focus especially on: resistance_triggers, identity_anchor, personal_vision -- these are most valuable.
"""
        try:
            raw = await self._complete(
                messages=[{"role": "user", "content": extraction_prompt}],
                user_id=user_id,
                temperature=0.1,
                max_tokens=400,
            )
            return self._parse_json(raw, fallback={})
        except Exception as e:
            logger.warning("extraction_failed", error=str(e))
            return {}

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
        completion_signal = "let's define your one goal" in ai_response.lower()

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
                    peak_performance_time = COALESCE(:peak_time, peak_performance_time),
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
                "peak_time": extracted.get("peak_performance_time"),
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
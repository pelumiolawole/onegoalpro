import posthog from "posthog-js";

const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.posthog.com";

// PostHog is never initialised until the visitor accepts analytics, so it cannot
// write a cookie, write storage or send a request before consent.
export const CONSENT_KEY = "ogp_cookie_consent";
export const CONSENT_CHANGED_EVENT = "ogp-consent-changed";
export const OPEN_COOKIE_SETTINGS_EVENT = "ogp-open-cookie-settings";

export type Consent = "accepted" | "declined" | null;

let initialised = false;
let pendingUserId: string | null = null;
let pendingProperties: Record<string, any> | undefined;

export function getConsent(): Consent {
  try {
    const value = localStorage.getItem(CONSENT_KEY);
    return value === "accepted" || value === "declined" ? value : null;
  } catch {
    return null;
  }
}

function startPostHog() {
  if (typeof window === "undefined" || !POSTHOG_KEY) return;

  if (initialised) {
    posthog.opt_in_capturing();
  } else {
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      person_profiles: "identified_only",
      loaded: (ph) => {
        if (process.env.NODE_ENV === "development") ph.debug();
      },
    });
    initialised = true;
  }

  if (pendingUserId) posthog.identify(pendingUserId, pendingProperties);
}

function clearPostHogStorage() {
  try {
    document.cookie.split(";").forEach((cookie) => {
      const name = cookie.split("=")[0].trim();
      if (name.startsWith("ph_")) {
        document.cookie = `${name}=; Max-Age=0; path=/`;
        document.cookie = `${name}=; Max-Age=0; path=/; domain=.${location.hostname}`;
      }
    });
    Object.keys(localStorage)
      .filter((key) => key.startsWith("ph_"))
      .forEach((key) => localStorage.removeItem(key));
    Object.keys(sessionStorage)
      .filter((key) => key.startsWith("ph_"))
      .forEach((key) => sessionStorage.removeItem(key));
  } catch {
    // Storage unavailable; nothing to clear
  }
}

export function setConsent(consent: "accepted" | "declined") {
  try {
    localStorage.setItem(CONSENT_KEY, consent);
  } catch {
    // Choice still applies for this page load
  }

  if (consent === "accepted") {
    startPostHog();
  } else {
    if (initialised) posthog.opt_out_capturing();
    clearPostHogStorage();
  }

  window.dispatchEvent(new Event(CONSENT_CHANGED_EVENT));
}

export function openCookieSettings() {
  window.dispatchEvent(new Event(OPEN_COOKIE_SETTINGS_EVENT));
}

export const initPostHog = () => {
  if (typeof window !== "undefined" && getConsent() === "accepted") startPostHog();
};

// Internal user ID only. Never pass email, name or other direct identifiers.
export const identifyUser = (userId: string, properties?: Record<string, any>) => {
  pendingUserId = userId;
  pendingProperties = properties;
  if (initialised && getConsent() === "accepted") posthog.identify(userId, properties);
};

export const resetAnalyticsUser = () => {
  pendingUserId = null;
  pendingProperties = undefined;
  if (initialised) posthog.reset();
};

export const trackEvent =(event: string, properties?: Record<string, any>) => {
  if (initialised && getConsent() === "accepted") posthog.capture(event, properties);
};

export default posthog;

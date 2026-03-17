import posthog from "posthog-js";

const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";

export const initPostHog = () => {
  if (typeof window !== "undefined" && POSTHOG_KEY) {
    posthog.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST,
      loaded: (posthog) => {
        if (process.env.NODE_ENV === "development") posthog.debug();
      },
    });
  }
};

export const identifyUser = (userId: string, email: string, properties?: Record<string, any>) => {
  if (POSTHOG_KEY) {
    posthog.identify(userId, { email, ...properties });
  }
};

export const trackEvent = (event: string, properties?: Record<string, any>) => {
  if (POSTHOG_KEY) {
    posthog.capture(event, properties);
  }
};

export default posthog;
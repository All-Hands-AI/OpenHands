/// <reference types="react-scripts" />

interface Window {
  posthog?: {
    capture: (event: string, properties?: Record<string, unknown>) => void;
  };
}

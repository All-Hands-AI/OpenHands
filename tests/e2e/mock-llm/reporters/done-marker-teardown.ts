import { finishTestRun } from "./done-marker-reporter";

// Global teardown precedes webServer plugin teardown; reporter.onEnd does not.
export default function doneMarkerTeardown() {
  finishTestRun();
}

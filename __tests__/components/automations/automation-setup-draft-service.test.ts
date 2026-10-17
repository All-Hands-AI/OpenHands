import { describe, expect, it } from "vitest";
import { HttpError } from "@openhands/typescript-client";
import {
  extractDraftDispatchErrors,
  formFromServerDraft,
  getDraftExecutionStatusText,
  setupDraftFromServerDraft,
} from "#/components/features/automations/setup/automation-setup-draft-service";
import type { AutomationSetupFormValues } from "#/api/automation-setup-types";
import { I18nKey } from "#/i18n/declaration";
import type { AutomationDraftApiResponse } from "#/manifests/types";
import { AutomationRunStatus, type AutomationRun } from "#/types/automation";

const detailEnvelope = {
  detail: {
    message: "Draft is not dispatchable",
    errors: [
      {
        field: "prompt",
        code: "required",
        message: "Prompt is required",
      },
    ],
  },
};

describe("extractDraftDispatchErrors", () => {
  it("reads FastAPI detail envelopes from axios draft dispatch errors", () => {
    const error = {
      isAxiosError: true,
      response: { data: detailEnvelope },
    };

    expect(extractDraftDispatchErrors(error)).toBe("Prompt is required");
  });

  it("reads FastAPI detail envelopes from SDK HttpError draft dispatch errors", () => {
    const error = new HttpError(422, "Unprocessable Entity", detailEnvelope);

    expect(extractDraftDispatchErrors(error)).toBe("Prompt is required");
  });

  it("falls back to the detail message when no field errors are present", () => {
    const error = new HttpError(422, "Unprocessable Entity", {
      detail: { message: "Draft is not dispatchable", errors: [] },
    });

    expect(extractDraftDispatchErrors(error)).toBe("Draft is not dispatchable");
  });
});

const baseSavedDraft: AutomationDraftApiResponse = {
  id: "draft-1",
  endpoint: "/v1/preset/prompt",
  name: "Saved draft",
  draft: {},
  validationErrors: null,
  dispatchable: true,
  sourceAutomationId: null,
  materializedAutomationId: null,
  lastTestRunId: null,
  createdAt: "2026-01-01T00:00:00.000Z",
  updatedAt: "2026-01-01T00:00:00.000Z",
};

const baseForm: AutomationSetupFormValues = {
  name: "",
  prompt: "",
  repository: "",
  pluginSource: "",
  pluginRef: "",
  pluginList: "",
  customCode: "",
  entrypoint: "",
  setupScriptPath: "",
  setupScript: "",
  triggerKind: "cron",
  frequency: "daily",
  time: "09:00",
  scheduleDateTime: "",
  timezone: "UTC",
  weekday: "1",
  customSchedule: "",
  eventSource: "github",
  eventKey: "",
  eventFilter: "",
  model: "",
  agentProfileId: "",
  showTimeout: false,
  timeoutSeconds: "",
  kind: "prompt",
};

describe("setupDraftFromServerDraft", () => {
  it("hydrates all repositories and event keys from saved drafts", () => {
    const saved = {
      ...baseSavedDraft,
      draft: {
        prompt: "Triage issues",
        repos: [{ url: "acme/one" }, { url: "acme/two" }],
        trigger: {
          type: "event",
          source: "github",
          on: ["pull_request", "issues"],
        },
      },
    } satisfies AutomationDraftApiResponse;

    const draft = setupDraftFromServerDraft(saved);

    expect(draft.form?.repository).toBe("acme/one, acme/two");
    expect(draft.form?.eventKey).toBe("pull_request,issues");
  });

  it("updates an existing form with all repositories and event keys", () => {
    const saved = {
      ...baseSavedDraft,
      draft: {
        repos: [{ url: "acme/one" }, { url: "acme/two" }],
        trigger: {
          type: "event",
          source: "github",
          on: ["push", "release.published"],
        },
      },
    } satisfies AutomationDraftApiResponse;

    const form = formFromServerDraft(saved, baseForm);

    expect(form.repository).toBe("acme/one, acme/two");
    expect(form.eventKey).toBe("push,release.published");
  });
});

const t = (key: I18nKey) => key;

const cronValidationError = "Value error, Invalid cron expression: every day";

function draftRun(status: AutomationRunStatus, id = "run-1"): AutomationRun {
  return {
    id,
    status,
    conversation_id: null,
    bash_command_id: null,
    error_detail: null,
    started_at: "2026-01-01T00:00:00.000Z",
    completed_at:
      status === AutomationRunStatus.COMPLETED
        ? "2026-01-01T00:01:00.000Z"
        : null,
  };
}

function invalidCronDraft(): AutomationDraftApiResponse {
  return {
    ...baseSavedDraft,
    dispatchable: false,
    validationErrors: [
      {
        field: "trigger.schedule",
        code: "value_error",
        message: cronValidationError,
      },
    ],
  };
}

describe("getDraftExecutionStatusText", () => {
  it("prefers the current validation error over a successful historical test", () => {
    expect(
      getDraftExecutionStatusText(
        invalidCronDraft(),
        [draftRun(AutomationRunStatus.COMPLETED)],
        t,
      ),
    ).toBe(cronValidationError);
  });

  it("shows the validation error when the invalid draft has no runs", () => {
    expect(getDraftExecutionStatusText(invalidCronDraft(), [], t)).toBe(
      cronValidationError,
    );
  });

  it("keeps the latest run status when the saved draft is valid", () => {
    expect(
      getDraftExecutionStatusText(
        baseSavedDraft,
        [draftRun(AutomationRunStatus.COMPLETED)],
        t,
      ),
    ).toBe(I18nKey.AUTOMATION_SETUP$LATEST_TEST_PASSED);
    expect(
      getDraftExecutionStatusText(
        baseSavedDraft,
        [draftRun(AutomationRunStatus.FAILED)],
        t,
      ),
    ).toBe(I18nKey.AUTOMATION_SETUP$LATEST_TEST_FAILED);
    expect(
      getDraftExecutionStatusText(
        baseSavedDraft,
        [draftRun(AutomationRunStatus.RUNNING)],
        t,
      ),
    ).toBe(I18nKey.AUTOMATION_SETUP$LATEST_TEST_RUNNING);
    expect(
      getDraftExecutionStatusText(
        baseSavedDraft,
        [draftRun(AutomationRunStatus.PENDING)],
        t,
      ),
    ).toBe(I18nKey.AUTOMATION_SETUP$LATEST_TEST_RUNNING);
  });

  it("says the draft is ready to test when it is valid and has no runs", () => {
    expect(getDraftExecutionStatusText(baseSavedDraft, [], t)).toBe(
      I18nKey.AUTOMATION_SETUP$READY_TO_TEST,
    );
  });

  it("ignores a blank validation message and uses the latest run", () => {
    const draft: AutomationDraftApiResponse = {
      ...baseSavedDraft,
      validationErrors: [{ field: null, code: "value_error", message: "   " }],
    };

    expect(
      getDraftExecutionStatusText(
        draft,
        [draftRun(AutomationRunStatus.COMPLETED)],
        t,
      ),
    ).toBe(I18nKey.AUTOMATION_SETUP$LATEST_TEST_PASSED);
  });
});

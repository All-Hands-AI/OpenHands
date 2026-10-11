import test, { expect } from "@playwright/test";
import {
  advanceOnboardingToLlmStep,
  ONBOARDING_BACKEND_STEP,
  showOnboarding,
  waitForOnboardingStep,
} from "../../support/onboarding-helpers";
import {
  BACKEND_URL,
  routeSessionApiKey,
  SESSION_API_KEY,
} from "../utils/mock-llm-helpers";

test.describe.configure({ mode: "serial" });

test.describe("onboarding recent regressions", () => {
  // Regression coverage for #1085 / PR #1100: errant outside
  // interactions must not permanently mark onboarding complete.

  test("keeps the modal open on backdrop click and Escape", async ({
    page,
  }) => {
    await showOnboarding(page, {
      apiKey: SESSION_API_KEY,
      beforeGoto: () => routeSessionApiKey(page),
    });

    // Exercise the original first-load path before any onboarding step
    // interaction.
    await page.mouse.click(8, 8);
    await page.keyboard.press("Escape");

    await expect(
      page.getByTestId("onboarding-modal"),
      "onboarding modal should ignore backdrop clicks and Escape",
    ).toBeVisible();
    await waitForOnboardingStep(page, ONBOARDING_BACKEND_STEP);
    await expect
      .poll(
        () =>
          page.evaluate(() =>
            window.localStorage.getItem("openhands-onboarded"),
          ),
        {
          message:
            "onboarding should not be marked complete by outside interactions",
        },
      )
      .toBeNull();

    await page.getByTestId("onboarding-skip").click();
    await expect(
      page.getByTestId("onboarding-modal"),
      "skip should close the onboarding modal",
    ).toHaveCount(0);
    await expect
      .poll(
        () =>
          page.evaluate(() =>
            window.localStorage.getItem("openhands-onboarded"),
          ),
        { message: "skip should persist onboarding completion" },
      )
      .toBe("1");
  });

  // Regression coverage for #1077 / PR #1089: first-run LLM setup
  // should default users to the configured default provider and model.

  test("defaults the LLM setup step to OpenAI GPT-5.6 Sol", async ({
    page,
  }) => {
    await showOnboarding(page, {
      apiKey: SESSION_API_KEY,
      beforeGoto: async () => {
        await routeSessionApiKey(page);
        // Intercept GET /api/settings so the LLM form sees a clean
        // base_url, forcing basic view mode regardless of what earlier
        // specs configured. Registered AFTER routeSessionApiKey so
        // Playwright's LIFO matching picks this up first for settings.
        await page.route("**/api/settings", async (route, req) => {
          if (req.method() !== "GET") {
            await route.fallback();
            return;
          }
          const response = await route.fetch();
          const body = await response.json();
          if (body?.agent_settings?.llm) {
            body.agent_settings.llm.base_url = null;
          }
          await route.fulfill({ response, json: body });
        });
      },
    });
    await advanceOnboardingToLlmStep(page);

    const providerInput = page.locator('input[name="llm-provider-input"]');
    const modelInput = page.locator('input[name="llm-model-input"]');

    await expect(
      providerInput,
      "first-run onboarding should default to the OpenAI provider",
    ).toHaveValue("OpenAI", { timeout: 10_000 });
    // The model input displays the model ID without the provider prefix.
    await expect(
      modelInput,
      "first-run onboarding should default to GPT-5.6 Sol",
    ).toHaveValue("gpt-5.6-sol", {
      timeout: 10_000,
    });
    await expect(
      page.getByTestId("openhands-account-help"),
      "OpenHands account helper should be hidden for OpenAI defaults",
    ).toBeHidden();
  });

  // Re-onboarding coverage for profile-first onboarding (#18214):
  // When an active profile has a custom Base URL and key, onboarding
  // pre-fills both and enters All view.
  test("re-onboarding with an active profile preserves custom base URL and key", async ({
    page,
    request,
  }) => {
    const profileName = `test-reonboard-${Date.now()}`;
    const customBaseUrl = "http://localhost:19118/v1";
    const customKey = "test-reonboard-key";

    await request.post(`${BACKEND_URL}/api/profiles`, {
      headers: {
        "X-Session-API-Key": SESSION_API_KEY,
        "Content-Type": "application/json",
      },
      data: {
        name: profileName,
        llm: {
          model: "openai/gpt-4o-mini",
          base_url: customBaseUrl,
          api_key: customKey,
        },
        include_secrets: true,
      },
    });

    await request.post(
      `${BACKEND_URL}/api/profiles/${encodeURIComponent(profileName)}/activate`,
      {
        headers: { "X-Session-API-Key": SESSION_API_KEY },
      },
    );

    try {
      await showOnboarding(page, {
        apiKey: SESSION_API_KEY,
        beforeGoto: () => routeSessionApiKey(page),
      });

      await advanceOnboardingToLlmStep(page);

      const baseUrlInput = page.getByTestId("base-url-input");
      await expect(baseUrlInput).toHaveValue(customBaseUrl, {
        timeout: 10_000,
      });
      const apiKeyInput = page.getByTestId("llm-api-key-input");
      await expect(apiKeyInput).toHaveAttribute("placeholder", "<hidden>");
    } finally {
      try {
        await request.delete(
          `${BACKEND_URL}/api/profiles/${encodeURIComponent(profileName)}`,
          {
            headers: { "X-Session-API-Key": SESSION_API_KEY },
          },
        );
      } catch {
        // best-effort
      }
    }
  });
});

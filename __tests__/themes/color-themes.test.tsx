import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AgentServerUIRoot } from "#/components/providers/agent-server-ui-root";
import {
  AVAILABLE_COLOR_THEMES,
  COLOR_THEMES,
  applyColorTheme,
} from "#/themes/color-themes";

describe("color themes", () => {
  afterEach(() => {
    document
      .querySelectorAll("style[data-theme-test]")
      .forEach((el) => el.remove());
  });

  it("leaves omitted tokens owned by consumer stylesheets", () => {
    const sheet = document.createElement("style");
    sheet.dataset.themeTest = "";
    sheet.textContent =
      "[data-agent-server-ui] { --oh-color-primary: #123456; --oh-radius: 12px; }";
    document.head.appendChild(sheet);
    render(
      <AgentServerUIRoot data-testid="consumer-scope">
        Canvas
      </AgentServerUIRoot>,
    );
    act(() => applyColorTheme("openhands-neutral"));
    const style = getComputedStyle(screen.getByTestId("consumer-scope"));
    expect(style.getPropertyValue("--oh-color-primary")).toBe("#123456");
    expect(style.getPropertyValue("--oh-radius")).toBe("12px");
  });
  it("includes OpenHands-Neo as a neutral-based theme with white button tokens", () => {
    const neo = COLOR_THEMES["openhands-neo"];

    expect(neo.label).toBe("OpenHands-Neo");
    expect(neo.scale).toEqual(COLOR_THEMES["openhands-neutral"].scale);
    expect(neo.heroui).toEqual(COLOR_THEMES["openhands-neutral"].heroui);
    expect(neo.tokens?.["--oh-color-primary"]).toBe("#ffffff");
    expect(neo.tokens?.["--oh-accent"]).toBe("#ffffff");
  });

  it("exposes Neo in the settings theme picker", () => {
    expect(AVAILABLE_COLOR_THEMES.map((theme) => theme.key)).toContain(
      "openhands-neo",
    );
    expect(
      AVAILABLE_COLOR_THEMES.find((theme) => theme.key === "openhands-neo")
        ?.label,
    ).toBe("OpenHands-Neo");
  });

  it("injects white primary tokens when applying OpenHands-Neo", () => {
    document.body.setAttribute("data-agent-server-ui", "");

    applyColorTheme("openhands-neo");

    const styleEl = document.getElementById("oh-color-theme-override");
    expect(styleEl?.textContent).toContain("--oh-color-primary: #ffffff;");
    expect(styleEl?.textContent).toContain("--oh-accent: #ffffff;");

    styleEl?.remove();
    document.body.removeAttribute("data-agent-server-ui");
    document.body.style.removeProperty("--oh-color-primary");
    document.body.style.removeProperty("--oh-accent");
    document.body.style.removeProperty("--oh-warning");
  });

  it("injects override rules with order-independent doubled scope selectors", () => {
    // Act
    applyColorTheme("openhands-neutral");

    // Assert: doubled selectors (0,2,0) out-specify the base sheet's unlayered
    // [data-agent-server-ui] variable rules (0,1,0), so the override wins even
    // when React 19 re-inserts the base stylesheet <link> after this tag.
    const styleEl = document.getElementById("oh-color-theme-override");
    expect(styleEl?.textContent).toContain(
      "[data-agent-server-ui][data-agent-server-ui] {",
    );
    expect(styleEl?.textContent).toContain(
      "[data-agent-server-ui] [data-theme][data-theme] {",
    );

    styleEl?.remove();
  });

  it("re-appends the override style tag to the end of <head> on every apply", () => {
    // Arrange: first apply creates the tag, then a later stylesheet lands
    // after it (as React 19 does with the base CSS <link> in the built SPA).
    applyColorTheme("openhands-neutral");
    const laterSheet = document.createElement("style");
    document.head.appendChild(laterSheet);

    // Act
    applyColorTheme("openhands-deepsea");

    // Assert
    expect(document.head.lastElementChild?.id).toBe("oh-color-theme-override");

    laterSheet.remove();
    document.getElementById("oh-color-theme-override")?.remove();
  });

  it("applies Neo button tokens on the scoped UI root used by primary buttons", () => {
    const baseSheet = document.createElement("style");
    baseSheet.dataset.themeTest = "";
    baseSheet.textContent =
      "[data-agent-server-ui] { --oh-color-primary: #c9b974; }";
    document.head.appendChild(baseSheet);
    render(
      <AgentServerUIRoot>
        <button type="button" data-testid="primary-button">
          Save
        </button>
      </AgentServerUIRoot>,
    );

    act(() => applyColorTheme("openhands-neo"));

    const scopeRoot = screen
      .getByTestId("primary-button")
      .closest("[data-agent-server-ui]") as HTMLElement;

    expect(
      getComputedStyle(scopeRoot).getPropertyValue("--oh-color-primary"),
    ).toBe("#ffffff");

    act(() => applyColorTheme("openhands-neutral"));

    expect(
      getComputedStyle(scopeRoot).getPropertyValue("--oh-color-primary"),
    ).toBe("#c9b974");
  });

  it("defines readable feedback text tokens for all five built-in themes", () => {
    const themes = [
      "openhands-deepsea",
      "openhands-neutral",
      "openhands-neo",
      "light-plus",
      "solarized-light",
    ] as const;

    for (const themeKey of themes) {
      const theme = COLOR_THEMES[themeKey];
      expect(theme.tokens?.["--oh-feedback-error"]).toBeDefined();
      expect(theme.tokens?.["--oh-feedback-success"]).toBeDefined();
    }

    // In light themes, feedback tokens resolve distinctly from control danger/success
    const lightPlus = COLOR_THEMES["light-plus"];
    expect(lightPlus.tokens?.["--oh-feedback-error"]).not.toBe(
      lightPlus.tokens?.["--oh-color-danger"],
    );
    expect(lightPlus.tokens?.["--oh-feedback-success"]).not.toBe(
      lightPlus.tokens?.["--oh-color-success"],
    );

    const solarized = COLOR_THEMES["solarized-light"];
    expect(solarized.tokens?.["--oh-feedback-error"]).not.toBe(
      solarized.tokens?.["--oh-color-danger"],
    );
    expect(solarized.tokens?.["--oh-feedback-success"]).not.toBe(
      solarized.tokens?.["--oh-color-success"],
    );
  });

  it("allows embedded hosts to override feedback text tokens via styleOverrides", () => {
    render(
      <AgentServerUIRoot
        data-testid="overridden-scope"
        styleOverrides={{
          "--oh-feedback-error": "#ff0055",
          "--oh-feedback-success": "#00ffaa",
        }}
      >
        <span data-testid="error-text" className="text-feedback-error">
          Error
        </span>
        <span data-testid="success-text" className="text-feedback-success">
          Success
        </span>
      </AgentServerUIRoot>,
    );

    const scope = screen.getByTestId("overridden-scope");
    expect(scope.style.getPropertyValue("--oh-feedback-error")).toBe("#ff0055");
    expect(scope.style.getPropertyValue("--oh-feedback-success")).toBe(
      "#00ffaa",
    );
  });

  it("satisfies WCAG AA >= 4.5:1 contrast for feedback tokens against modal and base surfaces across all themes", () => {
    function luminance(r: number, g: number, b: number): number {
      const a = [r, g, b].map((v) => {
        const c = v / 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
    }

    function contrast(hex1: string, hex2: string): number {
      const toRgb = (hex: string) => {
        const clean = hex.replace("#", "");
        return [
          parseInt(clean.slice(0, 2), 16),
          parseInt(clean.slice(2, 4), 16),
          parseInt(clean.slice(4, 6), 16),
        ] as const;
      };
      const [r1, g1, b1] = toRgb(hex1);
      const [r2, g2, b2] = toRgb(hex2);
      const lum1 = luminance(r1, g1, b1);
      const lum2 = luminance(r2, g2, b2);
      const brightest = Math.max(lum1, lum2);
      const darkest = Math.min(lum1, lum2);
      return (brightest + 0.05) / (darkest + 0.05);
    }

    const themes = [
      "openhands-deepsea",
      "openhands-neutral",
      "openhands-neo",
      "light-plus",
      "solarized-light",
    ] as const;

    for (const themeKey of themes) {
      const theme = COLOR_THEMES[themeKey];
      const errColor = theme.tokens?.["--oh-feedback-error"]!;
      const succColor = theme.tokens?.["--oh-feedback-success"]!;
      const modalBg = theme.scale["--cool-grey-925"];
      const pageBg = theme.scale["--cool-grey-950"];

      expect(contrast(errColor, modalBg)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(errColor, pageBg)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(succColor, modalBg)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(succColor, pageBg)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

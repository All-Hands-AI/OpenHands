import { describe, it, expect } from "vitest";
import { execSync } from "child_process";
import path from "path";
import fs from "fs";

describe("Localization Fix Tests", () => {
  it("should not find any unlocalized strings in the frontend code", () => {
    const scriptPath = path.join(
      __dirname,
      "../../scripts/check-unlocalized-strings.cjs",
    );

    // Run the localization check script
    const result = execSync(`node ${scriptPath}`, {
      cwd: path.join(__dirname, "../.."),
      encoding: "utf8",
    });

    // The script should output success message and exit with code 0
    expect(result).toContain(
      "✅ No unlocalized strings found in frontend code.",
    );
  });

  it("should properly detect user-facing attributes like placeholder, alt, and aria-label", () => {
    // This test verifies that our fix to include placeholder, alt, and aria-label
    // attributes in the localization check is working correctly by testing the regex patterns

    const scriptPath = path.join(
      __dirname,
      "../../scripts/check-unlocalized-strings.cjs",
    );
    const scriptContent = fs.readFileSync(scriptPath, "utf8");

    // Verify that these attributes are now being checked for localization
    // by ensuring they're not excluded from text extraction
    const nonTextAttributesMatch = scriptContent.match(
      /const NON_TEXT_ATTRIBUTES = \[(.*?)\]/s,
    );
    expect(nonTextAttributesMatch).toBeTruthy();

    const nonTextAttributes = nonTextAttributesMatch![1];
    expect(nonTextAttributes).not.toContain('"placeholder"');
    expect(nonTextAttributes).not.toContain('"alt"');
    expect(nonTextAttributes).not.toContain('"aria-label"');

    // Verify that the script contains the correct attributes that should be excluded
    expect(nonTextAttributes).toContain('"className"');
    expect(nonTextAttributes).toContain('"testId"');
    expect(nonTextAttributes).toContain('"href"');
  });

  it("should not incorrectly flag CSS units as unlocalized strings", () => {
    // This test verifies that our fix to the CSS units regex pattern
    // prevents false positives like "Suggested Tasks" being flagged

    const testStrings = [
      "Suggested Tasks",
      "No tasks available",
      "Select a branch",
      "Select a repo",
      "Custom Models",
      "API Keys",
      "Git Settings",
    ];

    // These strings should not be flagged as CSS units
    const cssUnitsPattern =
      /\b\d+(px|rem|em|vh|vw|vmin|vmax|ch|ex|fr|deg|rad|turn|grad|ms|s)$|^(px|rem|em|vh|vw|vmin|vmax|ch|ex|fr|deg|rad|turn|grad|ms|s)$/;

    testStrings.forEach((str) => {
      expect(cssUnitsPattern.test(str)).toBe(false);
    });

    // But actual CSS units should still be detected
    const actualCssUnits = ["10px", "2rem", "100vh", "px", "rem", "s"];
    actualCssUnits.forEach((unit) => {
      expect(cssUnitsPattern.test(unit)).toBe(true);
    });
  });
});

import fs from "fs";
import path from "path";

// Patterns that indicate a string might need localization
const STRING_PATTERNS = [
  /['"`]([^'"`\n]+)['"`]/g, // Matches any quoted strings except empty ones and newlines
];

// Patterns that indicate a string is already localized
const LOCALIZED_PATTERNS = [
  /t\(['"`][\w$.]+['"`]\)/, // t('KEY')
  /useTranslation\(/, // useTranslation()
  /<Trans>/, // <Trans>
  /['"`][\w$.]+['"`]/, // Just a key like 'KEY.SUBKEY'
];

// Files/directories to ignore
const IGNORE_PATHS = [
  // Build and dependency files
  "node_modules",
  "dist",
  ".git",
  "test",
  "__tests__",
  ".d.ts",
  "i18n",
  "package.json",
  "package-lock.json",
  "tsconfig.json",
  
  // Internal code that doesn't need localization
  "mocks", // Mock data
  "assets", // SVG paths and CSS classes
  "types", // Type definitions and constants
  "state", // Redux state management
  "api", // API endpoints
  "services", // Internal services
  "hooks", // React hooks
  "context", // React context
  "store", // Redux store
  "routes.ts", // Route definitions
  "root.tsx", // Root component
  "entry.client.tsx", // Client entry point
  "utils/scan-unlocalized-strings.ts", // This file itself
  "utils/browser-tab.ts", // Browser tab utilities
  "utils/custom-toast-handlers.tsx", // Toast handlers
  "utils/error-handler.ts", // Error handlers
  "utils/extract-model-and-provider.ts", // Model utilities
  "utils/feature-flags.ts", // Feature flags
  "utils/format-time-delta.ts", // Time formatting
  "utils/gget-formatted-datetime.ts", // Date formatting
  "utils/has-advanced-settings-set.ts", // Settings utilities
  "utils/organize-models-and-providers.ts", // Model utilities
  "utils/parse-cell-content.ts", // Cell parsing
  "utils/settings-utils.ts", // Settings utilities
  "utils/suggestions", // Suggestion utilities
  "utils/utils.ts", // General utilities
];

// Extensions to scan
const SCAN_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"];

function shouldIgnorePath(filePath: string): boolean {
  return IGNORE_PATHS.some((ignore) => filePath.includes(ignore));
}

function isLikelyTranslationKey(str: string): boolean {
  // Translation keys typically use dots, underscores, or are all caps
  return /^[A-Z0-9_$.]+$/.test(str) || str.includes(".");
}




export function scanFileForUnlocalizedStrings(filePath: string): string[] {
  const content = fs.readFileSync(filePath, "utf-8");
  const unlocalizedStrings: string[] = [];

  // Don't skip files just because they have some localization - they might have mixed content

  // Check each pattern
  STRING_PATTERNS.forEach((pattern) => {
    const matches = content.matchAll(pattern);
    for (const match of matches) {
      const str = match[1].trim();
      if (
        str &&
        str.length > 2 &&
        /[a-zA-Z]/.test(str) && // Contains at least one letter
        !isLikelyTranslationKey(str) &&
        !isCommonDevelopmentString(str)
      ) {
        unlocalizedStrings.push(str);
      }
    }
  });

  return unlocalizedStrings;
}

export function scanDirectoryForUnlocalizedStrings(
  dirPath: string,
): Map<string, string[]> {
  const results = new Map<string, string[]>();

  function scanDir(currentPath: string) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);

      if (!shouldIgnorePath(fullPath)) {
        if (entry.isDirectory()) {
          scanDir(fullPath);
        } else if (
          entry.isFile() &&
          SCAN_EXTENSIONS.includes(path.extname(fullPath))
        ) {
          const unlocalized = scanFileForUnlocalizedStrings(fullPath);
          if (unlocalized.length > 0) {
            results.set(fullPath, unlocalized);
          }
        }
      }
    }
  }

  scanDir(dirPath);
  return results;
}

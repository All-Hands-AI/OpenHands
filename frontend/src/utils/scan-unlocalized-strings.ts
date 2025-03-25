import fs from "fs";
import path from "path";

// Patterns that indicate a string might need localization
const STRING_PATTERNS = [
  // Only match strings that are likely to be user-facing text
  // Look for strings with spaces, punctuation, or multiple words
  /['"`]([A-Z][a-z]+([ \t][A-Za-z][a-z]+)+)['"`]/g, // Capitalized phrases with spaces
  /['"`]([A-Za-z][a-z]+([ \t][a-z]+){2,})['"`]/g, // Lowercase phrases with multiple spaces
  /['"`]([^'"`\n]+\?|[^'"`\n]+\.|[^'"`\n]+!)['"`]/g, // Strings ending with punctuation
];

// Patterns that indicate a string is already localized
// eslint-disable-next-line @typescript-eslint/no-unused-vars
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
  "utils/base64-to-blob.ts", // Blob utilities
  "utils/download-json.ts", // JSON download utilities
  "utils/download-trajectory.ts", // Trajectory download utilities
  "utils/format-ms.ts", // Time formatting
  "utils/map-provider.ts", // Provider mapping
  "utils/retrieve-axios-error-message.ts", // Error handling
  "utils/verified-models.ts", // Model verification
  "components/agent-status-map.constant.ts", // Agent status constants
  "components/extension-icon-map.constant.tsx", // Icon mapping
  "components/features/browser", // Browser components
  "components/features/controls", // Control components
  "components/features/terminal", // Terminal components
  "components/features/jupyter", // Jupyter components
  "components/features/file-explorer", // File explorer components
  "components/shared/modals/security", // Security modals
  "components/shared/modals/base-modal", // Base modal components
  "components/shared/inputs", // Input components
  "components/shared/loading-spinner.tsx", // Loading spinner
  "query-client-config.ts", // Query client configuration
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

function isCommonDevelopmentString(str: string): boolean {
  // Common strings that don't need localization
  const commonPatterns = [
    /^https?:\/\//, // URLs
    /^[a-zA-Z0-9]+\.[a-zA-Z0-9]+$/, // File extensions, class names
    /^[a-zA-Z0-9_-]+$/, // Simple identifiers
    /^\d+(\.\d+)?$/, // Numbers
    /^#[0-9a-fA-F]{3,6}$/, // Color codes
    /^@[a-zA-Z0-9/-]+$/, // Import paths
    /^#\/[a-zA-Z0-9/-]+$/, // Alias imports
    /^[a-zA-Z0-9/-]+\/[a-zA-Z0-9/-]+$/, // Module paths
    /^flex(\s+[a-zA-Z0-9-]+)*$/, // Tailwind flex classes
    /^w-(\[[^\]]+\]|\S+)$/, // Tailwind width classes
    /^h-(\[[^\]]+\]|\S+)$/, // Tailwind height classes
    /^p-(\[[^\]]+\]|\S+)$/, // Tailwind padding classes
    /^m-(\[[^\]]+\]|\S+)$/, // Tailwind margin classes
    /^border(\s+[a-zA-Z0-9-]+)*$/, // Tailwind border classes
    /^bg-(\[[^\]]+\]|\S+)$/, // Tailwind background classes
    /^text-(\[[^\]]+\]|\S+)$/, // Tailwind text classes
    /^rounded(\s+[a-zA-Z0-9-]+)*$/, // Tailwind rounded classes
    /^gap-(\[[^\]]+\]|\S+)$/, // Tailwind gap classes
    /^items-(\[[^\]]+\]|\S+)$/, // Tailwind items classes
    /^justify-(\[[^\]]+\]|\S+)$/, // Tailwind justify classes
    /^overflow-(\[[^\]]+\]|\S+)$/, // Tailwind overflow classes
    /^transition(\s+[a-zA-Z0-9-]+)*$/, // Tailwind transition classes
    /^hover:(\S+)$/, // Tailwind hover classes
    /^focus-within:(\S+)$/, // Tailwind focus-within classes
    /^data:image\/[a-zA-Z0-9;,]+$/, // Data URLs
    /^application\/[a-zA-Z0-9-]+$/, // MIME types
    /^mm:ss$/, // Time format
    /^[a-zA-Z0-9]+\/[a-zA-Z0-9-]+$/, // Provider/model format
  ];

  return commonPatterns.some((pattern) => pattern.test(str));
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

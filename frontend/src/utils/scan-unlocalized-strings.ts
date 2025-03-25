import fs from "fs";
import path from "path";

// Patterns that indicate a string might need localization
const STRING_PATTERNS = [
  /['"`]([\w\s?]+)['"`]/g, // Matches quoted strings with words
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
  // Common strings that don't need translation
  const commonPatterns = [
    /^[a-z-]+$/, // CSS classes
    /^[A-Z][a-z]+$/, // Component names
    /^\d+$/, // Numbers
    /^https?:/, // URLs
    /^[<>{}()[\]]+$/, // Syntax characters
    /^[a-z]+:\/\//, // Protocol patterns
    /^#/, // Color codes or anchors
  ];
  return commonPatterns.some((pattern) => pattern.test(str));
}

export function scanFileForUnlocalizedStrings(filePath: string): string[] {
  const content = fs.readFileSync(filePath, "utf-8");
  const unlocalizedStrings: string[] = [];

  // Skip files that are clearly localized
  if (LOCALIZED_PATTERNS.some((pattern) => pattern.test(content))) {
    return [];
  }

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

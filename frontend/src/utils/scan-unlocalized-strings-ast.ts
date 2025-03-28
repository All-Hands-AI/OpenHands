import fs from "fs";
import nodePath from "path";
import * as parser from "@babel/parser";
import traverse from "@babel/traverse";
import type { NodePath } from "@babel/traverse";
import * as t from "@babel/types";

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
  "utils/scan-unlocalized-strings.ts", // Original scanner
  "utils/scan-unlocalized-strings-ast.ts", // This file itself
];

// Extensions to scan
const SCAN_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"];

// Attributes that typically don't contain user-facing text
const NON_TEXT_ATTRIBUTES = [
  "className",
  "testId",
  "id",
  "name",
  "type",
  "href",
  "src",
  "alt",
  "placeholder",
  "rel",
  "target",
  "style",
  "onClick",
  "onChange",
  "onSubmit",
  "data-testid",
  "aria-label",
  "aria-labelledby",
  "aria-describedby",
  "aria-hidden",
  "role",
];

function shouldIgnorePath(filePath: string): boolean {
  return IGNORE_PATHS.some((ignore) => filePath.includes(ignore));
}

// Check if a string looks like a translation key
// Translation keys typically use dots, underscores, or are all caps
// Also check for the pattern with $ which is used in our translation keys
function isLikelyTranslationKey(str: string): boolean {
  return (
    /^[A-Z0-9_$.]+$/.test(str) ||
    str.includes(".") ||
    /[A-Z0-9_]+\$[A-Z0-9_]+/.test(str)
  );
}

// Check if a string is a raw translation key that should be wrapped in t()
function isRawTranslationKey(str: string): boolean {
  // Check for our specific translation key pattern (e.g., "SETTINGS$GITHUB_SETTINGS")
  // Exclude specific keys that are already properly used with i18next.t() in the code
  const excludedKeys = [
    "STATUS$ERROR_LLM_OUT_OF_CREDITS",
    "ERROR$GENERIC",
    "GITHUB$AUTH_SCOPE",
  ];

  if (excludedKeys.includes(str)) {
    return false;
  }

  return /^[A-Z0-9_]+\$[A-Z0-9_]+$/.test(str);
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
    /^!\[image]\(data:image\/png;base64,$/, // Markdown image with base64 data
    /^\?notification$/, // URL parameter for notifications
  ];

  // Skip provider names and file type descriptions
  if (
    str === "JSON File" ||
    str === "Azure AI Studio" ||
    str === "AWS SageMaker" ||
    str === "AWS Bedrock" ||
    str === "Mistral AI" ||
    str === "Perplexity AI" ||
    str === "Fireworks AI" ||
    str === "Cloudflare Workers AI" ||
    str === "Voyage AI" ||
    str.includes("AI") ||
    str.includes("OpenAI") ||
    str.includes("VertexAI") ||
    str.includes("PaLM") ||
    str.includes("Gemini") ||
    str.includes("Anthropic") ||
    str.includes("Anyscale") ||
    str.includes("Databricks") ||
    str.includes("Ollama") ||
    str.includes("FriendliAI") ||
    str.includes("Groq") ||
    str.includes("DeepInfra") ||
    str.includes("AI21") ||
    str.includes("Replicate") ||
    str.includes("OpenRouter") ||
    str.includes("claude-") ||
    str.includes("gpt-") ||
    str.includes("o1-") ||
    str.includes("o3-") ||
    // File extensions and paths
    str === ".png" ||
    str === ".jpg" ||
    str === ".jpeg" ||
    str === ".bmp" ||
    str === ".gif" ||
    str === ".pdf" ||
    str === ".mp4" ||
    str === ".webm" ||
    str === ".ogg" ||
    str === "/beep.wav"
  ) {
    return true;
  }

  // Check if the string is a CSS class or style
  if (
    // CSS units
    str.includes("px") ||
    str.includes("rem") ||
    str.includes("em") ||
    str.includes("vh") ||
    str.includes("vw") ||
    str.includes("vmin") ||
    str.includes("vmax") ||
    str.includes("ch") ||
    str.includes("ex") ||
    str.includes("fr") ||
    str.includes("deg") ||
    str.includes("rad") ||
    str.includes("turn") ||
    str.includes("grad") ||
    str.includes("ms") ||
    str.includes("s") ||
    // CSS values
    str.includes("#") || // Color codes
    str.includes("rgb") ||
    str.includes("rgba") ||
    str.includes("hsl") ||
    str.includes("hsla") ||
    // Tailwind classes
    str.includes("border") ||
    str.includes("rounded") ||
    str.includes("flex") ||
    str.includes("grid") ||
    str.includes("transition") ||
    str.includes("duration") ||
    str.includes("ease") ||
    str.includes("hover:") ||
    str.includes("focus:") ||
    str.includes("active:") ||
    str.includes("disabled:") ||
    str.includes("placeholder:") ||
    str.includes("text-") ||
    str.includes("bg-") ||
    str.includes("w-") ||
    str.includes("h-") ||
    str.includes("p-") ||
    str.includes("m-") ||
    str.includes("gap-") ||
    str.includes("items-") ||
    str.includes("justify-") ||
    str.includes("self-") ||
    str.includes("overflow-") ||
    str.includes("cursor-") ||
    str.includes("opacity-") ||
    str.includes("z-") ||
    str.includes("top-") ||
    str.includes("right-") ||
    str.includes("bottom-") ||
    str.includes("left-") ||
    str.includes("inset-") ||
    str.includes("font-") ||
    str.includes("tracking-") ||
    str.includes("leading-") ||
    str.includes("whitespace-") ||
    str.includes("break-") ||
    str.includes("truncate") ||
    str.includes("shadow-") ||
    str.includes("ring-") ||
    str.includes("outline-") ||
    str.includes("animate-") ||
    str.includes("transform") ||
    str.includes("rotate-") ||
    str.includes("scale-") ||
    str.includes("skew-") ||
    str.includes("translate-") ||
    str.includes("origin-") ||
    str.includes("first-of-type:") ||
    str.includes("last-of-type:") ||
    str.includes("group-data-") ||
    str.includes("max-") ||
    str.includes("min-") ||
    str.includes("px-") ||
    str.includes("py-") ||
    str.includes("mx-") ||
    str.includes("my-") ||
    str.includes("grow") ||
    str.includes("shrink") ||
    str.includes("resize-") ||
    str.includes("underline") ||
    str.includes("italic") ||
    str.includes("normal") ||
    // CSS properties
    str.includes("solid") ||
    str.includes("absolute") ||
    str.includes("relative") ||
    str.includes("sticky") ||
    str.includes("fixed") ||
    str.includes("static") ||
    // Common CSS class patterns
    /^[a-z0-9-]+(\s+[a-z0-9-]+)*$/.test(str) // CSS classes are typically lowercase with hyphens
  ) {
    return true;
  }

  return commonPatterns.some((pattern) => pattern.test(str));
}

function isLikelyUserFacingText(str: string): boolean {
  if (!str || str.length <= 2 || !/[a-zA-Z]/.test(str)) {
    return false;
  }

  // Check if it's a raw translation key that should be wrapped in t()
  if (isRawTranslationKey(str)) {
    return true;
  }

  // Check if it's a translation key pattern (e.g., "SETTINGS$BASE_URL")
  // These should be wrapped in t() or use I18nKey enum
  if (isLikelyTranslationKey(str) && /^[A-Z0-9_]+\$[A-Z0-9_]+$/.test(str)) {
    return true;
  }

  if (isCommonDevelopmentString(str)) {
    return false;
  }

  // Special case for known UI strings that should be localized
  const knownUIStrings = [
    "GitHub Settings",
    "API Key",
    "Base URL",
    "Agent",
    "Settings",
    "Advanced",
    "Enable confirmation mode",
    "Enable memory condensation",
    "GitHub Token",
    "Configure GitHub Repositories",
    "Save Changes",
    "JSON File",
    "Azure AI Studio",
    "AWS SageMaker",
    "AWS Bedrock",
    "Mistral AI",
    "Perplexity AI",
    "Fireworks AI",
    "Cloudflare Workers AI",
    "Voyage AI",
    "Beta",
    "documentation",
    "Language",
    "GitHub",
    "Sound Notifications",
    "Created",
    "ago",
    "and use the VS Code link to upload and download your code",
  ];

  if (knownUIStrings.includes(str)) {
    return true;
  }

  // Check if it's likely user-facing text
  // 1. Contains multiple words with spaces
  // 2. Contains punctuation like question marks, periods, or exclamation marks
  // 3. Starts with a capital letter and has multiple words
  const hasMultipleWords = /\s+/.test(str) && str.split(/\s+/).length > 1;
  const hasPunctuation = /[?!.]/.test(str);
  const isCapitalizedPhrase = /^[A-Z]/.test(str) && hasMultipleWords;

  // Additional check for "Title Case" phrases (multiple words with capital letters)
  const isTitleCase = hasMultipleWords && /\s[A-Z]/.test(str);

  // Check for product names (often have capital letters in the middle)
  const hasInternalCapitals = /[a-z][A-Z]/.test(str);

  // Check for UI element text (buttons, labels, etc.)
  const isUIElementText =
    /^(Save|Cancel|Submit|Delete|Add|Edit|Remove|Update|Create|View|Download|Upload|Login|Logout|Sign In|Sign Out|Register|Search|Filter|Sort|Next|Previous|Back|Continue|Finish|Done|Apply|Reset|Clear|Close|Open|Show|Hide|Enable|Disable)(\s+\w+)*$/.test(
      str,
    );

  return (
    hasMultipleWords ||
    hasPunctuation ||
    isCapitalizedPhrase ||
    isTitleCase ||
    hasInternalCapitals ||
    isUIElementText
  );
}

function isTranslationCall(node: t.Node): boolean {
  // Check for t('KEY') pattern
  if (
    t.isCallExpression(node) &&
    t.isIdentifier(node.callee) &&
    node.callee.name === "t" &&
    node.arguments.length > 0
  ) {
    // Check if using raw string instead of I18nKey enum
    if (t.isStringLiteral(node.arguments[0])) {
      const key = node.arguments[0].value;
      if (isRawTranslationKey(key)) {
        // This is a raw translation key passed to t() - should use I18nKey enum
        return false;
      }
    }
    return true;
  }

  // Check for useTranslation() pattern
  if (
    t.isCallExpression(node) &&
    t.isIdentifier(node.callee) &&
    node.callee.name === "useTranslation"
  ) {
    return true;
  }

  // Check for <Trans> component
  if (
    t.isJSXElement(node) &&
    t.isJSXIdentifier(node.openingElement.name) &&
    node.openingElement.name.name === "Trans"
  ) {
    return true;
  }

  return false;
}

function isInTranslationContext(currentNodePath: NodePath<t.Node>): boolean {
  let current: NodePath<t.Node> | null = currentNodePath;

  while (current) {
    if (isTranslationCall(current.node)) {
      return true;
    }
    current = current.parentPath;
  }

  return false;
}

export function scanFileForUnlocalizedStrings(filePath: string): string[] {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const unlocalizedStrings: string[] = [];

    // Skip files that are too large
    if (content.length > 1000000) {
      // eslint-disable-next-line no-console
      console.warn(`Skipping large file: ${filePath}`);
      return [];
    }

    // Check if file is using translations
    // We could use this to optimize scanning, but currently not used
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const hasTranslationImport =
      content.includes("useTranslation") ||
      content.includes("I18nKey") ||
      content.includes("<Trans");

    try {
      // Parse the file
      const ast = parser.parse(content, {
        sourceType: "module",
        plugins: ["jsx", "typescript", "classProperties", "decorators-legacy"],
      });

      // Traverse the AST
      traverse(ast, {
        // Find JSX text content
        JSXText(jsxTextPath) {
          const text = jsxTextPath.node.value.trim();
          if (
            text &&
            isLikelyUserFacingText(text) &&
            !isInTranslationContext(jsxTextPath)
          ) {
            unlocalizedStrings.push(text);
          }
        },

        // Find string literals in JSX attributes
        JSXAttribute(jsxAttrPath) {
          const attrName = jsxAttrPath.node.name.name.toString();

          // Skip attributes that typically don't contain user-facing text
          if (NON_TEXT_ATTRIBUTES.includes(attrName)) {
            return;
          }

          // Skip className attributes as they contain CSS classes
          if (attrName === "className" || attrName === "class") {
            return;
          }

          // Skip style attributes
          if (attrName === "style") {
            return;
          }

          // Skip data-* attributes
          if (attrName.startsWith("data-")) {
            return;
          }

          // Skip event handler attributes
          if (attrName.startsWith("on")) {
            return;
          }

          // Check the attribute value
          const { value } = jsxAttrPath.node;
          if (t.isStringLiteral(value)) {
            const text = value.value.trim();
            if (
              text &&
              isLikelyUserFacingText(text) &&
              !isInTranslationContext(jsxAttrPath)
            ) {
              unlocalizedStrings.push(text);
            }
          }

          // Check for JSX expressions that might contain t() calls with raw strings
          if (t.isJSXExpressionContainer(value)) {
            if (
              t.isCallExpression(value.expression) &&
              t.isIdentifier(value.expression.callee) &&
              value.expression.callee.name === "t" &&
              value.expression.arguments.length > 0 &&
              t.isStringLiteral(value.expression.arguments[0])
            ) {
              const key = value.expression.arguments[0].value;
              // Check if it's a raw translation key pattern (e.g., "SETTINGS$BASE_URL")
              if (/^[A-Z0-9_]+\$[A-Z0-9_]+$/.test(key)) {
                unlocalizedStrings.push(key);
              }
            }
          }
        },

        // Find string literals
        StringLiteral(strLiteralPath) {
          // Skip if parent is a JSX attribute (handled separately)
          if (t.isJSXAttribute(strLiteralPath.parent)) {
            return;
          }

          // Skip if it's part of an import statement
          if (
            t.isImportDeclaration(strLiteralPath.parent) ||
            t.isExportDeclaration(strLiteralPath.parent)
          ) {
            return;
          }

          const text = strLiteralPath.node.value.trim();
          if (
            text &&
            isLikelyUserFacingText(text) &&
            !isInTranslationContext(strLiteralPath)
          ) {
            unlocalizedStrings.push(text);
          }
        },

        // Find template literals
        TemplateLiteral(templatePath) {
          // Skip if it's a tagged template literal
          if (t.isTaggedTemplateExpression(templatePath.parent)) {
            return;
          }

          // Get the full template string if it's simple
          if (templatePath.node.quasis.length === 1) {
            const text = templatePath.node.quasis[0].value.raw.trim();
            if (
              text &&
              isLikelyUserFacingText(text) &&
              !isInTranslationContext(templatePath)
            ) {
              unlocalizedStrings.push(text);
            }
          }
        },
      });
    } catch (error) {
      // If parsing fails, fall back to regex-based scanning
      // eslint-disable-next-line no-console
      console.warn(
        `Failed to parse ${filePath}, falling back to regex scanning: ${error}`,
      );

      // Simple regex to find potential text strings
      const stringRegex = /['"`]([^'"`\n]{3,})['"`]/g;
      const jsxTextRegex = />([\s]*[A-Za-z][\w\s.,!?]+)[\s]*</g;

      let match: RegExpExecArray | null;

      // Find string literals
      // eslint-disable-next-line no-cond-assign
      while ((match = stringRegex.exec(content)) !== null) {
        const text = match[1].trim();
        if (text && isLikelyUserFacingText(text)) {
          unlocalizedStrings.push(text);
        }
      }

      // Find JSX text content
      // eslint-disable-next-line no-cond-assign
      while ((match = jsxTextRegex.exec(content)) !== null) {
        const text = match[1].trim();
        if (text && isLikelyUserFacingText(text)) {
          unlocalizedStrings.push(text);
        }
      }
    }

    // Filter out duplicates
    return [...new Set(unlocalizedStrings)];
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(`Error scanning file ${filePath}:`, error);
    return [];
  }
}

export function scanDirectoryForUnlocalizedStrings(
  dirPath: string,
): Map<string, string[]> {
  const results = new Map<string, string[]>();

  function scanDir(currentPath: string) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = nodePath.join(currentPath, entry.name);

      if (!shouldIgnorePath(fullPath)) {
        if (entry.isDirectory()) {
          scanDir(fullPath);
        } else if (
          entry.isFile() &&
          SCAN_EXTENSIONS.includes(nodePath.extname(fullPath))
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

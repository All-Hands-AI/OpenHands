import fs from "fs";
import nodePath from "path";
import * as parser from "@babel/parser";
import * as _traverse from "@babel/traverse";
import type { NodePath } from "@babel/traverse";
import * as t from "@babel/types";

// Fix for ESM/CJS compatibility
// @ts-expect-error - This is a workaround for ESM/CJS compatibility
const traverse = (_traverse as unknown).default || _traverse;

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
  "utils/scan-unlocalized-strings-new.ts", // This file
  "utils/scan-unlocalized-strings-ast.ts", // AST scanner
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
    /^noopener noreferrer$/, // Common rel attribute values
    /^noreferrer noopener$/, // Common rel attribute values
    /^cursor-(\[[^\]]+\]|\S+)$/, // Tailwind cursor classes
    /^absolute$/, // CSS position
    /^relative$/, // CSS position
    /^sticky$/, // CSS position
    /^fixed$/, // CSS position
    /^animate-(\[[^\]]+\]|\S+)$/, // Animation classes
    /^opacity-(\[[^\]]+\]|\S+)$/, // Opacity classes
    /^disabled:(\S+)$/, // Disabled state classes
    /^first-of-type:(\S+)$/, // First of type classes
    /^last-of-type:(\S+)$/, // Last of type classes
    /^group-data-\[[^\]]+\]:(\S+)$/, // Group data classes
    /^placeholder:(\S+)$/, // Placeholder classes
    /^self-(\[[^\]]+\]|\S+)$/, // Self classes
    /^max-[wh]-(\[[^\]]+\]|\S+)$/, // Max width/height classes
    /^min-[wh]-(\[[^\]]+\]|\S+)$/, // Min width/height classes
    /^px-(\[[^\]]+\]|\S+)$/, // Padding x classes
    /^py-(\[[^\]]+\]|\S+)$/, // Padding y classes
    /^mx-(\[[^\]]+\]|\S+)$/, // Margin x classes
    /^my-(\[[^\]]+\]|\S+)$/, // Margin y classes
    /^top-(\[[^\]]+\]|\S+)$/, // Top classes
    /^right-(\[[^\]]+\]|\S+)$/, // Right classes
    /^bottom-(\[[^\]]+\]|\S+)$/, // Bottom classes
    /^left-(\[[^\]]+\]|\S+)$/, // Left classes
    /^z-(\[[^\]]+\]|\S+)$/, // Z-index classes
    /^font-(\[[^\]]+\]|\S+)$/, // Font classes
    /^leading-(\[[^\]]+\]|\S+)$/, // Line height classes
    /^tracking-(\[[^\]]+\]|\S+)$/, // Letter spacing classes
    /^underline(\s+[a-zA-Z0-9-]+)*$/, // Underline classes
    /^italic$/, // Italic class
    /^normal$/, // Normal class
    /^duration-(\[[^\]]+\]|\S+)$/, // Duration classes
    /^ease-(\[[^\]]+\]|\S+)$/, // Easing classes
    /^ring-(\[[^\]]+\]|\S+)$/, // Ring classes
    /^outline-(\[[^\]]+\]|\S+)$/, // Outline classes
    /^resize-(\[[^\]]+\]|\S+)$/, // Resize classes
    /^grow$/, // Grow class
    /^grow-(\[[^\]]+\]|\S+)$/, // Grow classes
    /^shrink$/, // Shrink class
    /^shrink-(\[[^\]]+\]|\S+)$/, // Shrink classes
    /^[0-9]+px(\s+[a-zA-Z0-9-]+)*$/, // Pixel dimensions
    /^[0-9]+rem(\s+[a-zA-Z0-9-]+)*$/, // Rem dimensions
    /^[0-9]+em(\s+[a-zA-Z0-9-]+)*$/, // Em dimensions
    /^[0-9]+%(\s+[a-zA-Z0-9-]+)*$/, // Percentage dimensions
    /^[0-9]+vh(\s+[a-zA-Z0-9-]+)*$/, // Viewport height dimensions
    /^[0-9]+vw(\s+[a-zA-Z0-9-]+)*$/, // Viewport width dimensions
    /^[0-9]+fr(\s+[a-zA-Z0-9-]+)*$/, // Grid fraction dimensions
    /^[0-9]+ch(\s+[a-zA-Z0-9-]+)*$/, // Character dimensions
    /^[0-9]+ex(\s+[a-zA-Z0-9-]+)*$/, // Ex dimensions
    /^[0-9]+vmin(\s+[a-zA-Z0-9-]+)*$/, // Viewport min dimensions
    /^[0-9]+vmax(\s+[a-zA-Z0-9-]+)*$/, // Viewport max dimensions
    /^[0-9]+s(\s+[a-zA-Z0-9-]+)*$/, // Seconds
    /^[0-9]+ms(\s+[a-zA-Z0-9-]+)*$/, // Milliseconds
    /^[0-9]+deg(\s+[a-zA-Z0-9-]+)*$/, // Degrees
    /^[0-9]+rad(\s+[a-zA-Z0-9-]+)*$/, // Radians
    /^[0-9]+turn(\s+[a-zA-Z0-9-]+)*$/, // Turns
    /^[0-9]+grad(\s+[a-zA-Z0-9-]+)*$/, // Gradians
    /^[0-9]+dpi(\s+[a-zA-Z0-9-]+)*$/, // DPI
    /^[0-9]+dpcm(\s+[a-zA-Z0-9-]+)*$/, // DPCM
    /^[0-9]+dppx(\s+[a-zA-Z0-9-]+)*$/, // DPPX
    /^[0-9]+x(\s+[a-zA-Z0-9-]+)*$/, // X
    /^[0-9]+x[0-9]+$/, // Dimensions like 2x4
    /^[0-9]+:[0-9]+$/, // Ratios like 16:9
    /^[0-9]+\/[0-9]+$/, // Fractions like 1/2
    /^[0-9]+\+[0-9]+$/, // Additions like 1+2
    /^[0-9]+-[0-9]+$/, // Ranges like 1-2
    /^[0-9]+\*[0-9]+$/, // Multiplications like 1*2
    /^[0-9]+\^[0-9]+$/, // Powers like 1^2
    /^[0-9]+\([0-9]+\)$/, // Function calls like 1(2)
    /^[0-9]+\[[0-9]+\]$/, // Array accesses like 1[2]
    /^[0-9]+\{[0-9]+\}$/, // Object accesses like 1{2}
    /^[0-9]+\([a-zA-Z0-9]+\)$/, // Function calls like 1(a)
    /^[0-9]+\[[a-zA-Z0-9]+\]$/, // Array accesses like 1[a]
    /^[0-9]+\{[a-zA-Z0-9]+\}$/, // Object accesses like 1{a}
    /^[a-zA-Z0-9]+\([0-9]+\)$/, // Function calls like a(2)
    /^[a-zA-Z0-9]+\[[0-9]+\]$/, // Array accesses like a[2]
    /^[a-zA-Z0-9]+\{[0-9]+\}$/, // Object accesses like a{2}
    /^[a-zA-Z0-9]+\([a-zA-Z0-9]+\)$/, // Function calls like a(b)
    /^[a-zA-Z0-9]+\[[a-zA-Z0-9]+\]$/, // Array accesses like a[b]
    /^[a-zA-Z0-9]+\{[a-zA-Z0-9]+\}$/, // Object accesses like a{b}
    /^[0-9]+x\s+\([0-9]+\s+core,\s+[0-9]+G\)$/, // Runtime options like "1x (2 core, 8G)"
    /^JSON File$/, // File type labels
    /^!\[image\]\(data:image\/png;base64,$/, // Image data URLs
    /^\?notification$/, // URL parameters
  ];

  return commonPatterns.some((pattern) => pattern.test(str));
}

function isLikelyUserFacingText(str: string): boolean {
  if (!str || str.length <= 2 || !/[a-zA-Z]/.test(str)) {
    return false;
  }

  if (isLikelyTranslationKey(str) || isCommonDevelopmentString(str)) {
    return false;
  }

  // Check if it's likely user-facing text
  // 1. Contains multiple words with spaces
  // 2. Contains punctuation like question marks, periods, or exclamation marks
  // 3. Starts with a capital letter and has multiple words
  const hasMultipleWords = /\s+/.test(str) && str.split(/\s+/).length > 1;
  const hasPunctuation = /[?!.]/.test(str);
  const isCapitalizedPhrase = /^[A-Z]/.test(str) && hasMultipleWords;

  return hasMultipleWords || hasPunctuation || isCapitalizedPhrase;
}

function isTranslationCall(node: t.Node): boolean {
  // Check for t('KEY') pattern
  if (
    t.isCallExpression(node) &&
    t.isIdentifier(node.callee) &&
    node.callee.name === "t" &&
    node.arguments.length > 0
  ) {
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

    try {
      // Parse the file
      const ast = parser.parse(content, {
        sourceType: "module",
        plugins: ["jsx", "typescript", "classProperties", "decorators-legacy"],
      });

      // Traverse the AST
      traverse(ast, {
        // Find JSX text content
        JSXText(jsxTextPath: NodePath<t.JSXText>) {
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
        JSXAttribute(jsxAttrPath: NodePath<t.JSXAttribute>) {
          const attrName = jsxAttrPath.node.name.name.toString();

          // Skip attributes that typically don't contain user-facing text
          if (NON_TEXT_ATTRIBUTES.includes(attrName)) {
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
        },

        // Find string literals
        StringLiteral(strLiteralPath: NodePath<t.StringLiteral>) {
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
        TemplateLiteral(templatePath: NodePath<t.TemplateLiteral>) {
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

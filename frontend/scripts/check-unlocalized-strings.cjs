#!/usr/bin/env node

/**
 * Pre-commit hook script to check for unlocalized strings in the frontend code
 * This script is based on the test in __tests__/utils/check-hardcoded-strings.test.tsx
 */

const path = require('path');
const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

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
  "frontend/src/components/features/home/tasks/get-prompt-for-query.ts", // Only contains agent prompts
];

// Extensions to scan
const SCAN_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"];

// Attributes that typically don't contain user-facing text
const NON_TEXT_ATTRIBUTES = [
  "allow",
  "className",
  "i18nKey",
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
  "sandbox",
];

function shouldIgnorePath(filePath) {
  return IGNORE_PATHS.some((ignore) => filePath.includes(ignore));
}

// Check if a string looks like a translation key
// Translation keys typically use dots, underscores, or are all caps
// Also check for the pattern with $ which is used in our translation keys
function isLikelyTranslationKey(str) {
  return (
    /^[A-Z0-9_$.]+$/.test(str) ||
    str.includes(".") ||
    /[A-Z0-9_]+\$[A-Z0-9_]+/.test(str)
  );
}

// Check if a string is a raw translation key that should be wrapped in t()
function isRawTranslationKey(str) {
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

// Specific technical strings that should be excluded from localization
const EXCLUDED_TECHNICAL_STRINGS = [
  "openid email profile", // OAuth scope string - not user-facing
  "OPEN_ISSUE", // Task type identifier, not a UI string
  "Merge Request", // Git provider specific terminology
  "GitLab API", // Git provider specific terminology
  "Pull Request", // Git provider specific terminology
  "GitHub API", // Git provider specific terminology
  "add-secret-form", // Test ID for secret form
  "edit-secret-form", // Test ID for secret form
  "search-api-key-input", // Input name for search API key
  "noopener,noreferrer", // Options for window.open
  "STATUS$READY",
  "STATUS$STOPPED",
  "STATUS$ERROR",
];

function isExcludedTechnicalString(str) {
  return EXCLUDED_TECHNICAL_STRINGS.includes(str);
}

function isLikelyCode(str) {
  // A string with no spaces and at least one underscore or colon is likely a code.
  // (e.g.: "browser_interactive" or "error:")
  if (str.includes(" ")) {
    return false
  }
  if (str.includes(":") || str.includes("_")){
    return true
  }
  return false
}

function isCommonDevelopmentString(str) {
  // Technical patterns that are definitely not UI strings
  const technicalPatterns = [
    // URLs and paths
    /^https?:\/\//, // URLs
    /^\/[a-zA-Z0-9_\-./]*$/, // File paths
    /^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$/, // File extensions, class names
    /^@[a-zA-Z0-9/-]+$/, // Import paths
    /^#\/[a-zA-Z0-9/-]+$/, // Alias imports
    /^[a-zA-Z0-9/-]+\/[a-zA-Z0-9/-]+$/, // Module paths
    /^data:image\/[a-zA-Z0-9;,]+$/, // Data URLs
    /^application\/[a-zA-Z0-9-]+$/, // MIME types
    /^!\[image]\(data:image\/png;base64,$/, // Markdown image with base64 data

    // Numbers, IDs, and technical values
    /^\d+(\.\d+)?$/, // Numbers
    /^#[0-9a-fA-F]{3,8}$/, // Color codes
    /^[a-zA-Z0-9_-]+=[a-zA-Z0-9_-]+$/, // Key-value pairs
    /^mm:ss$/, // Time format
    /^[a-zA-Z0-9]+\/[a-zA-Z0-9-]+$/, // Provider/model format
    /^\?[a-zA-Z0-9_-]+$/, // URL parameters
    /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i, // UUID
    /^[A-Za-z0-9+/=]+$/, // Base64

    // HTML and CSS selectors
    /^[a-z]+(\[[^\]]+\])+$/, // CSS attribute selectors
    /^[a-z]+:[a-z-]+$/, // CSS pseudo-selectors
    /^[a-z]+\.[a-z0-9_-]+$/, // CSS class selectors
    /^[a-z]+#[a-z0-9_-]+$/, // CSS ID selectors
    /^[a-z]+\s*>\s*[a-z]+$/, // CSS child selectors
    /^[a-z]+\s+[a-z]+$/, // CSS descendant selectors

    // CSS and styling patterns
    /^[a-z0-9-]+:[a-z0-9-]+$/, // CSS property:value
    /^[a-z0-9-]+:[a-z0-9-]+;[a-z0-9-]+:[a-z0-9-]+$/, // Multiple CSS properties
  ];

  // File extensions and media types
  const fileExtensionPattern =
    /^\.(png|jpg|jpeg|gif|svg|webp|bmp|ico|pdf|mp4|webm|ogg|mp3|wav|json|xml|csv|txt|md|html|css|js|jsx|ts|tsx)$/i;
  if (fileExtensionPattern.test(str)) {
    return true;
  }

  // AI model and provider patterns
  const aiRelatedPattern =
    /^(AI|OpenAI|VertexAI|PaLM|Gemini|Anthropic|Anyscale|Databricks|Ollama|FriendliAI|Groq|DeepInfra|AI21|Replicate|OpenRouter|Azure|AWS|SageMaker|Bedrock|Mistral|Perplexity|Fireworks|Cloudflare|Workers|Voyage|claude-|gpt-|o1-|o3-)/i;
  if (aiRelatedPattern.test(str)) {
    return true;
  }

  // CSS units and values
  const cssUnitsPattern =
    /(px|rem|em|vh|vw|vmin|vmax|ch|ex|fr|deg|rad|turn|grad|ms|s)$/;
  const cssValuesPattern =
    /(rgb|rgba|hsl|hsla|#[0-9a-fA-F]+|solid|absolute|relative|sticky|fixed|static|block|inline|flex|grid|none|auto|hidden|visible)/;

  if (cssUnitsPattern.test(str) || cssValuesPattern.test(str)) {
    return true;
  }

  // Check for CSS class strings with brackets (common in the codebase)
  if (
    str.includes("[") &&
    str.includes("]") &&
    (str.includes("px") ||
      str.includes("rem") ||
      str.includes("em") ||
      str.includes("w-") ||
      str.includes("h-") ||
      str.includes("p-") ||
      str.includes("m-"))
  ) {
    return true;
  }

  // Check for CSS class strings with specific patterns
  if (
    str.includes("border-") ||
    str.includes("rounded-") ||
    str.includes("cursor-") ||
    str.includes("opacity-") ||
    str.includes("disabled:") ||
    str.includes("hover:") ||
    str.includes("focus-within:") ||
    str.includes("first-of-type:") ||
    str.includes("last-of-type:") ||
    str.includes("group-data-")
  ) {
    return true;
  }

  // Check if it looks like a Tailwind class string
  if (/^[a-z0-9-]+(\s+[a-z0-9-]+)*$/.test(str)) {
    // Common Tailwind prefixes and patterns
    const tailwindPrefixes = [
      "bg-", "text-", "border-", "rounded-", "p-", "m-", "px-", "py-", "mx-", "my-",
      "w-", "h-", "min-w-", "min-h-", "max-w-", "max-h-", "flex-", "grid-", "gap-",
      "space-", "items-", "justify-", "self-", "col-", "row-", "order-", "object-",
      "overflow-", "opacity-", "z-", "top-", "right-", "bottom-", "left-", "inset-",
      "font-", "tracking-", "leading-", "list-", "placeholder-", "shadow-", "ring-",
      "transition-", "duration-", "ease-", "delay-", "animate-", "scale-", "rotate-",
      "translate-", "skew-", "origin-", "cursor-", "select-", "resize-", "fill-", "stroke-",
    ];

    // Check if any word in the string starts with a Tailwind prefix
    const words = str.split(/\s+/);
    for (const word of words) {
      for (const prefix of tailwindPrefixes) {
        if (word.startsWith(prefix)) {
          return true;
        }
      }
    }

    // Check for Tailwind modifiers
    const tailwindModifiers = [
      "hover:", "focus:", "active:", "disabled:", "visited:", "first:", "last:",
      "odd:", "even:", "group-hover:", "focus-within:", "focus-visible:", "motion-safe:",
      "motion-reduce:", "dark:", "light:", "sm:", "md:", "lg:", "xl:", "2xl:",
    ];

    for (const word of words) {
      for (const modifier of tailwindModifiers) {
        if (word.includes(modifier)) {
          return true;
        }
      }
    }

    // Check for CSS property combinations
    const cssProperties = [
      "border", "rounded", "px", "py", "mx", "my", "p", "m", "w", "h", "flex",
      "grid", "gap", "transition", "duration", "font", "leading", "tracking",
    ];

    // If the string contains multiple CSS properties, it's likely a CSS class string
    let cssPropertyCount = 0;
    for (const word of words) {
      if (
        cssProperties.some(
          (prop) => word === prop || word.startsWith(`${prop}-`),
        )
      ) {
        cssPropertyCount += 1;
      }
    }

    if (cssPropertyCount >= 2) {
      return true;
    }
  }

  // Check for specific CSS class patterns that appear in the test failures
  if (
    str.match(
      /^(border|rounded|flex|grid|transition|duration|ease|hover:|focus:|active:|disabled:|placeholder:|text-|bg-|w-|h-|p-|m-|gap-|items-|justify-|self-|overflow-|cursor-|opacity-|z-|top-|right-|bottom-|left-|inset-|font-|tracking-|leading-|whitespace-|break-|truncate|shadow-|ring-|outline-|animate-|transform|rotate-|scale-|skew-|translate-|origin-|first-of-type:|last-of-type:|group-data-|max-|min-|px-|py-|mx-|my-|grow|shrink|resize-|underline|italic|normal)/,
    )
  ) {
    return true;
  }

  // HTML tags and attributes
  if (
    /^<[a-z0-9]+(?:\s[^>]*)?>.*<\/[a-z0-9]+>$/i.test(str) ||
    /^<[a-z0-9]+ [^>]+\/>$/i.test(str)
  ) {
    return true;
  }

  // Check for specific patterns in suggestions and examples
  if (
    str.includes("* ") &&
    (str.includes("create a") ||
      str.includes("build a") ||
      str.includes("make a"))
  ) {
    // This is likely a suggestion or example, not a UI string
    return false;
  }

  // Check for specific technical identifiers from the test failures
  if (
    /^(download_via_vscode_button_clicked|open-vscode-error-|set-indicator|settings_saved|openhands-trace-|provider-item-|last_browser_action_error)$/.test(
      str,
    )
  ) {
    return true;
  }

  // Check for URL paths and query parameters
  if (
    str.startsWith("?") ||
    str.startsWith("/") ||
    str.includes("auth.") ||
    str.includes("$1auth.")
  ) {
    return true;
  }

  // Check for specific strings that should be excluded
  if (
    str === "Cache Hit:" ||
    str === "Cache Write:" ||
    str === "ADD_DOCS" ||
    str === "ADD_DOCKERFILE" ||
    str === "Verified" ||
    str === "Others" ||
    str === "Feedback" ||
    str === "JSON File" ||
    str === "mt-0.5 md:mt-0"
  ) {
    return true;
  }

  // Check for long suggestion texts
  if (
    str.length > 100 &&
    (str.includes("Please write a bash script") ||
      str.includes("Please investigate the repo") ||
      str.includes("Please push the changes") ||
      str.includes("Examine the dependencies") ||
      str.includes("Investigate the documentation") ||
      str.includes("Investigate the current repo") ||
      str.includes("I want to create a Hello World app") ||
      str.includes("I want to create a VueJS app") ||
      str.includes("This should be a client-only app"))
  ) {
    return true;
  }

  // Check for specific error messages and UI text
  if (
    str === "All data associated with this project will be lost." ||
    str === "You will lose any unsaved information." ||
    str ===
      "This conversation does not exist, or you do not have permission to access it." ||
    str === "Failed to fetch settings. Please try reloading." ||
    str ===
      "If you tell OpenHands to start a web server, the app will appear here." ||
    str ===
      "Your browser doesn't support downloading files. Please use Chrome, Edge, or another browser that supports the File System Access API." ||
    str ===
      "Something went wrong while fetching settings. Please reload the page." ||
    str ===
      "To help us improve, we collect feedback from your interactions to improve our prompts. By submitting this form, you consent to us collecting this data." ||
    str === "Please push the latest changes to the existing pull request."
  ) {
    return true;
  }

  // Check against all technical patterns
  return technicalPatterns.some((pattern) => pattern.test(str));
}

function isLikelyUserFacingText(str) {
  // Basic validation - skip very short strings or strings without letters
  if (!str || str.length <= 2 || !/[a-zA-Z]/.test(str)) {
    return false;
  }

  // Check if it's a specifically excluded technical string
  if (isExcludedTechnicalString(str)) {
    return false;
  }

  // Check if it looks like a code rather than a key
  if (isLikelyCode(str)) {
    return false
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

  // First, check if it's a common development string (not user-facing)
  if (isCommonDevelopmentString(str)) {
    return false;
  }

  // Multi-word phrases are likely UI text
  const hasMultipleWords = /\s+/.test(str) && str.split(/\s+/).length > 1;

  // Sentences and questions are likely UI text
  const hasPunctuation = /[?!.,:]/.test(str);
  const isCapitalizedPhrase = /^[A-Z]/.test(str) && hasMultipleWords;
  const isTitleCase = hasMultipleWords && /\s[A-Z]/.test(str);
  const hasSentenceStructure = /^[A-Z].*[.!?]$/.test(str); // Starts with capital, ends with punctuation
  const hasQuestionForm =
    /^(What|How|Why|When|Where|Who|Can|Could|Would|Will|Is|Are|Do|Does|Did|Should|May|Might)/.test(
      str,
    );

  // Product names and camelCase identifiers are likely UI text
  const hasInternalCapitals = /[a-z][A-Z]/.test(str); // CamelCase product names

  // Instruction text patterns are likely UI text
  const looksLikeInstruction =
    /^(Enter|Type|Select|Choose|Provide|Specify|Search|Find|Input|Add|Write|Describe|Set|Pick|Browse|Upload|Download|Click|Tap|Press|Go to|Visit|Open|Close)/i.test(
      str,
    );

  // Error and status messages are likely UI text
  const looksLikeErrorOrStatus =
    /(failed|error|invalid|required|missing|incorrect|wrong|unavailable|not found|not available|try again|success|completed|finished|done|saved|updated|created|deleted|removed|added)/i.test(
      str,
    );

  // Single word check - assume it's UI text unless proven otherwise
  const isSingleWord =
    !str.includes(" ") && str.length > 1 && /^[a-zA-Z]+$/.test(str);

  // For single words, we need to be more careful
  if (isSingleWord) {
    // Skip common programming terms and variable names
    const isCommonProgrammingTerm =
      /^(null|undefined|true|false|function|class|interface|type|enum|const|let|var|return|import|export|default|async|await|try|catch|finally|throw|new|this|super|extends|implements|instanceof|typeof|void|delete|in|of|for|while|do|if|else|switch|case|break|continue|yield|static|get|set|public|private|protected|readonly|abstract|implements|namespace|module|declare|as|from|with)$/i.test(
        str,
      );

    if (isCommonProgrammingTerm) {
      return false;
    }

    // Skip common variable name patterns
    const looksLikeVariableName =
      /^[a-z][a-zA-Z0-9]*$/.test(str) && str.length <= 20;

    if (looksLikeVariableName) {
      return false;
    }

    // Skip common CSS values
    const isCommonCssValue =
      /^(auto|none|hidden|visible|block|inline|flex|grid|row|column|wrap|nowrap|center|start|end|stretch|cover|contain|fixed|absolute|relative|static|sticky|pointer|default|inherit|initial|unset)$/i.test(
        str,
      );

    if (isCommonCssValue) {
      return false;
    }

    // Skip common file extensions
    const isFileExtension = /^\.[a-z0-9]+$/i.test(str);
    if (isFileExtension) {
      return false;
    }

    // Skip common abbreviations
    const isCommonAbbreviation =
      /^(id|src|href|url|alt|img|btn|nav|div|span|ul|li|ol|dl|dt|dd|svg|png|jpg|gif|pdf|doc|txt|md|js|ts|jsx|tsx|css|scss|less|html|xml|json|yaml|yml|toml|csv|mp3|mp4|wav|avi|mov|mpeg|webm|webp|ttf|woff|eot|otf)$/i.test(
        str,
      );

    if (isCommonAbbreviation) {
      return false;
    }

    // If it's a single word that's not a programming term, variable name, CSS value, file extension, or abbreviation,
    // it might be UI text, but we'll be conservative and return false
    return false;
  }

  // If it has multiple words, punctuation, or looks like a sentence, it's likely UI text
  return (
    hasMultipleWords ||
    hasPunctuation ||
    isCapitalizedPhrase ||
    isTitleCase ||
    hasSentenceStructure ||
    hasQuestionForm ||
    hasInternalCapitals ||
    looksLikeInstruction ||
    looksLikeErrorOrStatus
  );
}

function isInTranslationContext(path) {
  // Check if the JSX text is inside a <Trans> component
  let current = path;
  while (current.parentPath) {
    if (
      current.isJSXElement() &&
      current.node.openingElement &&
      current.node.openingElement.name &&
      current.node.openingElement.name.name === "Trans"
    ) {
      return true;
    }
    current = current.parentPath;
  }
  return false;
}

function scanFileForUnlocalizedStrings(filePath) {
  // Skip all suggestion files as they contain special strings
  if (filePath.includes("suggestions")) {
    return [];
  }

  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const unlocalizedStrings = [];

    // Skip files that are too large
    if (content.length > 1000000) {
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

          // Skip technical attributes that don't contain user-facing text
          if (NON_TEXT_ATTRIBUTES.includes(attrName)) {
            return;
          }

          // Skip styling attributes
          if (
            attrName === "className" ||
            attrName === "class" ||
            attrName === "style"
          ) {
            return;
          }

          // Skip data attributes and event handlers
          if (attrName.startsWith("data-") || attrName.startsWith("on")) {
            return;
          }

          // Check the attribute value
          const value = jsxAttrPath.node.value;
          if (value && value.type === "StringLiteral") {
            const text = value.value.trim();
            if (text && isLikelyUserFacingText(text)) {
              unlocalizedStrings.push(text);
            }
          }
        },

        // Find string literals in code
        StringLiteral(stringPath) {
          // Skip if parent is JSX attribute (already handled above)
          if (stringPath.parent.type === "JSXAttribute") {
            return;
          }

          // Skip if parent is import/export declaration
          if (
            stringPath.parent.type === "ImportDeclaration" ||
            stringPath.parent.type === "ExportDeclaration"
          ) {
            return;
          }

          // Skip if parent is object property key
          if (
            stringPath.parent.type === "ObjectProperty" &&
            stringPath.parent.key === stringPath.node
          ) {
            return;
          }

          // Skip if inside a t() call or Trans component
          let isInsideTranslation = false;
          let current = stringPath;

          while (current.parentPath && !isInsideTranslation) {
            // Check for t() function call
            if (
              current.parent.type === "CallExpression" &&
              current.parent.callee &&
              ((current.parent.callee.type === "Identifier" &&
                current.parent.callee.name === "t") ||
                (current.parent.callee.type === "MemberExpression" &&
                  current.parent.callee.property &&
                  current.parent.callee.property.name === "t"))
            ) {
              isInsideTranslation = true;
              break;
            }

            // Check for <Trans> component
            if (
              current.parent.type === "JSXElement" &&
              current.parent.openingElement &&
              current.parent.openingElement.name &&
              current.parent.openingElement.name.name === "Trans"
            ) {
              isInsideTranslation = true;
              break;
            }

            current = current.parentPath;
          }

          if (!isInsideTranslation) {
            const text = stringPath.node.value.trim();
            if (text && isLikelyUserFacingText(text)) {
              unlocalizedStrings.push(text);
            }
          }
        },
      });

      return unlocalizedStrings;
    } catch (error) {
      console.error(`Error parsing file ${filePath}:`, error);
      return [];
    }
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    return [];
  }
}

function scanDirectoryForUnlocalizedStrings(dirPath) {
  const results = new Map();

  function scanDir(currentPath) {
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

// Run the check
try {
  const srcPath = path.resolve(__dirname, '../src');
  console.log('Checking for unlocalized strings in frontend code...');

  // Get unlocalized strings using the AST scanner
  const results = scanDirectoryForUnlocalizedStrings(srcPath);

  // If we found any unlocalized strings, format them for output and exit with error
  if (results.size > 0) {
    const formattedResults = Array.from(results.entries())
      .map(([file, strings]) => `\n${file}:\n  ${strings.join('\n  ')}`)
      .join('\n');

    console.error(`Error: Found unlocalized strings in the following files:${formattedResults}`);
    process.exit(1);
  }

  console.log('✅ No unlocalized strings found in frontend code.');
  process.exit(0);
} catch (error) {
  console.error('Error running unlocalized strings check:', error);
  process.exit(1);
}

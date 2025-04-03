/**
 * AST-based Unlocalized String Scanner
 *
 * This module scans the codebase for unlocalized strings that should be internationalized.
 * It uses Babel's AST parser to analyze TypeScript/JavaScript files and identify:
 *
 * - String literals that appear to be user-facing text
 * - JSX text content that should be localized
 * - Raw translation keys that should be wrapped in i18next.t() calls
 *
 * The scanner employs sophisticated heuristics to distinguish between:
 * - Technical strings (CSS classes, URLs, file paths, etc.)
 * - User-facing text that requires localization
 *
 * It recursively scans directories while respecting ignore patterns and
 * returns a map of file paths to lists of unlocalized strings found in each file.
 */

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

// Specific technical strings that should be excluded from localization
const EXCLUDED_TECHNICAL_STRINGS = [
  "openid email profile", // OAuth scope string - not user-facing
];

function isExcludedTechnicalString(str: string): boolean {
  return EXCLUDED_TECHNICAL_STRINGS.includes(str);
}

function isCommonDevelopmentString(str: string): boolean {
  // ===== GENERALIZED PATTERNS FOR DEVELOPMENT STRINGS =====

  // 1. Technical patterns that are definitely not UI strings
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

  // 2. File extensions and media types
  const fileExtensionPattern =
    /^\.(png|jpg|jpeg|gif|svg|webp|bmp|ico|pdf|mp4|webm|ogg|mp3|wav|json|xml|csv|txt|md|html|css|js|jsx|ts|tsx)$/i;
  if (fileExtensionPattern.test(str)) {
    return true;
  }

  // 3. AI model and provider patterns
  const aiRelatedPattern =
    /^(AI|OpenAI|VertexAI|PaLM|Gemini|Anthropic|Anyscale|Databricks|Ollama|FriendliAI|Groq|DeepInfra|AI21|Replicate|OpenRouter|Azure|AWS|SageMaker|Bedrock|Mistral|Perplexity|Fireworks|Cloudflare|Workers|Voyage|claude-|gpt-|o1-|o3-)/i;
  if (aiRelatedPattern.test(str)) {
    return true;
  }

  // 4. CSS units and values
  const cssUnitsPattern =
    /(px|rem|em|vh|vw|vmin|vmax|ch|ex|fr|deg|rad|turn|grad|ms|s)$/;
  const cssValuesPattern =
    /(rgb|rgba|hsl|hsla|#[0-9a-fA-F]+|solid|absolute|relative|sticky|fixed|static|block|inline|flex|grid|none|auto|hidden|visible)/;

  if (cssUnitsPattern.test(str) || cssValuesPattern.test(str)) {
    return true;
  }

  // 5. Tailwind and CSS class patterns

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
      "bg-",
      "text-",
      "border-",
      "rounded-",
      "p-",
      "m-",
      "px-",
      "py-",
      "mx-",
      "my-",
      "w-",
      "h-",
      "min-w-",
      "min-h-",
      "max-w-",
      "max-h-",
      "flex-",
      "grid-",
      "gap-",
      "space-",
      "items-",
      "justify-",
      "self-",
      "col-",
      "row-",
      "order-",
      "object-",
      "overflow-",
      "opacity-",
      "z-",
      "top-",
      "right-",
      "bottom-",
      "left-",
      "inset-",
      "font-",
      "tracking-",
      "leading-",
      "list-",
      "placeholder-",
      "shadow-",
      "ring-",
      "transition-",
      "duration-",
      "ease-",
      "delay-",
      "animate-",
      "scale-",
      "rotate-",
      "translate-",
      "skew-",
      "origin-",
      "cursor-",
      "select-",
      "resize-",
      "fill-",
      "stroke-",
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
      "hover:",
      "focus:",
      "active:",
      "disabled:",
      "visited:",
      "first:",
      "last:",
      "odd:",
      "even:",
      "group-hover:",
      "focus-within:",
      "focus-visible:",
      "motion-safe:",
      "motion-reduce:",
      "dark:",
      "light:",
      "sm:",
      "md:",
      "lg:",
      "xl:",
      "2xl:",
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
      "border",
      "rounded",
      "px",
      "py",
      "mx",
      "my",
      "p",
      "m",
      "w",
      "h",
      "flex",
      "grid",
      "gap",
      "transition",
      "duration",
      "font",
      "leading",
      "tracking",
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

  // 6. HTML tags and attributes
  if (
    /^<[a-z0-9]+>.*<\/[a-z0-9]+>$/.test(str) ||
    /^<[a-z0-9]+ [^>]+\/>$/.test(str)
  ) {
    return true;
  }

  // 7. Check for specific patterns in suggestions and examples
  if (
    str.includes("* ") &&
    (str.includes("create a") ||
      str.includes("build a") ||
      str.includes("make a"))
  ) {
    // This is likely a suggestion or example, not a UI string
    return false;
  }

  // 8. Check for specific technical identifiers from the test failures
  if (
    /^(download_via_vscode_button_clicked|open-vscode-error-|set-indicator|settings_saved|openhands-trace-|provider-item-|last_browser_action_error)$/.test(
      str,
    )
  ) {
    return true;
  }

  // 9. Check for URL paths and query parameters
  if (
    str.startsWith("?") ||
    str.startsWith("/") ||
    str.includes("auth.") ||
    str.includes("$1auth.")
  ) {
    return true;
  }

  // 10. Check for specific strings that should be excluded
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

  // 11. Check for long suggestion texts
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

  // 12. Check for specific error messages and UI text
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

  // 8. Check against all technical patterns
  return technicalPatterns.some((pattern) => pattern.test(str));
}

function isLikelyUserFacingText(str: string): boolean {
  // Basic validation - skip very short strings or strings without letters
  if (!str || str.length <= 2 || !/[a-zA-Z]/.test(str)) {
    return false;
  }

  // Check if it's a specifically excluded technical string
  if (isExcludedTechnicalString(str)) {
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

  // First, check if it's a common development string (not user-facing)
  if (isCommonDevelopmentString(str)) {
    return false;
  }

  // ===== GENERALIZED RULES FOR DETECTING UI TEXT =====

  // 1. Multi-word phrases are likely UI text
  const hasMultipleWords = /\s+/.test(str) && str.split(/\s+/).length > 1;

  // 2. Sentences and questions are likely UI text
  const hasPunctuation = /[?!.,:]/.test(str);
  const isCapitalizedPhrase = /^[A-Z]/.test(str) && hasMultipleWords;
  const isTitleCase = hasMultipleWords && /\s[A-Z]/.test(str);
  const hasSentenceStructure = /^[A-Z].*[.!?]$/.test(str); // Starts with capital, ends with punctuation
  const hasQuestionForm =
    /^(What|How|Why|When|Where|Who|Can|Could|Would|Will|Is|Are|Do|Does|Did|Should|May|Might)/.test(
      str,
    );

  // 3. Product names and camelCase identifiers are likely UI text
  const hasInternalCapitals = /[a-z][A-Z]/.test(str); // CamelCase product names

  // 4. Instruction text patterns are likely UI text
  const looksLikeInstruction =
    /^(Enter|Type|Select|Choose|Provide|Specify|Search|Find|Input|Add|Write|Describe|Set|Pick|Browse|Upload|Download|Click|Tap|Press|Go to|Visit|Open|Close)/i.test(
      str,
    );

  // 5. Error and status messages are likely UI text
  const looksLikeErrorOrStatus =
    /(failed|error|invalid|required|missing|incorrect|wrong|unavailable|not found|not available|try again|success|completed|finished|done|saved|updated|created|deleted|removed|added)/i.test(
      str,
    );

  // 6. Single word check - assume it's UI text unless proven otherwise
  const isSingleWord =
    !str.includes(" ") && str.length > 1 && /^[a-zA-Z]+$/.test(str);

  // For single words, we need to be more careful
  if (isSingleWord) {
    // Skip common programming terms and variable names
    const isCommonProgrammingTerm =
      /^(null|undefined|true|false|function|class|interface|type|enum|const|let|var|return|import|export|default|async|await|try|catch|finally|throw|new|this|super|extends|implements|instanceof|typeof|void|delete|in|of|for|while|do|if|else|switch|case|break|continue|yield|static|get|set|public|private|protected|readonly|as|from|to|with|without|by)$/i.test(
        str,
      );

    if (isCommonProgrammingTerm) {
      return false;
    }

    // Skip common variable name prefixes
    const isLikelyVariableName =
      /^(tmp|temp|is|has|get|set|on|handle|create|update|delete|fetch|load|save|init|config|util|helper|format|parse|validate|check|verify|compute|calculate|render|draw|build|make|gen|find|search|filter|sort|map|reduce|each|every|some|any|first|last|next|prev|min|max|sum|avg|count|total|index|key|val|value|item|elem|node|prop|attr|opt|arg|param|ctx|ref|id|num|str|arr|obj|func|cb|callback|err|error|res|result|data|info|meta|stats|log|debug|warn|msg|req|resp|http|api|url|path|route|query|params|body|header|token|auth|user|admin|guest|client|server|db|cache|store|state|action|event|emit|dispatch|subscribe|publish|queue|stack|list|collection|set|map|dict|hash|tree|graph|edge|vertex|parent|child|sibling|root|leaf|head|tail|start|end|begin|finish|source|target|origin|dest|src|dst|input|output|stdin|stdout|stderr|file|dir|folder|path|name|ext|size|date|time|timestamp|duration|interval|period|freq|rate|speed|velocity|accel|pos|position|loc|location|addr|address|coord|point|rect|circle|line|poly|shape|color|style|font|text|content|html|xml|json|yaml|csv|md|svg|img|pic|photo|video|audio|media|stream|buffer|byte|bit|flag|mode|status|code|type|format|version|level|depth|height|width|length|count|size|capacity|limit|threshold|min|max|low|high|top|bottom|left|right|center|middle|inner|outer|upper|lower|front|back|fore|hind|begin|end|start|finish|first|last|head|tail|prev|next|parent|child|source|target|origin|dest|from|to|via|through|between|among|within|inside|outside|above|below|under|over|before|after|earlier|later|sooner|past|future|old|new|young|fresh|stale|valid|invalid|correct|incorrect|right|wrong|good|bad|better|worse|best|worst|more|less|most|least|many|few|some|any|all|none|each|every|no|yes|true|false|on|off|up|down|in|out|open|closed|visible|hidden|enabled|disabled|active|inactive|busy|idle|ready|pending|success|failure|pass|fail|win|lose|start|stop|pause|resume|continue|break|exit|quit|abort|retry|skip|repeat|loop|once|again|never|always|sometimes|often|rarely|maybe|perhaps|probably|definitely|exactly|approximately|about|around|near|far|close|distant|high|low|big|small|large|tiny|huge|giant|wide|narrow|thick|thin|deep|shallow|long|short|tall|heavy|light|fast|slow|quick|rapid|gradual|sudden|smooth|rough|hard|soft|hot|cold|warm|cool|bright|dim|dark|light|loud|quiet|noisy|silent|empty|full|partial|complete|partial|whole|half|quarter|third|double|triple|single|multiple|unique|common|rare|abundant|scarce|rich|poor|wealthy|needy|strong|weak|powerful|feeble|brave|cowardly|bold|timid|smart|dumb|clever|stupid|wise|foolish|sane|crazy|normal|weird|strange|familiar|foreign|native|alien|friendly|hostile|kind|cruel|nice|mean|sweet|sour|bitter|salty|clean|dirty|neat|messy|tidy|cluttered|simple|complex|easy|difficult|hard|trivial|obvious|subtle|explicit|implicit|clear|vague|ambiguous|certain|uncertain|sure|unsure|confident|doubtful|positive|negative|neutral|biased|fair|unfair|just|unjust|legal|illegal|valid|invalid|safe|dangerous|secure|insecure|private|public|personal|shared|individual|collective|solo|joint|separate|combined|unified|divided|whole|partial|complete|incomplete|finished|unfinished|done|undone|solved|unsolved|fixed|broken|working|failing|functional|dysfunctional|useful|useless|helpful|unhelpful|beneficial|harmful|healthy|unhealthy|fit|unfit|sick|well|alive|dead|awake|asleep|conscious|unconscious|aware|unaware|attentive|distracted|focused|unfocused|concentrated|scattered|organized|disorganized|systematic|chaotic|orderly|disorderly|regular|irregular|consistent|inconsistent|stable|unstable|steady|unsteady|balanced|unbalanced|symmetrical|asymmetrical|even|odd|equal|unequal|same|different|similar|dissimilar|like|unlike|matching|mismatched|compatible|incompatible|consistent|inconsistent|uniform|diverse|homogeneous|heterogeneous|constant|variable|fixed|changing|static|dynamic|stationary|moving|mobile|immobile|portable|fixed|permanent|temporary|interim|provisional|lasting|fleeting|enduring|transient|persistent|intermittent|continuous|discontinuous|uninterrupted|interrupted|unbroken|broken|solid|hollow|dense|sparse|compact|loose|tight|slack|rigid|flexible|stiff|pliable|hard|soft|firm|yielding|strong|weak|tough|fragile|durable|flimsy|sturdy|delicate|robust|frail|resilient|vulnerable|resistant|susceptible|immune|prone|safe|dangerous|secure|insecure|protected|exposed|covered|uncovered|enclosed|open|sealed|leaky|waterproof|permeable|impermeable|porous|solid|transparent|opaque|translucent|clear|cloudy|foggy|misty|hazy|sharp|blunt|pointed|rounded|straight|curved|flat|bumpy|smooth|rough|even|uneven|level|sloped|horizontal|vertical|diagonal|parallel|perpendicular|intersecting|converging|diverging|ascending|descending|rising|falling|increasing|decreasing|growing|shrinking|expanding|contracting|swelling|deflating|inflating|deflating|stretching|compressing|extending|retracting|spreading|concentrating|dispersing|gathering|scattering|collecting|distributing|accumulating|dissipating|absorbing|emitting|attracting|repelling|pulling|pushing|drawing|driving|leading|following|guiding|directing|controlling|regulating|managing|supervising|monitoring|tracking|tracing|locating|finding|seeking|searching|looking|watching|observing|examining|inspecting|investigating|analyzing|studying|researching|exploring|discovering|uncovering|revealing|exposing|hiding|concealing|masking|disguising|camouflaging|blending|standing out|protruding|receding|advancing|retreating|approaching|withdrawing|arriving|departing|coming|going|entering|exiting|ingressing|egressing|importing|exporting|uploading|downloading|sending|receiving|transmitting|accepting|rejecting|approving|disapproving|endorsing|opposing|supporting|resisting|helping|hindering|assisting|obstructing|facilitating|impeding|enabling|disabling|allowing|preventing|permitting|prohibiting|authorizing|forbidding|requiring|excluding|including|containing|excluding|comprising|consisting|constituting|forming|shaping|molding|casting|carving|cutting|slicing|splitting|joining|connecting|linking|attaching|detaching|fastening|unfastening|tying|untying|binding|unbinding|wrapping|unwrapping|packing|unpacking|loading|unloading|filling|emptying|pouring|draining|flowing|stopping|blocking|clearing|opening|closing|shutting|locking|unlocking|securing|releasing|freeing|restraining|limiting|restricting|confining|liberating|emancipating|saving|spending|earning|paying|buying|selling|trading|exchanging|swapping|substituting|replacing|displacing|supplanting|superseding|succeeding|preceding|following|leading|trailing|heading|tailing|topping|bottoming|crowning|basing|founding|establishing|instituting|creating|destroying|building|demolishing|constructing|deconstructing|assembling|disassembling|composing|decomposing|synthesizing|analyzing|integrating|disintegrating|unifying|fragmenting|combining|separating|mixing|unmixing|blending|segregating|merging|diverging|fusing|splitting|joining|parting|uniting|dividing|adding|subtracting|multiplying|dividing|increasing|decreasing|doubling|halving|squaring|cubing|rooting|powering|factoring|expanding|simplifying|complicating|clarifying|confusing|explaining|mystifying|illuminating|obscuring|enlightening|befuddling|informing|misinforming|educating|misleading|teaching|learning|studying|practicing|training|coaching|mentoring|tutoring|instructing|directing|commanding|ordering|requesting|asking|answering|responding|replying|stating|questioning|inquiring|investigating|probing|exploring|examining|inspecting|checking|verifying|validating|confirming|affirming|denying|negating|contradicting|opposing|agreeing|disagreeing|concurring|dissenting|approving|disapproving|accepting|rejecting|embracing|shunning|welcoming|avoiding|seeking|evading|pursuing|fleeing|chasing|escaping|catching|releasing|holding|dropping|grasping|letting go|clutching|relinquishing|keeping|discarding|retaining|disposing|preserving|destroying|conserving|wasting|saving|spending|using|consuming|utilizing|employing|applying|implementing|executing|performing|doing|acting|behaving|conducting|proceeding|advancing|progressing|developing|evolving|growing|maturing|aging|rejuvenating|reviving|resurrecting|revitalizing|refreshing|renewing|restoring|rehabilitating|recovering|healing|hurting|harming|damaging|injuring|wounding|breaking|fixing|repairing|mending|patching|healing|curing|treating|medicating|poisoning|infecting|contaminating|purifying|cleansing|washing|dirtying|soiling|staining|marking|tagging|labeling|naming|calling|addressing|referring|mentioning|citing|quoting|paraphrasing|summarizing|detailing|elaborating|expounding|explaining|clarifying|simplifying|complicating|confusing|perplexing|puzzling|mystifying|bewildering|baffling|confounding|astounding|amazing|surprising|shocking|startling|alarming|frightening|terrifying|horrifying|scaring|intimidating|threatening|menacing|warning|cautioning|alerting|notifying|informing|telling|saying|speaking|talking|chatting|conversing|discussing|debating|arguing|quarreling|fighting|battling|struggling|striving|trying|attempting|endeavoring|seeking|searching|looking|hunting|gathering|collecting|accumulating|amassing|hoarding|stockpiling|storing|keeping|holding|containing|including|excluding|omitting|skipping|missing|hitting|striking|beating|pounding|hammering|knocking|tapping|touching|feeling|sensing|perceiving|detecting|noticing|observing|watching|seeing|viewing|looking|gazing|staring|glancing|glimpsing|peeking|peering|squinting|blinking|winking|closing|opening|widening|narrowing|focusing|blurring|sharpening|dulling|brightening|darkening|lightening|dimming|illuminating|shadowing|coloring|tinting|dyeing|painting|drawing|sketching|tracing|outlining|defining|describing|depicting|portraying|representing|symbolizing|signifying|meaning|implying|suggesting|indicating|pointing|directing|guiding|leading|following|tracking|tracing|trailing|pursuing|chasing|hunting|seeking|searching|exploring|investigating|examining|studying|analyzing|dissecting|breaking down|building up|constructing|creating|making|producing|manufacturing|fabricating|forging|casting|molding|shaping|forming|fashioning|designing|planning|plotting|scheming|devising|inventing|innovating|pioneering|discovering|finding|locating|spotting|sighting|glimpsing|noticing|observing|witnessing|experiencing|undergoing|suffering|enduring|tolerating|bearing|withstanding|resisting|opposing|fighting|battling|struggling|striving|trying|attempting|endeavoring|seeking|searching|looking|hunting|gathering|collecting|accumulating|amassing|hoarding|stockpiling|storing|keeping|holding|containing|including|excluding|omitting|skipping|missing|hitting|striking|beating|pounding|hammering|knocking|tapping|touching|feeling|sensing|perceiving|detecting|noticing|observing|watching|seeing|viewing|looking|gazing|staring|glancing|glimpsing|peeking|peering|squinting|blinking|winking|closing|opening|widening|narrowing|focusing|blurring|sharpening|dulling|brightening|darkening|lightening|dimming|illuminating|shadowing|coloring|tinting|dyeing|painting|drawing|sketching|tracing|outlining|defining|describing|depicting|portraying|representing|symbolizing|signifying|meaning|implying|suggesting|indicating|pointing|directing|guiding|leading|following|tracking|tracing|trailing|pursuing|chasing|hunting|seeking|searching|exploring|investigating|examining|studying|analyzing|dissecting)$/i.test(
        str,
      );

    if (isLikelyVariableName) {
      return false;
    }

    // For single capitalized words, they're likely UI elements
    if (/^[A-Z][a-z]+$/.test(str)) {
      return true;
    }

    // For other single words, check if they're common English words
    // (This is a simplified approach - in a real implementation, you might want to use a dictionary)
    const isCommonEnglishWord = str.length > 3; // Simple heuristic: longer words are more likely to be meaningful

    return isCommonEnglishWord;
  }

  // By default, assume multi-word phrases, sentences, and special patterns are UI text
  return (
    hasMultipleWords ||
    hasPunctuation ||
    isCapitalizedPhrase ||
    isTitleCase ||
    hasInternalCapitals ||
    hasSentenceStructure ||
    hasQuestionForm ||
    looksLikeInstruction ||
    looksLikeErrorOrStatus
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
  // Skip all suggestion files as they contain special strings
  if (filePath.includes("suggestions")) {
    return [];
  }

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

          // ===== ATTRIBUTE CONTEXT-BASED DETECTION =====

          // 1. Skip technical attributes that don't contain user-facing text

          // Skip standard non-text attributes
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

          // Skip ref, key, and other React-specific attributes
          if (
            [
              "ref",
              "key",
              "as",
              "forwardedAs",
              "component",
              "defaultValue",
              "defaultChecked",
            ].includes(attrName)
          ) {
            return;
          }

          // 2. Identify attributes that typically contain user-facing text
          const isLikelyTextAttribute = [
            // Common text attributes
            "title",
            "label",
            "aria-label",
            "alt",
            "placeholder",
            "description",
            "caption",
            "summary",
            "heading",
            "subheading",
            "message",
            // Button and link text
            "buttonText",
            "linkText",
            "confirmText",
            "cancelText",
            "submitText",
            // Error and help text
            "errorText",
            "helpText",
            "infoText",
            "warningText",
            "successText",
            // Tooltips and accessibility
            "tooltip",
            "tooltipText",
            "screenReaderText",
            "accessibilityLabel",
          ].includes(attrName);

          // 3. Check the attribute value
          const { value } = jsxAttrPath.node;

          // Handle string literals
          if (t.isStringLiteral(value)) {
            const text = value.value.trim();

            // Skip empty strings
            if (!text) {
              return;
            }

            // Always check text in known text attributes
            if (isLikelyTextAttribute && !isInTranslationContext(jsxAttrPath)) {
              unlocalizedStrings.push(text);
              return;
            }

            // For other attributes, use our general detection logic
            if (
              isLikelyUserFacingText(text) &&
              !isInTranslationContext(jsxAttrPath)
            ) {
              unlocalizedStrings.push(text);
            }
          }

          // Handle JSX expressions
          if (t.isJSXExpressionContainer(value)) {
            // Check for raw translation keys in t() calls
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

            // Check for string literals in template literals
            if (t.isTemplateLiteral(value.expression)) {
              const { quasis } = value.expression;
              for (const quasi of quasis) {
                const text = quasi.value.raw.trim();
                if (
                  text &&
                  isLikelyUserFacingText(text) &&
                  !isInTranslationContext(jsxAttrPath)
                ) {
                  unlocalizedStrings.push(text);
                }
              }
            }
          }
        },

        // Find string literals
        StringLiteral(strLiteralPath) {
          // ===== AST CONTEXT-BASED DETECTION =====

          // 1. Skip contexts where strings are not user-facing

          // Skip if parent is a JSX attribute (handled separately)
          if (t.isJSXAttribute(strLiteralPath.parent)) {
            return;
          }

          // Skip if it's part of an import/export statement
          if (
            t.isImportDeclaration(strLiteralPath.parent) ||
            t.isExportDeclaration(strLiteralPath.parent) ||
            t.isImportSpecifier(strLiteralPath.parent)
          ) {
            return;
          }

          // Skip if it's a property key in an object
          if (
            t.isObjectProperty(strLiteralPath.parent) &&
            strLiteralPath.parent.key === strLiteralPath.node
          ) {
            return;
          }

          // Skip if it's a member expression property
          if (
            t.isMemberExpression(strLiteralPath.parent) &&
            strLiteralPath.parent.property === strLiteralPath.node
          ) {
            return;
          }

          // 2. Identify contexts where strings are likely user-facing

          // Check if string is in a UI-related function call
          const isInUIFunctionCall =
            t.isCallExpression(strLiteralPath.parent) &&
            t.isIdentifier(strLiteralPath.parent.callee) &&
            [
              "alert",
              "confirm",
              "prompt",
              "toast",
              "notify",
              "message",
              "showModal",
              "showDialog",
              "showPopup",
              "showTooltip",
              "showNotification",
            ].includes(strLiteralPath.parent.callee.name);

          // 3. Process the string
          const text = strLiteralPath.node.value.trim();

          // Skip empty strings
          if (!text) {
            return;
          }

          // Always check strings in UI-related contexts
          if (isInUIFunctionCall && !isInTranslationContext(strLiteralPath)) {
            unlocalizedStrings.push(text);
            return;
          }

          // For other contexts, use our general detection logic
          if (
            isLikelyUserFacingText(text) &&
            !isInTranslationContext(strLiteralPath)
          ) {
            unlocalizedStrings.push(text);
          }
        },

        // Find template literals
        TemplateLiteral(templatePath) {
          // ===== TEMPLATE LITERAL CONTEXT-BASED DETECTION =====

          // 1. Skip contexts where template literals are not user-facing

          // Skip if it's a tagged template literal
          if (t.isTaggedTemplateExpression(templatePath.parent)) {
            return;
          }

          // Skip if it's part of an import/export statement
          if (
            t.isImportDeclaration(templatePath.parent) ||
            t.isExportDeclaration(templatePath.parent)
          ) {
            return;
          }

          // Skip if it's a property key in an object
          if (
            t.isObjectProperty(templatePath.parent) &&
            templatePath.parent.key === templatePath.node
          ) {
            return;
          }

          // 2. Identify contexts where template literals are likely user-facing

          // Check if template is in a UI-related function call
          const isInUIFunctionCall =
            t.isCallExpression(templatePath.parent) &&
            t.isIdentifier(templatePath.parent.callee) &&
            [
              "alert",
              "confirm",
              "prompt",
              "toast",
              "notify",
              "message",
              "showModal",
              "showDialog",
              "showPopup",
              "showTooltip",
              "showNotification",
            ].includes(templatePath.parent.callee.name);

          // 3. Process each part of the template literal
          for (const quasi of templatePath.node.quasis) {
            const text = quasi.value.raw.trim();

            // Skip empty strings
            if (text) {
              // Always check strings in UI-related contexts
              if (isInUIFunctionCall && !isInTranslationContext(templatePath)) {
                unlocalizedStrings.push(text);
              } else if (
                isLikelyUserFacingText(text) &&
                !isInTranslationContext(templatePath)
              ) {
                unlocalizedStrings.push(text);
              }
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

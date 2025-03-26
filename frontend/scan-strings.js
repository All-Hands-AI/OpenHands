// Script to scan for unlocalized strings
import fs from 'fs';
import path from 'path';
import * as parser from '@babel/parser';
import _traverse from '@babel/traverse';
import * as t from '@babel/types';

// Fix for ESM import
const traverse = _traverse.default;

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
  "utils/scan-unlocalized-strings-ast.ts", // AST scanner
  "scan-strings.js", // This file
];

// Extensions to scan
const SCAN_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"];

function shouldIgnorePath(filePath) {
  return IGNORE_PATHS.some((ignore) => filePath.includes(ignore));
}

function isLikelyTranslationKey(str) {
  // Translation keys typically use dots, underscores, or are all caps
  return /^[A-Z0-9_$.]+$/.test(str) || str.includes(".");
}

function isCommonDevelopmentString(str) {
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
    /^underline(\s+[a-zA-Z0-9-]+)*$/, // Tailwind underline classes
    /^cursor-(\[[^\]]+\]|\S+)$/, // Tailwind cursor classes
    /^tracking-(\[[^\]]+\]|\S+)$/, // Tailwind tracking classes
    /^leading-(\[[^\]]+\]|\S+)$/, // Tailwind leading classes
    /^font-(\[[^\]]+\]|\S+)$/, // Tailwind font classes
    /^text-(\[[^\]]+\]|\S+)$/, // Tailwind text classes
  ];

  return commonPatterns.some((pattern) => pattern.test(str));
}

function isLikelyUserFacingText(str) {
  if (!str || str.length <= 2 || !(/[a-zA-Z]/.test(str))) {
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

function isTranslationCall(node) {
  // Check for t('KEY') pattern
  if (
    t.isCallExpression(node) &&
    t.isIdentifier(node.callee) &&
    node.callee.name === 't' &&
    node.arguments.length > 0
  ) {
    return true;
  }
  
  // Check for useTranslation() pattern
  if (
    t.isCallExpression(node) &&
    t.isIdentifier(node.callee) &&
    node.callee.name === 'useTranslation'
  ) {
    return true;
  }
  
  // Check for <Trans> component
  if (
    t.isJSXElement(node) &&
    t.isJSXIdentifier(node.openingElement.name) &&
    node.openingElement.name.name === 'Trans'
  ) {
    return true;
  }
  
  return false;
}

function isInTranslationContext(path) {
  let current = path;
  
  while (current) {
    if (isTranslationCall(current.node)) {
      return true;
    }
    current = current.parentPath;
  }
  
  return false;
}

function scanFileForUnlocalizedStrings(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const unlocalizedStrings = [];
    
    // Skip files that are too large
    if (content.length > 1000000) {
      console.warn(`Skipping large file: ${filePath}`);
      return [];
    }
    
    try {
      // Parse the file
      const ast = parser.parse(content, {
        sourceType: 'module',
        plugins: ['jsx', 'typescript', 'classProperties', 'decorators-legacy'],
      });
      
      // Traverse the AST
      traverse(ast, {
        // Find JSX text content
        JSXText(path) {
          const text = path.node.value.trim();
          if (text && isLikelyUserFacingText(text) && !isInTranslationContext(path)) {
            unlocalizedStrings.push(text);
          }
        },
        
        // Find string literals in JSX attributes
        JSXAttribute(path) {
          const attrName = path.node.name.name.toString();
          
          // Skip attributes that typically don't contain user-facing text
          if (NON_TEXT_ATTRIBUTES.includes(attrName)) {
            return;
          }
          
          // Check the attribute value
          const value = path.node.value;
          if (t.isStringLiteral(value)) {
            const text = value.value.trim();
            if (text && isLikelyUserFacingText(text) && !isInTranslationContext(path)) {
              unlocalizedStrings.push(text);
            }
          }
        },
        
        // Find string literals
        StringLiteral(path) {
          // Skip if parent is a JSX attribute (handled separately)
          if (t.isJSXAttribute(path.parent)) {
            return;
          }
          
          // Skip if it's part of an import statement
          if (t.isImportDeclaration(path.parent) || t.isExportDeclaration(path.parent)) {
            return;
          }
          
          const text = path.node.value.trim();
          if (text && isLikelyUserFacingText(text) && !isInTranslationContext(path)) {
            unlocalizedStrings.push(text);
          }
        },
        
        // Find template literals
        TemplateLiteral(path) {
          // Skip if it's a tagged template literal
          if (t.isTaggedTemplateExpression(path.parent)) {
            return;
          }
          
          // Get the full template string if it's simple
          if (path.node.quasis.length === 1) {
            const text = path.node.quasis[0].value.raw.trim();
            if (text && isLikelyUserFacingText(text) && !isInTranslationContext(path)) {
              unlocalizedStrings.push(text);
            }
          }
        }
      });
    } catch (error) {
      // If parsing fails, fall back to regex-based scanning
      console.warn(`Failed to parse ${filePath}, falling back to regex scanning: ${error}`);
      
      // Simple regex to find potential text strings
      const stringRegex = /['"`]([^'"`\n]{3,})['"`]/g;
      const jsxTextRegex = />([\s]*[A-Za-z][\w\s.,!?]+)[\s]*</g;
      
      let match;
      
      // Find string literals
      while ((match = stringRegex.exec(content)) !== null) {
        const text = match[1].trim();
        if (text && isLikelyUserFacingText(text)) {
          unlocalizedStrings.push(text);
        }
      }
      
      // Find JSX text content
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
    console.error(`Error scanning file ${filePath}:`, error);
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

// Run the scanner
console.log('Scanning for unlocalized strings...');
const results = scanDirectoryForUnlocalizedStrings('./src');

// Print the results
console.log('\nUnlocalized strings found:');
let totalStrings = 0;

// Sort results by file path
const sortedResults = new Map([...results.entries()].sort());

for (const [filePath, strings] of sortedResults) {
  console.log(`\n${filePath}:`);
  strings.forEach(str => console.log(`  - "${str}"`));
  totalStrings += strings.length;
}

console.log(`\nTotal: ${totalStrings} unlocalized strings in ${sortedResults.size} files`);
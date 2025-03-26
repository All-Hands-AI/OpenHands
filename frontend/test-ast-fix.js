// Test script to check if our AST-based approach works correctly
import fs from 'fs';
import path from 'path';
import * as parser from '@babel/parser';
import _traverse from '@babel/traverse';
import * as t from '@babel/types';

// Fix for ESM import
const traverse = _traverse.default;

// Test file
const testFile = path.join(__dirname, 'src/components/features/github/code-not-in-github-link.tsx');
const content = fs.readFileSync(testFile, 'utf-8');

// Parse the file
const ast = parser.parse(content, {
  sourceType: 'module',
  plugins: ['jsx', 'typescript', 'classProperties', 'decorators-legacy'],
});

// Traverse the AST
const unlocalizedStrings = [];

traverse(ast, {
  // Find JSX text content
  JSXText(path) {
    const text = path.node.value.trim();
    if (text) {
      console.log(`Found JSX text: "${text}"`);
      unlocalizedStrings.push(text);
    }
  },
  
  // Find string literals
  StringLiteral(path) {
    const text = path.node.value.trim();
    if (text) {
      console.log(`Found string literal: "${text}"`);
      unlocalizedStrings.push(text);
    }
  },
});

console.log('\nAll unlocalized strings found:');
unlocalizedStrings.forEach(str => console.log(`- "${str}"`));
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function fixImportsInFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const fixed = content.replace(/require\("\.\/([^"]+)"\)/g, 'require("./$1.cjs")');
  fs.writeFileSync(filePath, fixed);
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      walkDir(filePath);
    } else if (file.endsWith('.cjs')) {
      fixImportsInFile(filePath);
    }
  }
}

walkDir('./dist/cjs');
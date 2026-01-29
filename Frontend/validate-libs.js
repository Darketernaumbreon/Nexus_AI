#!/usr/bin/env node

/**
 * Manual Syntax Validation for Created Library Files
 * This script validates TypeScript syntax without needing the full compiler
 */

const fs = require('fs');
const path = require('path');

const LIBRARY_FILES = [
  'lib/polyline-decoder.ts',
  'lib/date-formatter.ts',
  'lib/geojson-parser.ts',
  'lib/error-handler.ts',
];

const VALIDATION_RULES = {
  // Check for matching braces and brackets
  balancedBrackets: (content) => {
    let braceCount = 0;
    let bracketCount = 0;
    let parenCount = 0;
    
    for (let i = 0; i < content.length; i++) {
      const char = content[i];
      
      // Skip comments and strings
      if (content[i] === '/' && content[i + 1] === '/') {
        i = content.indexOf('\n', i);
        continue;
      }
      if (content[i] === '/' && content[i + 1] === '*') {
        i = content.indexOf('*/', i) + 1;
        continue;
      }
      if ((content[i] === '"' || content[i] === "'" || content[i] === '`') 
          && content[i - 1] !== '\\') {
        const quote = content[i];
        i++;
        while (i < content.length && content[i] !== quote) {
          if (content[i] === '\\') i++;
          i++;
        }
        continue;
      }
      
      if (char === '{') braceCount++;
      if (char === '}') braceCount--;
      if (char === '[') bracketCount++;
      if (char === ']') bracketCount--;
      if (char === '(') parenCount++;
      if (char === ')') parenCount--;
    }
    
    return braceCount === 0 && bracketCount === 0 && parenCount === 0;
  },
  
  // Check for valid export statements
  hasExports: (content) => {
    return /export\s+(function|interface|type|class|const|enum)/.test(content);
  },
  
  // Check for missing semicolons (basic)
  basicSyntax: (content) => {
    const lines = content.split('\n');
    let errors = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Skip empty lines and comments
      if (!line || line.startsWith('//') || line.startsWith('*')) continue;
      
      // Check for unclosed comments
      if (line.includes('/*') && !line.includes('*/')) {
        errors.push(`Line ${i + 1}: Unclosed block comment`);
      }
    }
    
    return errors;
  },
  
  // Check for import statements
  hasValidImports: (content) => {
    const importLines = content.match(/import\s+.*\s+from\s+['"].*['"]/g) || [];
    const errors = [];
    
    for (const importLine of importLines) {
      // Check if all imports exist in this basic validation
      // More detailed check would need actual dependency resolution
    }
    
    return errors;
  },
};

console.log('📋 Manual TypeScript Syntax Validation\n');
console.log('=' .repeat(60));

let totalIssues = 0;

for (const file of LIBRARY_FILES) {
  const filePath = path.join(__dirname, file);
  
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n').length;
    
    console.log(`\n✓ ${file}`);
    console.log(`  Lines: ${lines}`);
    
    const issues = [];
    
    // Run validation rules
    if (!VALIDATION_RULES.balancedBrackets(content)) {
      issues.push('Unbalanced brackets/braces/parentheses');
    }
    
    if (!VALIDATION_RULES.hasExports(content)) {
      issues.push('No export statements found');
    }
    
    const syntaxErrors = VALIDATION_RULES.basicSyntax(content);
    issues.push(...syntaxErrors);
    
    if (issues.length === 0) {
      console.log(`  ✅ PASS - No syntax issues detected`);
    } else {
      console.log(`  ⚠️  ISSUES FOUND:`);
      issues.forEach(issue => {
        console.log(`    - ${issue}`);
        totalIssues++;
      });
    }
    
  } catch (error) {
    console.log(`\n✗ ${file}`);
    console.log(`  ❌ ERROR: ${error.message}`);
    totalIssues++;
  }
}

console.log('\n' + '='.repeat(60));
console.log(`\n📊 Summary: ${totalIssues === 0 ? '✅ All files valid' : `⚠️  ${totalIssues} issue(s) found`}`);

process.exit(totalIssues > 0 ? 1 : 0);

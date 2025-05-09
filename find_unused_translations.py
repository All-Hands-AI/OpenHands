#!/usr/bin/env python3
import json
import os
import re
from typing import Set, Dict, List

def get_translation_keys_from_json(json_file_path: str) -> Set[str]:
    """Extract all translation keys from the translation.json file."""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    return set(translations.keys())

def get_translation_keys_from_declaration(declaration_file_path: str) -> Set[str]:
    """Extract all translation keys from the declaration.ts file."""
    with open(declaration_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract keys from the enum definition
    pattern = r'(\w+)\s*=\s*"(\w+\$\w+)"'
    matches = re.findall(pattern, content)
    return {key for _, key in matches}

def find_used_keys_in_codebase(frontend_dir: str) -> Set[str]:
    """Find all translation keys that are used in the codebase."""
    used_keys = set()
    
    # Patterns to match translation key usage
    patterns = [
        r't\(I18nKey\.(\w+\$\w+)',  # t(I18nKey.KEY$SUBKEY)
        r'i18next\.t\(I18nKey\.(\w+\$\w+)',  # i18next.t(I18nKey.KEY$SUBKEY)
        r'translate\(I18nKey\.(\w+\$\w+)',  # translate(I18nKey.KEY$SUBKEY)
        r'I18nKey\.(\w+\$\w+)',  # Any other reference to I18nKey.KEY$SUBKEY
    ]
    
    # Walk through all TypeScript and TypeScript React files
    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx', '.js', '.jsx')) and 'node_modules' not in root and 'declaration.ts' not in file:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for each pattern
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        used_keys.update(matches)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
    
    return used_keys

def main():
    # Paths
    frontend_dir = '/workspace/OpenHands/frontend'
    translation_json_path = os.path.join(frontend_dir, 'src/i18n/translation.json')
    declaration_ts_path = os.path.join(frontend_dir, 'src/i18n/declaration.ts')
    
    # Get all keys from both files
    json_keys = get_translation_keys_from_json(translation_json_path)
    declaration_keys = get_translation_keys_from_declaration(declaration_ts_path)
    
    # Find keys that are used in the codebase
    used_keys = find_used_keys_in_codebase(frontend_dir)
    
    # Find unused keys
    unused_json_keys = json_keys - used_keys
    unused_declaration_keys = declaration_keys - used_keys
    
    # Print results
    print(f"Total keys in translation.json: {len(json_keys)}")
    print(f"Total keys in declaration.ts: {len(declaration_keys)}")
    print(f"Total keys used in codebase: {len(used_keys)}")
    print(f"Unused keys in translation.json: {len(unused_json_keys)}")
    print(f"Unused keys in declaration.ts: {len(unused_declaration_keys)}")
    
    print("\nUnused keys in translation.json:")
    for key in sorted(unused_json_keys):
        print(f"  - {key}")
    
    print("\nUnused keys in declaration.ts:")
    for key in sorted(unused_declaration_keys):
        print(f"  - {key}")
    
    # Create a new translation.json without unused keys
    if unused_json_keys:
        with open(translation_json_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Create a new dictionary without unused keys
        cleaned_translations = {k: v for k, v in translations.items() if k not in unused_json_keys}
        
        # Save to a new file for review
        cleaned_json_path = os.path.join(frontend_dir, 'src/i18n/translation.cleaned.json')
        with open(cleaned_json_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_translations, f, indent=4, ensure_ascii=False)
        
        print(f"\nCleaned translation file saved to: {cleaned_json_path}")
    
    # Create a new declaration.ts without unused keys
    if unused_declaration_keys:
        with open(declaration_ts_path, 'r', encoding='utf-8') as f:
            declaration_content = f.readlines()
        
        # Filter out lines with unused keys
        cleaned_declaration_lines = []
        for line in declaration_content:
            skip_line = False
            for unused_key in unused_declaration_keys:
                if f'"{unused_key}"' in line:
                    skip_line = True
                    break
            if not skip_line:
                cleaned_declaration_lines.append(line)
        
        # Save to a new file for review
        cleaned_declaration_path = os.path.join(frontend_dir, 'src/i18n/declaration.cleaned.ts')
        with open(cleaned_declaration_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_declaration_lines)
        
        print(f"Cleaned declaration file saved to: {cleaned_declaration_path}")

if __name__ == "__main__":
    main()
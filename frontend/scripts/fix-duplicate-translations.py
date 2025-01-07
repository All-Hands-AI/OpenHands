#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from typing import Dict, List, Set

def load_json_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_json_file(file_path: str, content: dict) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
        f.write('\n')  # Add newline at end of file

def find_duplicate_keys(content: str) -> Dict[str, List[int]]:
    """Find all duplicate keys and their line numbers in the file."""
    key_pattern = r'"([^"]+)": {'
    matches = re.finditer(key_pattern, content)
    key_positions = defaultdict(list)
    
    for match in matches:
        key = match.group(1)
        # Get line number by counting newlines before this position
        line_number = content[:match.start()].count('\n') + 1
        key_positions[key].append(line_number)
    
    return {k: v for k, v in key_positions.items() if len(v) > 1}

def merge_translations(translations: List[dict]) -> dict:
    """Merge multiple translation objects, keeping all unique translations."""
    result = {}
    for trans in translations:
        for lang, text in trans.items():
            if lang not in result:
                result[lang] = text
            elif result[lang].lower() != text.lower():
                # If we have conflicting translations, prefer the one with proper capitalization
                if text[0].isupper():
                    result[lang] = text
    return result

def fix_duplicates(file_path: str) -> None:
    content = load_json_file(file_path)
    data = json.loads(content)
    
    # Find all duplicate keys
    duplicates = find_duplicate_keys(content)
    
    # Process each duplicate
    for key, positions in duplicates.items():
        print(f"Processing duplicate key: {key}")
        
        # Collect all translations for this key
        translations = []
        for pos in positions:
            if key in data:
                translations.append(data[key])
                del data[key]  # Remove the duplicate
        
        # Merge translations and add back to data
        if translations:
            data[key] = merge_translations(translations)
    
    # Save the fixed file
    save_json_file(file_path, data)

if __name__ == "__main__":
    file_path = "src/i18n/translation.json"
    fix_duplicates(file_path)
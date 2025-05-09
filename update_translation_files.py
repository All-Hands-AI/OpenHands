#!/usr/bin/env python3
import os
import shutil
import json

def main():
    # Paths
    frontend_dir = '/workspace/OpenHands/frontend'
    translation_json_path = os.path.join(frontend_dir, 'src/i18n/translation.json')
    declaration_ts_path = os.path.join(frontend_dir, 'src/i18n/declaration.ts')
    cleaned_json_path = os.path.join(frontend_dir, 'src/i18n/translation.cleaned.json')
    cleaned_declaration_path = os.path.join(frontend_dir, 'src/i18n/declaration.cleaned.ts')
    
    # Backup original files
    backup_dir = os.path.join(frontend_dir, 'src/i18n/backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    translation_backup = os.path.join(backup_dir, 'translation.json.bak')
    declaration_backup = os.path.join(backup_dir, 'declaration.ts.bak')
    
    shutil.copy2(translation_json_path, translation_backup)
    shutil.copy2(declaration_ts_path, declaration_backup)
    
    print(f"Original files backed up to {backup_dir}")
    
    # Replace with cleaned files
    shutil.copy2(cleaned_json_path, translation_json_path)
    shutil.copy2(cleaned_declaration_path, declaration_ts_path)
    
    print(f"Files updated with cleaned versions")
    
    # Count keys in new files
    with open(translation_json_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    with open(declaration_ts_path, 'r', encoding='utf-8') as f:
        declaration_content = f.read()
        enum_entries = declaration_content.count(' = "')
    
    print(f"New translation.json contains {len(translations)} keys")
    print(f"New declaration.ts contains approximately {enum_entries} keys")
    
    # Clean up temporary files
    os.remove(cleaned_json_path)
    os.remove(cleaned_declaration_path)
    print("Temporary files removed")

if __name__ == "__main__":
    main()
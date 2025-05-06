#!/usr/bin/env python3
import os
import re

# List of translation files to update
translation_files = [
    "docs/i18n/fr/docusaurus-plugin-content-docs/current/usage/configuration-options.md",
    "docs/i18n/ja/docusaurus-plugin-content-docs/current/usage/configuration-options.md",
    "docs/i18n/zh-Hans/docusaurus-plugin-content-docs/current/usage/configuration-options.md",
    "docs/i18n/pt-BR/docusaurus-plugin-content-docs/current/usage/configuration-options.md"
]

# Function to update a file
def update_file(file_path):
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Mark workspace_base as deprecated
        content = re.sub(
            r'(`workspace_base`)\s*\n\s*- Type',
            r'\1 **(Deprecated)**\n  - Type', 
            content
        )
        
        # Add sandbox volumes parameter
        sandbox_config_pattern = r'(\*\*Configuration du bac à sable\*\*|\*\*サンドボックス設定\*\*|\*\*沙盒配置\*\*|\*\*Configuração do Sandbox\*\*)'
        if re.search(sandbox_config_pattern, content):
            # Add volumes parameter after the sandbox configuration heading
            volumes_param = """- `volumes`
  - Type : `str`
  - Valeur par défaut : `None`
  - Description : Montages de volumes au format 'chemin_hôte:chemin_conteneur[:mode]', par exemple '/mon/répertoire/hôte:/workspace:rw'. Plusieurs montages peuvent être spécifiés en utilisant des virgules, par exemple '/chemin1:/workspace/chemin1,/chemin2:/workspace/chemin2:ro'

"""
            content = re.sub(
                sandbox_config_pattern + r'\s*\n',
                r'\1\n\n' + volumes_param,
                content
            )
        
        # Mark workspace_mount_path_in_sandbox as deprecated
        content = re.sub(
            r'(`workspace_mount_path_in_sandbox`)\s*\n\s*- Type',
            r'\1 **(Deprecated)**\n  - Type', 
            content
        )
        
        # Mark workspace_mount_path as deprecated
        content = re.sub(
            r'(`workspace_mount_path`)\s*\n\s*- Type',
            r'\1 **(Deprecated)**\n  - Type', 
            content
        )
        
        # Mark workspace_mount_rewrite as deprecated
        content = re.sub(
            r'(`workspace_mount_rewrite`)\s*\n\s*- Type',
            r'\1 **(Deprecated)**\n  - Type', 
            content
        )
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"Updated {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

# Update all translation files
success_count = 0
for file_path in translation_files:
    if update_file(file_path):
        success_count += 1

print(f"Updated {success_count} out of {len(translation_files)} translation files")
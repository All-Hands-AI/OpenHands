#!/usr/bin/env python3
"""
Script to update translations for configuration-options.md
"""

import os
import re

def update_workspace_base(content):
    """Update workspace_base section to mark as deprecated"""
    pattern = r'(### Workspace\n- `workspace_base`\n  - [^\n]+\n  - [^\n]+\n  - [^\n]+)'
    replacement = r'\1 **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**'
    
    # Add (Deprecated) marker
    content = re.sub(r'(### Workspace\n- `workspace_base`)', r'\1 **(Obsoleto)**', content)
    
    # Add deprecation message
    content = re.sub(pattern, replacement, content)
    
    return content

def update_sandbox_config(content):
    """Update sandbox configuration section to mark workspace_* params as deprecated and add volumes param"""
    # Pattern to match the entire sandbox configuration section
    pattern = r'(### Configuração do Sandbox\n)(- `workspace_mount_path_in_sandbox`\n  - [^\n]+\n  - [^\n]+\n  - [^\n]+\n\n- `workspace_mount_path`\n  - [^\n]+\n  - [^\n]+\n  - [^\n]+\n\n- `workspace_mount_rewrite`\n  - [^\n]+\n  - [^\n]+\n  - [^\n]+)'
    
    # New content with volumes parameter and deprecated markers
    replacement = r'\1\n- `volumes`\n  - Tipo: `str`\n  - Padrão: `None`\n  - Descrição: Montagens de volume no formato \'caminho_host:caminho_container[:modo]\', por exemplo \'/meu/diretorio/host:/workspace:rw\'. Múltiplas montagens podem ser especificadas usando vírgulas, por exemplo \'/caminho1:/workspace/caminho1,/caminho2:/workspace/caminho2:ro\'\n\n- `workspace_mount_path_in_sandbox` **(Obsoleto)**\n  - Tipo: `str`\n  - Padrão: `"/workspace"`\n  - Descrição: Caminho para montar o workspace no sandbox. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**\n\n- `workspace_mount_path` **(Obsoleto)**\n  - Tipo: `str`\n  - Padrão: `""`\n  - Descrição: Caminho para montar o workspace. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**\n\n- `workspace_mount_rewrite` **(Obsoleto)**\n  - Tipo: `str`\n  - Padrão: `""`\n  - Descrição: Caminho para reescrever o caminho de montagem do workspace. Você geralmente pode ignorar isso, refere-se a casos especiais de execução dentro de outro contêiner. **Obsoleto: Use `SANDBOX_VOLUMES` em vez disso.**'
    
    content = re.sub(pattern, replacement, content)
    
    return content

def process_file(file_path):
    """Process a single translation file"""
    print(f"Processing {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update workspace_base section
        content = update_workspace_base(content)
        
        # Update sandbox configuration section
        content = update_sandbox_config(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    """Main function"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    i18n_dir = os.path.join(base_dir, 'docs', 'i18n')
    
    # List of languages to process
    languages = ['ja', 'zh-Hans', 'pt-BR', 'fr']
    
    for lang in languages:
        file_path = os.path.join(i18n_dir, lang, 'docusaurus-plugin-content-docs', 'current', 'usage', 'configuration-options.md')
        if os.path.exists(file_path):
            process_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
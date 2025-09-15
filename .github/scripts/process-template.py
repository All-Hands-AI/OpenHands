#!/usr/bin/env python3
"""
Template processor for release reports using Python's built-in string.Template.
Much cleaner than bash/sed approach and no external dependencies!
"""

import os
import sys
from datetime import datetime, timezone
from string import Template

def main():
    if len(sys.argv) < 8:
        print("❌ Error: Not enough arguments provided")
        print("Usage: process-template.py <template_file> <output_file> <tag> <bucket> <tag_folder> <download_url> <repository> <run_id> [url_length] [expires_at]")
        sys.exit(1)
    
    template_file = sys.argv[1]
    output_file = sys.argv[2]
    tag = sys.argv[3]
    bucket = sys.argv[4]
    tag_folder = sys.argv[5]
    download_url = sys.argv[6]
    repository = sys.argv[7]
    run_id = sys.argv[8]
    url_length = sys.argv[9] if len(sys.argv) > 9 else 'unknown'
    expires_at = sys.argv[10] if len(sys.argv) > 10 else 'unknown'
    
    # Validate template file exists
    if not os.path.exists(template_file):
        print(f"❌ Error: Template file not found: {template_file}")
        sys.exit(1)
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print("🔄 Processing template with Python string.Template...")
    print(f"  Template: {template_file}")
    print(f"  Output: {output_file}")
    print(f"  Tag: {tag}")
    print(f"  Bucket: {bucket}")
    print(f"  Repository: {repository}")
    print(f"  Run ID: {run_id}")
    print()
    
    try:
        # Load template
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Convert {{variable}} syntax to $variable for string.Template
        # This is much simpler than using regex or complex string manipulation
        template_content = template_content.replace('{{TAG}}', '$TAG')
        template_content = template_content.replace('{{BUCKET}}', '$BUCKET')
        template_content = template_content.replace('{{TAG_FOLDER}}', '$TAG_FOLDER')
        template_content = template_content.replace('{{DOWNLOAD_URL}}', '$DOWNLOAD_URL')
        template_content = template_content.replace('{{REPOSITORY}}', '$REPOSITORY')
        template_content = template_content.replace('{{RUN_ID}}', '$RUN_ID')
        template_content = template_content.replace('{{TIMESTAMP}}', '$TIMESTAMP')
        template_content = template_content.replace('{{URL_LENGTH}}', '$URL_LENGTH')
        template_content = template_content.replace('{{EXPIRES_AT}}', '$EXPIRES_AT')
        
        # Create template object (using Python's built-in string.Template)
        template = Template(template_content)
        
        # Prepare context
        context = {
            'TAG': tag,
            'BUCKET': bucket,
            'TAG_FOLDER': tag_folder,
            'DOWNLOAD_URL': download_url,
            'REPOSITORY': repository,
            'RUN_ID': run_id,
            'TIMESTAMP': timestamp,
            'URL_LENGTH': url_length,
            'EXPIRES_AT': expires_at
        }
        
        # Render template (string.Template uses safe_substitute to avoid KeyError)
        rendered_content = template.safe_substitute(**context)
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        # Verify output
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            print("❌ Error: Failed to create output file or file is empty")
            sys.exit(1)
        
        # Check for unreplaced tokens
        if '{{' in rendered_content:
            print("⚠️  Warning: Some template tokens were not replaced")
            import re
            unreplaced = re.findall(r'\{\{[^}]+\}\}', rendered_content)
            for token in set(unreplaced):
                print(f"  - {token}")
        
        output_size = os.path.getsize(output_file)
        print("✅ Template processed successfully")
        print(f"  File: {output_file}")
        print(f"  Size: {output_size} bytes")
        
    except Exception as e:
        print(f"❌ Error processing template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

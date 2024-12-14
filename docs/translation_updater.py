import hashlib
import json
import os
import sys

import anthropic
import frontmatter
import yaml

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print('Error: ANTHROPIC_API_KEY environment variable not set')
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

DOCS_DIR = 'docs/'
CACHE_FILE = os.path.join(DOCS_DIR, 'translation_cache.json')

# Supported languages and their codes
LANGUAGES = {'fr': 'French', 'zh-Hans': 'Simplified Chinese'}


def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def load_file_hashes():
    """Load previously saved file hashes."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_file_hashes(hashes):
    """Save current file hashes."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(hashes, f)


def get_translation_path(source_path, lang):
    """Get the corresponding translation file path for a source file."""
    relative_path = os.path.relpath(source_path, 'docs/modules')
    return f'docs/i18n/{lang}/docusaurus-plugin-content-docs/current/{relative_path}'


def translate_content(content, target_lang):
    """Translate content using Anthropic's Claude."""
    system_prompt = f'You are a professional translator. Translate the following content into {target_lang}. Preserve all Markdown formatting, code blocks, and front matter. Keep any {{% jsx %}} tags and similar intact. Do not translate code examples, URLs, or technical terms.'

    message = client.messages.create(
        model='claude-3-opus-20240229',
        max_tokens=4096,
        temperature=0,
        system=system_prompt,
        messages=[
            {'role': 'user', 'content': f'Please translate this content:\n\n{content}'}
        ],
    )

    return message.content[0].text


def process_file(source_path, lang):
    """Process a single file for translation."""
    # Skip non-markdown files
    if not source_path.endswith(('.md', '.mdx')):
        return

    translation_path = get_translation_path(source_path, lang)
    os.makedirs(os.path.dirname(translation_path), exist_ok=True)

    # Read source content
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter if exists
    has_frontmatter = content.startswith('---')
    if has_frontmatter:
        post = frontmatter.loads(content)
        metadata = post.metadata
        content_without_frontmatter = post.content
    else:
        metadata = {}
        content_without_frontmatter = content

    # Translate the content
    print('translating...', source_path, lang)
    translated_content = translate_content(content_without_frontmatter, LANGUAGES[lang])
    print('translation done')

    # Reconstruct the file with frontmatter if it existed
    if has_frontmatter:
        final_content = '---\n'
        final_content += yaml.dump(metadata, allow_unicode=True)
        final_content += '---\n\n'
        final_content += translated_content
    else:
        final_content = translated_content

    # Write the translated content
    with open(translation_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f'Updated translation for {source_path} in {lang}')


def main():
    previous_hashes = load_file_hashes()

    current_hashes = {}

    # Walk through all files in docs/modules
    for root, _, files in os.walk('docs/modules'):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                filepath = os.path.join(root, file)
                current_hash = get_file_hash(filepath)
                current_hashes[filepath] = current_hash

                # Check if file is new or modified
                if (
                    filepath not in previous_hashes
                    or previous_hashes[filepath] != current_hash
                ):
                    print(f'Change detected in {filepath}')
                    for lang in LANGUAGES:
                        process_file(filepath, lang)

    print('all files up to date, saving hashes')
    save_file_hashes(current_hashes)
    previous_hashes = current_hashes


if __name__ == '__main__':
    main()

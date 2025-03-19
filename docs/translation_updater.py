import hashlib
import asyncio
import json
import os
import sys
from typing import List, Tuple

import anthropic
import frontmatter
import yaml
from anthropic.types import ContentBlock

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print('Error: ANTHROPIC_API_KEY environment variable not set')
    sys.exit(1)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

BATCH_SIZE = 10  # Number of translations to process concurrently

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(DOCS_DIR, 'translation_cache.json')

# Supported languages and their codes
LANGUAGES = {
    'ar': 'Arabic',
    'de': 'German',
    'es': 'Spanish',
    'fa': 'Persian',
    'fr': 'French',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko-KR': 'Korean',
    'no': 'Norwegian',
    'pt': 'Portuguese',
    'tr': 'Turkish',
    'zh-Hans': 'Simplified Chinese',
    'zh-TW': 'Traditional Chinese'
}


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
    relative_path = os.path.relpath(source_path, 'modules')
    return os.path.join(DOCS_DIR, 'i18n', lang, 'docusaurus-plugin-content-docs/current', relative_path)


async def translate_content(content: str, target_lang: str) -> str:
    """Translate content using Anthropic's Claude."""
    system_prompt = f'You are a professional translator. Translate the following content into {target_lang}. Preserve all Markdown formatting, code blocks, and front matter. Keep any {{% jsx %}} tags and similar intact. Do not translate code examples, URLs, or technical terms.'

    try:
        async with asyncio.timeout(120):  # 120 second timeout
            message = await client.messages.create(
                model='claude-3-opus-20240229',
                max_tokens=4096,
                temperature=0,
                system=system_prompt,
                messages=[
                    {'role': 'user', 'content': f'Please translate this content:\n\n{content}'}
                ],
            )
            return message.content[0].text
    except asyncio.TimeoutError:
        raise Exception("Translation timed out after 120 seconds")
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

async def process_translation_batch(batch: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Process a batch of translations concurrently.
    
    Args:
        batch: List of (filepath, content, lang) tuples
        
    Returns:
        List of (filepath, translated_content, lang) tuples
    """
    tasks = []
    for filepath, content, lang in batch:
        print(f"Starting translation of {filepath} to {lang}")
        task = translate_content(content, LANGUAGES[lang])
        tasks.append(task)
    
    try:
        translations = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for i, translation in enumerate(translations):
            filepath, content, lang = batch[i]
            if isinstance(translation, Exception):
                print(f"Error translating {filepath} to {lang}: {translation}")
                continue
            results.append((filepath, translation, lang))
        return results
    except Exception as e:
        print(f"Error processing batch: {e}")
        return []


def prepare_file_for_translation(source_path: str) -> Tuple[str, bool, dict]:
    """Prepare a file for translation by extracting content and metadata.
    
    Returns:
        Tuple of (content_without_frontmatter, has_frontmatter, metadata)
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    has_frontmatter = content.startswith('---')
    if has_frontmatter:
        post = frontmatter.loads(content)
        metadata = post.metadata
        content_without_frontmatter = post.content
    else:
        metadata = {}
        content_without_frontmatter = content
        
    return content_without_frontmatter, has_frontmatter, metadata

def write_translated_file(translation_path: str, translated_content: str, has_frontmatter: bool, metadata: dict):
    """Write translated content to a file, including frontmatter if needed."""
    os.makedirs(os.path.dirname(translation_path), exist_ok=True)
    
    if has_frontmatter:
        final_content = '---\n'
        final_content += yaml.dump(metadata, allow_unicode=True)
        final_content += '---\n\n'
        final_content += translated_content
    else:
        final_content = translated_content

    with open(translation_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

async def process_files(files_to_translate: List[Tuple[str, str]]):
    """Process multiple files in batches."""
    current_batch = []
    total_files = len(files_to_translate)
    processed_files = 0
    
    print(f"\nProcessing {total_files} files...")
    
    for filepath, lang in files_to_translate:
        try:
            content, has_frontmatter, metadata = prepare_file_for_translation(filepath)
            translation_path = get_translation_path(filepath, lang)
            
            # Store all info needed to process and write the translation
            current_batch.append((filepath, content, lang, translation_path, has_frontmatter, metadata))
            
            if len(current_batch) >= BATCH_SIZE:
                # Process current batch
                translation_batch = [(f[0], f[1], f[2]) for f in current_batch]
                results = await process_translation_batch(translation_batch)
                
                # Write results
                for result in results:
                    filepath, translated_content, lang = result
                    # Find matching batch item
                    batch_item = next(item for item in current_batch if item[0] == filepath and item[2] == lang)
                    _, _, _, translation_path, has_frontmatter, metadata = batch_item
                    write_translated_file(translation_path, translated_content, has_frontmatter, metadata)
                    print(f'Updated translation for {filepath} in {lang}')
                    processed_files += 1
                
                print(f"\nProgress: {processed_files}/{total_files} files processed")
                current_batch = []
        except Exception as e:
            print(f"Error processing {filepath} for {lang}: {e}")
            continue
    
    # Process remaining files
    if current_batch:
        try:
            translation_batch = [(f[0], f[1], f[2]) for f in current_batch]
            results = await process_translation_batch(translation_batch)
            
            for result in results:
                filepath, translated_content, lang = result
                # Find matching batch item
                batch_item = next(item for item in current_batch if item[0] == filepath and item[2] == lang)
                _, _, _, translation_path, has_frontmatter, metadata = batch_item
                write_translated_file(translation_path, translated_content, has_frontmatter, metadata)
                print(f'Updated translation for {filepath} in {lang}')
                processed_files += 1
            
            print(f"\nProgress: {processed_files}/{total_files} files processed")
        except Exception as e:
            print(f"Error processing final batch: {e}")
    
    print(f"\nCompleted! {processed_files}/{total_files} files processed successfully")


async def main():
    previous_hashes = load_file_hashes()
    print(f"Previous hashes: {previous_hashes}")

    current_hashes = {}
    files_to_translate = []

    # Walk through all files in docs/modules
    for root, _, files in os.walk('modules'):
        print(f"Scanning directory: {root}")
        for file in files:
            if file.endswith(('.md', '.mdx')):
                filepath = os.path.join(root, file)
                print(f"Found file: {filepath}")
                current_hash = get_file_hash(filepath)
                current_hashes[filepath] = current_hash
                print(f"Hash: {current_hash}")

                # Check if file is new or modified
                if (
                    filepath not in previous_hashes
                    or previous_hashes[filepath] != current_hash
                ):
                    print(f'Change detected in {filepath}')
                    for lang in LANGUAGES:
                        files_to_translate.append((filepath, lang))

    if files_to_translate:
        await process_files(files_to_translate)

    print('all files up to date, saving hashes')
    save_file_hashes(current_hashes)
    previous_hashes = current_hashes


if __name__ == '__main__':
    asyncio.run(main())

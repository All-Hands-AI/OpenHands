# Translation Keys Cleanup

This PR removes unused translation keys from the frontend i18n files.

## What was done

1. Created a script (`find_unused_translations.py`) to identify translation keys that are not used anywhere in the frontend codebase.
2. Removed 265 unused keys from `frontend/src/i18n/translation.json` and 261 unused keys from `frontend/src/i18n/declaration.ts`.
3. Verified that the frontend still builds correctly after removing the unused keys.

## Results

- Original translation.json: 523 keys
- Cleaned translation.json: 258 keys
- Original declaration.ts: 519 keys
- Cleaned declaration.ts: 258 keys

## How it works

The script:
1. Extracts all translation keys from both `translation.json` and `declaration.ts`
2. Scans the entire frontend codebase for usage of these keys in patterns like:
   - `t(I18nKey.KEY$SUBKEY)`
   - `i18next.t(I18nKey.KEY$SUBKEY)`
   - `translate(I18nKey.KEY$SUBKEY)`
   - Any other reference to `I18nKey.KEY$SUBKEY`
3. Identifies keys that are not used anywhere
4. Creates cleaned versions of both files

## Benefits

- Reduced file size for translation files
- Easier maintenance of translations
- Cleaner codebase with less unused code
- Better developer experience when working with translations

## How to run the cleanup again in the future

If you need to clean up unused translation keys again in the future, you can run:

```bash
python3 find_unused_translations.py
python3 update_translation_files.py
cd frontend && npm run make-i18n && npm run build
```

This will:
1. Find unused keys
2. Update the translation files (with backups)
3. Regenerate the i18n declaration file
4. Verify the build works correctly
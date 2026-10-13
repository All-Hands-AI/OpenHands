# LLM profile contracts

### LLP-001: A new profile preserves its form's non-secret options

- [x] Saving a new profile persists the form's untouched inherited options as
      well as explicit edits, using the schema's normal value coercion.
- [x] Fresh profiles begin with schema-declared credentials blank. Existing
      redacted or encrypted credentials are never copied by option inheritance;
      credentials explicitly entered in the new form are saved.
- [x] An untouched nullable boolean with a null default and a null or omitted
      raw value retains provider auto-detection. Its normalized unchecked
      appearance does not become an explicit false override. An inherited
      explicit false and dirty boolean edits retain their meaning.
- [x] Background settings refreshes do not change the raw origin of an open
      draft. Editing an existing profile continues to merge over its saved config.

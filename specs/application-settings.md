# Application settings contracts

### APS-001: A failed Save preserves the user's draft

- [x] Saving application settings keeps the form mounted. Its controls are
      disabled while the request is pending, preventing a concurrent edit/save.
- [x] A failed request displays its error and retains checkbox, text, and other
      draft values. Save becomes available for retry without re-entering edits.
- [x] A successful request clears dirty state only after persistence succeeds.
      Native form submission does not reset uncontrolled inputs on failure.

# Publishing Process

1. **Version Check**: The workflow first checks if the version in `package.json` has changed compared to the previous commit
2. **Build**: If version changed, it sets up Bun, installs dependencies, and builds the package
3. **Duplicate Check**: Verifies the version doesn't already exist on npm
4. **Publish**: Publishes the package to npm using the `NPM_TOKEN` secret

# Publishing a New Version

1. **Update the version** in `openhands-ui/package.json`:

   ```bash
   cd openhands-ui
   # For patch release (1.0.0 → 1.0.1)
   npm version patch

   # For minor release (1.0.0 → 1.1.0)
   npm version minor

   # For major release (1.0.0 → 2.0.0)
   npm version major

   # For pre-release (1.0.0 → 1.0.1-beta.0)
   npm version prerelease --preid=beta
   ```

2. **Commit and push** the version change:

   ```bash
   git add package.json
   git commit -m "chore(ui): bump version to X.X.X"
   ```

3. **Create a PR** with your changes and the version bump

4. **Merge the PR** - the package will be automatically published

## Manual Publishing (Fallback)

If the automated workflow fails, you can manually publish:

```bash
cd openhands-ui
bun install
bun run build
npm publish
```

## Version Strategy

- **Patch** (X.X.1): Bug fixes, small improvements
- **Minor** (X.1.X): New features, non-breaking changes
- **Major** (1.X.X): Breaking changes
- **Pre-release** (X.X.X-beta.X): Beta versions for testing

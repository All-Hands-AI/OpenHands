# Publishing Process

1. **Version Check**: The workflow first checks if the version in `package.json` has changed compared to the previous commit
2. **Build**: If version changed, it sets up Bun, installs dependencies, and builds the package
3. **Duplicate Check**: Verifies the version doesn't already exist on npm
4. **Publish**: Publishes the package to npm using the `NPM_TOKEN` secret

# OpenHands Documentation

This directory contains the documentation for OpenHands. The documentation is automatically synchronized with the [All-Hands-AI/docs](https://github.com/All-Hands-AI/docs) repository, which hosts the unified documentation site using Mintlify.

## Documentation Structure

The documentation files in this directory are automatically included in the main documentation site via Git submodules. When you make changes to documentation in this repository, they will be automatically synchronized to the docs repository.

## How It Works

1. **Automatic Sync**: When documentation changes are pushed to the `main` branch, a GitHub Action automatically notifies the docs repository
2. **Submodule Update**: The docs repository updates its submodule reference to include your latest changes  
3. **Site Rebuild**: Mintlify automatically rebuilds and deploys the documentation site

## Making Documentation Changes

Simply edit the documentation files in this directory as usual. The synchronization happens automatically when changes are merged to the main branch.

## Local Development

For local documentation development in this repository only:

```bash
npm install -g mint
# or
yarn global add mint

# Preview local changes
mint dev
```

For the complete unified documentation site, work with the [All-Hands-AI/docs](https://github.com/All-Hands-AI/docs) repository.

## Configuration

The Mintlify configuration (`docs.json`) has been moved to the root of the [All-Hands-AI/docs](https://github.com/All-Hands-AI/docs) repository to enable unified documentation across multiple repositories.

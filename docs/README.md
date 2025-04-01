# OpenHands Documentation

This website is built using [Docusaurus](https://docusaurus.io/).

When published, the content will be published at https://docs.all-hands.dev/.

### Installation

```bash
$ cd docs
$ yarn
```

### Local Development

```
$ yarn start # for the default English version
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

Alternatively, you can pass a `--locale` argument to render a specific language in dev mode as in:

```
$ yarn start --locale pt-BR # for the Brazilian Portuguese version
$ yarn start --locale fr # for the French version
$ yarn start --locale zh-Hans # for the Chinese Han (simplified variant) version
```

### Build

```
$ yarn build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

It compiles all languages.

### Deployment

Open a new pull request and - when it is merged - the [deploy-docs](.github/workflows/deploy-docs.yml) GH action will take care of everything else.

## Automatic Translations

Translations can be automatically updated when the original English content changes, this is done by the script [`translation_updater.py`](./translation_updater.py).

From the root of the repository, you can run the following:

```bash
$ export ANTHROPIC_API_KEY=<your_api_key>
$ poetry run python docs/translation_updater.py
# ...
# Change detected in docs/modules/usage/getting-started.mdx
# translating... docs/modules/usage/getting-started.mdx pt-BR
# translation done
# ...
```

This process uses `claude-3-7-sonnet-20250219` as base model and each language consumes at least ~30k input tokens and ~35k output tokens.

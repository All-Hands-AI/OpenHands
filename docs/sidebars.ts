import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  apiSidebar: [require("./modules/python/sidebar.json")],
  docsSidebar: [
    {
      type: 'doc',
      label: 'Installation',
      id: 'usage/installation',
    },
    {
      type: 'doc',
      label: 'Getting Started',
      id: 'usage/getting-started',
    },
    {
      type: 'category',
      label: 'Prompting',
      items: [
        {
          type: 'doc',
          label: 'Best Practices',
          id: 'usage/prompting/prompting-best-practices',
        },
        {
          type: 'category',
          label: 'Micro-Agents',
          items: [
            {
              type: 'doc',
              label: 'Public',
              id: 'usage/prompting/microagents-public',
            },
            {
              type: 'doc',
              label: 'Repository',
              id: 'usage/prompting/microagents-repo',
            },
          ],
        }
      ],
    },
    {
      type: 'category',
      label: 'Usage Methods',
      items: [
        {
          type: 'doc',
          label: 'GUI Mode',
          id: 'usage/how-to/gui-mode',
        },
        {
          type: 'doc',
          label: 'CLI Mode',
          id: 'usage/how-to/cli-mode',
        },
        {
          type: 'doc',
          label: 'Headless Mode',
          id: 'usage/how-to/headless-mode',
        },
        {
          type: 'doc',
          label: 'Github Actions',
          id: 'usage/how-to/github-action',
        },
      ],
    },
    {
      type: 'category',
      label: 'Advanced Configuration',
      items: [
        {
          type: 'category',
          label: 'LLM Configuration',
          items: [
            {
              type: 'doc',
              label: 'Overview',
              id: 'usage/llms/llms',
            },
            {
              type: 'category',
              label: 'Providers',
              items: [
                {
                  type: 'doc',
                  label: 'Azure',
                  id: 'usage/llms/azure-llms',
                },
                {
                  type: 'doc',
                  label: 'Google',
                  id: 'usage/llms/google-llms',
                },
                {
                  type: 'doc',
                  label: 'Groq',
                  id: 'usage/llms/groq',
                },
                {
                  type: 'doc',
                  label: 'LiteLLM Proxy',
                  id: 'usage/llms/litellm-proxy',
                },
                {
                  type: 'doc',
                  label: 'OpenAI',
                  id: 'usage/llms/openai-llms',
                },
                {
                  type: 'doc',
                  label: 'OpenRouter',
                  id: 'usage/llms/openrouter',
                },
              ],
            },
          ],
        },
        {
          type: 'doc',
          label: 'Runtime Configuration',
          id: 'usage/runtimes',
        },
        {
          type: 'doc',
          label: 'Configuration Options',
          id: 'usage/configuration-options',
        },
        {
          type: 'doc',
          label: 'Custom Sandbox',
          id: 'usage/how-to/custom-sandbox-guide',
        },
        {
          type: 'doc',
          label: 'Persist Session Data',
          id: 'usage/how-to/persist-session-data',
        },
      ],
    },
    {
      type: 'doc',
      label: 'Troubleshooting',
      id: 'usage/troubleshooting/troubleshooting',
    },
    {
      type: 'doc',
      label: 'Feedback',
      id: 'usage/feedback',
    },
    {
      type: 'category',
      label: 'For OpenHands Developers',
      items: [
        {
          type: 'category',
          label: 'Architecture',
          items: [
            {
              type: 'doc',
              label: 'Backend',
              id: 'usage/architecture/backend',
            },
            {
              type: 'doc',
              label: 'Runtime',
              id: 'usage/architecture/runtime',
            },
          ],
        },
        {
          type: 'doc',
          label: 'Debugging',
          id: 'usage/how-to/debugging',
        },
        {
          type: 'doc',
          label: 'Evaluation',
          id: 'usage/how-to/evaluation-harness',
        },
      ],
    },
    {
      type: 'doc',
      label: 'About',
      id: 'usage/about',
    }
  ],
};

export default sidebars;

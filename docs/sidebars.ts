import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  apiSidebar: [require("./modules/python/sidebar.json")],
  docsSidebar: [
    {
      type: 'doc',
      label: 'Getting Started',
      id: 'usage/getting-started',
    },
    {
      type: 'category',
      label: 'LLMs',
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
              label: 'OpenAI',
              id: 'usage/llms/openai-llms',
            },
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
              label: 'Local/ollama',
              id: 'usage/llms/local-llms',
            }
          ],
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
      label: 'How-to Guides',
      items: [
        {
          type: 'doc',
          id: 'usage/how-to/cli-mode',
        },
        {
          type: 'doc',
          id: 'usage/how-to/headless-mode',
        },
        {
          type: 'doc',
          id: 'usage/how-to/custom-sandbox-guide',
        },
        {
          type: 'doc',
          id: 'usage/how-to/evaluation-harness',
        },
        {
          type: 'doc',
          id: 'usage/how-to/openshift-example',
        }
      ]
    },
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
        }
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

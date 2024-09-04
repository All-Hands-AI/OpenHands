import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  apiSidebar: [require("./modules/python/sidebar.json")],
  docsSidebar: [{
    type: 'doc',
    label: 'Getting Started',
    id: 'usage/getting-started',
  }, {
    type: 'doc',
    label: 'Troubleshooting',
    id: 'usage/troubleshooting/troubleshooting',
  }, {
    type: 'doc',
    label: 'Feedback',
    id: 'usage/feedback',
  }, {
    type: 'category',
    label: 'How-to Guides',
      items: [{
        type: 'doc',
        id: 'usage/how-to/cli-mode',
      }, {
        type: 'doc',
        id: 'usage/how-to/headless-mode',
      }, {
        type: 'doc',
        id: 'usage/how-to/custom-sandbox-guide',
      }, {
        type: 'doc',
        id: 'usage/how-to/evaluation-harness',
      }, {
        type: 'doc',
        id: 'usage/how-to/openshift-example',
      }]
  }, {
    type: 'doc',
    label: 'LLMs',
    id: 'usage/llms/llms',
  }, {
    type: 'doc',
    label: 'Architecture',
    id: 'usage/architecture/architecture',
  }, {
    type: 'doc',
    label: 'About',
    id: 'usage/about',
  }],
};

export default sidebars;

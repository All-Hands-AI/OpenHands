import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  apiSidebar: [require("./modules/python/sidebar.json")],
  docsSidebar: [{
    type: 'doc',
    label: 'Getting Started',
    id: 'usage/getting-started',
  }, {
    type: 'doc',
    label: 'LLMs',
    id: 'usage/llms/llms',
  }, {
    type: 'doc',
    label: 'Troubleshooting',
    id: 'usage/troubleshooting/troubleshooting',
  }, {
    type: 'doc',
    label: 'Feedback',
    id: 'usage/feedback',
  }, {
    type: 'doc',
    label: 'How To',
    id: 'usage/how-to/how-to',
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

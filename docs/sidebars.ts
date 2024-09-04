import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  apiSidebar: [require("./modules/python/sidebar.json")],
  docsSidebar: [{
    type: 'doc',
    label: 'Getting Started',
    id: 'getting-started',
  }, {
    type: 'doc',
    label: 'LLMs',
    id: 'llms/llms',
  }, {
    type: 'doc',
    label: 'Troubleshooting',
    id: 'troubleshooting/troubleshooting',
  }, {
    type: 'doc',
    label: 'Feedback',
    id: 'feedback',
  }, {
    type: 'doc',
    label: 'How To',
    id: 'how-to/how-to',
  }, {
    type: 'doc',
    label: 'Architecture',
    id: 'architecture/architecture',
  }, {
    type: 'doc',
    label: 'About',
    id: 'about',
  }],
};

export default sidebars;

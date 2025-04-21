import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';
import openApiSidebar from './openapi/sidebar';

const sidebars: SidebarsConfig = {
  apiSidebar: [
    {
      type: "doc",
      id: "index",
      label: "API Overview",
    },
    {
      type: "category",
      label: "REST API Reference",
      items: openApiSidebar,
    },
  ],
};

export default sidebars;
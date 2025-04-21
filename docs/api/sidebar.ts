import openApiSidebar from './openapi/sidebar';

export default [
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
];
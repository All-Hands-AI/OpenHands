import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "open/openhands-api",
    },
    {
      type: "category",
      label: "UNTAGGED",
      items: [
        {
          type: "doc",
          id: "open/health",
          label: "Health check",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-remote-runtime-config",
          label: "Get runtime configuration",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-vscode-url",
          label: "Get VSCode URL",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-hosts",
          label: "Get runtime hosts",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/submit-feedback",
          label: "Submit feedback",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/list-files",
          label: "List files",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/select-file",
          label: "Get file content",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/zip-current-workspace",
          label: "Download workspace as zip",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/git-changes",
          label: "Get git changes",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/git-diff",
          label: "Get git diff",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-trajectory",
          label: "Get trajectory",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/security-api-get",
          label: "Security analyzer API (GET)",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/security-api-post",
          label: "Security analyzer API (POST)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/security-api-put",
          label: "Security analyzer API (PUT)",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "open/security-api-delete",
          label: "Security analyzer API (DELETE)",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "open/new-conversation",
          label: "Create new conversation",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/search-conversations",
          label: "Search conversations",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-conversation",
          label: "Get conversation",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/update-conversation",
          label: "Update conversation",
          className: "api-method patch",
        },
        {
          type: "doc",
          id: "open/delete-conversation",
          label: "Delete conversation",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "open/get-user-repositories",
          label: "Get user repositories",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-user",
          label: "Get user info",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/search-repositories",
          label: "Search repositories",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-suggested-tasks",
          label: "Get suggested tasks",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/load-settings",
          label: "Get settings",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/store-settings",
          label: "Store settings",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/unset-settings-tokens",
          label: "Unset settings tokens",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/reset-settings",
          label: "Reset settings",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "open/get-litellm-models",
          label: "Get models",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-agents",
          label: "Get agents",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-security-analyzers",
          label: "Get security analyzers",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "open/get-config",
          label: "Get config",
          className: "api-method get",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;

import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "openhands-api",
    },
    {
      type: "category",
      label: "UNTAGGED",
      items: [
        {
          type: "doc",
          id: "health",
          label: "Health check",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-remote-runtime-config",
          label: "Get runtime configuration",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-vscode-url",
          label: "Get VSCode URL",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-hosts",
          label: "Get runtime hosts",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "submit-feedback",
          label: "Submit feedback",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "list-files",
          label: "List files",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "select-file",
          label: "Get file content",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "zip-current-workspace",
          label: "Download workspace as zip",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "git-changes",
          label: "Get git changes",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "git-diff",
          label: "Get git diff",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-trajectory",
          label: "Get trajectory",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "security-api-get",
          label: "Security analyzer API (GET)",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "security-api-post",
          label: "Security analyzer API (POST)",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "security-api-put",
          label: "Security analyzer API (PUT)",
          className: "api-method put",
        },
        {
          type: "doc",
          id: "security-api-delete",
          label: "Security analyzer API (DELETE)",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "new-conversation",
          label: "Create new conversation",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "search-conversations",
          label: "Search conversations",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-conversation",
          label: "Get conversation",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "update-conversation",
          label: "Update conversation",
          className: "api-method patch",
        },
        {
          type: "doc",
          id: "delete-conversation",
          label: "Delete conversation",
          className: "api-method delete",
        },
        {
          type: "doc",
          id: "get-user-repositories",
          label: "Get user repositories",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-user",
          label: "Get user info",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "search-repositories",
          label: "Search repositories",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-suggested-tasks",
          label: "Get suggested tasks",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "load-settings",
          label: "Get settings",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "store-settings",
          label: "Store settings",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "unset-settings-tokens",
          label: "Unset settings tokens",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "reset-settings",
          label: "Reset settings",
          className: "api-method post",
        },
        {
          type: "doc",
          id: "get-litellm-models",
          label: "Get models",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-agents",
          label: "Get agents",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-security-analyzers",
          label: "Get security analyzers",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "get-config",
          label: "Get config",
          className: "api-method get",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;

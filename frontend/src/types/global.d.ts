declare global {
  interface Window {
    __APP_MODE__: "saas" | "oss";
    __GITHUB_CLIENT_ID__: string | null;
    __PREV_TOKEN__?: string | null;
    __PREV_GH_TOKEN__?: string | null;
  }
}

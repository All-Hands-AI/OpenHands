import type { PluginSpec } from "#/api/conversation-service/agent-server-conversation-service.types";

export function hasPluginParameters(
  plugins: PluginSpec[] | undefined,
): boolean {
  return (
    plugins?.some(
      (plugin) => Object.keys(plugin.parameters ?? {}).length > 0,
    ) ?? false
  );
}

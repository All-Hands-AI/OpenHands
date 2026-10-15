import { WorktreesClient } from "@openhands/typescript-client/clients";
import type { ConversationWorktree } from "@openhands/typescript-client/clients";
import { getAgentServerClientOptions } from "./agent-server-client-options";

export type { ConversationWorktree };

class WorktreesService {
  static async list(): Promise<ConversationWorktree[]> {
    return new WorktreesClient(getAgentServerClientOptions()).listWorktrees();
  }

  /** Refused (409) while it has changes or a conversation using it is open. */
  static async remove(name: string): Promise<void> {
    await new WorktreesClient(getAgentServerClientOptions()).removeWorktree(
      name,
    );
  }
}

export default WorktreesService;

import React from "react";
import { ApiKeysManager } from "#/components/features/settings/api-keys-manager";

function ApiKeysScreen() {
  return (
    <div className="flex flex-col grow overflow-auto p-9">
      <ApiKeysManager />
    </div>
  );
}

export default ApiKeysScreen;

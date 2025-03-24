#!/bin/bash

# Update all query hooks to remove Redux bridge references
for file in $(find /workspace/OpenHands/frontend/src/hooks/query -name "use-*.ts"); do
  # Replace import statements
  sed -i 's/import { getQueryReduxBridge } from "#\/utils\/query-redux-bridge";/import { QueryKeys } from ".\/query-keys";/g' $file
  
  # Replace bridge initialization
  sed -i 's/let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;/const queryClient = useQueryClient();/g' $file
  sed -i 's/let bridge: ReturnType<typeof getQueryReduxBridge> | undefined;/const queryClient = useQueryClient();/g' $file
  
  # Remove try/catch block for bridge initialization
  sed -i '/try {/,/}/d' $file
  
  # Replace bridge.getReduxSliceState with queryClient.getQueryData
  sed -i 's/bridge.getReduxSliceState/queryClient.getQueryData/g' $file
  
  # Replace bridge.isSliceMigrated checks
  sed -i '/if (bridge && !bridge.isSliceMigrated/d' $file
  
  # Replace bridge.syncReduxToQuery with queryClient.setQueryData
  sed -i 's/bridge.syncReduxToQuery/queryClient.setQueryData/g' $file
done

# Update services/actions.ts
sed -i 's/import { queryClient } from "#\/query-redux-bridge-init";/import { queryClient } from "#\/query-client-init";/g' /workspace/OpenHands/frontend/src/services/actions.ts

# Update services/observations.ts
sed -i 's/import { queryClient } from "#\/query-redux-bridge-init";/import { queryClient } from "#\/query-client-init";/g' /workspace/OpenHands/frontend/src/services/observations.ts

# Update routes/billing.tsx
sed -i 's/import { queryClient } from "#\/query-redux-bridge-init";/import { queryClient } from "#\/query-client-init";/g' /workspace/OpenHands/frontend/src/routes/billing.tsx
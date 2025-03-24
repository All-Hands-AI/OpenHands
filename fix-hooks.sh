#!/bin/bash

# Fix the hooks one by one
for file in $(find /workspace/OpenHands/frontend/src/hooks/query -name "use-*.ts"); do
  echo "Fixing $file"
  
  # Create a backup
  cp "$file" "${file}.bak"
  
  # Replace import statements
  sed -i 's/import { getQueryReduxBridge } from "#\/utils\/query-redux-bridge";/import { QueryKeys } from ".\/query-keys";/g' "$file"
  
  # Replace bridge initialization with queryClient
  sed -i 's/let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;/const queryClient = useQueryClient();/g' "$file"
  sed -i 's/let bridge: ReturnType<typeof getQueryReduxBridge> | undefined;/const queryClient = useQueryClient();/g' "$file"
  
  # Remove try/catch blocks for bridge initialization
  sed -i '/try {/,/} catch (error) {/d' "$file"
  sed -i '/console.warn(/,/);/d' "$file"
  sed -i '/\/\/ In tests/,/}/d' "$file"
  
  # Clean up any remaining closing braces from removed try/catch blocks
  sed -i 's/^  }$//' "$file"
  
  # Replace bridge references with queryClient
  sed -i 's/bridge.getReduxSliceState/queryClient.getQueryData/g' "$file"
  sed -i 's/bridge.syncReduxToQuery/queryClient.setQueryData/g' "$file"
  
  # Remove bridge conditional checks
  sed -i '/if (bridge)/d' "$file"
  sed -i '/if (bridge && !bridge.isSliceMigrated/d' "$file"
  
  # Clean up the file
  sed -i '/^\s*$/d' "$file"
done
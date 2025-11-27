interface LumioConfig {
  rpcUrl: string;
  contractAddress: string;
}

const getConfig = (): LumioConfig => ({
  rpcUrl: import.meta.env.VITE_LUMIO_RPC_URL || "https://api.testnet.lumio.io/",
  contractAddress: import.meta.env.VITE_VIBE_BALANCE_CONTRACT || "",
});

const buildViewRequest = (functionName: string, args: string[] = []) => {
  const { contractAddress } = getConfig();
  return {
    function: `${contractAddress}::vibe_balance::${functionName}`,
    type_arguments: [],
    arguments: args,
  };
};

const callView = async <T>(
  functionName: string,
  args: string[] = [],
): Promise<T> => {
  const { rpcUrl } = getConfig();
  const response = await fetch(`${rpcUrl}v1/view`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildViewRequest(functionName, args)),
  });

  if (!response.ok) {
    throw new Error(`Lumio API error: ${response.statusText}`);
  }

  const data = await response.json();
  return data[0] as T;
};

export const vibeBalance = {
  getConfig,

  isConfigured: (): boolean => {
    const { contractAddress } = getConfig();
    return Boolean(contractAddress);
  },

  getBalance: async (address: string): Promise<bigint> => {
    const result = await callView<string>("get_balance", [address]);
    return BigInt(result);
  },

  isWhitelisted: async (address: string): Promise<boolean> =>
    callView<boolean>("is_whitelisted", [address]),

  getTokenPrice: async (): Promise<bigint> => {
    const result = await callView<string>("get_token_price");
    return BigInt(result);
  },
};

export default vibeBalance;

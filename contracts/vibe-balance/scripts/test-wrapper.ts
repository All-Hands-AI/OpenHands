const TESTNET_RPC = "https://api.testnet.lumio.io/";
const CONTRACT_ADDRESS = "0xac1f48e2c77b95f2646c37ff629dbd27fa1a1f0857f7260ddf59ed14a13063fb";

interface ViewRequest {
  function: string;
  type_arguments: string[];
  arguments: string[];
}

async function callView<T>(functionName: string, args: string[] = []): Promise<T> {
  const request: ViewRequest = {
    function: `${CONTRACT_ADDRESS}::vibe_balance::${functionName}`,
    type_arguments: [],
    arguments: args,
  };

  const response = await fetch(`${TESTNET_RPC}v1/view`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const data = await response.json();
  return data[0] as T;
}

async function test() {
  console.log("Testing vibe-balance wrapper...\n");
  console.log("RPC:", TESTNET_RPC);
  console.log("Contract:", CONTRACT_ADDRESS);
  console.log("");

  const testAddress = CONTRACT_ADDRESS;

  console.log("1. Checking whitelist...");
  const isWhitelisted = await callView<boolean>("is_whitelisted", [testAddress]);
  console.log(`   is_whitelisted(${testAddress}): ${isWhitelisted}`);

  console.log("\n2. Getting balance...");
  const balance = await callView<string>("get_balance", [testAddress]);
  console.log(`   get_balance(${testAddress}): ${balance}`);

  console.log("\n3. Getting token price...");
  const price = await callView<string>("get_token_price");
  console.log(`   get_token_price(): ${price}`);

  console.log("\n✅ All tests passed!");
}

test().catch((err) => {
  console.error("❌ Test failed:", err.message);
  process.exit(1);
});

import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { QueryClient } from "@tanstack/react-query";
import { bsc, mainnet } from "wagmi/chains";

export const queryClient = new QueryClient();
export const wagmiConfig = getDefaultConfig({
  appName: "Thesis Capsule Web App",
  projectId: "Thesis_Capsule",
  chains: [bsc, mainnet],
  ssr: false,
});

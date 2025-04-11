import { getDefaultConfig } from "@rainbow-me/rainbowkit"
import { QueryClient } from "@tanstack/react-query"
import { bsc, mainnet } from "wagmi/chains"

export const queryClient = new QueryClient()
export const wagmiConfig = getDefaultConfig({
  appName: "Thesis Web App",
  projectId: "Thesis",
  chains: [bsc, mainnet],
  ssr: false,
})

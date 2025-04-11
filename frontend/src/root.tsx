import "@rainbow-me/rainbowkit/styles.css"

import React from "react"
import { Toaster } from "react-hot-toast"
import {
  Links,
  Meta,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router"
import "./index.css"
import "./tailwind.css"

import {
  darkTheme,
  lightTheme,
  RainbowKitProvider,
} from "@rainbow-me/rainbowkit"
import { QueryClientProvider } from "@tanstack/react-query"
import { WagmiProvider } from "wagmi"
import { queryClient, wagmiConfig } from "./config/config"
import { useTheme } from "./components/layout/theme-provider"

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
        <Toaster />
      </body>
    </html>
  )
}

export const meta: MetaFunction = () => [
  { title: "Thesis" },
  { name: "description", content: "From curiosity to clarity!" },
]

export default function App() {
  const { theme } = useTheme()

  return (
    <WagmiProvider config={wagmiConfig}>
      <RainbowKitProvider
        theme={theme === "light" ? lightTheme() : darkTheme()}
        locale="en-US"
        modalSize="compact"
        appInfo={{
          appName: "Thesis",
          learnMoreUrl: "https://thesis.io",
        }}
      >
        <QueryClientProvider client={queryClient}>
          <Outlet />
        </QueryClientProvider>
      </RainbowKitProvider>
    </WagmiProvider>
  )
}

import {
  Links,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";
import "./tailwind.css";
import "./index.css";
import React from "react";
import { Toaster } from "react-hot-toast";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* eslint-disable-next-line i18next/no-literal-string */}
        <title>OpenHands</title>
        <meta name="description" content="Let's Start Building!" />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
        <Toaster />
      </body>
    </html>
  );
}

export const meta: MetaFunction = () => [
  { title: "OpenHands" },
  { name: "description", content: "Let's Start Building!" },
];

export default function App() {
  return <Outlet />;
}

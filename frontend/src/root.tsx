import {
  Links,
  Meta,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
  LinksFunction,
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
  );
}

export const meta: MetaFunction = () => [
  { title: "GP-KhayaL | VIRTUAL CYBER SECURITY" },
  { name: "description", content: "GP-KhayaL is a virtual cyber security agent platform powered by advanced AI." },
  { name: "theme-color", content: "#0A1128" },
  // Open Graph
  { property: "og:type", content: "website" },
  { property: "og:title", content: "GP-KhayaL | VIRTUAL CYBER SECURITY" },
  { property: "og:description", content: "Virtual Cyber Security agent platform for repositories and AI models." },
  { property: "og:image", content: "/android-chrome-512x512.png" },
  { property: "og:url", content: "https://gp-khayal.top" },
  // Twitter
  { name: "twitter:card", content: "summary_large_image" },
  { name: "twitter:title", content: "GP-KhayaL | VIRTUAL CYBER SECURITY" },
  { name: "twitter:description", content: "Virtual Cyber Security agent platform for repositories and AI models." },
  { name: "twitter:image", content: "/android-chrome-512x512.png" },
];

export const links: LinksFunction = () => [
  { rel: "icon", type: "image/x-icon", href: "/favicon.ico" },
  { rel: "icon", type: "image/png", href: "/favicon-32x32.png", sizes: "32x32" },
  { rel: "icon", type: "image/png", href: "/favicon-16x16.png", sizes: "16x16" },
  { rel: "apple-touch-icon", href: "/apple-touch-icon.png", sizes: "180x180" },
  { rel: "manifest", href: "/site.webmanifest" },
  { rel: "mask-icon", href: "/safari-pinned-tab.svg", color: "#00F5D4" },
];

export default function App() {
  return <Outlet />;
}

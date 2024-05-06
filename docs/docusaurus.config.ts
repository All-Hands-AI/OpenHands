import type * as Preset from "@docusaurus/preset-classic";
import type { Config } from "@docusaurus/types";
import { themes as prismThemes } from "prism-react-renderer";

const config: Config = {
  title: "OpenDevin",
  tagline: "Code Less, Make More",
  favicon: "img/logo.png",

  // Set the production url of your site here
  url: "https://OpenDevin.github.io",
  baseUrl: "/OpenDevin/",

  // GitHub pages deployment config.
  organizationName: "OpenDevin",
  projectName: "OpenDevin",
  trailingSlash: false,

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          path: "modules",
          routeBasePath: "modules",
          sidebarPath: "./sidebars.ts",
          exclude: [
            // '**/_*.{js,jsx,ts,tsx,md,mdx}',
            // '**/_*/**',
            "**/*.test.{js,jsx,ts,tsx}",
            "**/__tests__/**",
          ],
        },
        blog: {
          showReadingTime: true,
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/docusaurus.png",
    navbar: {
      title: "OpenDevin",
      logo: {
        alt: "OpenDevin",
        src: "img/logo.png",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "docsSidebar",
          position: "left",
          label: "Docs",
        },
        {
          type: "docSidebar",
          sidebarId: "apiSidebar",
          position: "left",
          label: "Codebase",
        },
        { to: "/faq", label: "FAQ", position: "left" },
        {
          href: "https://github.com/OpenDevin/OpenDevin",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "OpenDevin",
          items: [
            {
              label: "Docs",
              to: "/modules/usage/intro",
            },
          ],
        },
        {
          title: "Community",
          items: [
            {
              label: "Slack",
              href: "https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw"
            },
            {
              label: "Discord",
              href: "https://discord.gg/ESHStjSjD4",
            },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "GitHub",
              href: "https://github.com/OpenDevin/OpenDevin",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} OpenDevin`,
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;

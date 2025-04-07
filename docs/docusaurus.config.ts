import type * as Preset from '@docusaurus/preset-classic';
import type { Config } from '@docusaurus/types';
import { themes as prismThemes } from 'prism-react-renderer';

const config: Config = {
  title: 'OpenHands',
  tagline: 'Code Less, Make More',
  favicon: 'img/logo-square.png',

  // Set the production url of your site here
  url: 'https://docs.all-hands.dev',
  baseUrl: '/',

  // GitHub pages deployment config.
  organizationName: 'All-Hands-AI',
  projectName: 'OpenHands',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr', 'zh-Hans', 'ja', 'pt-BR'],
    localeConfigs: {
      en: {
        htmlLang: 'en-GB',
      },
    },
  },

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],
  presets: [
    [
      'classic',
      {
        docs: {
          path: 'modules',
          routeBasePath: 'modules',
          sidebarPath: './sidebars.ts',
          exclude: [
            // '**/_*.{js,jsx,ts,tsx,md,mdx}',
            // '**/_*/**',
            '**/*.test.{js,jsx,ts,tsx}',
            '**/__tests__/**',
          ],
        },
        blog: {
          showReadingTime: true,
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  themeConfig: {
    image: 'img/docusaurus.png',
    navbar: {
      title: 'OpenHands',
      logo: {
        alt: 'OpenHands',
        src: 'img/logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'User Guides',
        },
        {
          type: 'localeDropdown',
          position: 'left',
        },
        {
          href: 'https://all-hands.dev',
          label: 'Company',
          position: 'right',
        },
        {
          href: 'https://github.com/All-Hands-AI/OpenHands',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;

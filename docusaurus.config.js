// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const {themes} = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Deep Dive into Agentic AI',
  tagline: 'Design, Implementation, and Production Systems',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://m-rizqinovniari.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  baseUrl: '/agentic-handbook/',

  // GitHub pages deployment config.
  organizationName: 'm-rizqinovniari',
  projectName: 'agentic-handbook',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang.
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'id'],
  },

  plugins: [
    [
      require.resolve("@easyops-cn/docusaurus-search-local"),
      {
        // Options untuk search plugin
        hashed: true,
        // Hapus language option untuk menghindari error dengan lunr-languages
        // Plugin akan otomatis mendeteksi dari i18n config
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
        // Enable indexing untuk development mode
        indexDocs: true,
        indexPages: false,
        indexBlog: false,
        docsRouteBasePath: '/',
        // Opsi untuk menampilkan hasil pencarian yang lebih detail
        searchResultLimits: 10,
        // Panjang context yang lebih panjang untuk menampilkan lebih banyak preview
        searchResultContextMaxLength: 150,
        // Menampilkan path file di hasil pencarian
        searchBarShortcut: true,
        searchBarShortcutHint: true,
      },
    ],
  ],

  markdown: {
    mermaid: true,
  },

  // Hanya tambahkan theme di sini
  themes: ['@docusaurus/theme-mermaid'],
  
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.json',
          // Please change this to your repo.
          editUrl: undefined,
          routeBasePath: '/', 
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Deep Dive into Agentic AI',
        items: [
          {
            type: 'search',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [],
        copyright: `Copyright © M. Rizqinovniari ${new Date().getFullYear()}. Built with Docusaurus.`,
      },
      prism: {
        theme: themes.github,
        darkTheme: themes.dracula,
      },
    }),
};

module.exports = config;
import { defineConfig } from 'astro/config';
import preact from '@astrojs/preact';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // SITE_URL / SITE_BASE are set when building for a sub-path host (see scripts/prefix-base.mjs)
  site: process.env.SITE_URL || 'https://observatoriolaboral.pe',
  base: process.env.SITE_BASE || '/',
  output: 'static',
  redirects: { '/historias/panorama-2024': '/historias/panorama', '/historias/panorama-2024/informe-completo': '/historias/panorama/informe-completo' },
  trailingSlash: 'always',
  integrations: [preact({ compat: false }), mdx(), sitemap({ filter: page => !page.includes('/embed/') })],
  i18n: { defaultLocale: 'es', locales: ['es', 'en'], routing: { prefixDefaultLocale: false } },
  vite: { build: { chunkSizeWarningLimit: 900 } },
});

import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import lucode from 'lucode-starlight';
import { visit } from 'unist-util-visit';
import { unified } from '@astrojs/markdown-remark';

const base = `/${(process.env.DOCS_BASE || '').replace(/^\/+|\/+$/g, '')}/`.replace('//', '/');

// Authored Markdown uses root-relative links; prefix them with the deploy base (a no-op when base is '/').
function prefixLinks() {
  return (tree) => visit(tree, 'link', (node) => {
    if (node.url.startsWith('/') && !node.url.startsWith('//') && !node.url.startsWith(base)) {
      node.url = `${base}${node.url.slice(1)}`;
    }
  });
}

export default defineConfig({
  site: process.env.DOCS_SITE || 'https://ttl.docs.isaackogan.com',
  base,
  trailingSlash: 'always',
  markdown: { processor: unified({ remarkPlugins: [prefixLinks] }) },
  integrations: [
    starlight({
      title: 'TikTokLive',
      description: 'Unofficial TikTok LIVE API for Python. Guides, events, and generated API reference.',
      favicon: '/favicon.png',
      head: [
        { tag: 'meta', attrs: { property: 'og:image', content: 'https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/SquareLogo.png' } },
        { tag: 'meta', attrs: { property: 'og:image:alt', content: 'TikTokLive, TikTok LIVE API for Python' } },
        { tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' } },
      ],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/isaackogan/TikTokLive' },
        { icon: 'discord', label: 'Discord', href: 'https://discord.gg/uja6SajDxd' },
      ],
      editLink: { baseUrl: 'https://github.com/isaackogan/TikTokLive/edit/master/docs/' },
      sidebar: [
        { label: 'Start here', items: [
          { label: 'Getting Started', slug: '' },
          { label: 'Connection lifecycle', slug: 'getting-started/connection' },
          { label: 'Migration', slug: 'getting-started/migration' },
        ] },
        { label: 'Configuration', items: [{ autogenerate: { directory: 'configuration' } }] },
        { label: 'Guides', items: [{ autogenerate: { directory: 'guides' } }] },
        { label: 'Events', items: [{ autogenerate: { directory: 'events' } }], collapsed: true },
        { label: 'Advanced', items: [{ autogenerate: { directory: 'advanced' } }], collapsed: true },
        { label: 'Troubleshooting', slug: 'troubleshooting' },
        { label: 'Contributing to the docs', slug: 'contributing' },
        { label: 'Hosting', slug: 'hosting' },
        { label: 'API reference', items: [{ autogenerate: { directory: 'api' } }], collapsed: true },
        { label: 'Protobuf schema', items: [{ autogenerate: { directory: 'schema' } }], collapsed: true },
      ],
      plugins: [
        lucode({
          navLinks: [
            { label: 'Docs', link: base },
            { label: 'Events', link: `${base}events/` },
            { label: 'API', link: `${base}api/` },
          ],
          footerText: 'Unofficial project, not affiliated with TikTok or ByteDance Ltd. Signing by [Euler Stream](https://www.eulerstream.com/). Source on [GitHub](https://github.com/isaackogan/TikTokLive).',
        }),
        starlightLinksValidator(),
      ],
    }),
  ],
});

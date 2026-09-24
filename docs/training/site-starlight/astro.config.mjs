// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'SSSF Training',
			components: {
				PageTitle: './src/components/PageTitle.astro',
			},
			// Stamp stable data-testid hooks onto Starlight's own nav chrome (which
			// ships none) so navigation is testable. Runs on first load and after
			// every view-transition navigation.
			head: [
				{
					tag: 'script',
					content: `
						function stampTestIds() {
							const set = (el, id) => { if (el && !el.dataset.testid) el.dataset.testid = id; };
							set(document.querySelector('header.header'), 'site-header');
							const sel = document.querySelector('starlight-theme-select select');
							set(sel, 'theme-select');
							set(document.querySelector('site-search button, [data-open-modal] button, site-search'), 'search');
							const sidebar = document.querySelector('nav.sidebar-content') || document.querySelector('.sidebar-content') || document.querySelector('nav[aria-label]');
							set(sidebar, 'sidebar');
							if (sidebar) sidebar.querySelectorAll('a[href]').forEach((a) => {
								a.dataset.testid = 'nav-link';
								try { a.dataset.navSlug = new URL(a.href).pathname.replace(/\\/$/, '').split('/').pop() || 'home'; } catch (e) {}
							});
							set(document.querySelector('starlight-toc') || document.querySelector('.right-sidebar'), 'toc');
							set(document.querySelector('.pagination-links'), 'pager');
						}
						if (document.readyState !== 'loading') stampTestIds();
						document.addEventListener('DOMContentLoaded', stampTestIds);
						document.addEventListener('astro:page-load', stampTestIds);
					`,
				},
			],
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/joystick/super-simple-software-factory' }],
			sidebar: [
				{ label: 'Mission', slug: 'mission' },
				{ label: 'Notes', slug: 'notes' },
				{
					label: 'Chapter 1 — SSSF Fundamentals',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '01-sssf-fundamentals/lessons' } }] },
						{ label: 'Reference', items: [{ autogenerate: { directory: '01-sssf-fundamentals/reference' } }] },
						{ label: 'Learning records', items: [{ autogenerate: { directory: '01-sssf-fundamentals/learning-records' } }] },
					],
				},
				{
					label: 'Chapter 2 — Gates, Deep Dive',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '02-gates-deep-dive/lessons' } }] },
						{ label: 'Reference', items: [{ autogenerate: { directory: '02-gates-deep-dive/reference' } }] },
						{ label: 'Learning records', items: [{ autogenerate: { directory: '02-gates-deep-dive/learning-records' } }] },
						{ label: 'Resources', slug: '02-gates-deep-dive/resources' },
					],
				},
				{
					label: 'Chapter 3 — Adopting a Factory',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '03-adopting-a-factory/lessons' } }] },
					],
				},
				{
					label: 'Chapter 4 — Coding Agents and Cost',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '04-coding-agents-and-cost/lessons' } }] },
					],
				},
				{
					label: 'Chapter 5 — Owning Your Workflow',
					items: [
						{ label: 'Overview', slug: '05-owning-your-workflow' },
						{ label: 'Lessons', items: [{ autogenerate: { directory: '05-owning-your-workflow/lessons' } }] },
					],
				},
				{
					label: 'Chapter 6 — Going Dark',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '06-going-dark/lessons' } }] },
					],
				},
				{
					label: 'Chapter 7 — The Queue',
					items: [
						{ label: 'Lessons', items: [{ autogenerate: { directory: '07-the-queue/lessons' } }] },
					],
				},
			],
		}),
	],
});

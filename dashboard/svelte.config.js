import preprocess from 'svelte-preprocess';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/kit/vite';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: [
		vitePreprocess(),
		preprocess({
			postcss: true
		})
	],

	kit: {
		adapter: adapter({
			pages: '../chimerapy/orchestrator/build',
			strict: false,
			fallback: 'index.html'
		}),
		paths: {
			base: process.env.NODE_ENV === 'development' ? '' : '/dashboard'
		}
	}
};

export default config;

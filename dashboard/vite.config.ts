import { sveltekit } from '@sveltejs/kit/vite';
import type { UserConfig } from 'vite';

const config: UserConfig = {
	plugins: [sveltekit()],
	define: {
		'process.env': {}
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom'
	},
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false,
				rewrite: (path: string) => path.replace('/api', '')
			},
			'/cluster': {
				target: 'ws://localhost:8000/cluster/',
				changeOrigin: true,
				secure: false,
				rewrite: (path: string) => path.replace('/cluster', ''),
				ws: true
			}
		}
	}
};

export default config;

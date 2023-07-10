export const ssr = false;
export const prerender = true;
import type { LayoutLoad } from './$types';
import { populateStores } from '$lib/stores';
import { dev } from '$app/environment';

export const load: LayoutLoad = ({ fetch }) => {
	populateStores();
	return {
		sections: [
			{ slug: dev ? '/pipeline-design' : '/dashboard/pipeline-design', title: 'Pipeline Design' }
			// { slug: dev ? '/cluster-control': '/dashboard/cluster-control', title: 'Cluster Control' },
			// { slug: dev ? '/data-dashboard': '/dashboard/data-dashboard', title: 'Data Dashboard' },
			// { slug: dev ? '/help': '/dashboard/help', title: 'Help' },
			// { slug: dev ? '/about': '/dashboard/about', title: 'About' }
		],
		logo: dev ? '/ChimeraPy.png' : '/dashboard/ChimeraPy.png',
		copyrightHolderURL: 'https://wp0.vanderbilt.edu/oele/',
		copyrightHolder: 'oele-isis-vanderbilt'
	};
};

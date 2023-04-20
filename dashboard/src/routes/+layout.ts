export const ssr = false;
import type { LayoutLoad } from './$types';
import { populateStores } from '$lib/stores';

export const load: LayoutLoad = ({ fetch }) => {
	populateStores();
	return {
		sections: [
			{ slug: '/pipeline', title: 'Pipeline Design' },
			{ slug: '/cluster', title: 'Cluster Control' },
			{ slug: '/dashboard', title: 'Data Dashboard' },
			{ slug: '/help', title: 'Help' },
			{ slug: '/about', title: 'About' }
		],
		logo: '/ChimeraPy.png',
		copyrightHolderURL: 'https://wp0.vanderbilt.edu/oele/',
		copyrightHolder: 'oele-isis-vanderbilt'
	};
};

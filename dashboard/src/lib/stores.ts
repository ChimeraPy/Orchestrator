import { writable } from 'svelte/store';
import type { Manager, ResponseError } from './models';

import { networkClient } from './services';

// ToDo: this store is fine for now and distributed async requires the tree to be regenerated in realtime. But something diff based maybe?
export const networkStore = writable<Manager | null>(null);
export const errorStore = writable<ResponseError | null>(null);

export async function initNetwork(
	fetch: (input: RequestInfo | URL, init?: RequestInit | undefined) => Promise<Response>
) {
	networkClient.getNetworkMap(fetch).then((result) => {
		if (result.ok().isSome()) {
			networkStore.set(result.unwrap());
			errorStore.set(null);
		} else {
			errorStore.set(result.unwrap());
			networkStore.set(null);
		}
	});
}

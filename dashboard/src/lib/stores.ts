import { writable } from 'svelte/store';
import type { ClusterState, Pipeline, ResponseError } from './models';
import readableWebSocketStore from './Services/ReadableWebSocketStore';

import { networkClient } from './services';

// ToDo: this store is fine for now and distributed async requires the tree to be regenerated in realtime. But something diff based maybe?

export const errorStore = writable<ResponseError | null>(null);
const stores = new Map<string, any>();

export function populateStores() {
	const networkStore = readableWebSocketStore<ClusterState>(
		'/cluster/updates',
		null,
		(payload) => payload.data
	);

	const committedPipelineStore = readableWebSocketStore<Pipeline>(
		'/cluster/pipeline-lifecycle',
		null,
		(payload) => payload
	);

	stores.set('network', networkStore);
	stores.set('committedPipeline', committedPipelineStore);
}

export function getStore<T>(name: string): T | null {
	return stores.get(name);
}

import { writable } from 'svelte/store';
import type { ClusterState, ResponseError, SelectedPipeline } from './models';
import readableWebSocketStore from './Services/ReadableWebSocketStore';

// ToDo: this store is fine for now and distributed async requires the tree to be regenerated in realtime. But something diff based maybe?

export const errorStore = writable<ResponseError | null>(null);
const stores = new Map<string, any>();

export function populateStores() {
	const networkStore = readableWebSocketStore<ClusterState>(
		'/cluster/updates',
		null,
		(payload) => payload.data
	);

	const lifeCycleStore = readableWebSocketStore<ClusterState>(
		'/cluster/pipeline-lifecycle',
		null,
		(payload) => payload.data
	);

	const selectedPipelineStore = writable<SelectedPipeline>({
		pipeline: null,
		selectedNodeId: null
	});

	stores.set('network', networkStore);
	stores.set('selectedPipeline', selectedPipelineStore);
}

export function getStore<T>(name: string): T | null {
	return stores.get(name);
}

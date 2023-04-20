import type { ClusterState } from '../models';

export class ClusterUtils {
	static clusterStateToWorkerListItems(
		state: ClusterState
	): { id: string; text: string; active: boolean }[] {
		return Object.values(state?.workers || []).map((worker) => {
			return {
				id: worker.id,
				text: worker.name,
				active: false
			};
		});
	}
}

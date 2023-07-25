<script lang="ts">
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import { clusterClient } from '$lib/services';
	import { ClusterUtils } from '$lib/Services/ClusterUtils';

	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import { getStore } from '$lib/stores';
	import type { ClusterState } from '$lib/models';
	import Alert from './Alert.svelte';

	let modal: Alert | null = null;

	let networkStore = getStore('network');

	function getNetworkTitle(clusterState: ClusterState | null) {
		if (!clusterState) {
			return 'No active network';
		}
		return `${clusterState.id}#${clusterState.ip}`;
	}

	function getNetworkIcons() {
		if (!$networkStore) {
			return [];
		}
		const zeroConfEnabled = $networkStore?.zeroconf_discovery;
		const icons = [
			{
				type: zeroConfEnabled ? 'eyeOpen' : 'eyeClosed',
				tooltip: `Zeroconf discovery ${zeroConfEnabled ? 'enabled' : 'disabled'}. Click to toggle`,
				dispatchEventName: zeroConfEnabled ? 'disableZeroconfDiscovery' : 'enableZeroconfDiscovery',
				fill: 'none',
				strokeWidth: 2
			}
		];

		return icons;
	}

	async function enableZeroconfDiscovery() {
		(await clusterClient.enableZeroConf()).mapError((err) => {
			modal?.display({
				title: 'Error enabling zeroconf discovery',
				content: JSON.stringify(err, null, 2)
			});
		});
	}

	async function disableZeroconfDiscovery() {
		(await clusterClient.disableZeroConf()).mapError((err) => {
			modal?.display({
				title: 'Error disabling zeroconf discovery',
				content: JSON.stringify(err, null, 2)
			});
		});
	}

	function displayWorkerInfo(worker) {
		const workerDetails = Object.values($networkStore?.workers || []).find(
			(w) => w.id === worker.id
		);
		if (workerDetails) {
			modal.display({
				title: `Worker - ${workerDetails.name}`,
				content: workerDetails
			});
		}
	}
</script>

<div class="h-full w-full">
	<div>
		<HorizontalMenu
			title={getNetworkTitle($networkStore)}
			backgroundClass="bg-blue-600"
			icons={getNetworkIcons($networkStore)}
			on:enableZeroconfDiscovery={() => enableZeroconfDiscovery()}
			on:disableZeroconfDiscovery={() => disableZeroconfDiscovery()}
		/>
	</div>
	<div class="bg-[#F3F7F6] w-full h-full">
		<EditableList
			editable={false}
			items={ClusterUtils.clusterStateToWorkerListItems($networkStore)}
			on:info={(event) => displayWorkerInfo(event.detail)}
		/>
	</div>
</div>

<Alert bind:this={modal} />

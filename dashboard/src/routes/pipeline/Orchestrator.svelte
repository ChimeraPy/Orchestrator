<script lang="ts">
	import { clusterClient } from '$lib/services';
	import { getStore } from '$lib/stores';
	import { ClusterUtils } from '$lib/Services/ClusterUtils';

	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import type { ClusterState } from '$lib/models';

	let networkStore = getStore('network');

	let infoModalContent: { title: string; content: any } | null = null;

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
		console.log('enabling zeroconf discovery');
		(await clusterClient.enableZeroConf()).mapError((err) => {
			infoModalContent = {
				title: 'Error enabling zeroconf discovery',
				content: JSON.stringify(err, null, 2)
			};
		});
	}

	async function disableZeroconfDiscovery() {
		(await clusterClient.disableZeroConf()).mapError((err) => {
			infoModalContent = {
				title: 'Error disabling zeroconf discovery',
				content: JSON.stringify(err, null, 2)
			};
		});
	}

	function displayWorkerInfo(worker) {
		const workerDetails = Object.values($networkStore?.workers || []).find(
			(w) => w.id === worker.id
		);
		if (workerDetails) {
			infoModalContent = {
				title: workerDetails.name,
				content: workerDetails
			};
		}
	}
</script>

<div class="flex flex-row w-full h-full">
	<div class="w-1/6 flex flex-col border-r-2 border-gray-400">
		<div>
			<HorizontalMenu
				title={getNetworkTitle($networkStore)}
				backgroundClass="bg-blue-600"
				icons={getNetworkIcons($networkStore)}
				on:enableZeroconfDiscovery={() => enableZeroconfDiscovery()}
				on:disableZeroconfDiscovery={() => disableZeroconfDiscovery()}
			/>
		</div>
		<div class="flex-1 flex justify-center items-center bg-[#F3F7F6]">
			<EditableList
				editable={false}
				items={ClusterUtils.clusterStateToWorkerListItems($networkStore)}
				on:info={(event) => displayWorkerInfo(event.detail)}
			/>
		</div>
	</div>
	<div class="flex flex-col w-4/6 h-full bg-indigo-100 border-r-2 border-gray-400">
		<HorizontalMenu title="Active Jobs" />
		<div class="flex-1 flex justify-center items-center bg-[#F3F7F6]">
			<p>Active Jobs go here</p>
		</div>
	</div>
	<div class="w-1/6 flex flex-col border-gray-400">
		<div>
			<HorizontalMenu title="Selected Node" backgroundClass="bg-blue-600" />
		</div>
		<div class="flex-1 flex justify-center items-center bg-[#F3F7F6]">
			<p>Selected Node attributes</p>
		</div>
	</div>
</div>

<!-- Alert Modal -->
<Modal
	type="alert"
	title={infoModalContent?.title}
	bind:modalOpen={infoModalContent}
	autoclose={true}
	alertMessage="Close"
	on:cancel={() => (infoModalContent = null)}
	on:alert={() => (infoModalContent = null)}
>
	<div slot="content">
		<h3 class="text-xl font-medium text-green-900 p-2">{infoModalContent.title}</h3>
		<pre>{JSON.stringify(infoModalContent.content, null, 2)}</pre>
	</div>
</Modal>

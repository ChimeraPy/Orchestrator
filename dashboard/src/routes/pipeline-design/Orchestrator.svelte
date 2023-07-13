<script lang="ts">
	import { clusterClient } from '$lib/services';
	import { getStore } from '$lib/stores';
	import { ClusterUtils } from '$lib/Services/ClusterUtils';
	import { Ok } from 'ts-monads';
	import { ToolViewType } from '$lib/Components/JointJS/utils';

	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import type { ClusterState } from '$lib/models';
	import type { IconType } from '$lib/Icons';
	import { Icons, getIconFromFSMActions } from '$lib/Icons';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';

	import { Select, Label } from 'flowbite-svelte';
	import type { Pipeline, PipelineNode } from '$lib/models';
	import { onMount } from 'svelte';

	let networkStore = getStore('network');
	let selectedPipelineStore = getStore('selectedPipeline');
	let lifeCycleStore = getStore('lifeCycle');

	let infoModalContent: { title: string; content: any } | null = null;
	let icons: IconType[] = [];
	let pipelineGraph: any = null;
	let pipelineCells = [];
	let selectedWorkerId: string | null = null;

	onMount(async () => {
		const clusterActionsResult = await clusterClient.getActionsFSM();
		clusterActionsResultToIcons(clusterActionsResult);
	});

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

	function getWorkerItems(networkDetails, selectedPipelineDetails) {
		const workers = Object.values(networkDetails?.workers || {})
			.map((w) => ({ value: w.id, name: w.name }))
			.concat([{ value: null, name: 'Select a worker' }]);
		const nodeId = selectedPipelineDetails.selectedNodeId;
		nodeId === null
			? (selectedWorkerId = null)
			: (selectedWorkerId =
					selectedPipelineDetails?.pipeline?.nodes.find((n) => n.id === nodeId)?.worker_id || null);
		return workers; // TODO: Fix this after proper worker heartbeat handling
	}

	function getNodeTitle() {
		const node = getNode($selectedPipelineStore.pipeline, $selectedPipelineStore.selectedNodeId);
		return node?.name || 'No node selected';
	}

	async function enableZeroconfDiscovery() {
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

	function onWorkerIdSelectionChange() {
		if ($selectedPipelineStore?.selectedNodeId === null) return;
		let selectedNode = getNode(
			$selectedPipelineStore.pipeline,
			$selectedPipelineStore.selectedNodeId
		);
		selectedNode ? (selectedNode.worker_id = selectedWorkerId) : null;
		selectedNode = selectedNode;
	}

	function getNode(pipeline: Pipeline, nodeId: string): PipelineNode | null {
		if (!pipeline) return null;
		if (!nodeId) return null;

		return pipeline.nodes.find((n) => n.id === nodeId);
	}

	function clusterActionsResultToIcons(clusterActionsResult) {
		clusterActionsResult.map((fsm) => {
			const statesArray = Object.values(fsm.states);
			const currentState = statesArray.find((state) => state.name === fsm.current_state);
			const validTransitions = currentState.valid_transitions.map((transition) => transition.name);
			const actions = [];
			Object.values(fsm.states).forEach((state) => {
				state.valid_transitions.forEach((transition) => {
					if (!actions.includes(transition.name)) {
						actions.push(transition.name);
					}
				});
			});

			icons = actions
				.filter((action) => action !== '/instantiate')
				.map((action) => {
					return getIconFromFSMActions(
						action,
						fsm.active_pipeline_id === null || !validTransitions.includes(action)
					);
				})
				.concat({
					tooltip: 'Get Actions and States Info',
					type: Icons.info,
					disabled: false,
					fill: 'none',
					strokeWidth: 2
				});
		});
	}

	async function displayClusterStatesInfo() {
		(await clusterClient.getActionsFSM())
			.map((fsm) => {
				infoModalContent = {
					title: 'Cluster States Info',
					content: fsm
				};
			})
			.mapError((err) => {
				infoModalContent = {
					title: 'Error getting cluster states info',
					content: err
				};
			});
	}

	function renderChanges(pipeline, fsm) {
		if (pipeline) {
			pipelineCells = PipelineUtils.committablePipelineToJointCells(pipeline);
			pipelineCells = pipelineCells;
		} else {
			pipelineCells = [];
		}

		pipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
		pipelineGraph?.layout();
		if (fsm) {
			clusterActionsResultToIcons(new Ok(fsm));
		}
	}

	async function commitPipeline() {
		(await clusterClient.commitPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error committing pipeline',
				content: err
			};
		});
	}

	async function previewPipeline() {
		(await clusterClient.previewPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error previewing pipeline',
				content: err
			};
		});
	}

	async function recordPipeline() {
		(await clusterClient.recordPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error recording pipeline',
				content: err
			};
		});
	}

	async function stopPipeline() {
		(await clusterClient.stopPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error stopping pipeline',
				content: err
			};
		});
	}

	async function collectPipeline() {
		(await clusterClient.collectPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error stopping pipeline',
				content: err
			};
		});
	}

	async function resetPipeline() {
		(await clusterClient.resetPipeline()).mapError((err) => {
			infoModalContent = {
				title: 'Error resetting pipeline',
				content: err
			};
		});
	}

	$: renderChanges($lifeCycleStore?.pipeline, $lifeCycleStore?.fsm);
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
		<HorizontalMenu
			{icons}
			on:info={displayClusterStatesInfo}
			on:commit={commitPipeline}
			on:preview={previewPipeline}
			on:record={recordPipeline}
			on:stop={stopPipeline}
			on:reset={resetPipeline}
			on:collect={collectPipeline}
			title="Active Jobs"
		/>
		<div class="flex-1 flex justify-center items-center bg-[#F3F7F6]">
			<EditableDagViewer
				bind:this={pipelineGraph}
				editable={false}
				additionalLinkValidators={[]}
				toolViewAttachments={[ToolViewType.INFO]}
			/>
		</div>
	</div>
	<div class="w-1/6 flex flex-col border-gray-400">
		<div>
			<HorizontalMenu title={getNodeTitle($selectedPipelineStore)} backgroundClass="bg-blue-600" />
		</div>
		<div class="flex-1 flex flex-col w-full bg-[#F3F7F6]">
			{#if $selectedPipelineStore?.selectedNodeId}
				<div class="p-2">
					<Label>Select a worker</Label>
					<Select
						mt-2
						items={getWorkerItems($networkStore, $selectedPipelineStore)}
						bind:value={selectedWorkerId}
						on:change={onWorkerIdSelectionChange}
					/>
				</div>
			{/if}
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

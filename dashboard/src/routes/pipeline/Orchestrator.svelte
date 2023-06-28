<script lang="ts">
	import { pipelineClient, clusterClient } from '$lib/services';
	import { onMount } from 'svelte';
	import { getStore } from '$lib/stores';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';
	import { ClusterUtils } from '$lib/Services/ClusterUtils';
	import { debounce } from '$lib/utils';

	import PartBrowser from '$lib/Components/JointJS/PartBrowser.svelte';
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import PluginInstaller from '$lib/Components/PluginInstaller/PluginInstaller.svelte';
	import PipelineImporter from '$lib/Components/PipelineImporter/PipelineImporter.svelte';
	import * as joint from 'jointjs';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { CreatePipelineStages } from '$lib/models';
	import type { Pipeline, ClusterState } from '$lib/models';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import PipelineDesigner from './PipelineDesigner.svelte';
	import { Icons } from '$lib/Icons';

	import { Input, Label, Spinner } from 'flowbite-svelte';

	let networkStore = getStore('network');

	let nodeCells: joint.dia.Cell[];
	let pipelineName: string = '',
		pipelineDescription: string = '';
	let createPipelineStage: CreatePipelineStages = CreatePipelineStages.INACTIVE;
	let pipelineCreationMessage: string = '';
	export let modalOpen: boolean;
	let confirmMessage = 'Create Pipeline';
	let cancelMessage;

	let pipelines = [],
		pipelineListItems = [];
	let activePipeline: Pipeline | null = null;
	let pipelineGraph: EditableDagViewer;
	let pluginInstaller: PluginInstaller;
	let pipelineImporter: PipelineImporter;
	let infoModalContent: { title: string; content: any } | null = null;

	let editorContainer: HTMLElement, horizontalMenu: HTMLElement;

	$: {
		modalOpen = createPipelineStage !== CreatePipelineStages.INACTIVE;
		cancelMessage = [CreatePipelineStages.OK, CreatePipelineStages.ERROR].includes(
			createPipelineStage
		)
			? 'Close'
			: 'Cancel';
		createPipelineStage === CreatePipelineStages.OK ? (activePipeline = null) : null;
		[CreatePipelineStages.OK, CreatePipelineStages.ERROR].includes(createPipelineStage)
			? fetchPipelines()
			: null;
	}

	// Part Browser
	async function fetchPartBrowserNodes(): Promise<joint.dia.Graph> {
		const result = await pipelineClient.getNodes();
		nodeCells = PipelineUtils.pipelineNodeResultToJointCells(result);
		nodeCells = nodeCells;
	}

	const debouncedFetchNodes = debounce(fetchPartBrowserNodes);

	// Pipeline Editor
	async function addNodeToActivePipeline(cell) {
		if (!activePipeline) {
			infoModalContent = {
				title: 'No active pipeline',
				content: 'Please create or activate a pipeline to add nodes to it.'
			};
			return;
		}

		const node = {
			name: cell.prop('registryName'),
			registry_name: cell.prop('registryName'),
			package: cell.prop('package'),
			id: cell.id
		};

		const result = await pipelineClient.addNodeTo(activePipeline.id, node);
		result.mapAsync(async (node) => {
			await renderActivePipelineGraph();
		});
	}

	async function removeNodeFromPipeline(cell) {
		if (!activePipeline) {
			return;
		}
		const nodeToRemove = activePipeline.nodes.find((n) => n.id === cell.id);
		if (nodeToRemove) {
			const result = await pipelineClient.removeNodeFrom(activePipeline.id, nodeToRemove);
			result.mapError((error) => {
				infoModalContent = {
					title: 'Error removing node',
					content: error
				};
			});
			await renderActivePipelineGraph(true);
		}
	}

	async function fetchPipelines(rerender = true) {
		const result = await pipelineClient.getPipelines();

		pipelineListItems = PipelineUtils.pipelinesResultToEditableListItems(result, activePipeline);
		pipelineListItems = pipelineListItems;

		result.map((p) => {
			pipelines = p;
		});

		if (!activePipeline) {
			activePipeline = pipelines.length ? pipelines[0] : null;
		} else {
			activePipeline = pipelines.find((p) => p.id === activePipeline.id);
		}
		rerender ? await renderActivePipelineGraph() : null;
	}

	const debouncedFetchPipelines = debounce(fetchPipelines);

	async function renderActivePipelineGraph(clear = true) {
		if (!activePipeline) {
			return;
		}
		const result = await pipelineClient.getPipeline(activePipeline.id);
		result.map((pipeline) => {
			activePipeline = pipeline;
		});
		const cells = PipelineUtils.pipelineResultToJointCells(result);
		pipelineGraph?.render(cells, clear);
		pipelineGraph?.layout();
	}

	async function addLinkToPipeline({ src, tgt, link }) {
		const source = activePipeline?.nodes.find((n) => n.id === src?.id);
		const target = activePipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineClient.addEdgeTo(activePipeline.id, source, target, link.id);
			result.map((edge) => {
				link.prop('id', edge.id);
			});
		}

		await fetchPipelines(false);
	}

	async function removeLinkFromPipeline({ src, tgt, link }) {
		const source = activePipeline?.nodes.find((n) => n.id === src?.id);
		const target = activePipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineClient.removeEdgeFrom(
				activePipeline.id,
				source,
				target,
				link.id
			);
			result
				.map((edge) => {
					pipelineGraph?.removeCell(link.id);
				})
				.mapError((error) => {
					infoModalContent = {
						title: 'Error removing edge',
						content: error
					};
				});
			await fetchPipelines(false);
		}
	}

	function highlightPipelineEdge(link: joint.dia.Link) {
		const otherLinks = activePipeline?.edges.filter((e) => {
			return e.id !== link.id;
		});

		otherLinks.forEach((l) => {
			pipelineGraph?.setCellStrokeWidth(l.id, 2);
		});

		pipelineGraph?.setCellStrokeWidth(link.id, 4);
	}

	function clearPipelineEdgeHighlight() {
		activePipeline?.edges.forEach((l) => {
			pipelineGraph?.setCellStrokeWidth(l.id, 2);
		});
	}

	function showNodeInfo(node) {
		const nodeDetails = activePipeline?.nodes.find((n) => n.id === node.id);
		if (nodeDetails) {
			infoModalContent = {
				title: nodeDetails.name,
				content: nodeDetails
			};
		}
	}

	function linkExistsInActivePipeline(linkView: joint.dia.LinkView, paper: joint.dia.Paper) {
		const link = linkView.model;
		const source = link.get('source');
		const target = link.get('target');
		const sourceNode = paper.findViewByModel(source.id);
		const targetNode = paper.findViewByModel(target.id);
		const sourceNodeModel = sourceNode.model;
		const targetNodeModel = targetNode.model;

		const linkExists = activePipeline?.edges.some(
			(e) => e.source === sourceNodeModel.id && e.sink === targetNodeModel.id
		);
		return !linkExists;
	}

	// Pipeline Creator/ Info List
	function showAddPipelineModal() {
		createPipelineStage = CreatePipelineStages.ACTIVE;
	}

	async function requestPipelineCreation() {
		if (createPipelineStage === CreatePipelineStages.CREATING) {
			return;
		}

		createPipelineStage = CreatePipelineStages.CREATING;

		const result = await pipelineClient.createPipeline(pipelineName, pipelineDescription);

		result
			.map((pipeline) => {
				createPipelineStage = CreatePipelineStages.OK;
				pipelineCreationMessage = JSON.stringify(pipeline, null, 2);
			})
			.mapError((error) => {
				createPipelineStage = CreatePipelineStages.ERROR;
				pipelineCreationMessage = JSON.stringify(error, null, 2);
			});

		pipelineName = '';
		pipelineDescription = '';
	}

	async function requestPipelineDeletion(item) {
		await pipelineClient.removePipeline(item.id);
		if (activePipeline?.id === item.id) {
			activePipeline = null;
			pipelineGraph?.clearGraph();
		}

		fetchPipelines();
	}

	async function requestPipelineInfo(item) {
		const requestedPipeline = pipelines.find((p) => p.id === item.id);
		(await pipelineClient.getPipeline(requestedPipeline.id)).map((pipeline) => {
			infoModalContent = {
				title: pipeline.name,
				content: pipeline
			};
		});
	}

	function activatePipeline(item) {
		pipelineListItems = pipelineListItems.map((i) => {
			i.active = i.id === item.id;
			return i;
		});
		if (activePipeline && activePipeline.id !== item.id) {
			pipelineGraph?.clearGraph();
		}
		activePipeline = pipelines.find((p) => p.id === item.id);
		renderActivePipelineGraph();
	}

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

	function showPluginInstaller() {
		pluginInstaller?.display();
	}

	function showPipelineImporter() {
		pipelineImporter.display();
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

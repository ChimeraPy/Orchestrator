<script lang="ts">
	import { pipelineClient, clusterClient } from '$lib/services';
	import { onMount } from 'svelte';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';
	import { debounce } from '$lib/utils';

	import PartBrowser from '$lib/Components/JointJS/PartBrowser.svelte';
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import PluginInstaller from './PluginInstaller.svelte';
	import PipelineImporter from '$lib/Components/PipelineImporter/PipelineImporter.svelte';
	import * as joint from 'jointjs';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { CreatePipelineStages } from '$lib/models';
	import type { Pipeline } from '$lib/models';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import { Icons } from '$lib/Icons';
	import { getStore } from '$lib/stores';

	import { Input, Label, Spinner } from 'flowbite-svelte';

	let nodeCells: joint.dia.Cell[];
	let pipelineName: string = '',
		pipelineDescription: string = '';
	let createPipelineStage: CreatePipelineStages = CreatePipelineStages.INACTIVE;
	let pipelineCreationMessage: string = '';
	export let modalOpen: boolean;
	let confirmMessage = 'Create Pipeline';
	let cancelMessage;
	const selectedPipelineStore = getStore('selectedPipeline');

	let pipelines = [],
		pipelineListItems = [];
	let selectedPipeline: Pipeline | null = null;
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
		createPipelineStage === CreatePipelineStages.OK ? (selectedPipeline = null) : null;
		[CreatePipelineStages.OK, CreatePipelineStages.ERROR].includes(createPipelineStage)
			? fetchPipelines()
			: null;
	}

	onMount(async () => {
		await fetchPartBrowserNodes();
		await fetchPipelines();
		const observer = new ResizeObserver((entries) => {
			entries.forEach((entry) => {
				if (entry.target === editorContainer) {
					pipelineGraph?.resize();
				}
			});
		});

		observer.observe(editorContainer);
	});

	// Part Browser
	async function fetchPartBrowserNodes(): Promise<joint.dia.Graph> {
		const result = await pipelineClient.getNodes();
		nodeCells = PipelineUtils.pipelineNodeResultToJointCells(result);
		nodeCells = nodeCells;
	}

	const debouncedFetchNodes = debounce(fetchPartBrowserNodes);

	// Pipeline Editor
	async function addNodeToActivePipeline(cell) {
		if (!selectedPipeline) {
			infoModalContent = {
				title: 'No active  ',
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

		const result = await pipelineClient.addNodeTo(selectedPipeline.id, node);
		result.mapAsync(async (node) => {
			await renderSelectedPipelineGraph();
		});
	}

	async function removeNodeFromPipeline(cell) {
		if (!selectedPipeline) {
			return;
		}
		const nodeToRemove = selectedPipeline.nodes.find((n) => n.id === cell.id);
		if (nodeToRemove) {
			const result = await pipelineClient.removeNodeFrom(selectedPipeline.id, nodeToRemove);
			result.mapError((error) => {
				infoModalContent = {
					title: 'Error removing node',
					content: error
				};
			});
			await renderSelectedPipelineGraph(true);
		}
	}

	async function fetchPipelines(rerender = true) {
		const result = await pipelineClient.getPipelines();

		pipelineListItems = PipelineUtils.pipelinesResultToEditableListItems(result, selectedPipeline);
		pipelineListItems = pipelineListItems;

		result.map((p) => {
			pipelines = p;
		});

		if (!selectedPipeline) {
			selectedPipeline = pipelines.length ? pipelines[0] : null;
		} else {
			selectedPipeline = pipelines.find((p) => p.id === selectedPipeline.id);
		}
		$selectedPipelineStore.pipeline = selectedPipeline;
		rerender ? await renderSelectedPipelineGraph() : null;
	}

	const debouncedFetchPipelines = debounce(fetchPipelines);

	async function renderSelectedPipelineGraph(clear = true) {
		if (!selectedPipeline) {
			return;
		}
		const result = await pipelineClient.getPipeline(selectedPipeline.id);
		result.map((pipeline) => {
			selectedPipeline = pipeline;
		});
		const cells = PipelineUtils.pipelineResultToJointCells(result);
		pipelineGraph?.render(cells, clear);
		pipelineGraph?.layout();
		$selectedPipelineStore.pipeline = selectedPipeline;
	}

	async function addLinkToPipeline({ src, tgt, link }) {
		const source = selectedPipeline?.nodes.find((n) => n.id === src?.id);
		const target = selectedPipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineClient.addEdgeTo(selectedPipeline.id, source, target, link.id);
			result.map((edge) => {
				link.prop('id', edge.id);
			});
		}

		await fetchPipelines(false);
	}

	async function removeLinkFromPipeline({ src, tgt, link }) {
		const source = selectedPipeline?.nodes.find((n) => n.id === src?.id);
		const target = selectedPipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineClient.removeEdgeFrom(
				selectedPipeline.id,
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

	function highlightPipelineNode(cell) {
		clearPipelineHighlights();

		pipelineGraph?.setCellStrokeWidth(cell.id, 4);
		if ($selectedPipelineStore) {
			$selectedPipelineStore.selectedNodeId = cell.id;
		}
	}

	function highlightPipelineEdge(link: joint.dia.Link) {
		clearPipelineHighlights();

		pipelineGraph?.setCellStrokeWidth(link.id, 4);
	}

	function clearPipelineHighlights() {
		selectedPipeline?.edges.forEach((l) => {
			pipelineGraph?.setCellStrokeWidth(l.id, 2);
		});

		selectedPipeline?.nodes.forEach((n) => {
			pipelineGraph?.setCellStrokeWidth(n.id, 2);
		});

		if ($selectedPipelineStore) {
			$selectedPipelineStore.selectedNodeId = null;
		}
	}

	function showNodeInfo(node) {
		const nodeDetails = selectedPipeline?.nodes.find((n) => n.id === node.id);
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

		const linkExists = selectedPipeline?.edges.some(
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
		if (selectedPipeline?.id === item.id) {
			selectedPipeline = null;
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

	function selectPipeline(item) {
		pipelineListItems = pipelineListItems.map((i) => {
			i.active = i.id === item.id;
			return i;
		});
		if (selectedPipeline && selectedPipeline.id !== item.id) {
			pipelineGraph?.clearGraph();
		}
		selectedPipeline = pipelines.find((p) => p.id === item.id);
		renderSelectedPipelineGraph();
	}

	function showPluginInstaller() {
		pluginInstaller?.display();
	}

	function showPipelineImporter() {
		pipelineImporter.display();
	}

	async function activatePipeline() {
		if (!selectedPipeline) {
			return;
		}

		const updateResult = await pipelineClient.updatePipeline(selectedPipeline.id, selectedPipeline);
		updateResult
			.map((pipeline) => {
				selectedPipeline = pipeline;
				renderSelectedPipelineGraph();
			})
			.mapError((err) => {
				infoModalContent = {
					title: 'Error activating pipeline',
					content: err
				};
			});

		const instantiationResult = await clusterClient.instantiatePipeline(selectedPipeline.id);
		instantiationResult.mapError((err) => {
			infoModalContent = {
				title: 'Error instantiating pipeline',
				content: err
			};
		});
	}
</script>

<div bind:this={editorContainer} class="w-full h-full">
	<div>
		<HorizontalMenu
			bind:this={horizontalMenu}
			on:magnify={() => pipelineGraph?.zoomIn()}
			on:reduce={() => pipelineGraph?.zoomOut()}
			on:refresh={() => pipelineGraph?.scaleContentToFit()}
			on:activatePipeline={() => activatePipeline()}
			icons={[
				{
					type: Icons.magnify,
					tooltip: 'Zoom in',
					disabled: !selectedPipeline
				},
				{
					type: Icons.reduce,
					tooltip: 'Zoom out',
					disabled: !selectedPipeline
				},
				{
					type: Icons.refresh,
					tooltip: 'Fit to screen',
					disabled: !selectedPipeline
				},
				{
					type: Icons.bolt,
					tooltip: 'Activate pipeline',
					disabled: !selectedPipeline,
					dispatchEventName: 'activatePipeline'
				}
			]}
			title="Pipeline Editor"
		/>
	</div>
	<div class="w-full h-full">
		<EditableDagViewer
			bind:this={pipelineGraph}
			additionalLinkValidators={[PipelineUtils.isValidLink, linkExistsInActivePipeline]}
			on:nodeInfo={(event) => showNodeInfo(event.detail.cell)}
			on:linkAdd={(event) => addLinkToPipeline(event.detail)}
			on:linkDblClick={(event) => removeLinkFromPipeline(event.detail)}
			on:nodeDelete={(event) => removeNodeFromPipeline(event.detail.cell)}
			on:nodeClick={(event) => highlightPipelineNode(event.detail.cell)}
			on:linkClick={(event) => highlightPipelineEdge(event.detail.cell)}
			on:blankClick={(event) => clearPipelineHighlights()}
		/>
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

<PluginInstaller bind:this={pluginInstaller} on:pluginInstalled={() => fetchPartBrowserNodes()} />
<PipelineImporter
	bind:this={pipelineImporter}
	on:importSuccess={() => {
		fetchPipelines();
		fetchPartBrowserNodes();
	}}
/>

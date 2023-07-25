<script lang="ts">
	import { pipelineClient, clusterClient } from '$lib/services';
	import { onMount } from 'svelte';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';

	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import * as joint from 'jointjs';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import { Icons } from '$lib/Icons';
	import { getStore } from '$lib/stores';
	import Alert from './Alert.svelte';
	import { Ok } from 'ts-monads';
	import { JSONEditor } from 'svelte-jsoneditor';

	enum EditorModes {
		JSON = 'json',
		GRAPH = 'graph'
	}

	let content = {
		json: {},
		text: undefined
	}

	const selectedPipelineStore = getStore('selectedPipeline');
	let modal: Alert | null = null;
	let pipelineGraph: EditableDagViewer;

	let editorContainer: HTMLElement, horizontalMenu: HTMLElement;
	let editorMode: EditorModes = EditorModes.GRAPH;

	onMount(async () => {
		const observer = new ResizeObserver((entries) => {
			entries.forEach((entry) => {
				if (entry.target === editorContainer) {
					pipelineGraph?.resize();
				}
			});
		});

		observer.observe(editorContainer);
		renderSelectedPipelineGraph(true);
	});

	async function removeNodeFromPipeline(cell) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		if (!selectedPipeline) {
			return;
		}

		const nodeToRemove = selectedPipeline.nodes.find((n) => n.id === cell.id);
		if (nodeToRemove) {
			const result = await pipelineClient.removeNodeFrom(selectedPipeline.id, nodeToRemove);
			result.mapError((error) => {
				modal?.display({
					title: 'Error removing node',
					content: error
				});
			});
			setSelectedPipeline();
		}
	}

	async function setSelectedPipeline(clear = true) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		if (!selectedPipeline) return;
		(await pipelineClient.getPipeline(selectedPipeline?.id)).map((pipeline) => {
			$selectedPipelineStore.pipeline = pipeline;
		});
		renderSelectedPipelineGraph(clear);
	}

	async function renderSelectedPipelineGraph(clear = true) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		if (!selectedPipeline) {
			return;
		}
		const cells = PipelineUtils.pipelineResultToJointCells(new Ok(selectedPipeline));
		pipelineGraph?.render(cells, clear);
		pipelineGraph?.layout();
	}

	async function addLinkToPipeline({ src, tgt, link }) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		const source = selectedPipeline?.nodes.find((n) => n.id === src?.id);
		const target = selectedPipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineClient.addEdgeTo(selectedPipeline.id, source, target, link.id);
			result.map((edge) => {
				link.prop('id', edge.id);
			});
		}
		setSelectedPipeline(false);
	}

	async function removeLinkFromPipeline({ src, tgt, link }) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
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
					modal?.display({
						title: 'Error removing edge',
						content: error
					});
				});
		}
		setSelectedPipeline(true);
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
		const selectedPipeline = $selectedPipelineStore.pipeline;
		selectedPipeline?.edges.forEach((l) => {
			pipelineGraph?.setCellStrokeWidth(l.id, 2);
		});

		selectedPipeline?.nodes.forEach((n) => {
			pipelineGraph?.setCellStrokeWidth(n.id, 2);
		});

		if ($selectedPipelineStore) {
			$selectedPipelineStore.selectedNodeId = undefined;
		}
	}

	function showNodeInfo(node) {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		const nodeDetails = selectedPipeline?.nodes.find((n) => n.id === node.id);
		if (nodeDetails) {
			modal?.display({
				title: nodeDetails.name,
				content: nodeDetails
			});
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
		const selectedPipeline = $selectedPipelineStore.pipeline;
		const linkExists = selectedPipeline?.edges.some(
			(e) => e.source === sourceNodeModel.id && e.sink === targetNodeModel.id
		);
		return !linkExists;
	}

	async function instantiatePipeline() {
		const selectedPipeline = $selectedPipelineStore.pipeline;
		if (!selectedPipeline) {
			return;
		}
		const updateResult = await pipelineClient.updatePipeline(selectedPipeline.id, selectedPipeline);
		updateResult
			.map((pipeline) => {
				$selectedPipelineStore.pipeline = pipeline;
			})
			.mapError((err) => {
				modal?.display({
					title: 'Error activating pipeline',
					content: err
				});
			});

		const instantiationResult = await clusterClient.instantiatePipeline(selectedPipeline.id);
		instantiationResult.mapError((err) => {
			modal?.display({
				title: 'Error instantiating pipeline',
				content: err
			});
		});
	}

	function setPipelineJSONContent() {
		const pipeline = $selectedPipelineStore.pipeline;
		content = {
			json: pipeline ? PipelineUtils.pipelineToEditableJSON(pipeline): {},
			text: undefined
		};
	}

	function toggleEditorMode() {
		if (editorMode === EditorModes.GRAPH) {
			editorMode = EditorModes.JSON;
		} else {
			editorMode = EditorModes.GRAPH;
			setPipelineJSONContent();
		}
	}


	$: {
		if ($selectedPipelineStore.pipeline && $selectedPipelineStore.selectedNodeId === null) {
			if (editorMode === EditorModes.GRAPH) {
				renderSelectedPipelineGraph(true);
			} else {
				setPipelineJSONContent();
			}
		} else if ($selectedPipelineStore.pipeline === null) {
			pipelineGraph?.clearGraph();
		}
	}
</script>

<div bind:this={editorContainer} class="w-full h-full">
	<div>
		<HorizontalMenu
			bind:this={horizontalMenu}
			on:magnify={() => pipelineGraph?.zoomIn()}
			on:reduce={() => pipelineGraph?.zoomOut()}
			on:refresh={() => pipelineGraph?.scaleContentToFit()}
			on:activatePipeline={() => instantiatePipeline()}
			on:toggleEditorMode={() => toggleEditorMode()}
			icons={[
				{
					type: editorMode === EditorModes.GRAPH ? Icons.code : Icons.graph,
					tooltip: editorMode === EditorModes.GRAPH ? 'JSON' : 'Graph',
					tooltipPlacement: 'bottom',
					disabled: !$selectedPipelineStore.pipeline,
					dispatchEventName: 'toggleEditorMode',
					strokeWidth: 2
				},
				{
					type: Icons.magnify,
					tooltip: 'Zoom in',
					disabled: !$selectedPipelineStore.pipeline,
					tooltipPlacement: 'bottom'
				},
				{
					type: Icons.reduce,
					tooltip: 'Zoom out',
					disabled: !$selectedPipelineStore.pipeline,
					tooltipPlacement: 'bottom'
				},
				{
					type: Icons.refresh,
					tooltip: 'Fit to screen',
					disabled: !$selectedPipelineStore.pipeline,
					tooltipPlacement: 'bottom'
				},
				{
					type: Icons.bolt,
					tooltip: 'Activate pipeline',
					disabled: !$selectedPipelineStore.pipeline,
					dispatchEventName: 'activatePipeline',
					tooltipPlacement: 'bottom'
				}
			]}
			title="Pipeline Editor"
		/>
	</div>
	<div class="w-full h-full">
		{#if editorMode === EditorModes.GRAPH}
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
		{:else}
			<JSONEditor {content} navigationBar="{false}" />
		{/if}
	</div>
</div>

<Alert bind:this={modal} />

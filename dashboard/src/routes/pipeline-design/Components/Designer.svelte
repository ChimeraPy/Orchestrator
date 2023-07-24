<script lang="ts">
	import { pipelineClient, clusterClient } from '$lib/services';
	import { onMount } from 'svelte';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';

	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import * as joint from 'jointjs';
	import type { Pipeline } from '$lib/models';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import { Icons } from '$lib/Icons';
	import { getStore } from '$lib/stores';
	import Alert from './Alert.svelte';

	let nodeCells: joint.dia.Cell[];
	const selectedPipelineStore = getStore('selectedPipeline');
	let modal: Alert | null = null;
	let selectedPipeline: Pipeline | null = null;
	let pipelineGraph: EditableDagViewer;

	let editorContainer: HTMLElement, horizontalMenu: HTMLElement;

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
		if (!$selectedPipelineStore.pipeline) {
			return;
		}
		const selectedPipeline = $selectedPipelineStore.pipeline;
		const nodeToRemove = selectedPipeline.nodes.find((n) => n.id === cell.id);
		if (nodeToRemove) {
			const result = await pipelineClient.removeNodeFrom(selectedPipeline.id, nodeToRemove);
			result.mapError((error) => {
				modal?.display({
					title: 'Error removing node',
					content: error
				});
			});
			await renderSelectedPipelineGraph(true);
		}
	}

	async function renderSelectedPipelineGraph(clear = true) {
		if (!$selectedPipelineStore.pipeline) {
			return;
		}
		const result = await pipelineClient.getPipeline($selectedPipelineStore.pipeline.id);
		const cells = PipelineUtils.pipelineResultToJointCells(result);
		pipelineGraph?.render(cells, clear);
		pipelineGraph?.layout();
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
			$selectedPipelineStore.selectedNodeId = null;
		}
	}

	function showNodeInfo(node) {
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

		const linkExists = selectedPipeline?.edges.some(
			(e) => e.source === sourceNodeModel.id && e.sink === targetNodeModel.id
		);
		return !linkExists;
	}

	async function instantiatePipeline() {
		if (!$selectedPipelineStore.pipeline) {
			return;
		}
		const selectedPipeline = $selectedPipelineStore.pipeline;
		const updateResult = await pipelineClient.updatePipeline(selectedPipeline.id, selectedPipeline);
		updateResult
			.map((pipeline) => {
				$selectedPipelineStore.pipeline = pipeline;
				renderSelectedPipelineGraph();
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
</script>

<div bind:this={editorContainer} class="w-full h-full">
	<div>
		<HorizontalMenu
			bind:this={horizontalMenu}
			on:magnify={() => pipelineGraph?.zoomIn()}
			on:reduce={() => pipelineGraph?.zoomOut()}
			on:refresh={() => pipelineGraph?.scaleContentToFit()}
			on:activatePipeline={() => instantiatePipeline()}
			icons={[
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

<Alert bind:this={modal} />

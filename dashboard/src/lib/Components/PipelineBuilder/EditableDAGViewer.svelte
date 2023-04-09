<script lang="ts">
	import * as joint from 'jointjs';
	import * as dagre from 'dagre';
	import * as graphLib from 'graphlib';
	import { LinkValidator, getConnectTool, getInfoButton, getDeleteButton } from './utils';
	import type { ValidatorFunc } from './utils';
	import { createEventDispatcher } from 'svelte';

	import { onMount } from 'svelte';

	export let additionalLinkValidators: ValidatorFunc[] = [];

	let cells: joint.dia.Cell[] = [];

	let paper: joint.dia.Paper;
	let graph: joint.dia.Graph;
	let paperEl: HTMLDivElement;
	const dispatch = createEventDispatcher();

	onMount(() => {
		graph = new joint.dia.Graph();
		graph.addCells(cells);
		const validator = new LinkValidator([...additionalLinkValidators]);
		paper = new joint.dia.Paper({
			el: paperEl,
			model: graph,
			width: '100%',
			height: '100%',
			gridSize: 10,
			drawGrid: {
				name: 'fixedDot',
				args: {
					color: 'rgba(0, 0, 0, 0.5)',
					thickness: 1
				}
			},
			interactive: true,
			allowLink: validator.isValidLink.bind(validator),
			defaultRouter: {
				name: 'manhattan',
				args: {
					step: 30
				}
			},

			defaultLink: new joint.shapes.standard.Link({
				attrs: {
					line: {
						stroke: '#000000',
						strokeWidth: 2,
						targetMarker: {
							type: 'path',
							d: 'M 10 -5 0 0 10 5 z'
						}
					}
				}
			})
		} as joint.dia.Paper.Options);

		paper.on('element:mouseenter', (elementView) => {
			elementView.showTools();
		});

		paper.on('element:mouseleave', (elementView) => {
			elementView.hideTools();
		});

		paper.on('link:pointerdblclick', (cellView) => {
			doubleClickEvent(cellView.model);
		});

		paper.on('link:connect', (linkView) => {
			const link = linkView.model;
			const src = link.getSourceElement();
			const tgt = link.getTargetElement();
			if (src && tgt) {
				dispatch('linkAdd', { src, tgt, link });
			}
		});

		paper.on('cell:pointerclick', (cellView) => {
			const cell = cellView.model;
			clickEvent(cell);
		});
	});

	export function clearGraph() {
		graph?.clear();
	}

	export function render(cells: joint.dia.Cell[], clear = false) {
		clearGraph();
		graph?.addCells(cells);

		graph?.getElements().forEach((element) => {
			const toolsView = new joint.dia.ToolsView({
				tools: [
					getConnectTool(),
					getInfoButton((cell) => infoEvent(cell)),
					getDeleteButton((cell) => doubleClickEvent(cell))
				]
			});
			element.findView(paper)?.addTools(toolsView);
			element.findView(paper)?.hideTools();
		});
	}

	function doubleClickEvent(cell: joint.dia.Cell) {
		if (cell.isLink()) {
			const src = cell.source();
			const tgt = cell.target();
			const link = cell;
			dispatch('linkDblClick', { src, tgt, link });
		} else {
			dispatch('nodeDblClick', { cell });
		}
	}

	function clickEvent(cell) {
		const event = cell.isLink() ? 'linkClick' : 'nodeClick';
		dispatch(event, { cell });
	}

	function infoEvent(cell) {
		cell.isLink() ? null : dispatch('nodeInfo', { cell });
	}

	export function removeCell(cellId: string) {
		const modelView = paper.findViewByModel(cellId);
		modelView.model.remove();
	}

	export function setCellStrokeWidth(cellId: string, width: number) {
		const modelView = paper.findViewByModel(cellId);
		const cell = modelView?.model;
		if (!cell) return;
		if (cell.isLink()) {
			cell.attr('line/strokeWidth', width);
		} else {
			cell.attr('body/strokeWidth', width);
		}
	}

	export function layout() {
		if (!graph) return;

		joint.layout.DirectedGraph.layout(graph, {
			setLinkVertices: false,
			rankDir: 'TB',
			marginX: 100,
			marginY: 100,
			nodeSep: 100,
			edgeSep: 10,
			rankSep: 50,
			resizeCluster: true,
			ranker: 'tight-tree',
			align: 'DR',
			dagre: dagre,
			graphlib: graphLib
		});

		paper?.scaleContentToFit({
			padding: 20,
			useModelGeometry: true,
			maxScale: 1.5,
			minScale: 0.6
		});
	}

	export function resize() {
		paper?.setDimensions('100%', '100%');
	}
</script>

<div class="w-full h-full">
	<div use:resize bind:this={paperEl} />
</div>

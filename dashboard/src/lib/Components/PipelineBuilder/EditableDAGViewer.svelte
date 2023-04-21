<script lang="ts">
	import * as joint from 'jointjs';
	import * as dagre from 'dagre';
	import * as graphLib from 'graphlib';
	import { LinkValidator, ToolViewType, getToolType } from './utils';
	import type { DispatcherFunc, ToolOptions, ValidatorFunc } from './utils';
	import { createEventDispatcher } from 'svelte';
	import { PaperScaler } from './PaperScaler';

	import { onMount } from 'svelte';

	export let additionalLinkValidators: ValidatorFunc[] = [];
	export let toolViewAttachments: ToolViewType[] = [
		ToolViewType.HOVER_CONNECT,
		ToolViewType.DELETE,
		ToolViewType.INFO // ToDo: Make sure this is added in the end
	];
	export let tooViewAttachmentsOptions: { [key in ToolViewType]: ToolOptions } = {
		[ToolViewType.DELETE]: {},
		[ToolViewType.INFO]: {},
		[ToolViewType.HOVER_CONNECT]: {}
	};

	let cells: joint.dia.Cell[] = [];
	const dispatchers: { [key in ToolViewType]: DispatcherFunc | null } = {
		[ToolViewType.DELETE]: deleteEvent,
		[ToolViewType.INFO]: infoEvent,
		[ToolViewType.HOVER_CONNECT]: null
	};

	let paper: joint.dia.Paper;
	let graph: joint.dia.Graph;
	let paperEl: HTMLDivElement;
	let paperContainer: HTMLDivElement;
	const dispatch = createEventDispatcher();
	let paperScaler: PaperScaler | null = null;

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
		paperScaler = new PaperScaler(paper);

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

		paper.on('blank:pointerclick', () => {
			dispatch('blankClick');
		});
	});

	export function clearGraph() {
		graph?.clear();
	}

	export function zoomIn() {
		paperScaler?.zoomIn();
	}

	export function zoomOut() {
		paperScaler?.zoomOut();
	}

	function getTools() {
		return toolViewAttachments.map((tool) => {
			const options = tooViewAttachmentsOptions[tool];
			return getToolType(tool, dispatchers[tool], options);
		});
	}

	export function render(cells: joint.dia.Cell[], clear = false) {
		clearGraph();
		graph?.addCells(cells);

		graph?.getElements().forEach((element) => {
			const toolsView = new joint.dia.ToolsView({
				tools: getTools(element)
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

	function deleteEvent(cell: joint.dia.Cell) {
		if (cell.isLink()) {
			const src = cell.source();
			const tgt = cell.target();
			const link = cell;
			dispatch('linkDelete', { src, tgt, link });
		} else {
			dispatch('nodeDelete', { cell });
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
		} as joint.layout.DirectedGraph.LayoutOptions);
		scaleContentToFit();
	}

	export function resize() {
		if(!paperContainer) return;
		paper?.setDimensions(paperContainer.clientWidth, paperContainer.clientHeight);
	}

	export function scaleContentToFit() {
		paper?.setDimensions(paperContainer?.clientWidth, paperContainer.clientHeight);
		paperScaler?.scaleContentToFit();
	}
</script>

<div
	bind:this={paperContainer}
	class="w-full h-full overflow-scroll scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-100 "
>
	<div bind:this={paperEl}>
	</div>
</div>

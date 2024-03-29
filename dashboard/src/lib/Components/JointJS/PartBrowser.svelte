<script lang="ts">
	import 'jointjs/dist/joint.css';
	import * as joint from 'jointjs';
	import { onMount, createEventDispatcher } from 'svelte';
	import { getAddTool, getInfoTool } from './utils';

	export let cells: joint.dia.Cell[] = [];
	export let mode: 'vertical' | 'horizontal' = 'vertical';
	export let offsetX: number = 100;
	export let offsetY: number = 80;
	let paperContainer: HTMLElement;
	let paper: joint.dia.Paper;
	let graph: joint.dia.Graph;

	let width: number = 0,
		height: number = 0;
	const dispatch = createEventDispatcher();
	const bgColor = '#F3F7F6';

	function layoutCells(width: number, height: number) {
		if (!paper) return;
		if (!graph) return;
		if (width === 0) return;
		if (height === 0) return;
		paper.freeze();
		let xpos: number = 0,
			ypos: number = 0;

		graph.getElements().forEach((element, index) => {
			if (!element.isLink()) {
				const bbox = element.getBBox();
				const elW = bbox.width;
				const elH = bbox.height;

				if (mode == 'vertical') {
					xpos = (width - elW) * 0.5;
					ypos = index * offsetY + elH;
				} else {
					xpos = index * offsetX + elW;
					ypos = (height - elH) * 0.5;
				}
				element.position(xpos, ypos);
			}
		});
		let w: number, h: number;
		if (mode == 'vertical') {
			w = width;
			h = Math.max(height, ypos + 2 * offsetY);
		} else {
			w = Math.max(width, xpos + 2 * offsetX);
			h = height;
		}

		paper.setDimensions(w, h);

		paper.unfreeze();
	}

	function reLayout(entry: ResizeObserverEntry): void {
		if (entry.target == paperContainer) {
			const cr = entry.contentRect;
			if (paper) {
				const w = Math.floor(cr.width);
				const h = Math.floor(cr.height);
				width = w;
				height = h;
			}
		}
	}

	$: layoutCells(width, height);

	$: {
		cells = cells;
		refreshGraph(cells);
	}

	function refreshGraph(cells: joint.dia.Cell[]) {
		addCells(cells);
	}

	function addCells(cells: joint.dia.Cell[]) {
		if (!paper) return;
		if (!graph) return;
		paper.freeze();
		graph.clear();
		graph.addCells(cells);
		graph.getElements().forEach((element) => {
			if (!element.isLink()) {
				const elementTools = new joint.dia.ToolsView({
					tools: [
						getAddTool((node) => {
							dispatchElementClickEvent(node as joint.dia.Element);
						}, {}),
						getInfoTool(
							(node) => {
								dispatchElementInfoEvent(node as joint.dia.Element);
							},
							{ x: '0%' }
						)
					]
				});
				element.findView(paper).addTools(elementTools);
			}
		});
		paper.unfreeze();
		layoutCells(width, height);
	}

	onMount(() => {
		const el = document.getElementById('paper');
		graph = new joint.dia.Graph();
		paper = new joint.dia.Paper({
			el: el,
			model: graph,
			gridSize: 5,
			drawGrid: false,
			interactive: false,
			async: true,
			frozen: true,
			sorting: joint.dia.Paper.sorting.APPROX,
			background: { color: bgColor },
			snapLinks: false
		} as joint.dia.Paper.Options);

		const observer = new ResizeObserver((entries) => {
			entries.forEach(reLayout);
		});

		paper.on('element:pointerdblclick', (elementView: joint.dia.ElementView) => {
			const isElement = elementView.model.isElement();
			if (isElement) {
				dispatchElementClickEvent(elementView.model);
			}
		});

		observer.observe(paperContainer);
	});

	function dispatchElementClickEvent(cell: joint.dia.Element) {
		dispatch('cellClick', cell);
	}

	function dispatchElementInfoEvent(cell: joint.dia.Element) {
		dispatch('cellInfo', cell);
	}

	function resize() {
		paper?.setDimensions('100%', '100%');
	}
</script>

<div
	class="relative
			h-full
			w-full
			scrollbar-thin
            scrollbar-thumb-gray-700
            scrollbar-track-gray-100
            bg-[{bgColor}]
            overflow-auto"
	id="paper-container"
	bind:this={paperContainer}
>
	<div use:resize id="paper" />
</div>

<style>
	/* Proper Cursor was not showing up for the jointjs nodes in arch linux */
	:global(g) {
		cursor: pointer !important;
	}
</style>

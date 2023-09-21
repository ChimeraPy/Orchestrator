<script lang="ts">
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import { Select, Label } from 'flowbite-svelte';
	import { getStore } from '$lib/stores';
	import type { Pipeline, PipelineNode } from '$lib/models';
	import {JSONEditor} from "svelte-jsoneditor";

	let networkStore = getStore('network');
	let selectedPipelineStore = getStore('selectedPipeline');
	let lifeCycleStore = getStore('lifeCycle');
	let selectedWorkerId = null;
	let kwargs = {
		text: {}
	};

	function getNodeTitle() {
		const node = getNode($selectedPipelineStore.pipeline, $selectedPipelineStore.selectedNodeId);
		return node?.name || 'No node selected';
	}

	function getNode(pipeline: Pipeline, nodeId: string): PipelineNode | null {
		if (!pipeline) return null;
		if (!nodeId) return null;

		return pipeline.nodes.find((n) => n.id === nodeId);
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

	function onWorkerIdSelectionChange() {
		if ($selectedPipelineStore?.selectedNodeId === null) return;
		let selectedNode = getNode(
			$selectedPipelineStore.pipeline,
			$selectedPipelineStore.selectedNodeId
		);
		selectedNode ? (selectedNode.worker_id = selectedWorkerId) : null;
		selectedNode = selectedNode;
	}

	function getNodeKwargs() {
		const node = getNode($selectedPipelineStore.pipeline, $selectedPipelineStore.selectedNodeId);
		return node?.kwargs || {};
	}

	$: {
		if ($selectedPipelineStore?.selectedNodeId !== null) {
			kwargs = {
				text: JSON.stringify(getNodeKwargs(), null, 2)
			};
		}

	}
</script>

<div class="w-full h-full">
	<div>
		<HorizontalMenu title={getNodeTitle($selectedPipelineStore)} backgroundClass="bg-blue-600" />
	</div>
	<div class="w-full h-full bg-[#F3F7F6]">
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

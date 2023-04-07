<script lang="ts">
	import { pipelineService } from '$lib/stores';
	import { onMount } from 'svelte';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';
	import { debounce } from '$lib/utils';
	import PartBrowser from '$lib/Components/PipelineBuilder/PartBrowser.svelte';
	import HorizontalMenu from '$lib/Components/PipelineBuilder/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/PipelineBuilder/EditableList.svelte';
	import * as joint from 'jointjs';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { CreatePipelineStages } from '../../lib/models';
	import type { Pipeline } from '../../lib/models';
	import EditableDagViewer from '$lib/Components/PipelineBuilder/EditableDAGViewer.svelte';

	import { Input, Label, Spinner } from 'flowbite-svelte';

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
	let infoModalContent: { title: string; content: any } | null = null;

	let editorContainer: HTMLElement, horizontalMenu: HTMLElement;

	$: modalOpen = createPipelineStage !== CreatePipelineStages.INACTIVE;
	$: cancelMessage = [CreatePipelineStages.OK, CreatePipelineStages.ERROR].includes(
		createPipelineStage
	)
		? 'Close'
		: 'Cancel';

	$: [CreatePipelineStages.OK, CreatePipelineStages.ERROR].includes(createPipelineStage)
		? fetchPipelines()
		: null;

	onMount(async () => {
		await fetchNodes();
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

	async function fetchNodes(): Promise<joint.dia.Graph> {
		const result = await pipelineService.getNodes();
		nodeCells = PipelineUtils.pipelineNodeResultToJointCells(result);
		nodeCells = nodeCells;
	}

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
			id: cell.id
		};

		const result = await pipelineService.addNodeTo(activePipeline.id, node);
		result.mapAsync(async (node) => {
			await renderActivePipelineGraph();
		});
	}

	async function removeNodeFromPipeline(cell) {
		if (!activePipeline) {
			return;
		}
		const nodeToRemove = activePipeline.nodes.find((n) => n.id === cell.id);
		console.log(cell.id, nodeToRemove, Array.from(arguments));
		if (nodeToRemove) {
			const result = await pipelineService.removeNodeFrom(activePipeline.id, nodeToRemove);
			result.mapError((error) => {
				infoModalContent = {
					title: 'Error removing node',
					content: error
				};
			});
			await renderActivePipelineGraph(true);
		}
	}

	async function fetchPipelines() {
		const result = await pipelineService.getPipelines();
		pipelineListItems = PipelineUtils.pipelinesResultToEditableListItems(result);
		result.map((p) => {
			pipelines = p;
		});
		if (!activePipeline) {
			activePipeline = pipelines.length ? pipelines[0] : null;
			await renderActivePipelineGraph();
		}
	}

	const debouncedFetchNodes = debounce(fetchNodes);

	function showPipelineModal() {
		createPipelineStage = CreatePipelineStages.ACTIVE;
	}

	async function requestPipelineCreation() {
		if (createPipelineStage === CreatePipelineStages.CREATING) {
			return;
		}

		createPipelineStage = CreatePipelineStages.CREATING;

		const result = await pipelineService.createPipeline(pipelineName, pipelineDescription);

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

	async function showPipelineInfo(item) {
		const requestedPipeline = pipelines.find((p) => p.id === item.id);
		(await pipelineService.getPipeline(requestedPipeline.id)).map((pipeline) => {
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

	async function renderActivePipelineGraph(clear = true) {
		if (!activePipeline) {
			return;
		}
		const result = await pipelineService.getPipeline(activePipeline.id);
		result.map((pipeline) => {
			activePipeline = pipeline;
		});
		const cells = PipelineUtils.pipelineResultToJointCells(result);
		pipelineGraph?.render(cells, clear);
		pipelineGraph?.layout();
	}

	async function deletePipeline(item) {
		await pipelineService.deletePipeline(item.id);
		if (activePipeline?.id === item.id) {
			activePipeline = null;
			pipelineGraph?.clearGraph();
		}

		fetchPipelines();
	}

	async function addLinkToPipeline({ src, tgt, link }) {
		const source = activePipeline?.nodes.find((n) => n.id === src?.id);
		const target = activePipeline?.nodes.find((n) => n.id === tgt?.id);

		if (source && target) {
			const result = await pipelineService.addEdgeTo(activePipeline.id, source, target);
		}
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
</script>

<div class="h-full flex">
	<nav class="w-64 flex flex-col border-r-2 border-gray-400">
		<div>
			<HorizontalMenu
				on:refresh={debouncedFetchNodes}
				title="Nodes"
				refreshBtn={true}
				backgroundClass="bg-blue-600"
			/>
		</div>
		<PartBrowser
			on:cellClick={(event) => addNodeToActivePipeline(event.detail)}
			cells={nodeCells}
		/>
	</nav>
	<div class="flex flex-col flex-1 bg-indigo-100 border-r-2 border-gray-400">
		<div bind:this={editorContainer} class="flex-1 flex flex-col">
			<div>
				<HorizontalMenu bind:this={horizontalMenu} title="Pipeline Editor" />
			</div>
			<div class="flex-1">
				<EditableDagViewer
					bind:this={pipelineGraph}
					additionalLinkValidators={[PipelineUtils.isValidLink, linkExistsInActivePipeline]}
					on:nodeInfo={(event) => showNodeInfo(event.detail.cell)}
					on:linkAdd={(event) => addLinkToPipeline(event.detail)}
					on:linkRemove={(event) => removeLinkFromPipeline(event.detail)}
					on:nodeRemove={(event) => removeNodeFromPipeline(event.detail.cell)}
				/>
			</div>
		</div>
		<div class="flex-1">
			<HorizontalMenu title="Active Jobs" />
		</div>
	</div>
	<nav class="w-64 flex-none bg-indigo-50">
		<HorizontalMenu
			title="Pipelines"
			backgroundClass="bg-blue-600"
			refreshBtn={true}
			addBtn={true}
			on:add={showPipelineModal}
			on:refresh={fetchPipelines}
		/>
		<EditableList
			items={pipelineListItems}
			on:info={(event) => showPipelineInfo(event.detail)}
			on:click={(event) => activatePipeline(event.detail)}
			on:delete={(event) => deletePipeline(event.detail)}
		/>
	</nav>
</div>
<!-- Creation Modal -->
<Modal
	type="confirm"
	title="Pipeline Creator"
	bind:modalOpen
	disableConfirm={!pipelineName}
	autoclose={false}
	{confirmMessage}
	{cancelMessage}
	on:confirm={requestPipelineCreation}
	on:cancel={() => (createPipelineStage = CreatePipelineStages.INACTIVE)}
>
	<div slot="content">
		{#if createPipelineStage === CreatePipelineStages.ERROR}
			<div class="text-red-500">
				<h3 class="text-xl font-medium text-red-900 p-0">Error</h3>
				<pre>{pipelineCreationMessage}</pre>
			</div>
		{:else if createPipelineStage === CreatePipelineStages.OK}
			<div>
				<h3 class="text-xl font-medium text-green-900 p-0">Success</h3>
				<pre>{pipelineCreationMessage}</pre>
			</div>
		{:else}
			<h3 class="text-xl font-medium text-gray-900 p-0">
				{#if createPipelineStage === CreatePipelineStages.CREATING}
					<Spinner size={4} color="green" />
				{/if}
				{createPipelineStage === CreatePipelineStages.CREATING ? 'Creating' : 'Create'} a New Pipeline
			</h3>
			<br />
			<Label class="space-y-2">
				<span>Pipeline Name</span>
				<Input
					bind:value={pipelineName}
					type="text"
					name="pipeline"
					placeholder="Be creative here"
					required
				/>
			</Label>
			<br />
			<Label class="space-y-2">
				<span>Pipeline Description(optional)</span>
				<Input
					bind:value={pipelineDescription}
					type="text"
					name="pipeline"
					placeholder="Be creative here"
				/>
			</Label>
		{/if}
	</div>
</Modal>

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

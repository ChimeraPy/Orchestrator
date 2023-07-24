<script lang="ts">
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import EditableList from '$lib/Components/JointJS/EditableList.svelte';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { Icons } from '$lib/Icons';
	import { getStore } from '$lib/stores';
	import { pipelineClient } from '../../../lib/services';
	import { CreatePipelineStages } from '../../../lib/models';
	import type { Pipeline } from '../../../lib/models';
	import { PipelineUtils } from '../../../lib/Services/PipelineUtils';
	import { Input, Spinner, Label } from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import PipelineImporter from './PipelineImporter.svelte';
	import { debounce } from '$lib/utils';
	import Alert from './Alert.svelte';

	export let modalOpen;
	let modal: Alert | null = null;
	let confirmMessage = 'Create Pipeline';
	let cancelMessage;
	let pipelineName: string = '',
		pipelineDescription: string = '';
	let createPipelineStage: CreatePipelineStages = CreatePipelineStages.INACTIVE;
	let pipelineCreationMessage: string = '';
	let pipelines = [];
	let pipelineListItems = [];
	let selectedPipeline: Pipeline | null = null;
	let pipelineImporter: PipelineImporter | null = null;

	const selectedPipelineStore = getStore('selectedPipeline');

	onMount(() => {
		fetchPipelines();
	});

	async function fetchPipelines() {
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
	}

	const debouncedFetchPipelines = debounce(fetchPipelines);

	function showAddPipelineModal() {
		createPipelineStage = CreatePipelineStages.ACTIVE;
	}

	function showPipelineImporter() {
		pipelineImporter?.display();
	}

	async function requestPipelineInfo(item: Pipeline) {
		const requestedPipeline = pipelines.find((p) => p.id === item.id);
		(await pipelineClient.getPipeline(requestedPipeline.id)).map((pipeline) => {
			modal?.display({
				title: pipeline.name,
				content: pipeline
			});
		});
	}

	function selectPipeline(item) {
		pipelineListItems = pipelineListItems.map((i) => {
			i.active = i.id === item.id;
			return i;
		});

		selectedPipeline = pipelines.find((p) => p.id === item.id);
		$selectedPipelineStore.pipeline = selectedPipeline;
	}

	async function requestPipelineDeletion(item) {
		await pipelineClient.removePipeline(item.id);

		if (selectedPipeline?.id === item.id) {
			selectedPipeline = null;
		}

		fetchPipelines();
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
</script>

<div class="h-full w-full">
	<div>
		<HorizontalMenu
			title="Pipelines"
			backgroundClass="bg-blue-600"
			icons={[
				{ type: Icons.refresh, tooltip: 'Refresh Pipelines', tooltipPlacement: 'bottom' },
				{ type: Icons.add, tooltip: 'Create a new Pipeline', tooltipPlacement: 'bottom' },
				{
					type: Icons.upload,
					tooltip: 'Import a Pipeline',
					tooltipPlacement: 'bottom',
					fill: 'none',
					strokeWidth: 2
				}
			]}
			on:add={showAddPipelineModal}
			on:upload={showPipelineImporter}
			on:refresh={debouncedFetchPipelines}
		/>
	</div>
	<div class="h-full w-full bg-[#F3F7F6] pb-10">
		<EditableList
			items={pipelineListItems}
			on:info={(event) => requestPipelineInfo(event.detail)}
			on:click={(event) => selectPipeline(event.detail)}
			on:delete={(event) => requestPipelineDeletion(event.detail)}
		/>
	</div>
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

<PipelineImporter
	bind:this={pipelineImporter}
	on:importSuccess={() => {
		fetchPipelines();
	}}
/>

<Alert bind:this={modal} />

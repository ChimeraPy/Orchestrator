<script lang="ts">
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { Fileupload, Label, Helper, Spinner } from 'flowbite-svelte';
	import { pipelineClient } from '$lib/services';
	import type { ChimeraPyPipelineConfig } from '$lib/pipelineConfig';
	import { createEventDispatcher } from 'svelte';

	let modalOpen = false;
	const dispatch = createEventDispatcher();

	const HELP_TEXT = {
		link: 'https://github.com/ChimeraPy/Orchestrator/blob/main/chimerapy/orchestrator/models/pipeline_config.py',
		text: 'chimerapy.orchestrator.models.pipeline_models.pipeline_config.py'
	};

	enum ImportStages {
		IDLE = 0,
		READY = 2,
		IMPORTING = 3,
		IMPORTED = 4,
		ERROR = 5
	}

	let importStage = ImportStages.IDLE;
	let files: FileList | null = null;
	let error: string | null = null;
	let pipelineConfig: any | null = null;

	export function display() {
		reset();
		modalOpen = true;
	}

	export function hide() {
		reset();
		modalOpen = false;
	}

	function reset() {
		files = null;
		error = null;
		pipelineConfig = null;
		importStage = ImportStages.IDLE;
	}

	function dispatchImportSuccess(pipeline: any) {
		dispatch('importSuccess', pipeline);
	}

	function dispatchImportError(error: string) {
		dispatch('importError', error);
	}

	async function markImportReady(fileList: FileList) {
		const file = fileList[0];
		try {
			error = null;
			const contents = await file.text();
			pipelineConfig = JSON.parse(contents) as ChimeraPyPipelineConfig;
			importStage = ImportStages.READY;
		} catch (e) {
			pipelineConfig = null;
			importStage = ImportStages.ERROR;
			error = e.message;
		}
	}

	async function tryImportingPipeline() {
		importStage = ImportStages.IMPORTING;
		const importResult = await pipelineClient.importPipeline(pipelineConfig);
		importResult
			.map((pipeline) => {
				importStage = ImportStages.IMPORTED;
				dispatchImportSuccess(pipeline);
			})
			.mapError((e) => {
				error = e.message;
				importStage = ImportStages.ERROR;
				dispatchImportError(e.message);
			});
	}

	$: files && markImportReady(files);
</script>

<Modal
	type="confirm"
	title="Pipeline Importer"
	cancelMessage="Close"
	confirmMessage="Import"
	autoclose={false}
	disableConfirm={!(importStage === ImportStages.READY)}
	bind:modalOpen
	on:cancel={hide}
	on:confirm={tryImportingPipeline}
>
	<div slot="content">
		{#if importStage === ImportStages.IMPORTING}
			<Spinner color="gray" />
			<h2 class="text-xl text-gray-500 mt-6 p-2">Importing pipeline...</h2>
		{:else if importStage === ImportStages.IMPORTED}
			<h2 class="text-xl text-green-500 mt-6 p-2">Pipeline imported successfully!</h2>
		{:else if [ImportStages.READY, ImportStages.IDLE].includes(importStage)}
			<Label for="with_helper" class="pb-2">Upload a <code>PipelineConfig</code> JSON file</Label>
			<Fileupload bind:files id="with_helper" class="mb-2" />
			<Helper>
				See
				<a href={HELP_TEXT.link} target="_blank">
					<code class="bg-gray-200 text-red-500 p-1 font-mono">{HELP_TEXT.text}</code>
				</a> for further details.
			</Helper>
		{:else if importStage === ImportStages.ERROR}
			<h2 class="text-xl text-red-900">Error</h2>
			<p class="text-red-500 mt-6 p-2">{JSON.stringify(error)}</p>
		{/if}
	</div>
</Modal>

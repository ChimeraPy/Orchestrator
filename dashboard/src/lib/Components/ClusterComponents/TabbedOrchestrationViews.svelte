<script lang="ts">
	import { clusterClient } from '$lib/services';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { Tabs, TabItem } from 'flowbite-svelte';
	import { ToolViewType } from '$lib/Components/PipelineBuilder/utils';
	import { getIconPath, Icons } from '$lib/Icons';
	import HorizontalMenu from '$lib/Components/PipelineBuilder/HorizontalMenu.svelte';

	import EditableDagViewer from '$lib/Components/PipelineBuilder/EditableDAGViewer.svelte';
	import { onMount } from 'svelte';

	import { getStore } from '$lib/stores';
	import { PipelineUtils } from '../../Services/PipelineUtils';

	export let committablePipeline;
	let committedPipelineGraph, committedPipelineGraphContainer;
	export let cannotCommitModalContent: {
		title: string;
		content: any;
		alertMessage?: string;
	} | null = null;
	let pipelineCells = [];

	const pipelineStore = getStore('committedPipeline');

	export async function onConfirmCommit() {
		if (!committablePipeline) {
			return;
		}
		const responseResult = await clusterClient.commitPipeline(committablePipeline?.id);
		responseResult
			.map((pipeline) => {
				cannotCommitModalContent = {
					title: 'SUCCESS',
					content: pipeline,
					alertMessage: 'Close'
				};
			})
			.mapError((error) => {
				cannotCommitModalContent = {
					title: `Cannot commit pipeline ${committablePipeline?.name}`,
					content: error,
					alertMessage: 'Close'
				};
			});
		committablePipeline = null;
	}

	let icons = [
		{
			type: Icons.play,
			tooltip: 'Run',
			disabled: !committablePipeline
		}
	];

	$: committablePipeline && onConfirmCommit();

	$: {
		pipelineCells = $pipelineStore
			? PipelineUtils.committablePipelineToJointCells($pipelineStore)
			: [];
		pipelineCells = pipelineCells;
		committedPipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
		committedPipelineGraph?.layout();
	}

	function beginPipelineExecution() {
		if (!committablePipeline) {
			return;
		}
		// clusterClient.beginPipelineExecution(committablePipeline?.id);
	}

	export function resize() {
		committedPipelineGraph?.resize();
	}
</script>

<div>
	<HorizontalMenu title="Orchestration" {icons} on:play={beginPipelineExecution} />
</div>
<div class="flex-1 flex justify-center items-center bg-[#F3F7F6] overflow-hidden">
	<EditableDagViewer
		editable={false}
		bind:this={committedPipelineGraph}
		additionalLinkValidators={[]}
		toolViewAttachments={[ToolViewType.INFO]}
		on:info={(event) => {
			console.log('info', event.detail);
		}}
	/>
</div>

<!-- Info Modal -->
<Modal
	type="alert"
	title={cannotCommitModalContent?.title}
	bind:modalOpen={cannotCommitModalContent}
	autoclose={true}
	alertMessage={cannotCommitModalContent?.alertMessage || 'Close'}
	on:cancel={() => (cannotCommitModalContent = null)}
	on:alert={() => (cannotCommitModalContent = null)}
>
	<div slot="content">
		<h3 class="text-xl font-medium text-green-900 p-2">{cannotCommitModalContent.title}</h3>
		<pre>{JSON.stringify(cannotCommitModalContent.content, null, 2)}</pre>
	</div>
</Modal>

<style lang="postcss">
	.apply-width {
		/*width: 100%;*/
	}
</style>

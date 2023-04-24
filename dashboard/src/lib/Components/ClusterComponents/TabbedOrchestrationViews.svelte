<script lang="ts">
	import { clusterClient } from '$lib/services';
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { Tabs, TabItem } from 'flowbite-svelte';
	import { ToolViewType } from '$lib/Components/PipelineBuilder/utils';
	import { getIconPath, Icons } from '$lib/Icons';

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

	onMount(async () => {
		const observer = new ResizeObserver((entries) => {
			entries.forEach((entry) => {
				if (entry.target === committedPipelineGraphContainer) {
					// committedPipelineGraph?.resize(
					// );
				}
			});
		});

		observer.observe(committedPipelineGraphContainer);
		if (committedPipelineGraphContainer) {
			committedPipelineGraphContainer.parentNode.classList.add('h-full');
			committedPipelineGraphContainer.parentNode.classList.add('w-full');
		}
	});

	$: committablePipeline && onConfirmCommit();

	$: {
		pipelineCells = $pipelineStore
			? PipelineUtils.committablePipelineToJointCells($pipelineStore)
			: [];
		pipelineCells = pipelineCells;
		console.log('pipelineCells', pipelineCells);
		committedPipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
		committedPipelineGraph?.layout();
	}
</script>

<Tabs style="underline" contentClass="h-full w-full flex flex-col">
	<TabItem open>
		<div slot="title" class="flex items-center gap-2">
			<svg
				aria-hidden="true"
				class="w-5 h-5"
				fill="currentColor"
				viewBox="0 0 20 20"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path fill-rule="evenodd" d={getIconPath(Icons.bolt)} clip-rule="evenodd" />
			</svg>
			Committed Pipeline
		</div>
		<div class="w-full h-full" bind:this={committedPipelineGraphContainer}>
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
	</TabItem>
</Tabs>

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

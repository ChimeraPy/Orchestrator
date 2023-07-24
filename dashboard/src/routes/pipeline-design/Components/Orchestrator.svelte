<script lang="ts">
	import { clusterClient } from '$lib/services';
	import { getStore } from '$lib/stores';
	import { Ok } from 'ts-monads';
	import { ToolViewType } from '$lib/Components/JointJS/utils';

	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import Alert from './Alert.svelte';
	import EditableDagViewer from '$lib/Components/JointJS/EditableDAGViewer.svelte';
	import type { IconType } from '$lib/Icons';
	import { Icons, getIconFromFSMActions } from '$lib/Icons';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';

	import { onMount } from 'svelte';

	let lifeCycleStore = getStore('lifeCycle');

	let icons: IconType[] = [];
	let editorContainer: HTMLDivElement;
	let pipelineGraph: any = null;
	let modal: Alert | null = null;
	let pipelineCells = [];

	onMount(async () => {
		const clusterActionsResult = await clusterClient.getActionsFSM();
		clusterActionsResultToIcons(clusterActionsResult);
		const observer = new ResizeObserver((entries) => {
			entries.forEach((entry) => {
				if (entry.target === editorContainer) {
					pipelineGraph?.resize();
				}
			});
		});

		observer.observe(editorContainer);
	});

	function clusterActionsResultToIcons(clusterActionsResult) {
		clusterActionsResult.map((fsm) => {
			const statesArray = Object.values(fsm.states);
			const currentState = statesArray.find((state) => state.name === fsm.current_state);
			const validTransitions = currentState.valid_transitions.map((transition) => transition.name);
			const actions = [];
			Object.values(fsm.states).forEach((state) => {
				state.valid_transitions.forEach((transition) => {
					if (!actions.includes(transition.name)) {
						actions.push(transition.name);
					}
				});
			});

			icons = actions
				.filter((action) => action !== '/instantiate')
				.map((action) => {
					return getIconFromFSMActions(
						action,
						fsm.active_pipeline_id === null || !validTransitions.includes(action)
					);
				})
				.concat({
					tooltip: 'Get Actions and States Info',
					type: Icons.info,
					disabled: false,
					fill: 'none',
					strokeWidth: 2
				});
		});
	}

	async function displayClusterStatesInfo() {
		(await clusterClient.getActionsFSM())
			.map((fsm) => {
				modal?.display({
					title: 'Cluster States Info',
					content: fsm
				});
			})
			.mapError((err) => {
				modal?.display({
					title: 'Error getting cluster states info',
					content: err
				});
			});
	}

	function renderChanges(pipeline, fsm) {
		if (pipeline) {
			pipelineCells = PipelineUtils.committablePipelineToJointCells(pipeline);
			pipelineCells = pipelineCells;
		} else {
			pipelineCells = [];
		}

		pipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
		pipelineGraph?.layout();
		if (fsm) {
			clusterActionsResultToIcons(new Ok(fsm));
		}
	}

	async function commitPipeline() {
		(await clusterClient.commitPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error committing pipeline',
				content: err
			});
		});
	}

	async function previewPipeline() {
		(await clusterClient.previewPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error previewing pipeline',
				content: err
			});
		});
	}

	async function recordPipeline() {
		(await clusterClient.recordPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error recording pipeline',
				content: err
			});
		});
	}

	async function stopPipeline() {
		(await clusterClient.stopPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error stopping pipeline',
				content: err
			});
		});
	}

	async function collectPipeline() {
		(await clusterClient.collectPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error stopping pipeline',
				content: err
			});
		});
	}

	async function resetPipeline() {
		(await clusterClient.resetPipeline()).mapError((err) => {
			modal?.display({
				title: 'Error resetting pipeline',
				content: err
			});
		});
	}

	$: renderChanges($lifeCycleStore?.pipeline, $lifeCycleStore?.fsm);
</script>

<div class="w-full h-full" bind:this={editorContainer}>
	<HorizontalMenu
		{icons}
		on:info={displayClusterStatesInfo}
		on:commit={commitPipeline}
		on:preview={previewPipeline}
		on:record={recordPipeline}
		on:stop={stopPipeline}
		on:reset={resetPipeline}
		on:collect={collectPipeline}
		title="Active Jobs"
	/>
	<div class="w-full h-full bg-[#F3F7F6]">
		<EditableDagViewer
			bind:this={pipelineGraph}
			editable={false}
			additionalLinkValidators={[]}
			toolViewAttachments={[ToolViewType.INFO]}
		/>
	</div>
</div>

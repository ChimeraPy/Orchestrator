<script lang="ts">
	import HorizontalMenu from '$lib/Components/JointJS/HorizontalMenu.svelte';
	import PluginInstaller from './PluginInstaller.svelte';
	import PartBrowser from '$lib/Components/JointJS/PartBrowser.svelte';
	import * as joint from 'jointjs';
	import { debounce } from '$lib/utils';
	import { PipelineUtils } from '$lib/Services/PipelineUtils';
	import { pipelineClient } from '$lib/services';
	import { Icons } from '$lib/Icons';
	import { onMount } from 'svelte';
	import { getStore } from '$lib/stores';
	import Alert from './Alert.svelte';
	import MarkdownViewer from '$lib/Components/MarkdownViewer/MarkdownViewer.svelte';
	import NodeCreator from "./NodeCreator.svelte";

	let pluginInstaller: PluginInstaller;
	let markdownViewer: MarkdownViewer;
	let nodeCreator: NodeCreator;
	let nodeCells: joint.dia.Cell[] = [];
	let modal: Alert | null = null;
	let selectedPipelineStore = getStore('selectedPipeline');

	onMount(() => {
		fetchPartBrowserNodes();
	});

	function showPluginInstaller() {
		pluginInstaller?.display();
	}

	async function fetchPartBrowserNodes(): Promise<joint.dia.Graph> {
		const result = await pipelineClient.getNodes();
		nodeCells = PipelineUtils.pipelineNodeResultToJointCells(result);
		nodeCells = nodeCells;
	}

	const debouncedFetchNodes = debounce(fetchPartBrowserNodes);

	async function addNodeToActivePipeline(cell: joint.dia.Cell) {
		if ($selectedPipelineStore?.pipeline) {
			const node = {
				name: cell.prop('registryName'),
				registry_name: cell.prop('registryName'),
				package: cell.prop('package'),
				id: cell.id
			};

			const result = await pipelineClient.addNodeTo($selectedPipelineStore.pipeline.id, node);
			(
				await result.mapAsync(async (_) => {
					const result = await pipelineClient.getPipeline($selectedPipelineStore.pipeline.id);
					result
						.map((pipeline) => {
							$selectedPipelineStore.pipeline = pipeline;
						})
						.mapError((err) => {
							modal?.display({
								title: 'Error',
								content: err
							});
						});
				})
			).mapError((error) => {
				modal?.display({
					title: 'Error',
					content: error
				});
			});
		} else {
			displayNoActivePipelineError();
		}
	}

	async function showNodeCreator(cell: joint.dia.Cell) {
		if (!$selectedPipelineStore?.pipeline) {
			displayNoActivePipelineError();
			return;
		}

		const registryName = cell.prop('registryName');
		const pkg = cell.prop('package');

		nodeCreator?.display(registryName, pkg);
	}

	async function showNodeInfo(cell: joint.dia.Cell) {
		const registryName = cell.prop('registryName');
		const pkg = cell.prop('package');
		const result = await pipelineClient.getNodeSourceCode(registryName, pkg);

		result.map((nodeSourceCode) => {
			let docs = nodeSourceCode.doc;
			if (docs) {
				docs = docs
					.replace(/^\s*/gm, '') // default indentation creates code blocks
					// Convert the arguments to a list
					.replace(/^Args:/gm, (match, arg) => '## Arguments\n')
					.replace(/^Parameters/gm, (match, arg) => '\n## Parameters\n')
					.replace(/^([a-zA-Z_]+):/gm, (match, argName) => `- \`${argName}\`:`)
					.replace(/^\*\*kwargs:?/gm, (match, kwarg) => '- `**kwargs`'); // replace **kwargs and args
			} else {
				docs = 'No documentation found.';
			}

			docs += ['\n## Source code', '```python', nodeSourceCode.source_code, '```'].join('\n');
			markdownViewer.display(docs, `${registryName}/${pkg}`);
		}).mapError(err => {
			modal?.display({
				title: 'Error Fetching Node Info',
				content: err
			});
		});
	}

	function displayNoActivePipelineError() {
		modal?.display({
			title: 'No active  pipeline',
			content: 'Please create or activate a pipeline to add nodes to it.'
		});
	}
</script>

<div class="w-full h-full">
	<div>
		<HorizontalMenu
			on:refresh={debouncedFetchNodes}
			on:add={() => showPluginInstaller()}
			title="Nodes"
			icons={[
				{
					type: Icons.refresh,
					tooltip: 'Refresh nodes',
					tooltipPlacement: 'bottom'
				},
				{
					type: Icons.add,
					tooltip: 'Plugins',
					tooltipPlacement: 'bottom'
				}
			]}
			backgroundClass="bg-blue-600"
		/>
	</div>
	<div class="bg-[#F3F7F6] w-full h-full">
		<PartBrowser
			on:cellClick={(event) => showNodeCreator(event.detail)}
			on:cellInfo={(event) => showNodeInfo(event.detail)}
			cells={nodeCells}
		/>
	</div>
</div>

<PluginInstaller bind:this={pluginInstaller} on:pluginInstalled={() => fetchPartBrowserNodes()} />
<Alert bind:this={modal} />
<MarkdownViewer bind:this={markdownViewer} />
<NodeCreator bind:this={nodeCreator}/>

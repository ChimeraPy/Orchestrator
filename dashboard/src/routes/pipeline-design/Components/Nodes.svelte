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

	let pluginInstaller: PluginInstaller;
	let nodeCells: joint.dia.Cell[] = [];

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

	async function addNodeToActivePipeline(node: joint.dia.Cell) {}
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
			on:cellClick={(event) => addNodeToActivePipeline(event.detail)}
			cells={nodeCells}
		/>
	</div>
</div>

<PluginInstaller bind:this={pluginInstaller} on:pluginInstalled={() => fetchPartBrowserNodes()} />

<!--
	This is the /pipline route page.
	The following customizations should be made incrementally.
	1. Search/Filter capabilities for Nodes and Components
	2. The `InfoModal` component should be used to later customize the pipelines and nodes attributes.
	3. The `EditableList` component should be used to later customize the pipelines and nodes attributes.
	4. Add zoom capabilities to the pipeline editor.
	5. Accessibility improvements.
-->
<script lang="ts">
	import 'svelte-golden-layout/css/themes/goldenlayout-light-theme.css';
	import GoldenLayout from 'svelte-golden-layout';
	import Nodes from './Components/Nodes.svelte';
	import Pipelines from './Components/Pipelines.svelte';
	import Designer from './Components/Designer.svelte';
	import Network from './Components/Network.svelte';
	import Orchestrator from './Components/Orchestrator.svelte';
	import NodeAttributes from './Components/NodeAttributes.svelte';

	let components = {
		Nodes,
		Pipelines,
		Designer,
		Network,
		Orchestrator,
		NodeAttributes
	};

	const layout = {
		settings: {
			hasHeaders: true,
			constrainDragToContainer: false,
			popoutWholeStack: false,
			showPopoutIcon: false
		},
		dimensions: {
			headerHeight: 20
		},
		root: {
			type: 'column',
			content: [
				{
					type: 'row',
					content: [
						{
							type: 'component',
							width: 15,
							componentName: '',
							componentType: 'Nodes',
							componentState: {}
						},
						{
							width: 70,
							type: 'component',
							componentName: '',
							componentType: 'Designer',
							componentState: {}
						},
						{
							width: 15,
							type: 'component',
							componentName: '',
							componentType: 'Pipelines',
							componentState: {}
						}
					]
				},
				{
					type: 'row',
					content: [
						{
							type: 'component',
							width: 15,
							componentName: '',
							componentType: 'Network',
							componentState: {}
						},
						{
							width: 70,
							type: 'component',
							componentName: '',
							componentType: 'Orchestrator',
							componentState: {}
						},
						{
							width: 15,
							type: 'component',
							componentName: '',
							componentType: 'NodeAttributes',
							componentState: {}
						}
					]
				}
			]
		}
	};
</script>

<div class="h-full flex flex-col px-5">
	<GoldenLayout config={layout} let:componentType let:componentState>
		<svelte:component this={components[componentType]} {...componentState} />
	</GoldenLayout>
</div>

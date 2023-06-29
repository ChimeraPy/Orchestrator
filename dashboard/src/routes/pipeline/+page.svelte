<!--
	This is the /pipline route page.
	The following customizations should be made incrementally.
	1. Search/Filter capabilities for Nodes and Pipelines
	2. The `InfoModal` component should be used to later customize the pipelines and nodes attributes.
	3. The `EditableList` component should be used to later customize the pipelines and nodes attributes.
	4. Add zoom capabilities to the pipeline editor.
	5. Accessibility improvements.
-->
<script lang="ts">
	import PipelineDesigner from './PipelineDesigner.svelte';
	import Orchestrator from './Orchestrator.svelte';
</script>

<div class="h-full flex flex-col">
	<div class="h-1/2">
		<PipelineDesigner />
	</div>
	<div class="h-1/2">
		<Orchestrator />
	</div>
</div>

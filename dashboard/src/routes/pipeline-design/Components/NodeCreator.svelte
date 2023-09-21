<script lang="ts">
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { pipelineClient } from '$lib/services';
	import { getStore } from '$lib/stores';
	import { JSONEditor } from 'svelte-jsoneditor';
	import { Label, Select } from 'flowbite-svelte';
	import {NodeKwargsValidator} from './NodeKwargsValidator';

	let modalOpen = null;
	let disableConfirm = true;
	let selectedNode = {};
    let nodeAttributes = {};
	let nodeName = null;
	let selectedWorkerId = null;
	let nodeCreationError = null;
	const networkStore = getStore('network');
	const selectedPipelineStore = getStore('selectedPipeline');
	const validator: NodeKwargsValidator = new NodeKwargsValidator(null);


	export async function display(registryName, pkg) {

		(await pipelineClient.getNodes())
			.map((nodes) => {
				const nodeDetails = nodes.find((node) => {
					return node.registry_name === registryName && node.package === pkg;
				});
				if (nodeDetails) {
					selectedNode = nodeDetails;
                    disableConfirm = false;
					modalOpen = true;
					nodeName = nodeDetails.registry_name;
					nodeAttributes = {
						json: nodeDetails.kwargs
					};
					validator.setKwargs(nodeDetails.kwargs);
				} else {
					disableConfirm = true;
					modalOpen = true;
					nodeCreationError = `Node ${registryName} not found`;
				}
			})
			.mapError((err) => {
				disableConfirm = true;
				modalOpen = true;
				nodeCreationError = err;
			});
	}

	export async function addNodeToExistingPipeline(kwargs, workerId) {
        Object.assign(selectedNode, { kwargs, worker_id: workerId });
		console.log('Adding node to pipeline', selectedNode);

        (await pipelineClient.addNodeTo($selectedPipelineStore.pipeline.id, selectedNode))
            .mapAsync(async (_) => {
                (await pipelineClient.getPipeline($selectedPipelineStore.pipeline.id)).map((pipeline) => {
					$selectedPipelineStore.pipeline = pipeline;
				});
				hide();
            })
            .mapError((err) => {
                nodeCreationError = err;
            });
	}

	function hide() {
		modalOpen = false;
		disableConfirm = true;
		nodeCreationError = null;
		selectedNode = {
			json: {}
		};
        selectedWorkerId = null;
	}

	function getWorkerItems(networkDetails) {
		const workers = Object.values(networkDetails?.workers || {})
			.map((w) => ({ value: w.id, name: w.name }))
			.concat([{ value: null, name: 'Select a worker' }]);

		return workers;
	}

	function validate(json) {
		const errors = validator.validate(json)
		disableConfirm = errors.length > 0;
		return errors;
	}

</script>

<!-- Alert Modal -->
<Modal
	type="confirm"
	title="Add Node to Pipeline"
	bind:modalOpen
	autoclose={true}
	confirmMessage="Add to Pipeline"
	cancelMessage="Cancel"
	size="xl"
	{disableConfirm}
	on:confirm={() => addNodeToExistingPipeline(JSON.parse(nodeAttributes.text), selectedWorkerId)}
	on:cancel={hide}
>
	<div slot="content" class="w-96">
		{#if nodeCreationError}
			<div class="mb-4">
				<code class="text-sm text-red-500">
					{JSON.stringify(nodeCreationError, null, 2)}
				</code>
			</div>
		{:else}
			<div class="mb-4">
				<p class="text-sm text-gray-500">
					Customize Arguments for <code>{nodeName}</code>
				</p>
			</div>
			<div class="h-96 w-96 flex items-center mb-5">
				<JSONEditor
					mode="text"
					validator="{validate}"
					bind:content={nodeAttributes}
					mainMenuBar={false}
					navigationBar={true}
				/>
			</div>
			<div class="p-2">
				<Label>Select a worker</Label>
				<Select mt-2 items={getWorkerItems($networkStore)} bind:value={selectedWorkerId} />
			</div>
		{/if}
	</div>
</Modal>

<script lang="ts">
	import Modal from '$lib/Components/Modal/Modal.svelte';
	import { pipelineClient } from '$lib/services';
	import {
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Spinner
	} from 'flowbite-svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	let modalOpen = false;

	let pluginsFetchPromise;
	let installingPluginNames = [];
	let installedPluginNames = [];
	let installationErrors = null;

	export function display() {
		modalOpen = true;
		pluginsFetchPromise = fetchPlugins();
	}

	export function hide() {
		modalOpen = false;
		pluginsFetchPromise = null;
		installingPluginNames = [];
	}

	async function fetchPlugins() {
		installingPluginNames = [];
		return (await pipelineClient.getPlugins()).unwrap();
	}

	async function installPlugin(pluginName: string) {
		if (installedPluginNames.includes(pluginName)) {
			return;
		}

		installingPluginNames.push(pluginName);
		installingPluginNames = installingPluginNames;
		(await pipelineClient.installPlugin(pluginName))
			.map((nodes) => {
				dispatch('pluginInstalled', { nodes });
				installedPluginNames.push(pluginName);
				installedPluginNames = installedPluginNames;
			})
			.mapError((error) => {
				installationErrors[pluginName] = error;
			});

		installingPluginNames = installingPluginNames.filter((name) => name !== pluginName);
	}
</script>

<Modal
	type="alert"
	title="Plugin Installer"
	alertMessage="Close"
	autoclose={false}
	disableConfirm={false}
	bind:modalOpen
	on:alert={hide}
	on:close={hide}
>
	<div slot="content">
		<h3 class="h3 text-xl">Available Plugins</h3>
		{#await pluginsFetchPromise}
			<p>Loading plugins...</p>
		{:then plugins}
			<Table striped={true}>
				<TableHead>
					<TableHeadCell>Package</TableHeadCell>
					<TableHeadCell>Name</TableHeadCell>
					<TableHeadCell>Description</TableHeadCell>
					<TableHeadCell>Version</TableHeadCell>
					<TableHeadCell>Nodes</TableHeadCell>
					<TableHeadCell>Install</TableHeadCell>
				</TableHead>
				<TableBody>
					{#if plugins.length === 0}
						<TableBodyRow>
							<TableBodyCell colspan="6">No plugins available</TableBodyCell>
						</TableBodyRow>
					{:else}
						{#each plugins as plugin}
							<TableBodyRow>
								<TableBodyCell>{plugin.package}</TableBodyCell>
								<TableBodyCell>{plugin.name}</TableBodyCell>
								<TableBodyCell>{plugin.description}</TableBodyCell>
								<TableBodyCell>{plugin.version}</TableBodyCell>
								<TableBodyCell>{plugin.nodes.join(', ')}</TableBodyCell>
								<TableBodyCell>
									{#if installingPluginNames.includes(plugin.name)}
										<Spinner color="green" />
									{/if}
									<span
										role="button"
										disabled={installedPluginNames.includes(plugin.name)}
										class="underline text-blue-500"
										on:click|stopPropagation|preventDefault={() => installPlugin(plugin.name)}
									>
										{installingPluginNames.includes(plugin.name)
											? 'Installing...'
											: installedPluginNames.includes(plugin.name)
											? 'Installed'
											: 'Install'}
									</span>
								</TableBodyCell>
							</TableBodyRow>
						{/each}
					{/if}
				</TableBody>
			</Table>
			{#if installationErrors}
				<p>Failed to install plugins:</p>
				<pre class="text-red-900">
                    {JSON.stringify(installationErrors, null, 2)}
                </pre>
			{/if}
		{:catch error}
			<p>Failed to fetch plugins</p>
		{/await}
	</div>
</Modal>

<script lang="ts">
	export let title: string = 'Menu';
	export let backgroundClass: string = 'bg-green-800';
	export let refreshBtn = false;
	export let addBtn = false;
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();

	function dispatchRefreshEvent() {
		dispatch('refresh');
	}

	function dispathAddEvent() {
		dispatch('add');
	}
</script>

<div class="p-2 h-10 w-full {backgroundClass} text-white">
	<div class="flex flex-row justify-between">
		<h2>{title}</h2>
		<div clas="flex flex-row">
			{#if refreshBtn}
				<span
					role="button"
					class="hover:text-green-900 mr-2"
					on:click|preventDefault|stopPropagation={dispatchRefreshEvent}>&#10227;</span
				>
			{/if}
			{#if addBtn}
				<span
					role="button"
					class="hover:text-green-900"
					on:click|preventDefault|stopPropagation={dispathAddEvent}>+</span
				>
			{/if}
		</div>
	</div>
</div>

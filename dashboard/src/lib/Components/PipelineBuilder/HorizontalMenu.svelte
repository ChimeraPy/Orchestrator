<script lang="ts">
	import { getIconPath } from '$lib/Icons';
	import type { Icons } from '$lib/Icons';
	import { Tooltip } from 'flowbite-svelte';

	import { createEventDispatcher } from 'svelte';

	export let icons: { type: Icons; tooltip?: string; disabled?: boolean }[] = [];
	export let title: string = 'Menu';
	export let backgroundClass: string = 'bg-green-800';

	const dispatch = createEventDispatcher();

	function dispatchEvent(event: string) {
		dispatch(event);
	}
</script>

<div class="p-2 h-10 w-full {backgroundClass} text-white">
	<div class="flex flex-row justify-between">
		<h2>{title}</h2>
		<div class="flex flex-row">
			{#each icons as icon, index}
				<span
					role="button"
					class="mr-{index === icons.length - 1 ? 0 : 2}
						   hover:text-gray-900
						   text-xl
						   {icon.disabled ? 'pointer-events-none' : 'pointer-events-auto'}
						   {icon.disabled ? 'opacity-50' : 'opacity-100'}"
					on:click={() => dispatchEvent(icon.type)}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-6 h-6"
					>
						<path d={getIconPath(icon.type)} />
					</svg>
					{#if icon.tooltip}
						<Tooltip style={'dark'}>
							{icon.tooltip}
						</Tooltip>
					{/if}
				</span>
			{/each}
		</div>
	</div>
</div>

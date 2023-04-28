<script lang="ts">
	import { getIconPath } from '$lib/Icons';
	import type { IconType } from '$lib/Icons';
	import { Tooltip } from 'flowbite-svelte';

	import { createEventDispatcher } from 'svelte';
	import {Icons} from "$lib/Icons";

	export let icons: IconType[] = [];
	export let title: string = 'Menu';
	export let backgroundClass: string = 'bg-green-800';

	const dispatch = createEventDispatcher();

	function dispatchEvent(event: string) {
		dispatch(event);
	}

	function getPaths(iconType: Icons) {
		const paths = getIconPath(iconType);
		return Array.isArray(paths) ? paths : [paths];
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
					on:click={() => dispatchEvent(icon.dispatchEventName || icon.type)}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="{icon.fill || 'currentColor'}"
						stroke="currentColor"
						class="w-6 h-6"
						stroke-width="{icon.strokeWidth || 0.5}"
					>
						{#each getPaths(icon.type) as iconPath}
							<path stroke-linecap="round"
								  stroke-linejoin="round"
							d={iconPath} />
						{/each}
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

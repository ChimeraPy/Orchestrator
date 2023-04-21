<script lang="ts">
	import { Listgroup, ListgroupItem, Button } from 'flowbite-svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let items: { id: string; text: string; active: boolean }[] = [];
	export let emptyMessage = 'No items';
	export let editable = true;
</script>

<div
	class="relative
			h-full
			w-full
			scrollbar-thin
            scrollbar-thumb-gray-700
            scrollbar-track-gray-100
            overflow-y-scroll"
>
	<Listgroup>
		{#if items.length === 0}
			<ListgroupItem class="py-3">
				<span>{emptyMessage}</span>
			</ListgroupItem>
		{/if}
		{#each items as item}
			<ListgroupItem class={item.active ? 'bg-teal-100' : ''}>
				<div class="flex flex-row justify-between py-3 text-lg">
					<div
						class="flex-1"
						role="button"
						on:click={() => {
							dispatch('click', item);
						}}
					>
						{item.text}
					</div>
					<div>
						<span
							role="button"
							on:click={() => {
								dispatch('info', item);
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-6 h-6"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
								/>
							</svg>
						</span>
					</div>
					{#if editable}
						<div>
							<span
								role="button"
								on:click={() => {
									dispatch('delete', item);
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-6 h-6"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/>
								</svg>
							</span>
						</div>
					{/if}
				</div>
			</ListgroupItem>
		{/each}
	</Listgroup>
</div>

<script lang="ts">
	import * as showdown from 'showdown/dist/showdown.min';
	import Modal from '../Modal/Modal.svelte';
	const classMap = {
		h1: 'text-2xl',
		h2: 'text-lg mt-4',
		ul: 'list-disc list-inside',
		li: 'p-2',
		code: `bg-gray-200 text-red-500 p-1 font-mono`,
		// Scrolling behavior in flowbyte-svelte is not working properly
		// https://github.com/themesberg/flowbite-svelte/pull/637/files
		pre: `bg-gray-200 text-red-500 p-1 max-h-96 overflow-scroll font-mono scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-100 line-numbers`
	};
	const bindings = Object.keys(classMap).map((key) => ({
		type: 'output',
		regex: new RegExp(`<${key}(.*)>`, 'g'),
		replace: `<${key} class="${classMap[key]}" $1>`
	}));

	const mdConverter = new showdown.Converter({
		extensions: [...bindings]
	});
	let markdownHtml: string | null = null,
		markdownTitle: string = '';
	export let modalOpen = false;
	export function display(md: string, title: string) {
		markdownHtml = mdConverter.makeHtml(md);
		markdownTitle = title;
		modalOpen = true;
	}
	export function hide() {
		markdownHtml = null;
		markdownTitle = '';
		modalOpen = false;
	}
</script>

<Modal
	type="alert"
	title={markdownTitle || 'Nodes Help'}
	alertMessage="Close"
	autoclose={false}
	disableConfirm={false}
	bind:modalOpen
	on:alert={hide}
	on:close={hide}
>
	<div slot="content">
		{#if markdownHtml}
			{@html markdownHtml}
		{/if}
	</div>
</Modal>

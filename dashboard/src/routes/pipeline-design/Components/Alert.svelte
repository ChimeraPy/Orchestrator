<script lang="ts">
	import Modal from '$lib/Components/Modal/Modal.svelte';

	let infoModalContent: { title: string; content: any } | null = null;

	export function display(info: { title: string; content: any }) {
		infoModalContent = {
			title: info.title,
			content: info.content
		};
	}

	export function hide() {
		infoModalContent = null;
	}
</script>

<!-- Alert Modal -->
<Modal
	type="alert"
	title={infoModalContent?.title}
	bind:modalOpen={infoModalContent}
	autoclose={true}
	alertMessage="Close"
	on:cancel={() => (infoModalContent = null)}
	on:alert={() => (infoModalContent = null)}
>
	<div slot="content">
		<h3 class="text-xl font-medium text-green-900 p-2">{infoModalContent.title}</h3>
		<pre>{JSON.stringify(infoModalContent.content, null, 2)}</pre>
	</div>
</Modal>

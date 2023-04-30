<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Modal, Button } from 'flowbite-svelte';

	export let type: 'alert' | 'confirm' = 'confirm';
	export let autoclose = true;
	export let disableConfirm = true;
	export let confirmMessage: string = 'All Good!';
	export let cancelMessage: string = 'Nyae!';
	export let alertMessage: string = 'Understood!';
	export let title: string = 'A Modal';
	export let modalOpen = false;

	export let size = 'md';

	const dispatch = createEventDispatcher();

	function confirm() {
		dispatch('confirm');
	}

	function cancel() {
		dispatch('cancel');
	}

	function alert() {
		dispatch('alert');
	}
</script>

<Modal {title} bind:open={modalOpen} {size} {autoclose} on:hide={cancel}>
	<slot name="content">
		<em>Such Emtpy Here!</em>
	</slot>

	<svelte:fragment slot="footer">
		{#if type === 'confirm'}
			{#if disableConfirm}
				<Button disabled on:click={confirm}>{confirmMessage}</Button>
			{:else}
				<Button on:click={confirm}>{confirmMessage}</Button>
			{/if}
			<Button on:click={cancel} color="alternative">{cancelMessage}</Button>
		{:else}
			<Button on:click={alert}>{alertMessage}</Button>
		{/if}
	</svelte:fragment>
</Modal>

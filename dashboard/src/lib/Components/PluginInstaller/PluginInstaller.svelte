<script lang="ts">
    import Modal from '$lib/Components/Modal/Modal.svelte';
    import { pipelineClient } from '$lib/services';

    let modalOpen = false;

    export function display() {
        modalOpen = true;
    }

    export function hideModal() {
        modalOpen = false;
    }
</script>

<Modal
    type="alert"
    title="Plugin Installer"
    alertMessage="Close"
    autoclose="{false}"
    disableConfirm="{false}"
    bind:modalOpen
    on:alert="{hideModal}"
>
    <div slot="content">
        <h3 class="h3 text-xl">Available Plugins</h3>
    </div>

</Modal>

<script lang="ts">
    import Modal from '../Modal/Modal.svelte';
    import type { Pipeline } from '$lib/models';
    import { pipelineClient } from '$lib/services';
    import { getStore } from '$lib/stores';

    const networkStore = getStore('network');
    export let committablePipeline: Pipeline | null = null;

    enum PipelineCommitStatus {
        COMMITTING = 'COMMITTING',
        COMMITTED = 'COMMITTED',
        FAILED = 'FAILED',
        IDLE = 'IDLE',
    }

    let commitStatus: PipelineCommitStatus = PipelineCommitStatus.IDLE;




</script>

<Modal
	type="confirm"
	title="{`Commit Pipeline ${committablePipeline?.name}?`}"
	bind:modalOpen={committablePipeline}
	autoclose={false}
    confirmMessage="Commit"
    cancelMessage="Cancel"
    disableConfirm="{commitStatus !== PipelineCommitStatus.IDLE}"
	on:confirm={() => {}}
	on:cancel={() => committablePipeline = null}
>
    <div slot="content">
		<h3 class="text-xl font-medium text-green-900 p-2">{committablePipeline?.name}</h3>
        <hr/>
        <br/>
        {#if commitStatus === PipelineCommitStatus.IDLE}
    		<pre>{JSON.stringify(committablePipeline, null, 2)}</pre>
        {:else }
        {/if}

    </div>

</Modal>

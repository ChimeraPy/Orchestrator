<script lang="ts">
    import {clusterClient} from '$lib/services';
    import Modal from '$lib/Components/Modal/Modal.svelte';
    import {ToolViewType} from '$lib/Components/PipelineBuilder/utils';
    import {Icons, getIconFromFSMActions} from '$lib/Icons';
    import type {IconType} from "$lib/Icons";
    import HorizontalMenu from '$lib/Components/PipelineBuilder/HorizontalMenu.svelte';

    import EditableDagViewer from '$lib/Components/PipelineBuilder/EditableDAGViewer.svelte';
    import {onMount, createEventDispatcher} from 'svelte';

    import {getStore} from '$lib/stores';
    import {PipelineUtils} from '../../Services/PipelineUtils';

    export let committablePipeline;
    let committedPipelineGraph, committedPipelineGraphContainer;
    export let infoModalContent: {
        title: string;
        content: any;
        alertMessage?: string;
    } | null = null;
    let pipelineCells = [];
    let icons: IconType[] = [];

    const pipelineStore = getStore('committedPipeline');
    const dispatch = createEventDispatcher();

    onMount(async () => {
        const clusterActionsResult = await clusterClient.getActionsFSM();
        clusterActionsResult.map((fsm) => {
            const statesArray = Object.values(fsm.states);
            const currentState = statesArray.find(state => state.name === fsm.current_state);
            const validTransitions = currentState.valid_transitions.map(transition => transition.name);
            const actions = [];
            Object.values(fsm.states).forEach((state) => {
                state.valid_transitions.forEach((transition) => {
                    if(! actions.includes(transition.name)) {
                        actions.push(transition.name);
                    }
                });
            });
            icons = actions.map(action => {
                return getIconFromFSMActions(action, !validTransitions.includes(action));
            }).concat({
                tooltip: 'Get Actions and States Info',
                type: Icons.info,
                disabled: false,
                fill: 'none',
                strokeWidth: 2,
            });
        });
    });

    export async function onConfirmCommit() {
        if (!committablePipeline) {
            return;
        }
        const responseResult = await clusterClient.commitPipeline(committablePipeline?.id);
        responseResult
            .map((pipeline) => {
                infoModalContent = {
                    title: 'SUCCESS',
                    content: pipeline,
                    alertMessage: 'Close'
                };
            })
            .mapError((error) => {
                infoModalContent = {
                    title: `Cannot commit pipeline ${committablePipeline?.name}`,
                    content: error,
                    alertMessage: 'Close'
                };
            });
        committablePipeline = null;
    }


    $: committablePipeline && onConfirmCommit();

    $: {
        pipelineCells = $pipelineStore
            ? PipelineUtils.committablePipelineToJointCells($pipelineStore)
            : [];
        pipelineCells = pipelineCells;
        committedPipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
        committedPipelineGraph?.layout();
    }

    function beginPipelineExecution() {
        if (!committablePipeline) {
            return;
        }
        // clusterClient.beginPipelineExecution(committablePipeline?.id);
    }

    async function clusterInfo() {
        (await clusterClient.getActionsFSM()).map(fsm => {
            infoModalContent = {
                title: 'Cluster Actions and States',
                content: fsm,
                alertMessage: 'Close'
            };
        })
    }

    async function activatePipeline() {
        dispatch('activatePipeline');
    }

    async function nodeInfoEvent() {
        console.log('nodeInfoEvent');
    }

    export function resize() {
        committedPipelineGraph?.resize();
    }
</script>

<div>
    <HorizontalMenu
            title="Orchestration"
            {icons}
            on:play={beginPipelineExecution}
            on:info={clusterInfo}
            on:activate={activatePipeline}
    />
</div>
<div class="flex-1 flex justify-center items-center bg-[#F3F7F6] overflow-hidden">
    <EditableDagViewer
            editable={false}
            bind:this={committedPipelineGraph}
            additionalLinkValidators={[]}
            toolViewAttachments={[ToolViewType.INFO]}
            on:nodeInfo={nodeInfoEvent}
    />
</div>

<!-- Info Modal -->
<Modal
        type="alert"
        title={infoModalContent?.title}
        bind:modalOpen={infoModalContent}
        autoclose={true}
        alertMessage={infoModalContent?.alertMessage || 'Close'}
        on:cancel={() => (infoModalContent = null)}
        on:alert={() => (infoModalContent = null)}
>
    <div slot="content">
        <h3 class="text-xl font-medium text-green-900 p-2">{infoModalContent.title}</h3>
        <pre>{JSON.stringify(infoModalContent.content, null, 2)}</pre>
    </div>
</Modal>

<style lang="postcss">
    .apply-width {
        /*width: 100%;*/
    }
</style>

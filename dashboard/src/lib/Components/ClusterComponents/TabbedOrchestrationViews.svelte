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
    import {Ok} from 'ts-monads';
    import * as fs from "fs";

    export let committablePipeline;
    let committedPipelineGraph;
    export let infoModalContent: {
        title: string;
        content: any;
        alertMessage?: string;
    } | null = null;
    let pipelineCells = [];
    let icons: IconType[] = [];

    const lifeCycleStore = getStore('lifeCycle');
    const dispatch = createEventDispatcher();

    function clusterActionsResultToIcons(clusterActionsResult) {
        clusterActionsResult.map((fsm) => {
            const statesArray = Object.values(fsm.states);
            const currentState = statesArray.find(state => state.name === fsm.current_state);
            const validTransitions = currentState.valid_transitions.map(transition => transition.name);
            const actions = [];
            Object.values(fsm.states).forEach((state) => {
                state.valid_transitions.forEach((transition) => {
                    if (!actions.includes(transition.name)) {
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
    }

    onMount(async () => {
        const clusterActionsResult = await clusterClient.getActionsFSM();
        clusterActionsResultToIcons(clusterActionsResult);
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

    function renderChanges(pipeline, fsm) {
        if (pipeline) {
            pipelineCells = PipelineUtils.committablePipelineToJointCells(pipeline);
            pipelineCells = pipelineCells;
        } else {
            pipelineCells = [];
        }

        committedPipelineGraph?.render(pipelineCells, pipelineCells.length === 0);
        committedPipelineGraph?.layout();

        if (fsm) {
            clusterActionsResultToIcons(new Ok(fsm));
            if(fsm.current_state === "PREVIEWING") {
                committedPipelineGraph?.animateLinks('#FFDF00');
            } else if (fsm.current_state === "RECORDING") {
                committedPipelineGraph?.animateLinks('#0000FF');
            } else {
                committedPipelineGraph?.stopLinksAnimation();
            }
        }
    }


    $: committablePipeline && onConfirmCommit();

    $: renderChanges($lifeCycleStore?.pipeline, $lifeCycleStore?.fsm);

    $: console.log($lifeCycleStore);

    async function clusterInfo() {
        (await clusterClient.getActionsFSM()).map(fsm => {
            infoModalContent = {
                title: 'Cluster Actions and States',
                content: fsm,
                alertMessage: 'Close'
            };
        })
    }

    async function commitPipeline() {
        (await clusterClient.commitPipeline()).map(pipeline => {
            infoModalContent = {
                title: 'COMMITTING PIPELINE',
                content: pipeline,
                alertMessage: 'Close'
            };
        }).mapError(error => {
            infoModalContent = {
                title: 'ERROR',
                content: error,
                alertMessage: 'Close'
            };
        })
    }

    async function previewPipeline() {
        (await clusterClient.previewPipeline()).map(pipeline => {
            infoModalContent = {
                title: 'PREVIEWING PIPELINE',
                content: pipeline,
                alertMessage: 'Close'
            };
        }).mapError(error => {
            infoModalContent = {
                title: 'ERROR',
                content: error,
                alertMessage: 'Close'
            };
        })
    }

    async function recordPipeline() {
        (await clusterClient.recordPipeline()).map(pipeline => {
            infoModalContent = {
                title: 'RECORDING PIPELINE',
                content: pipeline,
                alertMessage: 'Close'
            };
        }).mapError(error => {
            infoModalContent = {
                title: 'ERROR',
                content: error,
                alertMessage: 'Close'
            };
        })
    }

    async function stopPipeline() {
        (await clusterClient.stopPipeline()).map(pipeline => {
            infoModalContent = {
                title: 'STOPPING PIPELINE',
                content: pipeline,
                alertMessage: 'Close'
            };
        }).mapError(error => {
            infoModalContent = {
                title: 'ERROR',
                content: error,
                alertMessage: 'Close'
            };
        });
    }

    async function resetPipeline() {
        (await clusterClient.resetPipeline()).map(pipeline => {
            infoModalContent = {
                title: 'RESETTING PIPELINE',
                content: pipeline,
                alertMessage: 'Close'
            };
        }).mapError(error => {
            infoModalContent = {
                title: 'ERROR',
                content: error,
                alertMessage: 'Close'
            };
        });
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
            on:info={clusterInfo}
            on:activate={activatePipeline}
            on:commit={commitPipeline}
            on:preview={previewPipeline}
            on:record={recordPipeline}
            on:stop={stopPipeline}
            on:reset={resetPipeline}
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

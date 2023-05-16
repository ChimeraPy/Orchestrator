<script lang="ts">
    import type {Attribute} from '$lib/models';
    import Input from './Input.svelte';
    import Bool from './Bool.svelte';

    export let selectedObject: {id: string, type: string, attributes: Attribute[]};


    function getComponent(attribute: Attribute) {
        if (attribute.type_info.type === 'Boolean') {
            return Bool;
        }
        return Input;
    }
</script>
{#if selectedObject}
<div
	class="relative
			h-full
			w-full
			scrollbar-thin
            scrollbar-thumb-gray-700
            scrollbar-track-gray-100
            overflow-y-scroll"
>
    {#each Object.entries(selectedObject.attributes) as [name, attribute], index}
        <svelte:component this={getComponent(attribute)} {attribute} {name} />
        <div class="border-t-2 border-gray-900"></div>
    {/each}
</div>
{/if}

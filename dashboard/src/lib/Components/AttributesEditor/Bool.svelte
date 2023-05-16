<script lang="ts">
    import type {Attribute} from "$lib/models";
    import {Select, Label} from 'flowbite-svelte';

    export let attribute: Attribute;
    let values = [
        {value: true, name: "True"},
        {value: false, name: "False"}
    ]
</script>

<div class="flex bg-indigo-50">
    <div class="pl-2 pt-2 w-2/5 h-10">
          <Label for="{attribute.name}">{attribute.name}:</Label>
    </div>
    <div class="pl-2 w-3/5 h-10">
      <Select class="h-10 text-sm" bind:value={attribute.value} type="text" items={values} required />
    </div>
</div>

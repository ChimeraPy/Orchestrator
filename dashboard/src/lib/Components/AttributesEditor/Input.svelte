<script lang="ts">
    import type {Attribute} from "$lib/models";
    import {Input, Label} from 'flowbite-svelte';

    export let attribute: Attribute;
</script>

<div class="flex bg-indigo-50">
    <div class="p-4 w-2/5">
          <Label for="{attribute.name}">{attribute.name}:</Label>
    </div>
    <div class="p-2">
      <Input bind:value={attribute.value} type="text" id="{attribute.name}" placeholder="{attribute.name}" required />
    </div>
</div>

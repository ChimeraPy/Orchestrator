<script lang="ts">
    import type {Attribute} from "$lib/models";
    import {Input, Label} from 'flowbite-svelte';

    export let attribute: Attribute;
</script>

<div class="flex bg-indigo-50">
    <div class="pl-2 pt-2 w-2/5">
          <Label for="{attribute.name}">{attribute.name}:</Label>
    </div>
    <div class="pl-2 w-3/5">
      <Input bind:value={attribute.value} type="text" id="{attribute.name}" placeholder="{attribute.name}" required />
    </div>
</div>

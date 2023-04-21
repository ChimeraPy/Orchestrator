<script>
  import { Tabs, TabItem } from 'flowbite-svelte';

  import {getIconPath, Icons} from '$lib/Icons';
</script>

<Tabs style="underline">
  <TabItem open>
    <div slot="title" class="flex items-center gap-2">
      <svg aria-hidden="true" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fill-rule="evenodd" d="{getIconPath(Icons.bolt)}" clip-rule="evenodd" /></svg>
      Committed Pipeline
    </div>
  </TabItem>
  <TabItem>
    <div slot="title" class="flex items-center gap-2">
      <svg aria-hidden="true" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fill-rule="evenodd" d="{getIconPath(Icons.computer)}" clip-rule="evenodd" /></svg>Cluster State
    </div>
    <p class="text-sm text-gray-500 dark:text-gray-400"><b>Contacts:</b> Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
  </TabItem>
</Tabs>

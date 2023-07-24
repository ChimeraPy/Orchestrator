<script lang="ts">
	import '../app.postcss';
	import Header from '$lib/Components/Header/Header.svelte';
	import Footer from '$lib/Components/Footer/Footer.svelte';
	import { dev } from '$app/environment';
	export let data;
</script>

<div class="mx-auto flex flex-col h-screen">
	<Header sections={data.sections} logo={data.logo} url={dev ? '/' : '/dashboard'} />
	<main class="mb-auto h-[calc(100vh-5rem)]">
		<slot />
	</main>
	<Footer copyrightHolder={data.copyrightHolder} copyrightHolderURL={data.copyrightHolderURL} />
</div>

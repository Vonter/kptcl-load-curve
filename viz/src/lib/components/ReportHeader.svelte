<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		actions
	}: {
		title: string;
		actions?: Snippet;
	} = $props();
</script>

<section class="report-heading">
	<div class="heading-copy">
		<h1>{title}</h1>
	</div>
	{#if actions}
		<div class="actions">{@render actions()}</div>
	{/if}
</section>

<style>
	.report-heading {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 28px;
		margin-bottom: 0;
	}

	.heading-copy {
		min-width: 0;
	}

	h1 {
		margin: 0;
		font-family: var(--font-display);
		font-size: clamp(2.4rem, 5vw, 4.7rem);
		font-weight: 720;
		letter-spacing: -0.055em;
		line-height: 0.96;
		color: var(--ink);
	}

	.actions {
		min-width: 0;
		flex: 0 1 auto;
	}

	@media (max-width: 620px) {
		.report-heading {
			align-items: stretch;
			flex-direction: column;
			gap: 16px;
		}

		h1 {
			font-size: 2.55rem;
		}
	}
</style>

<script lang="ts">
	import { page } from '$app/state';

	const SITE_URL = 'https://kptcl-load-curve.pages.dev';
	const SITE_NAME = 'KPTCL Load Curve';
	const DEFAULT_TITLE = 'KPTCL Load Curve';
	const DEFAULT_DESCRIPTION =
		"Visualize Karnataka's electricity demand, generation, reservoir levels, outages, " +
		'over multiple years of KPTCL load curve reports.';
	const DEFAULT_KEYWORDS =
		'KPTCL load curve,Karnataka electricity demand,Karnataka power generation,' +
		'Karnataka grid frequency,reservoir levels,power outages,electricity data,' +
		'Karnataka power transmission,KPTCL reports';
	const AUTHOR = 'Vivek Matthew';
	const DEFAULT_IMAGE = `${SITE_URL}/sharecard.jpg`;
	const DEFAULT_IMAGE_ALT = 'KPTCL Load Curve dashboard showing annual power demand and frequency';

	interface Props {
		title?: string;
		description?: string;
		keywords?: string;
		image?: string;
		imageAlt?: string;
	}

	let {
		title,
		description = DEFAULT_DESCRIPTION,
		keywords = DEFAULT_KEYWORDS,
		image = DEFAULT_IMAGE,
		imageAlt = DEFAULT_IMAGE_ALT
	}: Props = $props();

	const fullTitle = $derived(title ? `${title} - ${SITE_NAME}` : DEFAULT_TITLE);
	const canonical = $derived(`${SITE_URL}${page.url.pathname}`);
	const twitterCard = $derived(image ? 'summary_large_image' : 'summary');
</script>

<svelte:head>
	<!-- Basic -->
	<title>{fullTitle}</title>
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta name="author" content={AUTHOR} />
	<meta name="robots" content="index, follow" />

	<!-- Canonical URL -->
	<link rel="canonical" href={canonical} />

	<!-- Open Graph -->
	<meta property="og:title" content={fullTitle} />
	<meta property="og:site_name" content={SITE_NAME} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content={canonical} />
	<meta property="og:type" content="website" />
	<meta property="og:locale" content="en_IN" />
	{#if image}
		<meta property="og:image" content={image} />
		<meta property="og:image:width" content="1200" />
		<meta property="og:image:height" content="630" />
		<meta property="og:image:alt" content={imageAlt} />
	{/if}

	<!-- Twitter Card -->
	<meta name="twitter:card" content={twitterCard} />
	<meta name="twitter:title" content={fullTitle} />
	<meta name="twitter:description" content={description} />
	{#if image}
		<meta name="twitter:image" content={image} />
		<meta name="twitter:image:alt" content={imageAlt} />
	{/if}

	<!-- Additional -->
	<meta name="language" content="English" />
	<meta name="mobile-web-app-capable" content="yes" />
</svelte:head>

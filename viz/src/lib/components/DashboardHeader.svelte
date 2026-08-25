<script lang="ts">
	import { resolve } from '$app/paths';
	import type { ReportId } from '$lib/reports/config';
	import { reports } from '$lib/reports/config';
	import Icon from './Icon.svelte';

	let {
		activeReport,
		selectedDate = '',
		displayDate = '',
		minDate = '',
		maxDate = '',
		disabled = false,
		switcher = $bindable(),
		onChoose,
		onDate
	}: {
		activeReport: ReportId | 'workbook' | 'download';
		selectedDate?: string;
		displayDate?: string;
		minDate?: string;
		maxDate?: string;
		disabled?: boolean;
		switcher?: HTMLElement;
		onChoose?: (id: ReportId, event: MouseEvent) => void;
		onDate?: (date: string) => void;
	} = $props();
</script>

<header class="top-panel">
	<div class="brand-plate"><strong>KPTCL Load Curve</strong></div>
	<nav class="report-switcher" aria-label="Report type" bind:this={switcher}>
		{#each reports as report (report.id)}
			<a
				href={resolve(`/?report=${report.id}${selectedDate ? `&date=${selectedDate}` : ''}`)}
				class:active={activeReport === report.id}
				data-report={report.id}
				onclick={(event) => onChoose?.(report.id, event)}
				aria-current={activeReport === report.id ? 'page' : undefined}
			>
				<span class="switch-number">{report.number}</span>
				<span class="switch-icon"><Icon name={report.id} size={18} /></span>
				<span class="switch-copy"><strong>{report.label}</strong></span>
			</a>
		{/each}
	</nav>
	<div class="report-utilities">
		{#if onDate}
			<label class="report-date-control">
				<input
					type="date"
					min={minDate}
					max={maxDate}
					value={displayDate}
					{disabled}
					onchange={(event) => onDate(event.currentTarget.value)}
					aria-label="Report date"
				/>
			</label>
		{/if}
		<a
			class="source-link utility-link download-link"
			class:active={activeReport === 'download'}
			href={resolve('/download')}
			aria-current={activeReport === 'download' ? 'page' : undefined}
			title="Download datasets"
			aria-label="Download datasets"
		>
			<Icon name="download" size={20} />
		</a>
		<a
			class="source-link utility-link workbook-link"
			class:active={activeReport === 'workbook'}
			href={resolve('/workbook')}
			aria-current={activeReport === 'workbook' ? 'page' : undefined}
			title="Workbook cell trace"
			aria-label="Workbook cell trace"
		>
			<Icon name="workbook" size={20} />
		</a>
		<a
			class="source-link"
			href="https://github.com/Vonter/kptcl-load-curve"
			target="_blank"
			rel="noreferrer"
			title="View source repository on GitHub"
			aria-label="View source repository on GitHub"
		>
			<Icon name="github" size={20} />
		</a>
	</div>
</header>

<style>
	.top-panel {
		position: sticky;
		top: 0;
		z-index: 100;
		display: grid;
		grid-template-columns: 205px minmax(660px, 1fr) 320px;
		min-height: 74px;
		background: var(--ink);
		color: var(--paper);
		box-shadow: 0 5px 18px rgba(12, 22, 17, 0.2);
	}
	.brand-plate {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 12px 18px;
		border-right: 1px solid rgba(255, 255, 255, 0.12);
	}
	.brand-plate strong {
		display: block;
		font-family: var(--font-display);
		font-size: 1rem;
		font-weight: 800;
		letter-spacing: 0.07em;
	}
	.report-switcher {
		display: grid;
		grid-template-columns: repeat(7, minmax(98px, 1fr));
		min-width: 0;
	}
	.report-switcher a {
		position: relative;
		display: grid;
		grid-template-columns: auto 1fr;
		align-items: center;
		gap: 7px;
		min-width: 0;
		border-right: 1px solid rgba(255, 255, 255, 0.1);
		padding: 13px 9px 11px;
		text-decoration: none;
		color: rgba(255, 255, 255, 0.62);
		transition:
			background 150ms ease,
			color 150ms ease;
	}
	.report-switcher a::after {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		height: 4px;
		background: var(--yellow);
		content: '';
		transform: scaleX(0);
		transition: transform 150ms ease;
	}
	.report-switcher a:hover {
		background: rgba(255, 255, 255, 0.045);
		color: white;
	}
	.report-switcher a.active {
		background: rgba(246, 193, 54, 0.1);
		color: white;
	}
	.report-switcher a.active::after {
		transform: scaleX(1);
	}
	.switch-number {
		position: absolute;
		top: 7px;
		right: 7px;
		font-family: var(--font-mono);
		font-size: 0.45rem;
		color: rgba(255, 255, 255, 0.28);
	}
	.switch-icon {
		display: grid;
		place-items: center;
	}
	.switch-copy {
		min-width: 0;
	}
	.switch-copy strong {
		display: block;
		overflow: hidden;
		font-family: var(--font-display);
		font-size: 0.68rem;
		letter-spacing: 0.01em;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.report-utilities {
		display: flex;
		align-items: stretch;
		justify-content: flex-end;
		min-width: 0;
	}

	.utility-link {
		border-right: 1px solid rgba(255, 255, 255, 0.12);
	}
	.report-date-control {
		display: grid;
		flex: 1 1 auto;
		align-content: center;
		gap: 5px;
		min-width: 0;
		padding: 10px;
		border-right: 1px solid rgba(255, 255, 255, 0.12);
	}
	.report-date-control input {
		min-width: 0;
		width: 100%;
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 0;
		background: rgba(255, 255, 255, 0.08);
		padding: 6px 8px;
		font-family: var(--font-mono);
		font-size: 0.68rem;
		font-weight: 700;
		color: white;
		color-scheme: dark;
	}
	.report-date-control input:disabled {
		opacity: 0.55;
	}
	.source-link {
		position: relative;
		display: flex;
		flex: 0 0 58px;
		align-items: center;
		justify-content: center;
		padding: 10px 8px;
		text-decoration: none;
		color: rgba(255, 255, 255, 0.72);
		transition:
			background 150ms ease,
			color 150ms ease;
	}
	.source-link:hover {
		background: rgba(255, 255, 255, 0.06);
		color: white;
	}
	.source-link.active {
		background: rgba(246, 193, 54, 0.1);
		color: white;
	}
	.source-link.active::after {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		height: 4px;
		background: var(--yellow);
		content: '';
	}
	@media (max-width: 1200px) {
		.top-panel {
			grid-template-columns: 180px minmax(640px, 1fr) 290px;
			overflow-x: auto;
		}
		.brand-plate strong {
			font-size: 0.86rem;
		}
	}
	@media (max-width: 880px) {
		.top-panel {
			width: 100%;
			max-width: 100vw;
			min-width: 0;
			grid-template-columns: minmax(0, 1fr);
			overflow-x: clip;
		}
		.brand-plate {
			min-width: 0;
			overflow: hidden;
			height: 48px;
			border-bottom: 1px solid rgba(255, 255, 255, 0.12);
			padding-right: 110px;
		}
		.report-utilities {
			position: absolute;
			top: 0;
			right: 0;
			height: 48px;
			width: max-content;
			border-bottom: 1px solid rgba(255, 255, 255, 0.12);
		}
		.report-date-control {
			gap: 2px;
			padding: 5px 8px;
		}
		.report-date-control input {
			border: 0;
			background: transparent;
			padding: 1px 0;
		}
		.source-link {
			flex: 0 0 46px;
			padding: 5px;
		}
		.workbook-link {
			display: none;
		}
		.report-switcher {
			display: flex;
			width: 100%;
			max-width: 100vw;
			grid-column: 1 / -1;
			grid-row: 2;
			overflow-x: auto;
		}
		.report-switcher a {
			min-width: 140px;
		}
	}
	@media (max-width: 620px) {
		.brand-plate {
			padding-inline: 10px;
		}
		.brand-plate strong {
			font-size: 0.78rem;
			letter-spacing: 0.08em;
		}
	}
</style>

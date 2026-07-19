<script lang="ts">
	import { resolve } from '$app/paths';
	import type { ReportId } from '$lib/reports/config';
	import { reports } from '$lib/reports/config';
	import Icon from './Icon.svelte';

	let {
		activeReport,
		selectedDate,
		displayDate,
		minDate,
		maxDate,
		disabled,
		switcher = $bindable(),
		onChoose,
		onDate
	}: {
		activeReport: ReportId;
		selectedDate: string;
		displayDate: string;
		minDate: string;
		maxDate: string;
		disabled: boolean;
		switcher?: HTMLElement;
		onChoose: (id: ReportId, event: MouseEvent) => void;
		onDate: (date: string) => void;
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
				onclick={(event) => onChoose(report.id, event)}
				aria-current={activeReport === report.id ? 'page' : undefined}
			>
				<span class="switch-number">{report.number}</span>
				<span class="switch-icon"><Icon name={report.id} size={18} /></span>
				<span class="switch-copy"><strong>{report.label}</strong></span>
			</a>
		{/each}
	</nav>
	<div class="report-utilities">
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
		<a
			class="source-link"
			href="https://github.com/Vonter/kptcl-load-curve"
			target="_blank"
			rel="noreferrer"
			aria-label="View source repository on GitHub"
		>
			<Icon name="github" size={20} />
			<span>Source</span>
		</a>
	</div>
</header>

<style>
	.top-panel {
		position: sticky;
		top: 0;
		z-index: 100;
		display: grid;
		grid-template-columns: 205px minmax(735px, 1fr) 210px;
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
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		min-width: 0;
	}
	.report-date-control {
		display: grid;
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
		display: flex;
		min-width: 0;
		align-items: center;
		justify-content: center;
		gap: 7px;
		padding: 10px 8px;
		font-family: var(--font-mono);
		font-size: 0.58rem;
		font-weight: 750;
		letter-spacing: 0.06em;
		text-decoration: none;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.72);
		transition:
			background 150ms ease,
			color 150ms ease;
	}
	.source-link:hover {
		background: rgba(255, 255, 255, 0.06);
		color: white;
	}
	@media (max-width: 1200px) {
		.top-panel {
			grid-template-columns: 180px minmax(700px, 1fr) 195px;
			overflow-x: auto;
		}
		.brand-plate strong {
			font-size: 0.86rem;
		}
	}
	@media (max-width: 880px) {
		.top-panel {
			grid-template-columns: repeat(2, minmax(0, 1fr));
			overflow: visible;
		}
		.brand-plate {
			height: 48px;
			border-bottom: 1px solid rgba(255, 255, 255, 0.12);
		}
		.report-utilities {
			grid-column: 2;
			grid-row: 1;
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
			padding: 5px;
			font-size: 0.52rem;
		}
		.report-switcher {
			display: flex;
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

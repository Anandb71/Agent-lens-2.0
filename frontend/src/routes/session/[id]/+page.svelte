<script lang="ts">
	import { page } from '$app/stores';
	
	type Step = {
		id: number;
		step_type: string;
		content: string;
		session_id: number;
	};

	export let data: { steps: Step[]; id: string };
	
	let steps = data.steps;
	let sessionId = data.id;

	function getBorderColor(stepType: string): string {
		switch (stepType) {
			case 'THOUGHT':
				return 'border-blue-500';
			case 'TOOL_CALL':
				return 'border-green-500';
			case 'OBSERVATION':
				return 'border-gray-500';
			case 'ERROR':
				return 'border-red-500';
			default:
				return 'border-gray-300';
		}
	}

	function getBgColor(stepType: string): string {
		switch (stepType) {
			case 'THOUGHT':
				return 'bg-blue-50';
			case 'TOOL_CALL':
				return 'bg-green-50';
			case 'OBSERVATION':
				return 'bg-gray-50';
			case 'ERROR':
				return 'bg-red-50';
			default:
				return 'bg-white';
		}
	}

	function getStepTypeLabel(stepType: string): string {
		switch (stepType) {
			case 'THOUGHT':
				return 'Thought';
			case 'TOOL_CALL':
				return 'Tool Call';
			case 'OBSERVATION':
				return 'Observation';
			case 'ERROR':
				return 'Error';
			default:
				return stepType;
		}
	}
</script>

<div class="min-h-screen bg-gray-50 p-8">
	<div class="max-w-6xl mx-auto">
		<div class="mb-6">
			<a
				href="/"
				class="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
			>
				<svg
					class="w-5 h-5 mr-2"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 19l-7-7 7-7"
					/>
				</svg>
				Back to Sessions
			</a>
			<h1 class="text-3xl font-bold text-gray-900">Session {sessionId}</h1>
		</div>

		<div class="space-y-4">
			{#if steps.length === 0}
				<div class="bg-white rounded-lg shadow-sm p-6 text-center text-gray-500">
					No steps found for this session.
				</div>
			{:else}
				{#each steps as step}
					<div
						class="bg-white rounded-lg shadow-sm p-6 border-2 {getBorderColor(step.step_type)} {getBgColor(step.step_type)}"
					>
						<div class="flex items-center justify-between mb-3">
							<span
								class="px-3 py-1 rounded-full text-sm font-semibold {getBorderColor(step.step_type).replace('border-', 'text-').replace('-500', '-700')} bg-white border-2 {getBorderColor(step.step_type)}"
							>
								{getStepTypeLabel(step.step_type)}
							</span>
							<span class="text-xs text-gray-500">Step #{step.id}</span>
						</div>
						<div class="prose max-w-none">
							<pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-white/50 p-4 rounded border">{step.content}</pre>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>


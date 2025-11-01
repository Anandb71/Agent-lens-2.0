<script lang="ts">
	type Session = {
		id: number;
		name: string;
	};

	export let data: { sessions: Session[] };
	
	let sessions = data.sessions || [];
</script>

<div class="min-h-screen bg-gray-50 p-8">
	<div class="max-w-4xl mx-auto">
		<h1 class="text-3xl font-bold text-gray-900 mb-8">Agent-Lens Sessions</h1>
		
		<div class="space-y-4">
			{#if sessions.length === 0}
				<p class="text-gray-500">No sessions found. Start logging to see sessions here.</p>
			{:else}
				{#each sessions as session}
					<a
						href="/session/{session.id}"
						class="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-6 border border-gray-200 hover:border-blue-500"
					>
						<div class="flex items-center justify-between">
							<div>
								<h2 class="text-xl font-semibold text-gray-900">{session.name}</h2>
								<p class="text-sm text-gray-500 mt-1">Session ID: {session.id}</p>
							</div>
							<svg
								class="w-5 h-5 text-gray-400"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 5l7 7-7 7"
								/>
							</svg>
						</div>
					</a>
				{/each}
			{/if}
		</div>
	</div>
</div>


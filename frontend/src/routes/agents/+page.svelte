<script>
	import { onMount, onDestroy } from 'svelte';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Progress } from '$lib/components/ui/progress';
	import { LogViewer, MermaidRenderer } from '$lib/components';
	import { apiFetch, apiError, isLoading } from '$lib/stores';
	import { formatStatus, getStatusColor } from '$lib/utils';

	let runningWorkflows = [];
	let selectedWorkflow = null;
	let workflowDetails = null;
	let refreshInterval;

	const workflowDiagram = `
graph TD
    A[Requirements] --> B[Design]
    B --> C[Tasks]
    C --> D[Implementation]
    D --> E[Verification]
    E --> F[Review]
    F --> G{Approved?}
    G -->|Yes| H[Complete]
    G -->|No| C
`;

	onMount(async () => {
		await fetchRunningWorkflows();
		// Refresh every 5 seconds
		refreshInterval = setInterval(fetchRunningWorkflows, 5000);
	});

	onDestroy(() => {
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
	});

	async function fetchRunningWorkflows() {
		try {
			const data = await apiFetch('/api/agents/running');
			runningWorkflows = data.running || [];

			// Auto-select first workflow if none selected
			if (!selectedWorkflow && runningWorkflows.length > 0) {
				selectWorkflow(runningWorkflows[0]);
			}
		} catch (e) {
			console.error('Failed to fetch running workflows:', e);
		}
	}

	async function selectWorkflow(featId) {
		selectedWorkflow = featId;
		try {
			workflowDetails = await apiFetch(`/api/agents/status/${featId}`);
		} catch (e) {
			console.error('Failed to fetch workflow details:', e);
			workflowDetails = null;
		}
	}
</script>

<svelte:head>
	<title>Agent Monitor - ClaudeForge</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div>
		<h1 class="text-3xl font-bold">Agent Monitor</h1>
		<p class="text-muted-foreground">Monitor running workflows and agent activity</p>
	</div>

	<!-- Error Display -->
	{#if $apiError}
		<div class="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
			{$apiError}
		</div>
	{/if}

	<div class="grid gap-8 lg:grid-cols-3">
		<!-- Running Workflows -->
		<div class="space-y-4">
			<Card>
				<CardHeader>
					<CardTitle class="text-lg">Running Workflows</CardTitle>
					<CardDescription>{runningWorkflows.length} active</CardDescription>
				</CardHeader>
				<CardContent>
					{#if runningWorkflows.length === 0}
						<p class="text-muted-foreground text-center py-4">No active workflows</p>
					{:else}
						<div class="space-y-2">
							{#each runningWorkflows as featId}
								<button
									on:click={() => selectWorkflow(featId)}
									class="w-full text-left px-4 py-3 rounded-md transition-colors
										{selectedWorkflow === featId
											? 'bg-primary text-primary-foreground'
											: 'bg-secondary hover:bg-secondary/80'}"
								>
									<span class="font-mono text-sm">{featId}</span>
								</button>
							{/each}
						</div>
					{/if}
				</CardContent>
			</Card>

			<!-- Workflow Diagram -->
			<Card>
				<CardHeader>
					<CardTitle class="text-lg">Workflow Phases</CardTitle>
				</CardHeader>
				<CardContent>
					<MermaidRenderer diagram={workflowDiagram} />
				</CardContent>
			</Card>
		</div>

		<!-- Workflow Details -->
		<div class="lg:col-span-2 space-y-4">
			{#if selectedWorkflow && workflowDetails}
				<Card>
					<CardHeader>
						<div class="flex items-center justify-between">
							<CardTitle class="font-mono">{selectedWorkflow}</CardTitle>
							<Badge class={getStatusColor(workflowDetails.status)}>
								{formatStatus(workflowDetails.status)}
							</Badge>
						</div>
						<CardDescription>
							Current Phase: {formatStatus(workflowDetails.current_phase)}
						</CardDescription>
					</CardHeader>
					<CardContent class="space-y-4">
						<!-- Progress -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-sm font-medium">Progress</span>
								<span class="text-sm text-muted-foreground">
									{((workflowDetails.progress || 0) * 100).toFixed(0)}%
								</span>
							</div>
							<Progress value={(workflowDetails.progress || 0) * 100} max={100} />
						</div>

						<!-- Phase Timeline -->
						<div>
							<h4 class="text-sm font-medium mb-3">Phase Timeline</h4>
							<div class="flex items-center gap-1">
								{#each ['requirements', 'design', 'tasks', 'implementation', 'verification', 'review'] as phase, i}
									{@const currentPhaseIndex = ['requirements', 'design', 'tasks', 'implementation', 'verification', 'review'].indexOf(workflowDetails.current_phase)}
									<div class="flex-1 flex items-center">
										<div
											class="w-full h-2 rounded-full
												{i < currentPhaseIndex
													? 'bg-green-500'
													: i === currentPhaseIndex
														? 'bg-blue-500 progress-animated'
														: 'bg-muted'}"
										></div>
									</div>
								{/each}
							</div>
							<div class="flex justify-between mt-1 text-xs text-muted-foreground">
								<span>Req</span>
								<span>Des</span>
								<span>Task</span>
								<span>Impl</span>
								<span>Ver</span>
								<span>Rev</span>
							</div>
						</div>

						<!-- View Spec Button -->
						<a href="/specs/{selectedWorkflow}">
							<Button variant="outline" class="w-full">View Full Specification</Button>
						</a>
					</CardContent>
				</Card>

				<!-- Agent Logs -->
				<Card>
					<CardHeader>
						<CardTitle class="text-lg">Agent Logs</CardTitle>
						<CardDescription>Recent activity for this workflow</CardDescription>
					</CardHeader>
					<CardContent>
						<LogViewer logs={workflowDetails.logs?.map(msg => ({
							message: msg,
							level: 'info',
							timestamp: new Date().toISOString()
						})) || []} />
					</CardContent>
				</Card>
			{:else}
				<Card>
					<CardContent class="py-12 text-center">
						<p class="text-muted-foreground">
							{runningWorkflows.length === 0
								? 'No active workflows. Start a new workflow from the Projects page.'
								: 'Select a workflow to view details.'}
						</p>
					</CardContent>
				</Card>
			{/if}
		</div>
	</div>
</div>

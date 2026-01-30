<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Progress } from '$lib/components/ui/progress';
	import { Textarea } from '$lib/components/ui/textarea';
	import { LogViewer, MarkdownRenderer } from '$lib/components';
	import { fetchSpec, currentSpec, approveSpec, fetchWorkflowStatus, workflowStatus, apiError, isLoading } from '$lib/stores';
	import { logs, connectWS, disconnectWS } from '$lib/stores/websocket';
	import { formatStatus, getStatusColor, getPhaseProgress, formatDate } from '$lib/utils';

	const phases = ['requirements', 'design', 'tasks', 'implementation', 'verification', 'review'];

	$: featId = $page.params.feat_id;
	$: activePhase = $currentSpec?.phases ? Object.keys($currentSpec.phases)[0] || 'requirements' : 'requirements';

	let showApprovalModal = false;
	let approvalComment = '';
	let approvalAction = 'approve';
	let approvalPhase = '';

	onMount(async () => {
		if (featId) {
			// Parse project from URL query or default
			const urlParams = new URLSearchParams($page.url.search);
			const project = urlParams.get('project') || 'sample-project';

			await fetchSpec(project, featId);
			await fetchWorkflowStatus(featId);

			// Connect WebSocket for live logs
			connectWS(featId);
		}
	});

	onDestroy(() => {
		disconnectWS();
	});

	function openApprovalModal(phase, action) {
		approvalPhase = phase;
		approvalAction = action;
		approvalComment = '';
		showApprovalModal = true;
	}

	async function handleApproval() {
		if (!approvalPhase) return;

		try {
			await approveSpec(featId, approvalPhase, approvalAction, approvalComment);
			showApprovalModal = false;

			// Refresh spec data
			const urlParams = new URLSearchParams($page.url.search);
			const project = urlParams.get('project') || 'sample-project';
			await fetchSpec(project, featId);
		} catch (e) {
			console.error('Approval failed:', e);
		}
	}

	function selectPhase(phase) {
		activePhase = phase;
	}

	$: progress = $workflowStatus ? ($workflowStatus.progress || 0) * 100 : 0;
</script>

<svelte:head>
	<title>{featId} - ClaudeForge</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<nav class="text-sm text-muted-foreground mb-2">
				<a href="/" class="hover:text-foreground">Projects</a>
				<span class="mx-2">/</span>
				<span>{$currentSpec?.project_name || '...'}</span>
				<span class="mx-2">/</span>
				<span>{featId}</span>
			</nav>
			<h1 class="text-3xl font-bold font-mono">{featId}</h1>
			<p class="text-muted-foreground">{$currentSpec?.description || 'Loading...'}</p>
		</div>
		<a href="/">
			<Button variant="outline">Back to Projects</Button>
		</a>
	</div>

	<!-- Error Display -->
	{#if $apiError}
		<div class="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
			{$apiError}
		</div>
	{/if}

	<!-- Progress Bar -->
	{#if $workflowStatus}
		<Card>
			<CardContent class="py-4">
				<div class="flex items-center justify-between mb-2">
					<span class="text-sm font-medium">Workflow Progress</span>
					<span class="text-sm text-muted-foreground">{progress.toFixed(0)}%</span>
				</div>
				<Progress value={progress} max={100} />
				<div class="flex items-center justify-between mt-2">
					<Badge class={getStatusColor($workflowStatus.status)}>
						{formatStatus($workflowStatus.status)}
					</Badge>
					<span class="text-sm text-muted-foreground">
						Current: {formatStatus($workflowStatus.current_phase)}
					</span>
				</div>
			</CardContent>
		</Card>
	{/if}

	<div class="grid gap-8 lg:grid-cols-3">
		<!-- Phase Tabs -->
		<div class="lg:col-span-2 space-y-4">
			<!-- Phase Selector -->
			<div class="flex flex-wrap gap-2">
				{#each phases as phase}
					{@const phaseData = $currentSpec?.phases?.[phase]}
					<button
						on:click={() => selectPhase(phase)}
						class="px-4 py-2 rounded-md text-sm font-medium transition-colors
							{activePhase === phase
								? 'bg-primary text-primary-foreground'
								: 'bg-secondary text-secondary-foreground hover:bg-secondary/80'}
							{phaseData ? '' : 'opacity-50'}"
					>
						{phase.charAt(0).toUpperCase() + phase.slice(1)}
						{#if phaseData}
							<span class="ml-1 text-xs {getStatusColor(phaseData.status)}">
								({formatStatus(phaseData.status)})
							</span>
						{/if}
					</button>
				{/each}
			</div>

			<!-- Phase Content -->
			{#if $currentSpec?.phases?.[activePhase]}
				{@const phaseData = $currentSpec.phases[activePhase]}
				<Card>
					<CardHeader>
						<div class="flex items-center justify-between">
							<CardTitle>{activePhase.charAt(0).toUpperCase() + activePhase.slice(1)}</CardTitle>
							<Badge class={getStatusColor(phaseData.status)}>
								{formatStatus(phaseData.status)}
							</Badge>
						</div>
						<CardDescription>
							Updated: {formatDate(phaseData.updated_at)}
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div class="prose prose-invert prose-sm max-w-none bg-muted p-4 rounded-md max-h-96 overflow-auto">
							<MarkdownRenderer content={phaseData.content} />
						</div>
					</CardContent>
					<CardFooter class="flex gap-2">
						{#if phaseData.status === 'pending_approval' || phaseData.status === 'draft'}
							<Button
								variant="default"
								on:click={() => openApprovalModal(activePhase, 'approve')}
							>
								Approve
							</Button>
							<Button
								variant="destructive"
								on:click={() => openApprovalModal(activePhase, 'reject')}
							>
								Reject
							</Button>
						{/if}
					</CardFooter>
				</Card>
			{:else}
				<Card>
					<CardContent class="py-12 text-center">
						<p class="text-muted-foreground">No data for this phase yet.</p>
					</CardContent>
				</Card>
			{/if}
		</div>

		<!-- Logs Sidebar -->
		<div class="space-y-4">
			<Card>
				<CardHeader>
					<CardTitle class="text-lg">Agent Logs</CardTitle>
					<CardDescription>Real-time workflow activity</CardDescription>
				</CardHeader>
				<CardContent>
					<LogViewer logs={$logs} />
				</CardContent>
			</Card>
		</div>
	</div>
</div>

<!-- Approval Modal -->
{#if showApprovalModal}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
		<Card class="w-full max-w-md mx-4">
			<CardHeader>
				<CardTitle>
					{approvalAction === 'approve' ? 'Approve' : 'Reject'} Phase
				</CardTitle>
				<CardDescription>
					{approvalAction === 'approve'
						? 'Confirm approval of this phase to continue the workflow.'
						: 'Reject this phase with feedback for revision.'}
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Textarea
					bind:value={approvalComment}
					placeholder="Add a comment (optional)..."
					class="h-24"
				/>
			</CardContent>
			<CardFooter class="flex gap-2 justify-end">
				<Button variant="outline" on:click={() => showApprovalModal = false}>
					Cancel
				</Button>
				<Button
					variant={approvalAction === 'approve' ? 'default' : 'destructive'}
					on:click={handleApproval}
				>
					{approvalAction === 'approve' ? 'Approve' : 'Reject'}
				</Button>
			</CardFooter>
		</Card>
	</div>
{/if}

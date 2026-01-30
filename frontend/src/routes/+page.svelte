<script>
	import { onMount } from 'svelte';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Badge } from '$lib/components/ui/badge';
	import { projects, fetchProjects, startWorkflow, apiError, isLoading } from '$lib/stores';
	import { formatStatus, getStatusColor } from '$lib/utils';

	let showNewWorkflow = false;
	let selectedProject = '';
	let featureDesc = '';
	let startingWorkflow = false;

	onMount(() => {
		fetchProjects();
	});

	async function handleStartWorkflow() {
		if (!selectedProject || !featureDesc) return;

		startingWorkflow = true;
		try {
			const result = await startWorkflow(selectedProject, featureDesc);
			if (result.feat_id) {
				window.location.href = `/specs/${result.feat_id}?project=${encodeURIComponent(selectedProject)}`;
			}
		} catch (e) {
			console.error('Failed to start workflow:', e);
		} finally {
			startingWorkflow = false;
		}
	}
</script>

<svelte:head>
	<title>Projects - ClaudeForge</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold">Projects</h1>
			<p class="text-muted-foreground">Manage your spec-driven development workflows</p>
		</div>
		<Button on:click={() => showNewWorkflow = !showNewWorkflow}>
			{showNewWorkflow ? 'Cancel' : 'New Workflow'}
		</Button>
	</div>

	<!-- New Workflow Form -->
	{#if showNewWorkflow}
		<Card>
			<CardHeader>
				<CardTitle>Start New Workflow</CardTitle>
				<CardDescription>Create a new feature workflow for a project</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4">
				<div>
					<label for="project" class="block text-sm font-medium mb-2">Project</label>
					<select
						id="project"
						bind:value={selectedProject}
						class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
					>
						<option value="">Select a project...</option>
						{#each $projects as project}
							<option value={project.name}>{project.name}</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="feature" class="block text-sm font-medium mb-2">Feature Description</label>
					<Input
						id="feature"
						bind:value={featureDesc}
						placeholder="e.g., Add user authentication with JWT"
					/>
				</div>
			</CardContent>
			<CardFooter>
				<Button
					on:click={handleStartWorkflow}
					disabled={!selectedProject || !featureDesc || startingWorkflow}
				>
					{startingWorkflow ? 'Starting...' : 'Start Workflow'}
				</Button>
			</CardFooter>
		</Card>
	{/if}

	<!-- Error Display -->
	{#if $apiError}
		<div class="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
			{$apiError}
		</div>
	{/if}

	<!-- Projects Grid -->
	{#if $isLoading}
		<div class="text-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
			<p class="text-muted-foreground mt-4">Loading projects...</p>
		</div>
	{:else if $projects.length === 0}
		<Card>
			<CardContent class="py-12 text-center">
				<p class="text-muted-foreground">No projects found.</p>
				<p class="text-sm text-muted-foreground mt-2">
					Mount project directories to /projects/ to get started.
				</p>
			</CardContent>
		</Card>
	{:else}
		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each $projects as project}
				<a href="/projects/{project.name}" class="block">
					<Card class="hover:border-primary transition-colors cursor-pointer h-full">
						<CardHeader>
							<div class="flex items-center justify-between">
								<CardTitle class="text-lg">{project.name}</CardTitle>
								<Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
									{project.status}
								</Badge>
							</div>
							<CardDescription class="truncate">{project.path}</CardDescription>
						</CardHeader>
						<CardContent>
							<p class="text-sm text-muted-foreground">
								Click to view features and specs
							</p>
						</CardContent>
					</Card>
				</a>
			{/each}
		</div>
	{/if}
</div>

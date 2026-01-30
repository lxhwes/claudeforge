<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { fetchProjectFeatures, currentProjectFeatures, apiError, isLoading } from '$lib/stores';
	import { formatStatus, getStatusColor, formatDate } from '$lib/utils';

	$: projectName = $page.params.slug;

	onMount(() => {
		if (projectName) {
			fetchProjectFeatures(projectName);
		}
	});
</script>

<svelte:head>
	<title>{projectName} - ClaudeForge</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<nav class="text-sm text-muted-foreground mb-2">
				<a href="/" class="hover:text-foreground">Projects</a>
				<span class="mx-2">/</span>
				<span>{projectName}</span>
			</nav>
			<h1 class="text-3xl font-bold">{projectName}</h1>
			<p class="text-muted-foreground">Feature workflows and specifications</p>
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

	<!-- Features List -->
	{#if $isLoading}
		<div class="text-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
			<p class="text-muted-foreground mt-4">Loading features...</p>
		</div>
	{:else if $currentProjectFeatures.length === 0}
		<Card>
			<CardContent class="py-12 text-center">
				<p class="text-muted-foreground">No features found for this project.</p>
				<p class="text-sm text-muted-foreground mt-2">
					Start a new workflow from the Projects page.
				</p>
			</CardContent>
		</Card>
	{:else}
		<div class="space-y-4">
			{#each $currentProjectFeatures as feature}
				<a href="/specs/{feature.feature_id}" class="block">
					<Card class="hover:border-primary transition-colors cursor-pointer">
						<CardHeader>
							<div class="flex items-center justify-between">
								<CardTitle class="text-lg font-mono">{feature.feature_id}</CardTitle>
								<div class="flex items-center gap-2">
									<Badge class={getStatusColor(feature.status)}>
										{formatStatus(feature.status)}
									</Badge>
									<Badge variant="outline">
										{formatStatus(feature.current_phase)}
									</Badge>
								</div>
							</div>
							<CardDescription>{feature.description || 'No description'}</CardDescription>
						</CardHeader>
					</Card>
				</a>
			{/each}
		</div>
	{/if}
</div>

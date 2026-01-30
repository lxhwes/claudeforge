<script>
	import '../app.css';
	import { page } from '$app/stores';

	const navItems = [
		{ href: '/', label: 'Projects', icon: 'folder' },
		{ href: '/agents', label: 'Agents', icon: 'cpu' }
	];

	$: currentPath = $page.url.pathname;
</script>

<div class="min-h-screen flex flex-col">
	<!-- Header -->
	<header class="border-b bg-card">
		<div class="container mx-auto flex items-center justify-between h-16 px-4">
			<a href="/" class="flex items-center gap-2">
				<div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
					<span class="text-primary-foreground font-bold">CF</span>
				</div>
				<span class="text-xl font-bold">ClaudeForge</span>
			</a>

			<nav class="flex items-center gap-1">
				{#each navItems as item}
					<a
						href={item.href}
						class="px-4 py-2 rounded-md text-sm font-medium transition-colors
							{currentPath === item.href
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:text-foreground hover:bg-accent'}"
					>
						{item.label}
					</a>
				{/each}
			</nav>

			<div class="flex items-center gap-2">
				<a href="/api/health" target="_blank" rel="noopener" class="text-muted-foreground hover:text-foreground">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
					</svg>
				</a>
			</div>
		</div>
	</header>

	<!-- Main content -->
	<main class="flex-1 container mx-auto px-4 py-8">
		<slot />
	</main>

	<!-- Footer -->
	<footer class="border-t bg-card py-4">
		<div class="container mx-auto px-4 text-center text-sm text-muted-foreground">
			ClaudeForge v0.1.0 - Spec-Driven AI Development Framework
		</div>
	</footer>
</div>

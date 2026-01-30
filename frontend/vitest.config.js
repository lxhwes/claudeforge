import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		environment: 'jsdom'
	},
	resolve: {
		alias: {
			$lib: '/src/lib',
			$components: '/src/lib/components',
			$stores: '/src/lib/stores',
			$utils: '/src/lib/utils'
		}
	}
});

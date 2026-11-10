import { defineConfig } from 'astro/config';

// SITE_BASE is set for GitHub Pages project sites (e.g. "/Baseline_tests_for_AutoNav/").
export default defineConfig({
  output: 'static',
  base: process.env.SITE_BASE || '/',
  build: { assets: 'assets' },
});
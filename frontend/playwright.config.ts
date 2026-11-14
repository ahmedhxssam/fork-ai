import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir:'./e2e', timeout:180000, use:{channel:process.env.FORK_BROWSER_CHANNEL,baseURL:process.env.FORK_URL || 'http://127.0.0.1:5173',viewport:{width:1440,height:1000}}, reporter:'list' });

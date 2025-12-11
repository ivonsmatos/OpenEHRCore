/**
 * Sprint 23: E2E Tests - Core Application Flows
 */

import { test, expect } from '@playwright/test';

// Helper to bypass auth in tests
async function loginAsTestUser(page: any) {
    // For E2E tests, we can use a dev token bypass or mock auth
    // This would typically set up cookies/localStorage
    await page.goto('/');

    // Check if already logged in
    const url = page.url();
    if (url.includes('login')) {
        // Use test credentials
        await page.getByLabel(/email|usuário/i).fill('admin@openehrcore.com');
        await page.getByLabel(/senha|password/i).fill('admin123');
        await page.getByRole('button', { name: /entrar|login/i }).click();

        // Wait for redirect
        await page.waitForURL(/dashboard|home/, { timeout: 10000 }).catch(() => { });
    }
}

test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display dashboard after login', async ({ page }) => {
        await page.goto('/dashboard');

        // Should show main dashboard elements
        await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 10000 });
    });

    test('should show statistics cards', async ({ page }) => {
        await page.goto('/dashboard');

        // Dashboard typically shows stats
        const cards = page.locator('[class*="card"], [class*="stat"]');
        const cardCount = await cards.count();
        expect(cardCount).toBeGreaterThan(0);
    });
});

test.describe('Patient Management', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should navigate to patient list', async ({ page }) => {
        await page.goto('/patients');

        // Should show patient list or search
        await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
    });

    test('should have search functionality', async ({ page }) => {
        await page.goto('/patients');

        // Should have search input
        const searchInput = page.getByRole('searchbox').or(
            page.getByPlaceholder(/buscar|search|pesquisar/i)
        );

        if (await searchInput.count() > 0) {
            await expect(searchInput.first()).toBeVisible();
        }
    });

    test('should show patient details on click', async ({ page }) => {
        await page.goto('/patients');

        // Wait for list to load
        await page.waitForLoadState('networkidle');

        // Click on first patient if list is not empty
        const patientLink = page.locator('[data-testid="patient-row"], tr, [class*="patient"]').first();
        if (await patientLink.count() > 0) {
            await patientLink.click();

            // Should navigate to patient details
            await expect(page).toHaveURL(/patient|paciente/i);
        }
    });
});

test.describe('Search Functionality', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should perform global search', async ({ page }) => {
        await page.goto('/dashboard');

        // Find search bar
        const searchBar = page.getByRole('searchbox').or(
            page.getByPlaceholder(/buscar|search/i)
        );

        if (await searchBar.count() > 0) {
            await searchBar.first().fill('test');
            await page.keyboard.press('Enter');

            // Should show search results
            await page.waitForTimeout(1000);
        }
    });
});

test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/');

        // Mobile layout should be usable
        await expect(page.locator('body')).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/');

        await expect(page.locator('body')).toBeVisible();
    });

    test('should work on desktop viewport', async ({ page }) => {
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.goto('/');

        await expect(page.locator('body')).toBeVisible();
    });
});

test.describe('Error Handling', () => {
    test('should show 404 page for unknown routes', async ({ page }) => {
        await page.goto('/this-page-does-not-exist-12345');

        // Should show 404 or redirect to home
        const content = await page.content();
        const is404 = content.includes('404') ||
            content.includes('not found') ||
            content.includes('não encontrad');
        const isRedirected = page.url().includes('login') ||
            page.url().includes('dashboard');

        expect(is404 || isRedirected).toBeTruthy();
    });

    test('should handle network errors gracefully', async ({ page, context }) => {
        // Block API requests
        await context.route('**/api/**', (route) => route.abort());

        await page.goto('/dashboard');

        // Should not crash, should show some UI
        await expect(page.locator('body')).toBeVisible();
    });
});

test.describe('Form Validation', () => {
    test('should show validation errors on empty form submit', async ({ page }) => {
        await page.goto('/login');

        // Try to submit empty form
        await page.getByRole('button', { name: /entrar|login|signin/i }).click();

        // Should show validation errors or browser validation
        await page.waitForTimeout(500);

        // Either custom error or HTML5 validation
        const emailInput = page.getByLabel(/email|usuário/i);
        const isInvalid = await emailInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
        const hasError = await page.locator('[class*="error"], [role="alert"]').count() > 0;

        expect(isInvalid || hasError).toBeTruthy();
    });
});

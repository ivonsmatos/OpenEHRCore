/**
 * Sprint 23: E2E Tests - Authentication Flow
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
    test('should display login page', async ({ page }) => {
        await page.goto('/');

        // Should redirect to login or show login form
        await expect(page).toHaveURL(/login|auth/);
    });

    test('should show login form elements', async ({ page }) => {
        await page.goto('/login');

        // Check for login form elements
        await expect(page.getByLabel(/email|usuário/i)).toBeVisible();
        await expect(page.getByLabel(/senha|password/i)).toBeVisible();
        await expect(page.getByRole('button', { name: /entrar|login|signin/i })).toBeVisible();
    });

    test('should show error on invalid credentials', async ({ page }) => {
        await page.goto('/login');

        // Fill in invalid credentials
        await page.getByLabel(/email|usuário/i).fill('invalid@test.com');
        await page.getByLabel(/senha|password/i).fill('wrongpassword');

        // Submit form
        await page.getByRole('button', { name: /entrar|login|signin/i }).click();

        // Should show error message
        await expect(page.getByText(/erro|invalid|incorreto/i)).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Navigation', () => {
    // These tests assume user is logged in (need auth bypass for testing)

    test.beforeEach(async ({ page }) => {
        // Set up auth bypass for testing
        await page.goto('/');
        // In a real scenario, you would inject auth tokens here
    });

    test('should have responsive navigation', async ({ page }) => {
        await page.goto('/');

        // Check if navigation is visible (varies by viewport)
        const viewport = page.viewportSize();
        if (viewport && viewport.width < 768) {
            // Mobile: should have hamburger menu
            await expect(page.getByRole('button', { name: /menu/i })).toBeVisible();
        }
    });
});

test.describe('Accessibility', () => {
    test('should have proper page title', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/.+/); // Has some title
    });

    test('should have proper heading structure', async ({ page }) => {
        await page.goto('/login');

        // Should have at least one h1
        const h1Count = await page.locator('h1').count();
        expect(h1Count).toBeGreaterThanOrEqual(1);
    });

    test('should have proper focus management', async ({ page }) => {
        await page.goto('/login');

        // Tab should move focus to interactive elements
        await page.keyboard.press('Tab');

        const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
        expect(['INPUT', 'BUTTON', 'A']).toContain(focusedElement);
    });

    test('should have no accessibility violations on login page', async ({ page }) => {
        await page.goto('/login');

        // Basic accessibility checks
        // For full a11y testing, use @axe-core/playwright

        // All images should have alt text
        const images = page.locator('img');
        const imageCount = await images.count();
        for (let i = 0; i < imageCount; i++) {
            const alt = await images.nth(i).getAttribute('alt');
            expect(alt).not.toBeNull();
        }

        // All form inputs should have labels
        const inputs = page.locator('input:not([type="hidden"])');
        const inputCount = await inputs.count();
        for (let i = 0; i < inputCount; i++) {
            const input = inputs.nth(i);
            const id = await input.getAttribute('id');
            const ariaLabel = await input.getAttribute('aria-label');
            const ariaLabelledBy = await input.getAttribute('aria-labelledby');

            // Should have either label, aria-label, or aria-labelledby
            const hasLabel = id ? await page.locator(`label[for="${id}"]`).count() > 0 : false;
            expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
        }
    });
});

test.describe('Performance', () => {
    test('should load login page within acceptable time', async ({ page }) => {
        const startTime = Date.now();
        await page.goto('/login');
        const loadTime = Date.now() - startTime;

        // Page should load in under 5 seconds
        expect(loadTime).toBeLessThan(5000);
    });

    test('should have no console errors on load', async ({ page }) => {
        const errors: string[] = [];

        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });

        await page.goto('/login');
        await page.waitForLoadState('networkidle');

        // Filter out expected errors (like auth redirect)
        const unexpectedErrors = errors.filter(
            (err) => !err.includes('401') && !err.includes('Unauthorized')
        );

        expect(unexpectedErrors).toHaveLength(0);
    });
});

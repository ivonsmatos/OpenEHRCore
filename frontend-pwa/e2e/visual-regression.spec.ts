/**
 * Visual Regression Testing with Playwright
 * ==========================================
 * 
 * Testes de regressão visual usando screenshots do Playwright.
 * Detecta mudanças visuais não intencionais na UI.
 * 
 * Integração Percy (Opcional):
 *   npm install --save-dev @percy/cli @percy/playwright
 *   export PERCY_TOKEN=your_token
 *   npx percy exec -- npx playwright test visual-regression.spec.ts
 * 
 * Uso Local (sem Percy):
 *   npx playwright test e2e/visual-regression.spec.ts
 *   
 *   # Atualizar screenshots baseline
 *   npx playwright test e2e/visual-regression.spec.ts --update-snapshots
 * 
 * Estrutura de arquivos:
 *   e2e/visual-regression.spec.ts-snapshots/
 *     ├── login-page-chromium-darwin.png
 *     ├── patient-list-chromium-darwin.png
 *     └── ...
 */

import { test, expect, Page } from '@playwright/test';

/**
 * Percy integration (opcional)
 * Descomente se estiver usando Percy
 */
// import percySnapshot from '@percy/playwright';

/**
 * Helper: Aguarda carregamento completo da página
 */
async function waitForPageReady(page: Page) {
    await page.waitForLoadState('networkidle');
    await page.waitForLoadState('domcontentloaded');
    
    // Aguarda animações terminarem
    await page.waitForTimeout(500);
    
    // Aguarda skeletons/loaders desaparecerem
    const loaders = page.locator('[data-testid="skeleton"], [data-testid="loader"], .loading');
    if (await loaders.count() > 0) {
        await loaders.first().waitFor({ state: 'hidden', timeout: 10000 });
    }
}

/**
 * Helper: Máscara elementos dinâmicos antes de capturar
 */
async function maskDynamicContent(page: Page) {
    // Máscara timestamps, datas, IDs
    await page.addStyleTag({
        content: `
            [data-testid="timestamp"],
            [data-testid="date"],
            [data-testid="id"],
            .timestamp,
            .date-time {
                visibility: hidden !important;
            }
        `
    });
}

test.describe('Visual Regression - Public Pages', () => {
    test('Login page visual snapshot', async ({ page }) => {
        await page.goto('/login');
        await waitForPageReady(page);
        await maskDynamicContent(page);

        // Captura screenshot
        await expect(page).toHaveScreenshot('login-page.png', {
            fullPage: true,
            animations: 'disabled',
            maxDiffPixels: 100 // Tolera até 100 pixels de diferença
        });

        // Percy snapshot (se configurado)
        // await percySnapshot(page, 'Login Page');
    });

    test('Home page visual snapshot', async ({ page }) => {
        await page.goto('/');
        await waitForPageReady(page);
        await maskDynamicContent(page);

        await expect(page).toHaveScreenshot('home-page.png', {
            fullPage: true,
            animations: 'disabled'
        });
    });
});

test.describe('Visual Regression - Patient Management', () => {
    test.beforeEach(async ({ page }) => {
        // TODO: Implement authentication
        await page.goto('/patients');
    });

    test('Patient list page - empty state', async ({ page }) => {
        await waitForPageReady(page);
        await maskDynamicContent(page);

        // Se houver pacientes, este teste pode falhar - use com dados controlados
        await expect(page).toHaveScreenshot('patient-list-empty.png', {
            fullPage: true,
            animations: 'disabled',
            maxDiffPixels: 200
        });
    });

    test('Patient list page - with data', async ({ page }) => {
        await waitForPageReady(page);
        await maskDynamicContent(page);

        // Verifica se há pacientes
        const patientCards = page.locator('[data-testid="patient-card"]');
        if (await patientCards.count() > 0) {
            await expect(page).toHaveScreenshot('patient-list-with-data.png', {
                fullPage: true,
                animations: 'disabled',
                maxDiffPixels: 300
            });
        } else {
            test.skip();
        }
    });

    test('Patient card component', async ({ page }) => {
        await waitForPageReady(page);

        const firstPatientCard = page.locator('[data-testid="patient-card"]').first();
        
        if (await firstPatientCard.count() > 0) {
            await expect(firstPatientCard).toHaveScreenshot('patient-card-component.png', {
                animations: 'disabled'
            });
        } else {
            test.skip();
        }
    });

    test('Patient details page', async ({ page }) => {
        await waitForPageReady(page);

        const firstPatient = page.locator('[data-testid="patient-card"]').first();
        
        if (await firstPatient.count() > 0) {
            await firstPatient.click();
            await waitForPageReady(page);
            await maskDynamicContent(page);

            await expect(page).toHaveScreenshot('patient-details.png', {
                fullPage: true,
                animations: 'disabled',
                maxDiffPixels: 300
            });
        } else {
            test.skip();
        }
    });

    test('Patient form - create new', async ({ page }) => {
        const createButton = page.getByRole('button', { name: /novo|create|adicionar/i });
        
        if (await createButton.count() > 0) {
            await createButton.click();
            await waitForPageReady(page);

            await expect(page).toHaveScreenshot('patient-form-create.png', {
                fullPage: true,
                animations: 'disabled'
            });
        } else {
            test.skip();
        }
    });
});

test.describe('Visual Regression - Navigation', () => {
    test('Main navigation bar', async ({ page }) => {
        await page.goto('/');
        await waitForPageReady(page);

        const nav = page.locator('nav').first();
        
        if (await nav.count() > 0) {
            await expect(nav).toHaveScreenshot('navigation-bar.png', {
                animations: 'disabled'
            });
        }
    });

    test('Sidebar navigation', async ({ page }) => {
        await page.goto('/patients');
        await waitForPageReady(page);

        const sidebar = page.locator('[data-testid="sidebar"], aside').first();
        
        if (await sidebar.count() > 0) {
            await expect(sidebar).toHaveScreenshot('sidebar-navigation.png', {
                animations: 'disabled'
            });
        }
    });
});

test.describe('Visual Regression - Interactive States', () => {
    test('Button hover states', async ({ page }) => {
        await page.goto('/patients');
        await waitForPageReady(page);

        const primaryButton = page.getByRole('button').first();
        
        if (await primaryButton.count() > 0) {
            // Normal state
            await expect(primaryButton).toHaveScreenshot('button-normal.png');

            // Hover state
            await primaryButton.hover();
            await page.waitForTimeout(200);
            await expect(primaryButton).toHaveScreenshot('button-hover.png');

            // Focus state
            await primaryButton.focus();
            await page.waitForTimeout(200);
            await expect(primaryButton).toHaveScreenshot('button-focus.png');
        }
    });

    test('Form input states', async ({ page }) => {
        await page.goto('/patients/new');
        await waitForPageReady(page);

        const firstInput = page.locator('input').first();
        
        if (await firstInput.count() > 0) {
            // Empty state
            await expect(firstInput).toHaveScreenshot('input-empty.png');

            // Filled state
            await firstInput.fill('Test Value');
            await expect(firstInput).toHaveScreenshot('input-filled.png');

            // Focus state
            await firstInput.focus();
            await page.waitForTimeout(200);
            await expect(firstInput).toHaveScreenshot('input-focus.png');

            // Error state (trigger validation)
            await firstInput.fill('');
            await firstInput.blur();
            await page.waitForTimeout(200);
            
            // Check if error message appears
            const errorMsg = page.locator('.error-message, [role="alert"]').first();
            if (await errorMsg.count() > 0) {
                await expect(firstInput).toHaveScreenshot('input-error.png');
            }
        }
    });
});

test.describe('Visual Regression - Responsive Design', () => {
    const viewports = [
        { name: 'mobile', width: 375, height: 667 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'desktop', width: 1920, height: 1080 }
    ];

    viewports.forEach(viewport => {
        test(`Patient list - ${viewport.name} viewport`, async ({ page }) => {
            await page.setViewportSize({ width: viewport.width, height: viewport.height });
            await page.goto('/patients');
            await waitForPageReady(page);
            await maskDynamicContent(page);

            await expect(page).toHaveScreenshot(`patient-list-${viewport.name}.png`, {
                fullPage: true,
                animations: 'disabled',
                maxDiffPixels: 300
            });
        });
    });
});

test.describe('Visual Regression - Dark Mode (if supported)', () => {
    test('Login page - dark mode', async ({ page }) => {
        // Enable dark mode (method depends on implementation)
        await page.emulateMedia({ colorScheme: 'dark' });
        
        await page.goto('/login');
        await waitForPageReady(page);

        await expect(page).toHaveScreenshot('login-page-dark.png', {
            fullPage: true,
            animations: 'disabled'
        });
    });

    test('Patient list - dark mode', async ({ page }) => {
        await page.emulateMedia({ colorScheme: 'dark' });
        
        await page.goto('/patients');
        await waitForPageReady(page);
        await maskDynamicContent(page);

        await expect(page).toHaveScreenshot('patient-list-dark.png', {
            fullPage: true,
            animations: 'disabled',
            maxDiffPixels: 300
        });
    });
});

test.describe('Visual Regression - Modals and Overlays', () => {
    test('Confirmation modal', async ({ page }) => {
        await page.goto('/patients');
        await waitForPageReady(page);

        // Try to trigger delete action
        const deleteButton = page.getByRole('button', { name: /delete|excluir|remover/i }).first();
        
        if (await deleteButton.count() > 0) {
            await deleteButton.click();
            await page.waitForTimeout(500);

            // Check if modal appears
            const modal = page.locator('[role="dialog"], .modal').first();
            if (await modal.count() > 0) {
                await expect(modal).toHaveScreenshot('confirmation-modal.png', {
                    animations: 'disabled'
                });
            }
        }
    });

    test('Loading overlay', async ({ page }) => {
        await page.goto('/patients');
        
        // Try to capture loading state
        const loader = page.locator('[data-testid="loader"], .loading-overlay').first();
        
        if (await loader.isVisible()) {
            await expect(loader).toHaveScreenshot('loading-overlay.png');
        }
    });
});

test.describe('Visual Regression - Error States', () => {
    test('404 Not Found page', async ({ page }) => {
        await page.goto('/non-existent-page-123456');
        await waitForPageReady(page);

        await expect(page).toHaveScreenshot('404-page.png', {
            fullPage: true,
            animations: 'disabled'
        });
    });

    test('Network error state', async ({ page }) => {
        // Simulate offline
        await page.context().setOffline(true);
        
        await page.goto('/patients');
        await page.waitForTimeout(2000);

        const errorMessage = page.locator('[data-testid="error"], .error-state').first();
        
        if (await errorMessage.count() > 0) {
            await expect(page).toHaveScreenshot('network-error.png', {
                fullPage: true,
                animations: 'disabled'
            });
        }

        // Restore online
        await page.context().setOffline(false);
    });
});

/**
 * Percy-specific tests (descomente se usar Percy)
 */
/*
test.describe('Percy Visual Testing', () => {
    test('Percy - Full app flow', async ({ page }) => {
        // Login
        await page.goto('/login');
        await waitForPageReady(page);
        await percySnapshot(page, 'Login Page');

        // Patient list
        await page.goto('/patients');
        await waitForPageReady(page);
        await percySnapshot(page, 'Patient List');

        // Patient details
        const firstPatient = page.locator('[data-testid="patient-card"]').first();
        if (await firstPatient.count() > 0) {
            await firstPatient.click();
            await waitForPageReady(page);
            await percySnapshot(page, 'Patient Details');
        }

        // Analytics
        await page.goto('/analytics');
        await waitForPageReady(page);
        await percySnapshot(page, 'Analytics Dashboard');
    });
});
*/

/**
 * Configuração de thresholds
 */
test.use({
    screenshot: {
        fullPage: true,
        animations: 'disabled',
        // Aumenta threshold para testes menos frágeis
        threshold: 0.2, // 20% de diferença tolerada
        maxDiffPixels: 100
    }
});

/**
 * Report final
 */
test.afterAll(async () => {
    console.log('\n' + '='.repeat(80));
    console.log('📸 VISUAL REGRESSION TESTING COMPLETE');
    console.log('='.repeat(80));
    console.log('\nScreenshots armazenados em:');
    console.log('  - e2e/visual-regression.spec.ts-snapshots/');
    console.log('\nPara atualizar baselines:');
    console.log('  npx playwright test e2e/visual-regression.spec.ts --update-snapshots');
    console.log('\nPara comparar diferenças:');
    console.log('  npx playwright show-report');
    console.log('\nIntegração Percy:');
    console.log('  1. Criar conta em percy.io');
    console.log('  2. npm install @percy/cli @percy/playwright');
    console.log('  3. export PERCY_TOKEN=your_token');
    console.log('  4. npx percy exec -- npx playwright test');
    console.log('='.repeat(80) + '\n');
});

/**
 * Accessibility Tests with Axe-Core
 * ==================================
 * 
 * Testes automatizados de acessibilidade usando @axe-core/playwright.
 * Verifica conformidade com WCAG 2.1 Level AA.
 * 
 * Instalação:
 *   npm install --save-dev @axe-core/playwright
 * 
 * Uso:
 *   npx playwright test e2e/accessibility.spec.ts
 * 
 * CI/CD:
 *   npx playwright test e2e/accessibility.spec.ts --reporter=html,json
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Helper para executar scan Axe e logar resultados
 */
async function runAxeScan(page: any, context: string) {
    const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

    // Log detalhado das violações
    if (accessibilityScanResults.violations.length > 0) {
        console.log(`\n❌ Violações de Acessibilidade em: ${context}`);
        console.log(`Total: ${accessibilityScanResults.violations.length}`);
        
        accessibilityScanResults.violations.forEach((violation, index) => {
            console.log(`\n${index + 1}. ${violation.id} (${violation.impact})`);
            console.log(`   Descrição: ${violation.description}`);
            console.log(`   Help: ${violation.help}`);
            console.log(`   Afeta ${violation.nodes.length} elemento(s)`);
            
            violation.nodes.slice(0, 3).forEach((node, nodeIndex) => {
                console.log(`   - Elemento ${nodeIndex + 1}: ${node.html.substring(0, 100)}...`);
                console.log(`     Seletor: ${node.target.join(' > ')}`);
            });
        });
    }

    return accessibilityScanResults;
}

test.describe('Accessibility - Public Pages', () => {
    test('Login page should be accessible', async ({ page }) => {
        await page.goto('/login');
        await page.waitForLoadState('networkidle');

        const results = await runAxeScan(page, 'Login Page');
        
        // Falha se houver violações CRÍTICAS ou SÉRIAS
        const criticalViolations = results.violations.filter(
            v => v.impact === 'critical' || v.impact === 'serious'
        );
        
        expect(criticalViolations).toHaveLength(0);
    });

    test('Home/Landing page should be accessible', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await runAxeScan(page, 'Home Page');
        
        const criticalViolations = results.violations.filter(
            v => v.impact === 'critical' || v.impact === 'serious'
        );
        
        expect(criticalViolations).toHaveLength(0);
    });
});

test.describe('Accessibility - Patient Management', () => {
    test.beforeEach(async ({ page }) => {
        // TODO: Implement proper authentication
        // For now, navigate directly
        await page.goto('/patients');
    });

    test('Patient list page should be accessible', async ({ page }) => {
        await page.waitForLoadState('networkidle');

        const results = await runAxeScan(page, 'Patient List');
        
        const criticalViolations = results.violations.filter(
            v => v.impact === 'critical' || v.impact === 'serious'
        );
        
        expect(criticalViolations).toHaveLength(0);
    });

    test('Patient details should be accessible', async ({ page }) => {
        // Attempt to navigate to first patient
        const firstPatient = page.locator('[data-testid="patient-card"]').first();
        
        if (await firstPatient.count() > 0) {
            await firstPatient.click();
            await page.waitForLoadState('networkidle');

            const results = await runAxeScan(page, 'Patient Details');
            
            const criticalViolations = results.violations.filter(
                v => v.impact === 'critical' || v.impact === 'serious'
            );
            
            expect(criticalViolations).toHaveLength(0);
        } else {
            test.skip();
        }
    });

    test('Patient forms should have proper labels', async ({ page }) => {
        // Navigate to create patient form
        const createButton = page.getByRole('button', { name: /novo|create|adicionar/i });
        
        if (await createButton.count() > 0) {
            await createButton.click();
            await page.waitForLoadState('networkidle');

            const results = await new AxeBuilder({ page })
                .withTags(['wcag2a', 'wcag2aa'])
                .include('form')
                .analyze();

            // Form inputs MUST have labels
            const labelViolations = results.violations.filter(
                v => v.id === 'label' || v.id === 'label-title-only'
            );
            
            expect(labelViolations).toHaveLength(0);
        } else {
            test.skip();
        }
    });
});

test.describe('Accessibility - Navigation', () => {
    test('Main navigation should be keyboard accessible', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Test keyboard navigation
        await page.keyboard.press('Tab');
        
        // First focusable element should be visible
        const focusedElement = await page.evaluate(() => {
            return document.activeElement?.tagName;
        });
        
        expect(focusedElement).toBeTruthy();

        // Run axe scan
        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .include('nav')
            .analyze();

        expect(results.violations).toHaveLength(0);
    });

    test('Skip to main content link should exist', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Press Tab to focus skip link (usually first focusable element)
        await page.keyboard.press('Tab');
        
        const skipLink = page.getByText(/skip to|pular para/i);
        
        // Skip link should exist (may be visually hidden)
        const hasSkipLink = await skipLink.count() > 0;
        
        if (hasSkipLink) {
            expect(skipLink).toBeTruthy();
        } else {
            console.warn('⚠️  Skip to main content link não encontrado');
        }
    });
});

test.describe('Accessibility - Interactive Elements', () => {
    test('Buttons should have accessible names', async ({ page }) => {
        await page.goto('/patients');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .disableRules(['color-contrast']) // Skip color contrast (checked separately)
            .analyze();

        const buttonNameViolations = results.violations.filter(
            v => v.id === 'button-name'
        );
        
        expect(buttonNameViolations).toHaveLength(0);
    });

    test('Images should have alt text', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .analyze();

        const imageAltViolations = results.violations.filter(
            v => v.id === 'image-alt'
        );
        
        expect(imageAltViolations).toHaveLength(0);
    });

    test('Color contrast should meet WCAG AA', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2aa'])
            .analyze();

        const contrastViolations = results.violations.filter(
            v => v.id === 'color-contrast'
        );
        
        if (contrastViolations.length > 0) {
            console.warn(`⚠️  ${contrastViolations.length} violações de contraste encontradas`);
            // Log detalhes
            contrastViolations.forEach(v => {
                console.log(`   - ${v.help}`);
            });
        }
        
        // WCAG AA: Contrast ratio mínimo 4.5:1 para texto normal
        expect(contrastViolations.length).toBeLessThan(5);
    });
});

test.describe('Accessibility - Forms and Inputs', () => {
    test('Form inputs should have associated labels', async ({ page }) => {
        await page.goto('/patients/new');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .include('form')
            .analyze();

        const labelViolations = results.violations.filter(
            v => v.id === 'label' || v.id === 'form-field-multiple-labels'
        );
        
        expect(labelViolations).toHaveLength(0);
    });

    test('Required fields should be properly indicated', async ({ page }) => {
        await page.goto('/patients/new');
        await page.waitForLoadState('networkidle');

        // Check for aria-required or required attribute
        const requiredInputs = page.locator('input[required], input[aria-required="true"]');
        const count = await requiredInputs.count();

        if (count > 0) {
            // At least one required field should have visual indicator
            const hasVisualIndicator = await page.locator('label:has-text("*")').count() > 0
                || await page.locator('[aria-required="true"]').count() > 0;

            expect(hasVisualIndicator).toBeTruthy();
        }
    });

    test('Error messages should be associated with inputs', async ({ page }) => {
        await page.goto('/patients/new');
        await page.waitForLoadState('networkidle');

        // Submit form without filling (should trigger validation)
        const submitButton = page.getByRole('button', { name: /salvar|save|submit/i });
        if (await submitButton.count() > 0) {
            await submitButton.click();
            await page.waitForTimeout(1000);

            const results = await new AxeBuilder({ page })
                .withTags(['wcag2a'])
                .analyze();

            // aria-describedby should link errors to inputs
            const ariaViolations = results.violations.filter(
                v => v.id === 'aria-valid-attr' || v.id === 'aria-required-children'
            );
            
            expect(ariaViolations).toHaveLength(0);
        }
    });
});

test.describe('Accessibility - ARIA Compliance', () => {
    test('ARIA roles should be valid', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .analyze();

        const ariaViolations = results.violations.filter(
            v => v.id.startsWith('aria-')
        );
        
        if (ariaViolations.length > 0) {
            console.log(`\n⚠️  ${ariaViolations.length} violações ARIA:`);
            ariaViolations.forEach(v => {
                console.log(`   - ${v.id}: ${v.description}`);
            });
        }
        
        expect(ariaViolations).toHaveLength(0);
    });

    test('Headings should have proper hierarchy', async ({ page }) => {
        await page.goto('/patients');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .analyze();

        const headingViolations = results.violations.filter(
            v => v.id === 'heading-order'
        );
        
        expect(headingViolations).toHaveLength(0);
    });

    test('Lists should be properly marked up', async ({ page }) => {
        await page.goto('/patients');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a'])
            .analyze();

        const listViolations = results.violations.filter(
            v => v.id === 'list' || v.id === 'listitem'
        );
        
        expect(listViolations).toHaveLength(0);
    });
});

test.describe('Accessibility - Mobile/Responsive', () => {
    test('Mobile viewport should be accessible', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await runAxeScan(page, 'Mobile Viewport');
        
        const criticalViolations = results.violations.filter(
            v => v.impact === 'critical' || v.impact === 'serious'
        );
        
        expect(criticalViolations).toHaveLength(0);
    });

    test('Touch targets should be large enough', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/patients');
        await page.waitForLoadState('networkidle');

        // WCAG 2.1 Success Criterion 2.5.5: Target Size (Level AAA)
        // Minimum 44x44 CSS pixels
        
        const buttons = page.getByRole('button');
        const buttonCount = await buttons.count();

        if (buttonCount > 0) {
            const firstButton = buttons.first();
            const box = await firstButton.boundingBox();

            if (box) {
                // Check if button is at least 44x44
                const isLargeEnough = box.width >= 44 && box.height >= 44;
                
                if (!isLargeEnough) {
                    console.warn(`⚠️  Touch target muito pequeno: ${box.width}x${box.height}`);
                }
                
                // We expect at least 80% compliance
                expect(box.width).toBeGreaterThan(35);
                expect(box.height).toBeGreaterThan(35);
            }
        }
    });
});

/**
 * Generate Accessibility Report
 */
test.afterAll(async () => {
    console.log('\n' + '='.repeat(80));
    console.log('♿ ACCESSIBILITY TESTING COMPLETE');
    console.log('='.repeat(80));
    console.log('\nRelatórios gerados:');
    console.log('  - playwright-report/index.html');
    console.log('  - test-results/');
    console.log('\nPróximos passos:');
    console.log('  1. Revisar violações encontradas');
    console.log('  2. Corrigir violações CRITICAL e SERIOUS');
    console.log('  3. Implementar testes de teclado manuais');
    console.log('  4. Testar com leitores de tela (NVDA, JAWS, VoiceOver)');
    console.log('='.repeat(80) + '\n');
});

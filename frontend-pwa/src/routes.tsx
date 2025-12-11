/**
 * Sprint 25: Lazy Loading Routes with Code Splitting
 * 
 * Uses React.lazy() for route-based code splitting to improve
 * initial load performance.
 */

import React, { Suspense, lazy, ComponentType } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { spacing } from './theme/colors';
import AppShell from './components/base/AppShell';

// Loading fallback component
const LoadingFallback: React.FC = () => (
    <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        minHeight: '400px'
    }}>
        <div style={{ textAlign: 'center' }}>
            <div className="loading-spinner" style={{
                width: '40px',
                height: '40px',
                border: '3px solid #e5e7eb',
                borderTop: '3px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 16px'
            }} />
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>Carregando...</p>
        </div>
    </div>
);

// Add CSS animation for spinner
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Wrapper for lazy loading with error boundary
 */
function lazyLoad<T extends ComponentType<any>>(
    importFn: () => Promise<{ default: T }>
): React.LazyExoticComponent<T> {
    return lazy(importFn);
}

// =============================================================================
// Lazy-loaded Components (Code Splitting)
// =============================================================================

// Auth
const Login = lazyLoad(() => import('./components/Login'));

// Core pages
const PatientList = lazyLoad(() => import('./components/PatientList'));
const PatientDetail = lazyLoad(() => import('./components/PatientDetail'));
const PatientForm = lazyLoad(() => import('./components/forms/PatientForm'));

// Workspaces
const ClinicalWorkspace = lazyLoad(() => import('./components/clinical/ClinicalWorkspace'));
const SchedulingWorkspace = lazyLoad(() => import('./components/scheduling/SchedulingWorkspace'));
const CheckInWorkspace = lazyLoad(() => import('./components/checkin/CheckInWorkspace'));
const FinancialWorkspace = lazyLoad(() => import('./components/financial/FinancialWorkspace'));
const ClinicalDocumentWorkspace = lazyLoad(() => import('./components/documents/ClinicalDocumentWorkspace'));
const VisitorsWorkspace = lazyLoad(() => import('./components/workspaces/VisitorsWorkspace'));
const ChatWorkspace = lazyLoad(() => import('./components/workspaces/ChatWorkspace'));
const BedManagementWorkspace = lazyLoad(() => import('./components/workspaces/BedManagementWorkspace'));
const PractitionerWorkspace = lazyLoad(() => import('./components/workspaces/PractitionerWorkspace'));

// These need named exports, handle differently
const PatientPortalWorkspace = lazyLoad(() =>
    import('./components/patient/PatientPortalWorkspace').then(m => ({ default: m.PatientPortalWorkspace }))
);
const DashboardWorkspace = lazyLoad(() =>
    import('./components/analytics/DashboardWorkspace').then(m => ({ default: m.DashboardWorkspace }))
);
const OrganizationWorkspace = lazyLoad(() =>
    import('./components/workspaces/OrganizationWorkspace').then(m => ({ default: m.OrganizationWorkspace }))
);
const SettingsWorkspace = lazyLoad(() =>
    import('./components/settings/SettingsWorkspace').then(m => ({ default: m.SettingsWorkspace }))
);

// LGPD Dashboard (Sprint 24)
const LGPDDashboard = lazyLoad(() =>
    import('./components/privacy/LGPDDashboard').then(m => ({ default: m.LGPDDashboardComponent }))
);

/**
 * Rotas protegidas (requerem autenticação)
 */
const ProtectedRoutes: React.FC = () => {
    return (
        <AppShell>
            <Suspense fallback={<LoadingFallback />}>
                <Routes>
                    <Route path="/" element={<DashboardWorkspace />} />
                    <Route path="/patients" element={<PatientList />} />
                    <Route path="/patients/new" element={<PatientForm />} />
                    <Route path="/patients/:id" element={<PatientDetail loading={false} error={undefined} />} />
                    <Route path="/patients/:id/encounter/new" element={<ClinicalWorkspace />} />
                    <Route path="/practitioners" element={<PractitionerWorkspace />} />
                    <Route path="/scheduling" element={<SchedulingWorkspace />} />
                    <Route path="/checkin" element={<CheckInWorkspace />} />
                    <Route path="/portal" element={<PatientPortalWorkspace />} />
                    <Route path="/finance" element={<FinancialWorkspace />} />
                    <Route path="/documents" element={<ClinicalDocumentWorkspace />} />
                    <Route path="/visitors" element={<VisitorsWorkspace />} />
                    <Route path="/chat" element={<ChatWorkspace />} />
                    <Route path="/ipd" element={<BedManagementWorkspace />} />
                    <Route path="/organizations" element={<OrganizationWorkspace />} />
                    <Route path="/privacy" element={<LGPDDashboard />} />
                    <Route path="/profile" element={<SettingsWorkspace section="profile" />} />
                    <Route path="/settings/profile" element={<SettingsWorkspace section="profile" />} />
                    <Route path="/settings/security" element={<SettingsWorkspace section="security" />} />
                    <Route path="/settings/notifications" element={<SettingsWorkspace section="notifications" />} />
                    <Route path="/settings/preferences" element={<SettingsWorkspace section="preferences" />} />
                    <Route path="/help" element={<SettingsWorkspace section="profile" />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Suspense>
        </AppShell>
    );
};

/**
 * Componente principal de rotas com Lazy Loading
 */
export const AppRoutes: React.FC = () => {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', marginBottom: spacing.md }}>⟳</div>
                    <p>Carregando aplicação...</p>
                </div>
            </div>
        );
    }

    return (
        <Suspense fallback={<LoadingFallback />}>
            {isAuthenticated ? <ProtectedRoutes /> : <Login />}
        </Suspense>
    );
};

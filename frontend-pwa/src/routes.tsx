
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Login from './components/Login';
import PatientList from './components/PatientList';
import PatientDetail from './components/PatientDetail';
import PatientForm from './components/forms/PatientForm';
import ClinicalWorkspace from './components/clinical/ClinicalWorkspace';
import SchedulingWorkspace from './components/scheduling/SchedulingWorkspace';
import CheckInWorkspace from './components/checkin/CheckInWorkspace';
import { PatientPortalWorkspace } from './components/patient/PatientPortalWorkspace';
import FinancialWorkspace from './components/financial/FinancialWorkspace';
import ClinicalDocumentWorkspace from './components/documents/ClinicalDocumentWorkspace';
import { DashboardWorkspace } from './components/analytics/DashboardWorkspace';
import VisitorsWorkspace from './components/workspaces/VisitorsWorkspace';
import ChatWorkspace from './components/workspaces/ChatWorkspace';
import BedManagementWorkspace from './components/workspaces/BedManagementWorkspace';
import PractitionerWorkspace from './components/workspaces/PractitionerWorkspace';
import { OrganizationWorkspace } from './components/workspaces/OrganizationWorkspace';
import { SettingsWorkspace } from './components/settings/SettingsWorkspace';
import AppShell from './components/base/AppShell';
import { spacing } from './theme/colors';

/**
 * Rotas protegidas (requerem autenticação)
 */
const ProtectedRoutes: React.FC = () => {
    return (
        <AppShell>
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
                <Route path="/profile" element={<SettingsWorkspace section="profile" />} />
                <Route path="/settings/profile" element={<SettingsWorkspace section="profile" />} />
                <Route path="/settings/security" element={<SettingsWorkspace section="security" />} />
                <Route path="/settings/notifications" element={<SettingsWorkspace section="notifications" />} />
                <Route path="/settings/preferences" element={<SettingsWorkspace section="preferences" />} />
                <Route path="/help" element={<SettingsWorkspace section="profile" />} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </AppShell>
    );
};

/**
 * Componente principal de rotas
 * NOTA: BrowserRouter está em main.tsx, não duplicar aqui!
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

    return isAuthenticated ? <ProtectedRoutes /> : <Login />;
};

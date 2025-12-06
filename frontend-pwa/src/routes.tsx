
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
                <Route path="/scheduling" element={<SchedulingWorkspace />} />
                <Route path="/checkin" element={<CheckInWorkspace />} />
                <Route path="/portal" element={<PatientPortalWorkspace />} />
                <Route path="/finance" element={<FinancialWorkspace />} />
                <Route path="/documents" element={<ClinicalDocumentWorkspace />} />
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

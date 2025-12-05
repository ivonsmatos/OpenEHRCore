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
import Header from './components/base/Header';
import Button from './components/base/Button';
import { colors, spacing } from './theme/colors';

/**
 * Layout principal da aplicação (após login)
 */
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, logout, login } = useAuth();

    return (
        <div style={{ backgroundColor: colors.background.surface, minHeight: '100vh' }}>
            <Header
                title="OpenEHRCore - Sistema de Prontuários"
                subtitle={`Bem-vindo, ${user?.name || 'Usuário'}!`}
            >
                <div style={{ fontSize: '0.875rem', color: 'white', display: 'flex', alignItems: 'center', gap: spacing.md }}>
                    <span>👤 {user?.email}</span>
                    <span>🔖 {user?.roles?.join(', ') || 'sem role'}</span>

                    {/* Financeiro Link */}
                    <Button variant="ghost" size="sm"
                        style={{ color: 'white', border: '1px solid white' }}
                        onClick={() => window.location.href = '/finance'}>
                        Financeiro
                    </Button>

                    {/* Documents Link */}
                    <Button variant="ghost" size="sm"
                        style={{ color: 'white', border: '1px solid white' }}
                        onClick={() => window.location.href = '/documents'}>
                        Doc. Clínicos
                    </Button>

                    {/* Demo: Switch Context */}
                    <Button variant="ghost" size="sm"
                        style={{ color: 'white', border: '1px solid white' }}
                        onClick={() => login("patient-demo", "demo")}>
                        Acesso Paciente
                    </Button>

                    <Button variant="secondary" size="sm" onClick={logout}>
                        Sair
                    </Button>
                </div>
            </Header>

            <main style={{ maxWidth: '1200px', margin: '0 auto' }}>
                {children}
            </main>
        </div>
    );
};

/**
 * Rotas protegidas (requerem autenticação)
 */
const ProtectedRoutes: React.FC = () => {
    return (
        <MainLayout>
            <Routes>
                <Route path="/" element={<PatientList />} />
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
        </MainLayout>
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

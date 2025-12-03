import React, { useState } from "react";
import { AuthProvider, useAuth, ProtectedRoute, setupAxiosInterceptors } from "./hooks/useAuth";
import Login from "./components/Login";
import PatientDetail from "./components/PatientDetail";
import Header from "./components/base/Header";
import Button from "./components/base/Button";
import { colors, spacing } from "./theme/colors";

// Configurar interceptors do axios
setupAxiosInterceptors();

/**
 * Conteúdo principal (protegido por autenticação)
 */
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [currentPatientId, setCurrentPatientId] = useState<string | null>(null);

  return (
    <div style={{ backgroundColor: colors.background.surface, minHeight: "100vh" }}>
      <Header
        title="OpenEHRCore - Painel de Controle"
        subtitle={`Bem-vindo, ${user?.name || "Usuário"}!`}
      >
        <div style={{ fontSize: "0.875rem", color: "white" }}>
          <span style={{ marginRight: spacing.md }}>👤 {user?.email}</span>
          <span style={{ marginRight: spacing.md }}>
            🔖 {user?.roles?.join(", ") || "sem role"}
          </span>
          <Button variant="secondary" size="sm" onClick={logout}>
            Sair
          </Button>
        </div>
      </Header>

      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: spacing.xl }}>
        <PatientDetail loading={false} error={undefined} />
      </main>
    </div>
  );
};

/**
 * Componente App com roteamento
 * Implementação simples sem react-router (adicione depois se necessário)
 */
const AppContent = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: spacing.md }}>⟳</div>
          <p>Carregando aplicação...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <Dashboard /> : <Login />;
};

/**
 * App com Provider de Autenticação
 */
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;

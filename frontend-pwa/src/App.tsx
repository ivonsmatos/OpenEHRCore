import { AuthProvider, setupAxiosInterceptors } from "./hooks/useAuth";
import { AppRoutes } from "./routes";
import ErrorBoundary from "./components/base/ErrorBoundary";

// Configurar interceptors do axios
setupAxiosInterceptors();

/**
 * App com Provider de Autenticação, ErrorBoundary global e Rotas
 */
function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;


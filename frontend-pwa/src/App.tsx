import { AuthProvider, setupAxiosInterceptors } from "./hooks/useAuth";
import { AppRoutes } from "./routes";
import ErrorBoundary from "./components/base/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import "./styles/theme.css";

// Configurar interceptors do axios
setupAxiosInterceptors();

/**
 * App com Provider de Autenticação, ErrorBoundary global, Dark Mode e Rotas
 */
function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;

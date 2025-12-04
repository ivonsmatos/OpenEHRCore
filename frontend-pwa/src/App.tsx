import { AuthProvider, setupAxiosInterceptors } from "./hooks/useAuth";
import { AppRoutes } from "./routes";

// Configurar interceptors do axios
setupAxiosInterceptors();

/**
 * App com Provider de Autenticação e Rotas
 */
function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;

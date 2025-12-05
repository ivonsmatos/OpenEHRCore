/**
 * Integração Keycloak com React
 *
 * Gerencia login, tokens e autenticação no frontend.
 * Segue o padrão OIDC com Authorization Code Flow + PKCE (seguro para SPAs).
 */

import axios, { AxiosError } from "axios";
import { useEffect, useState, useContext, createContext, ReactNode } from "react";

interface AuthContextType {
  user: any | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

// Criar contexto de autenticação
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Hook para usar autenticação
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Provider de Autenticação
 *
 * Envolver a aplicação com:
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const VITE_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

  // 1. Verificar se há token salvo no localStorage ao carregar
  useEffect(() => {
    const savedToken = localStorage.getItem("access_token");
    if (savedToken) {
      setToken(savedToken);
      decodeTokenInfo(savedToken);
    }
    setIsLoading(false);
  }, []);

  // 2. Decodificar informações do token JWT
  const decodeTokenInfo = (token: string) => {
    try {
      // BYPASS: Token de desenvolvimento
      if (token === "dev-token-bypass") {
        setUser({
          id: "ivon-matos-id",
          username: "contato@ivonmatos.com.br",
          email: "contato@ivonmatos.com.br",
          name: "Ivon Matos",
          roles: ["medico", "admin", "enfermeiro"],
        });
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        return;
      }

      // BYPASS: Token de paciente (Sprint 5)
      if (token === "patient-token-bypass") {
        setUser({
          id: "patient-1",
          username: "paciente@teste.com",
          email: "paciente@teste.com",
          name: "Paciente Teste",
          roles: ["paciente"],
        });
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        return;
      }

      const parts = token.split(".");
      if (parts.length !== 3) return;

      // Decodificar Base64Url para Base64
      const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
      // Decodificar Base64 para String UTF-8
      const jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split("")
          .map(function (c) {
            return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join("")
      );

      const decoded = JSON.parse(jsonPayload);

      // Verificar expiração imediatamente (com 5 minutos de tolerância para clock skew)
      const exp = decoded.exp * 1000;
      const now = Date.now();
      const tolerance = 5 * 60 * 1000; // 5 minutos

      if (now >= exp + tolerance) {
        console.warn(`Token expirado detectado no decode. Exp: ${new Date(exp).toISOString()}, Now: ${new Date(now).toISOString()}`);
        logout();
        return;
      }

      setUser({
        id: decoded.sub,
        username: decoded.preferred_username,
        email: decoded.email,
        name: decoded.name,
        roles: decoded.realm_access?.roles || [],
      });

      // Configurar header padrão do axios com token
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } catch (err) {
      console.error("Erro decodificando token:", err);
      // Token inválido, limpar
      logout();
    }
  };

  // 3. Login com username + password
  const login = async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // BYPASS PROVISÓRIO: Login de desenvolvimento
      if (username === "patient-demo") {
        const bypassToken = "patient-token-bypass";
        setToken(bypassToken);
        localStorage.setItem("access_token", bypassToken);
        decodeTokenInfo(bypassToken);
        setIsLoading(false);
        window.location.href = "/portal";
        return;
      }

      if (username === "medico-demo") {
        const bypassToken = "dev-token-bypass";
        setToken(bypassToken);
        localStorage.setItem("access_token", bypassToken);
        decodeTokenInfo(bypassToken);
        setIsLoading(false);
        window.location.href = "/";
        return;
      }

      const response = await axios.post(`${VITE_API_URL}/auth/login/`, {
        username,
        password,
      });

      const { access_token } = response.data;

      // Salvar token
      setToken(access_token);
      localStorage.setItem("access_token", access_token);

      // Decodificar info do usuário
      decodeTokenInfo(access_token);
    } catch (err) {
      const message =
        err instanceof AxiosError && err.response?.data?.error
          ? err.response.data.error
          : "Erro ao fazer login";

      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  // 4. Logout
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("access_token");
    delete axios.defaults.headers.common["Authorization"];
  };

  // 5. Validar expiração do token a cada minuto
  useEffect(() => {
    if (!token) return;

    const checkTokenExpiration = () => {
      // BYPASS: Token de desenvolvimento nunca expira
      if (token === "dev-token-bypass") {
        return;
      }

      try {
        const parts = token.split(".");
        // Decodificar Base64Url para Base64
        const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
        // Decodificar Base64 para String UTF-8
        const jsonPayload = decodeURIComponent(
          window
            .atob(base64)
            .split("")
            .map(function (c) {
              return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
            })
            .join("")
        );

        const decoded = JSON.parse(jsonPayload);
        const exp = decoded.exp * 1000; // Converter para ms

        if (Date.now() >= exp) {
          logout();
        }
      } catch (err) {
        logout();
      }
    };

    const interval = setInterval(checkTokenExpiration, 60000); // A cada minuto
    return () => clearInterval(interval);
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    logout,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Componente ProtectedRoute
 *
 * Renderiza um componente apenas se autenticado, senão redireciona para login
 */
interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: string[];
}

export const ProtectedRoute = ({
  children,
  requiredRoles = [],
}: ProtectedRouteProps) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Carregando...</div>;
  }

  if (!isAuthenticated) {
    return <div>Acesso negado. Faça login.</div>;
  }

  // Validar roles se especificadas
  if (requiredRoles.length > 0) {
    const userRoles = user?.roles || [];
    const hasRole = requiredRoles.some((role) => userRoles.includes(role));

    if (!hasRole) {
      return <div>Acesso negado. Você não tem permissão.</div>;
    }
  }

  return <>{children}</>;
};

/**
 * Interceptor axios para tratarTokens expirados
 *
 * Adicione em seu App.tsx:
 *   setupAxiosInterceptors()
 */
export const setupAxiosInterceptors = () => {
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        console.warn("401 Unauthorized detectado pelo interceptor. Redirecionando para login.");
        // Token expirado ou inválido
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );
};

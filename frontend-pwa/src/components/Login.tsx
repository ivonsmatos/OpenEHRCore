import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Button from "./base/Button";
import Card from "./base/Card";
import "./Login.css";

/**
 * Tela de Login
 *
 * Autenticação com Keycloak via API Django
 * Sprint 29: Refatorado para usar CSS classes ao invés de inline styles
 */
export const Login: React.FC = () => {
  const [email, setEmail] = useState("contato@ivonmatos.com.br");
  const [password, setPassword] = useState("Protonsysdba@1986");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao fazer login"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Card padding="lg" elevation="base" className="login-card">
        {/* Header */}
        <div className="login-header">
          <div className="login-logo">🏥</div>
          <h1 className="login-title">OpenEHRCore</h1>
          <p className="login-subtitle">Sistema de Prontuários Eletrônicos</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          {/* Email Field */}
          <div className="login-field">
            <label htmlFor="email" className="login-label">
              Email ou Usuário
            </label>
            <input
              id="email"
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="contato@ivonmatos.com.br"
              className="login-input"
              autoComplete="username"
            />
          </div>

          {/* Password Field */}
          <div className="login-field">
            <label htmlFor="password" className="login-label">
              Senha
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="login-input"
              autoComplete="current-password"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="login-error" role="alert">
              <span className="login-error__icon">⚠️</span>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <Button
            variant="primary"
            size="lg"
            isLoading={isLoading}
            onClick={() => { }}
            type="submit"
          >
            {isLoading ? "Entrando..." : "Entrar"}
          </Button>
        </form>

        {/* Demo Info */}
        <div className="login-demo">
          <strong>Credenciais de Acesso:</strong>
          Email: <code>contato@ivonmatos.com.br</code>
          <br />
          Senha: <code>Protonsysdba@1986</code>
        </div>

        {/* Help Link */}
        <div className="login-help">
          <a href="#">Esqueceu sua senha?</a>
        </div>
      </Card>
    </div>
  );
};

export default Login;

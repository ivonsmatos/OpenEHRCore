import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { colors, spacing, borderRadius } from "../theme/colors";
import Button from "./base/Button";
import Card from "./base/Card";

/**
 * Tela de Login
 *
 * Autenticação com Keycloak via API Django
 */
export const Login: React.FC = () => {
  const [email, setEmail] = useState("medico@example.com");
  const [password, setPassword] = useState("senha123!@#");
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
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: colors.background.surface,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: spacing.lg,
      }}
    >
      {/* Container */}
      <Card
        padding="lg"
        elevation="base"
        className="w-full max-w-md"
        style={{
          maxWidth: "400px",
        }}
      >
        {/* Logo/Title */}
        <div
          style={{
            textAlign: "center",
            marginBottom: spacing.xl,
          }}
        >
          <div
            style={{
              fontSize: "2.5rem",
              marginBottom: spacing.md,
            }}
          >
            🏥
          </div>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: colors.primary.dark,
              margin: 0,
            }}
          >
            OpenEHRCore
          </h1>
          <p
            style={{
              fontSize: "0.875rem",
              color: colors.text.tertiary,
              margin: spacing.sm + " 0 0 0",
            }}
          >
            Sistema de Prontuários Eletrônicos
          </p>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
          {/* Email Field */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 600,
                color: colors.text.primary,
                marginBottom: "8px",
              }}
            >
              Email ou Usuário
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="medico@example.com"
              style={{
                width: "100%",
                padding: "12px",
                fontSize: "1rem",
                border: `1px solid ${colors.border.default}`,
                borderRadius: borderRadius.base,
                boxSizing: "border-box",
                fontFamily: "inherit",
                transition: `all 200ms ease-in-out`,
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = colors.primary.medium;
                e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary.light}40`;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = colors.border.default;
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Password Field */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 600,
                color: colors.text.primary,
                marginBottom: "8px",
              }}
            >
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="senha123!@#"
              style={{
                width: "100%",
                padding: "12px",
                fontSize: "1rem",
                border: `1px solid ${colors.border.default}`,
                borderRadius: borderRadius.base,
                boxSizing: "border-box",
                fontFamily: "inherit",
                transition: `all 200ms ease-in-out`,
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = colors.primary.medium;
                e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary.light}40`;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = colors.border.default;
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div
              style={{
                backgroundColor: `${colors.alert.critical}15`,
                border: `1px solid ${colors.alert.critical}`,
                color: colors.alert.critical,
                padding: spacing.md,
                borderRadius: borderRadius.base,
                fontSize: "0.875rem",
              }}
            >
              {error}
            </div>
          )}

          {/* Submit Button */}
          <Button
            variant="primary"
            size="lg"
            isLoading={isLoading}
            onClick={() => {}}
            type="submit"
          >
            {isLoading ? "Entrando..." : "Entrar"}
          </Button>
        </form>

        {/* Demo Info */}
        <div
          style={{
            marginTop: spacing.xl,
            padding: spacing.md,
            backgroundColor: colors.background.muted,
            borderRadius: borderRadius.base,
            fontSize: "0.75rem",
            color: colors.text.tertiary,
            lineHeight: "1.5rem",
          }}
        >
          <strong>Demo Credentials:</strong>
          <br />
          Email: <code>medico@example.com</code>
          <br />
          Senha: <code>senha123!@#</code>
        </div>

        {/* Help Link */}
        <div
          style={{
            marginTop: spacing.lg,
            textAlign: "center",
            fontSize: "0.875rem",
          }}
        >
          <a
            href="#"
            style={{
              color: colors.primary.medium,
              textDecoration: "none",
              fontWeight: 500,
            }}
          >
            Esqueceu sua senha?
          </a>
        </div>
      </Card>
    </div>
  );
};

export default Login;

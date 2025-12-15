import React, { useState, useEffect } from 'react';
import Card from '../base/Card';
import { colors, spacing } from '../../theme/colors';
import { Bot, AlertTriangle, CheckCircle } from 'lucide-react';

interface AICopilotProps {
  patientId?: string;
}

const AICopilot: React.FC<AICopilotProps> = ({ patientId }) => {
  const [summary, setSummary] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    if (!patientId) return;
    fetchSummary();
  }, [patientId]);

  const fetchSummary = async () => {
    if (!patientId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/ai/summary/${patientId}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-token-bypass'}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSummary(data.summary || 'Resumo não disponível');
      setOllamaStatus(data.using_ai ? 'online' : 'offline');
    } catch (err: any) {
      console.error('Erro ao buscar resumo:', err);
      setError(err.message || 'Não foi possível gerar o resumo clínico');
    } finally {
      setLoading(false);
    }
  };

  if (!patientId) return null;

  return (
    <Card
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        marginBottom: spacing.lg,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md }}>
        <Bot size={24} />
        <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>
          Resumo Inteligente (AI)
        </h3>
        {ollamaStatus === 'online' && (
          <span
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: spacing.xs,
              fontSize: '0.875rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              padding: `${spacing.xs} ${spacing.sm}`,
              borderRadius: '4px',
            }}
          >
            <CheckCircle size={16} />
            Ollama Ativo
          </span>
        )}
        {ollamaStatus === 'offline' && (
          <span
            style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: spacing.xs,
              fontSize: '0.875rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              padding: `${spacing.xs} ${spacing.sm}`,
              borderRadius: '4px',
            }}
          >
            <AlertTriangle size={16} />
            Modo Fallback
          </span>
        )}
      </div>

      {loading && (
        <div style={{ padding: spacing.md, textAlign: 'center' }}>
          <div className="spinner" style={{ borderColor: 'white', borderTopColor: 'transparent' }}></div>
          <p style={{ marginTop: spacing.sm }}>Gerando resumo clínico...</p>
        </div>
      )}

      {error && (
        <div
          style={{
            padding: spacing.md,
            backgroundColor: 'rgba(255, 0, 0, 0.1)',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.3)',
          }}
        >
          <AlertTriangle size={20} style={{ marginRight: spacing.sm, verticalAlign: 'middle' }} />
          {error}
        </div>
      )}

      {!loading && !error && summary && (
        <div
          style={{
            padding: spacing.md,
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            borderRadius: '8px',
            lineHeight: '1.6',
            whiteSpace: 'pre-wrap',
            maxHeight: '400px',
            overflowY: 'auto',
          }}
        >
          {summary.includes('#') ? (
            // Markdown format
            <div dangerouslySetInnerHTML={{ __html: renderMarkdown(summary) }} />
          ) : (
            // Plain text from AI
            <p style={{ margin: 0 }}>{summary}</p>
          )}
        </div>
      )}

      {ollamaStatus === 'offline' && !loading && summary && (
        <div
          style={{
            marginTop: spacing.md,
            padding: spacing.sm,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: spacing.xs,
          }}
        >
          <AlertTriangle size={16} />
          Ollama não detectado. Para ativar IA:
          <a
            href="https://ollama.ai/download"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'white', textDecoration: 'underline', marginLeft: spacing.xs }}
          >
            Instalar Ollama
          </a>
          → Execute: <code style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '2px 6px', borderRadius: '4px' }}>ollama pull mistral</code>
        </div>
      )}
    </Card>
  );
};

// Simple markdown renderer for structured summary
function renderMarkdown(text: string): string {
  return text
    .replace(/### (.*?)\n/g, '<h4 style="margin-top: 16px; font-weight: 600;">$1</h4>')
    .replace(/## (.*?)\n/g, '<h3 style="margin-top: 16px; font-weight: 600; font-size: 1.1rem;">$1</h3>')
    .replace(/# (.*?)\n/g, '<h2 style="margin-top: 16px; font-weight: 700; font-size: 1.25rem;">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/- (.*?)\n/g, '<li style="margin-left: 20px;">$1</li>')
    .replace(/\n/g, '<br />');
}

export default AICopilot;

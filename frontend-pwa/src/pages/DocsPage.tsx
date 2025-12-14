/**
 * Componente de Renderização de Documentação
 * 
 * Renderiza arquivos markdown com syntax highlighting,
 * tabelas, e componentes customizados
 */

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  ChevronRight,
  Copy,
  Check,
  ExternalLink,
  FileText
} from 'lucide-react';
import '../styles/docs.css';

interface DocsPageProps {
  markdownContent?: string;
  filePath?: string;
}

const DocsPage: React.FC<DocsPageProps> = ({ markdownContent, filePath }) => {
  const { category, page } = useParams<{ category?: string; page?: string }>();
  const [content, setContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    if (markdownContent) {
      setContent(markdownContent);
      setIsLoading(false);
      return;
    }

    // Mapear rotas para arquivos markdown
    const getMarkdownPath = (): string => {
      if (filePath) return filePath;

      // Mapeamento de rotas para arquivos
      const routeMap: Record<string, string> = {
        // Começando
        'intro': '/docs/INDEX.md',
        'setup': '/docs/SETUP.md',
        'architecture': '/docs/ARCHITECTURE.md',
        
        // Autenticação
        'auth/keycloak': '/docs/KEYCLOAK_SETUP.md',
        'auth/rbac': '/docs/ARCHITECTURE.md#segurança',
        'auth/tokens': '/docs/ARCHITECTURE.md#autenticação',
        
        // Implementação
        'implementation/responsive': '/docs/implementacao/RESPONSIVIDADE_IMPLEMENTADA.md',
        'implementation/improvements': '/frontend-pwa/MELHORIAS_APLICADAS.md',
        'implementation/design-system': '/docs/DESIGN_SYSTEM.md',
        
        // Pacientes
        'patients/registration': '/docs/WORKFLOWS.md#1-cadastro-de-paciente',
        'patients/ehr': '/docs/WORKFLOWS.md#4-atendimento-clínico-encounter',
        'patients/soap': '/docs/WORKFLOWS.md#5-soap-note',
        
        // Testes
        'testing/guide': '/docs/testes/TESTING_GUIDE.md',
        'testing/playwright': '/docs/testes/PLAYWRIGHT_DEMO.md',
        
        // Segurança
        'security/audit': '/docs/seguranca/SECURITY_AUDIT_REPORT.md',
        'security/devsecops': '/docs/seguranca/EXECUTIVE_SUMMARY_DEVSECOPS.md',
        
        // API
        'api/reference': '/docs/API.md',
        'api/fhir': '/docs/FHIR_IMPLEMENTATION_GUIDE.md',
        
        // FAQ
        'faq/troubleshooting': '/docs/FAQ.md#troubleshooting',
        'faq/performance': '/docs/FAQ.md#performance',
      };

      const routeKey = page ? `${category}/${page}` : category || 'intro';
      return routeMap[routeKey] || '/docs/INDEX.md';
    };

    const loadMarkdown = async () => {
      try {
        setIsLoading(true);
        const path = getMarkdownPath();
        const response = await fetch(path);
        
        if (!response.ok) {
          throw new Error(`Failed to load ${path}`);
        }
        
        const text = await response.text();
        setContent(text);
        setError(null);
      } catch (err) {
        console.error('Error loading markdown:', err);
        setError('Documento não encontrado. Verifique o caminho ou entre em contato com o suporte.');
        setContent('');
      } finally {
        setIsLoading(false);
      }
    };

    loadMarkdown();
  }, [category, page, markdownContent, filePath]);

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-[#0468BF] rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Carregando documentação...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Erro ao Carregar</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/docs"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#0468BF] text-white font-semibold rounded-lg hover:bg-[#0339A6] transition-colors"
          >
            <ChevronRight className="w-5 h-5 rotate-180" />
            Voltar ao Início
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="docs-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings com estilo customizado
          h1: ({ children }) => (
            <h1 className="text-4xl font-bold text-gray-900 mb-6 pb-4 border-b-2 border-gray-200">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-4 pb-2 border-b border-gray-200">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-2xl font-semibold text-gray-900 mt-8 mb-3">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-xl font-semibold text-gray-900 mt-6 mb-2">
              {children}
            </h4>
          ),

          // Parágrafos
          p: ({ children }) => (
            <p className="text-base text-gray-700 leading-relaxed mb-4">
              {children}
            </p>
          ),

          // Links
          a: ({ href, children }) => {
            const isExternal = href?.startsWith('http');
            return (
              <a
                href={href}
                className="text-[#0468BF] hover:text-[#0339A6] font-medium underline decoration-2 decoration-[#0468BF]/30 hover:decoration-[#0339A6] transition-colors inline-flex items-center gap-1"
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noopener noreferrer' : undefined}
              >
                {children}
                {isExternal && <ExternalLink className="w-3 h-3" />}
              </a>
            );
          },

          // Código inline
          code: ({ inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

            if (!inline && match) {
              return (
                <div className="relative group my-6">
                  <div className="flex items-center justify-between bg-gray-800 text-gray-100 px-4 py-2 rounded-t-lg text-sm font-mono">
                    <span className="text-gray-400">{match[1]}</span>
                    <button
                      onClick={() => copyToClipboard(codeString, codeId)}
                      className="flex items-center gap-2 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      {copiedCode === codeId ? (
                        <>
                          <Check className="w-4 h-4 text-green-400" />
                          <span className="text-green-400">Copiado!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>Copiar</span>
                        </>
                      )}
                    </button>
                  </div>
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    className="rounded-b-lg !mt-0"
                    {...props}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                </div>
              );
            }

            return (
              <code className="px-1.5 py-0.5 bg-gray-100 text-[#0468BF] rounded font-mono text-sm border border-gray-200" {...props}>
                {children}
              </code>
            );
          },

          // Listas
          ul: ({ children }) => (
            <ul className="list-disc list-inside space-y-2 mb-4 text-gray-700">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-700">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="ml-4">{children}</li>
          ),

          // Tabelas
          table: ({ children }) => (
            <div className="overflow-x-auto my-6">
              <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-[#F2F2F2]">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200">
              {children}
            </td>
          ),

          // Blockquotes (Callouts)
          blockquote: ({ children }) => {
            const text = String(children);
            let icon = <Info className="w-5 h-5" />;
            let bgColor = 'bg-blue-50';
            let borderColor = 'border-blue-200';
            let textColor = 'text-blue-800';
            let iconColor = 'text-blue-500';

            if (text.includes('⚠️') || text.includes('Warning')) {
              icon = <AlertTriangle className="w-5 h-5" />;
              bgColor = 'bg-yellow-50';
              borderColor = 'border-yellow-200';
              textColor = 'text-yellow-800';
              iconColor = 'text-yellow-500';
            } else if (text.includes('✅') || text.includes('Success')) {
              icon = <CheckCircle className="w-5 h-5" />;
              bgColor = 'bg-green-50';
              borderColor = 'border-green-200';
              textColor = 'text-green-800';
              iconColor = 'text-green-500';
            } else if (text.includes('❌') || text.includes('Error')) {
              icon = <AlertCircle className="w-5 h-5" />;
              bgColor = 'bg-red-50';
              borderColor = 'border-red-200';
              textColor = 'text-red-800';
              iconColor = 'text-red-500';
            }

            return (
              <div className={`${bgColor} border-l-4 ${borderColor} ${textColor} p-4 my-6 rounded-r-lg`}>
                <div className="flex gap-3">
                  <div className={iconColor}>{icon}</div>
                  <div className="flex-1">{children}</div>
                </div>
              </div>
            );
          },

          // Horizontal rule
          hr: () => (
            <hr className="my-8 border-t-2 border-gray-200" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>

      {/* Footer da página */}
      <div className="mt-16 pt-8 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>Última atualização: {new Date().toLocaleDateString('pt-BR')}</span>
          </div>
          <Link
            to="/docs"
            className="flex items-center gap-2 text-[#0468BF] hover:text-[#0339A6] font-medium"
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
            Voltar ao Índice
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DocsPage;

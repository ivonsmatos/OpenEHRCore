/**
 * Layout de Documentação Profissional
 * 
 * Design inspirado em Medplum Docs / GitBook
 * Usando nossa identidade visual institucional
 */

import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Menu, X, ChevronDown, ChevronRight, Home, Book, Shield, Users, FileText, HelpCircle } from 'lucide-react';

interface NavSection {
  title: string;
  icon: React.ElementType;
  items: NavItem[];
}

interface NavItem {
  title: string;
  path: string;
  badge?: string;
}

const navigationSections: NavSection[] = [
  {
    title: 'Começando',
    icon: Home,
    items: [
      { title: 'Introdução', path: '/docs/intro' },
      { title: 'Instalação Rápida', path: '/docs/setup', badge: 'Novo' },
      { title: 'Arquitetura', path: '/docs/architecture' },
    ]
  },
  {
    title: 'Autenticação',
    icon: Shield,
    items: [
      { title: 'Keycloak SSO', path: '/docs/auth/keycloak' },
      { title: 'Permissões RBAC', path: '/docs/auth/rbac' },
      { title: 'API Tokens', path: '/docs/auth/tokens' },
    ]
  },
  {
    title: 'Guias de Implementação',
    icon: Book,
    items: [
      { title: 'Responsividade', path: '/docs/implementation/responsive', badge: 'UX' },
      { title: 'Melhorias Aplicadas', path: '/docs/implementation/improvements' },
      { title: 'Design System', path: '/docs/implementation/design-system' },
    ]
  },
  {
    title: 'Gestão de Pacientes',
    icon: Users,
    items: [
      { title: 'Cadastro de Pacientes', path: '/docs/patients/registration' },
      { title: 'Prontuário Eletrônico', path: '/docs/patients/ehr' },
      { title: 'SOAP Note', path: '/docs/patients/soap' },
    ]
  },
  {
    title: 'Testes & Segurança',
    icon: FileText,
    items: [
      { title: 'Testing Guide', path: '/docs/testing/guide' },
      { title: 'Playwright E2E', path: '/docs/testing/playwright' },
      { title: 'Security Audit', path: '/docs/security/audit' },
      { title: 'DevSecOps', path: '/docs/security/devsecops' },
    ]
  },
  {
    title: 'FAQ Técnico',
    icon: HelpCircle,
    items: [
      { title: 'Troubleshooting', path: '/docs/faq/troubleshooting' },
      { title: 'Performance', path: '/docs/faq/performance' },
    ]
  },
];

const DocsLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['Começando']) // Primeira seção expandida por padrão
  );

  const toggleSection = (title: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(title)) {
        newSet.delete(title);
      } else {
        newSet.add(title);
      }
      return newSet;
    });
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header Mobile */}
      <div className="lg:hidden sticky top-0 z-50 bg-[#0339A6] text-white shadow-md">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Book className="w-5 h-5" />
            <h1 className="text-lg font-semibold">OpenEHR Docs</h1>
          </div>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-[#0468BF] rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            {isSidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`
            fixed lg:sticky top-0 left-0 h-screen
            w-[280px] bg-[#F2F2F2] border-r border-gray-200
            transition-transform duration-300 ease-in-out z-40
            ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            overflow-y-auto
          `}
        >
          {/* Logo/Header Desktop */}
          <div className="hidden lg:block p-6 border-b border-gray-300">
            <Link to="/docs" className="flex items-center gap-3 group">
              <div className="w-10 h-10 bg-[#0339A6] rounded-lg flex items-center justify-center">
                <Book className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#0339A6]">OpenEHR</h1>
                <p className="text-xs text-gray-600">Documentação</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="p-4 space-y-1">
            {navigationSections.map((section) => {
              const Icon = section.icon;
              const isExpanded = expandedSections.has(section.title);

              return (
                <div key={section.title}>
                  {/* Section Header */}
                  <button
                    onClick={() => toggleSection(section.title)}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-[#0468BF]" />
                      <span>{section.title}</span>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>

                  {/* Section Items */}
                  {isExpanded && (
                    <div className="ml-6 mt-1 space-y-1">
                      {section.items.map((item) => (
                        <Link
                          key={item.path}
                          to={item.path}
                          className="group flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:text-[#0468BF] hover:bg-gray-200 rounded-lg transition-colors"
                          onClick={() => setIsSidebarOpen(false)} // Fecha sidebar no mobile
                        >
                          <span className="group-hover:translate-x-1 transition-transform">
                            {item.title}
                          </span>
                          {item.badge && (
                            <span className="px-2 py-0.5 text-xs font-medium bg-[#0468BF] text-white rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Footer Sidebar */}
          <div className="p-4 mt-8 border-t border-gray-300">
            <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs font-semibold text-[#0339A6] mb-1">
                💡 Dica do Dia
              </p>
              <p className="text-xs text-gray-600">
                Use <code className="px-1 py-0.5 bg-gray-200 rounded text-[#0468BF]">Ctrl+K</code> para busca rápida
              </p>
            </div>
          </div>
        </aside>

        {/* Overlay Mobile */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="max-w-4xl mx-auto px-6 py-8 lg:px-12 lg:py-12">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DocsLayout;

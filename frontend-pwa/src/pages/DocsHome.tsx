/**
 * Página Principal do Portal de Documentação
 * 
 * Landing page com cards de navegação e busca rápida
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  Book,
  Shield,
  Users,
  FileText,
  Zap,
  Code,
  Sparkles,
  ArrowRight,
  Search,
  Star,
  TrendingUp
} from 'lucide-react';

interface QuickStartCard {
  title: string;
  description: string;
  icon: React.ElementType;
  link: string;
  color: string;
  badge?: string;
}

const quickStartCards: QuickStartCard[] = [
  {
    title: 'Início Rápido',
    description: 'Configure o ambiente em menos de 5 minutos',
    icon: Zap,
    link: '/docs/setup',
    color: 'bg-blue-500',
    badge: 'Popular'
  },
  {
    title: 'Autenticação SSO',
    description: 'Integre Keycloak e configure permissões RBAC',
    icon: Shield,
    link: '/docs/auth/keycloak',
    color: 'bg-green-500'
  },
  {
    title: 'Gestão de Pacientes',
    description: 'Cadastro, prontuário e SOAP Note',
    icon: Users,
    link: '/docs/patients/registration',
    color: 'bg-purple-500'
  },
  {
    title: 'Responsividade',
    description: 'Design mobile-first e UX moderna',
    icon: Sparkles,
    link: '/docs/implementation/responsive',
    color: 'bg-pink-500',
    badge: 'Novo'
  },
  {
    title: 'Testes Automatizados',
    description: 'Playwright E2E e unit tests com Vitest',
    icon: FileText,
    link: '/docs/testing/guide',
    color: 'bg-orange-500'
  },
  {
    title: 'API Reference',
    description: 'Endpoints FHIR e REST completos',
    icon: Code,
    link: '/docs/api/reference',
    color: 'bg-cyan-500'
  }
];

const DocsHome: React.FC = () => {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-6 py-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-full">
          <Star className="w-4 h-4 text-[#0468BF]" />
          <span className="text-sm font-medium text-[#0339A6]">
            v2.1.0 Mobile-First Update
          </span>
        </div>

        <h1 className="text-5xl font-bold text-gray-900 leading-tight">
          Documentação
          <span className="block text-[#0468BF]">OpenEHR Core</span>
        </h1>

        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Sistema de Prontuário Eletrônico completo, moderno e pronto para produção.
          Comece a desenvolver em menos de 1 hora.
        </p>

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar na documentação... (Ctrl+K)"
              className="w-full pl-12 pr-4 py-4 text-base border-2 border-gray-200 rounded-xl focus:border-[#0468BF] focus:outline-none focus:ring-2 focus:ring-[#0468BF] focus:ring-opacity-20 transition-all"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap justify-center gap-6 pt-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="font-semibold">Score 9.5/10</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <span className="font-semibold">100% Responsivo</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Shield className="w-4 h-4 text-purple-500" />
            <span className="font-semibold">WCAG 2.1 AA</span>
          </div>
        </div>
      </div>

      {/* Quick Start Cards */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          🚀 Início Rápido
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quickStartCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.link}
                to={card.link}
                className="group relative bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-[#0468BF] hover:shadow-lg transition-all duration-300"
              >
                {/* Badge */}
                {card.badge && (
                  <div className="absolute top-4 right-4">
                    <span className="px-2 py-1 text-xs font-semibold bg-[#0468BF] text-white rounded-full">
                      {card.badge}
                    </span>
                  </div>
                )}

                {/* Icon */}
                <div className={`w-12 h-12 ${card.color} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-[#0468BF] transition-colors">
                  {card.title}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {card.description}
                </p>

                {/* Arrow */}
                <div className="flex items-center gap-2 text-sm font-medium text-[#0468BF]">
                  <span>Saiba mais</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Featured Guides */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          📚 Guias em Destaque
        </h2>

        <div className="space-y-4">
          <Link
            to="/docs/implementation/responsive"
            className="flex items-center justify-between p-4 bg-white rounded-lg hover:shadow-md transition-shadow group"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-pink-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 group-hover:text-[#0468BF]">
                  Implementação de Responsividade
                </h3>
                <p className="text-sm text-gray-600">15+ páginas mobile-first</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-[#0468BF] group-hover:translate-x-1 transition-all" />
          </Link>

          <Link
            to="/docs/auth/keycloak"
            className="flex items-center justify-between p-4 bg-white rounded-lg hover:shadow-md transition-shadow group"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 group-hover:text-[#0468BF]">
                  Configuração Keycloak SSO
                </h3>
                <p className="text-sm text-gray-600">Autenticação enterprise-grade</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-[#0468BF] group-hover:translate-x-1 transition-all" />
          </Link>

          <Link
            to="/docs/testing/playwright"
            className="flex items-center justify-between p-4 bg-white rounded-lg hover:shadow-md transition-shadow group"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 group-hover:text-[#0468BF]">
                  Testes E2E com Playwright
                </h3>
                <p className="text-sm text-gray-600">Coverage completo</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-[#0468BF] group-hover:translate-x-1 transition-all" />
          </Link>
        </div>
      </div>

      {/* CTA Section */}
      <div className="text-center bg-[#0339A6] text-white rounded-2xl p-12">
        <Book className="w-12 h-12 mx-auto mb-4 opacity-80" />
        <h2 className="text-3xl font-bold mb-4">
          Pronto para começar?
        </h2>
        <p className="text-lg mb-8 opacity-90">
          Configure o ambiente completo em menos de 5 minutos
        </p>
        <Link
          to="/docs/setup"
          className="inline-flex items-center gap-2 px-8 py-4 bg-white text-[#0339A6] font-semibold rounded-xl hover:bg-gray-100 transition-colors shadow-lg"
        >
          <Zap className="w-5 h-5" />
          <span>Ver Guia de Instalação</span>
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
};

export default DocsHome;

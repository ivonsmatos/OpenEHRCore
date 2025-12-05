import React, { useState } from 'react';
import { CreditCard, FileText, User } from 'lucide-react';
import { Button } from '../base/Button';
import InvoiceList from './InvoiceList';
import CoverageList from './CoverageList';
import InvoiceForm from './InvoiceForm';
import CoverageForm from './CoverageForm';

const FinancialWorkspace: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'overview' | 'invoices' | 'coverage'>('overview');
    const [showForm, setShowForm] = useState(false);

    const handleTabChange = (tab: 'overview' | 'invoices' | 'coverage') => {
        setActiveTab(tab);
        setShowForm(false);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <Button
                        variant="secondary"
                        onClick={() => window.location.href = '/'}
                        className="mb-4"
                    >
                        ← Voltar para Dashboard
                    </Button>
                    <h1 className="text-2xl font-bold text-slate-900">Módulo Financeiro</h1>
                    <p className="text-slate-600">Gerenciamento de Faturas, Convênios e Contas</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-200">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => handleTabChange('overview')}
                        className={`${activeTab === 'overview'
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
                    >
                        <User size={18} />
                        Visão Geral
                    </button>
                    <button
                        onClick={() => handleTabChange('invoices')}
                        className={`${activeTab === 'invoices'
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
                    >
                        <FileText size={18} />
                        Faturas
                    </button>
                    <button
                        onClick={() => handleTabChange('coverage')}
                        className={`${activeTab === 'coverage'
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
                    >
                        <CreditCard size={18} />
                        Convênios
                    </button>
                </nav>
            </div>

            {/* Content */}
            <div className="mt-6">
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                            <h3 className="text-slate-500 text-sm font-medium">Saldo Devedor</h3>
                            <p className="text-3xl font-bold text-red-600 mt-2">R$ 450,00</p>
                            <p className="text-sm text-slate-400 mt-1">2 Faturas pendentes</p>
                        </div>
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                            <h3 className="text-slate-500 text-sm font-medium">Faturamento Total</h3>
                            <p className="text-3xl font-bold text-slate-900 mt-2">R$ 12.450,00</p>
                            <p className="text-sm text-slate-400 mt-1">Últimos 30 dias</p>
                        </div>
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                            <h3 className="text-slate-500 text-sm font-medium">Convênios Ativos</h3>
                            <p className="text-3xl font-bold text-emerald-600 mt-2">3</p>
                            <p className="text-sm text-slate-400 mt-1">Unimed, Bradesco</p>
                        </div>
                    </div>
                )}

                {activeTab === 'invoices' && (
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                        {!showForm ? (
                            <>
                                <div className="flex justify-between mb-4">
                                    <h3 className="text-lg font-medium text-slate-900">Suas Faturas</h3>
                                    <button
                                        onClick={() => setShowForm(true)}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                                    >
                                        Nova Fatura
                                    </button>
                                </div>
                                <InvoiceList />
                            </>
                        ) : (
                            <InvoiceForm
                                onSuccess={() => setShowForm(false)}
                                onCancel={() => setShowForm(false)}
                            />
                        )}
                    </div>
                )}

                {activeTab === 'coverage' && (
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                        {!showForm ? (
                            <>
                                <div className="flex justify-between mb-4">
                                    <h3 className="text-lg font-medium text-slate-900">Seus Convênios</h3>
                                    <button
                                        onClick={() => setShowForm(true)}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                                    >
                                        Adicionar Convênio
                                    </button>
                                </div>
                                <CoverageList />
                            </>
                        ) : (
                            <CoverageForm
                                onSuccess={() => setShowForm(false)}
                                onCancel={() => setShowForm(false)}
                            />
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FinancialWorkspace;

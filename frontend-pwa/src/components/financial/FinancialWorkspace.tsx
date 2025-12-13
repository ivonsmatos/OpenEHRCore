import React, { useState } from 'react';
import { CreditCard, FileText, User } from 'lucide-react';
import { Button } from '../base/Button';
import InvoiceList from './InvoiceList';
import CoverageList from './CoverageList';
import InvoiceForm from './InvoiceForm';
import CoverageForm from './CoverageForm';
import { FinancialDashboard } from './FinancialDashboard';

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
                        Dashboard Gerencial
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
                    <FinancialDashboard />
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

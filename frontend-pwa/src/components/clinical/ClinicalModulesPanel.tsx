/**
 * ClinicalModulesPanel - Painel de módulos clínicos com carregamento de dados
 * 
 * Renderiza os botões de módulos clínicos e abre modais/seções com dados reais:
 * - Vacinas (Immunization)
 * - Resultados de Exames (DiagnosticReport)
 * - Timeline Unificada (todos os eventos)
 * - Gráficos Vitais (Observation historical)
 * - Medicamentos (MedicationRequest)
 */

import React, { useState } from 'react';
import { useClinicalData } from '../../hooks/useClinicalData';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import {
    Syringe,
    FileText,
    Activity,
    BarChart3,
    Pill,
    X,
    Calendar,
    CheckCircle,
    AlertTriangle,
    Clock,
    ChevronRight
} from 'lucide-react';

interface ClinicalModulesPanelProps {
    patientId: string;
}

type ModuleType = 'vaccines' | 'exams' | 'timeline' | 'vitals' | 'medications' | null;

const ClinicalModulesPanel: React.FC<ClinicalModulesPanelProps> = ({ patientId }) => {
    const { token } = useAuth();
    const { data, loading, refresh } = useClinicalData(patientId, token);
    const [activeModule, setActiveModule] = useState<ModuleType>(null);

    const modules = [
        { id: 'vaccines' as const, label: 'Vacinas', icon: Syringe, color: '#ec4899', count: data.immunizations.length },
        { id: 'exams' as const, label: 'Resultados de Exames', icon: FileText, color: '#3b82f6', count: data.diagnosticResults.length },
        { id: 'timeline' as const, label: 'Timeline Unificada', icon: Activity, color: '#8b5cf6', count: data.timeline.length },
        { id: 'vitals' as const, label: 'Gráficos Vitais', icon: BarChart3, color: '#10b981', count: data.vitalSigns.length },
        { id: 'medications' as const, label: 'Medicamentos', icon: Pill, color: '#f59e0b', count: data.medications.filter(m => m.status === 'active').length },
    ];

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    };

    const renderModuleContent = () => {
        switch (activeModule) {
            case 'vaccines':
                return (
                    <div className="clinical-module-content">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <Syringe className="text-pink-500" size={20} />
                            Carteira de Vacinação
                        </h3>
                        {data.immunizations.length === 0 ? (
                            <p className="text-gray-500 italic">Nenhuma vacina registrada.</p>
                        ) : (
                            <div className="space-y-3">
                                {data.immunizations.map(imm => (
                                    <div key={imm.id} className="flex items-center justify-between p-3 bg-pink-50 rounded-lg border border-pink-100">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-pink-100 rounded-full">
                                                <Syringe size={16} className="text-pink-600" />
                                            </div>
                                            <div>
                                                <p className="font-medium">{imm.vaccineName}</p>
                                                <p className="text-sm text-gray-500 flex items-center gap-1">
                                                    <Calendar size={12} /> {formatDate(imm.date)}
                                                    {imm.lotNumber && <span className="ml-2">| Lote: {imm.lotNumber}</span>}
                                                </p>
                                            </div>
                                        </div>
                                        <span className="flex items-center gap-1 text-green-600 text-sm bg-green-50 px-2 py-1 rounded-full">
                                            <CheckCircle size={14} /> Aplicada
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );

            case 'exams':
                return (
                    <div className="clinical-module-content">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <FileText className="text-blue-500" size={20} />
                            Resultados de Exames
                        </h3>
                        {data.diagnosticResults.length === 0 ? (
                            <p className="text-gray-500 italic">Nenhum exame registrado.</p>
                        ) : (
                            <div className="space-y-3">
                                {data.diagnosticResults.map(exam => (
                                    <div key={exam.id} className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p className="font-medium">{exam.display}</p>
                                                <p className="text-sm text-gray-500">{exam.category}</p>
                                            </div>
                                            <span className="text-sm text-gray-400">{formatDate(exam.effectiveDate)}</span>
                                        </div>
                                        {exam.results.length > 0 && (
                                            <div className="mt-2 pt-2 border-t border-blue-100">
                                                {exam.results.slice(0, 3).map((r, i) => (
                                                    <div key={i} className="flex justify-between text-sm">
                                                        <span className="text-gray-600">{r.display}</span>
                                                        <span className={`font-medium ${r.interpretation === 'high' || r.interpretation === 'low' ? 'text-amber-600' :
                                                                r.interpretation === 'critical' ? 'text-red-600' : 'text-gray-700'
                                                            }`}>
                                                            {r.value} {r.unit}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );

            case 'timeline':
                return (
                    <div className="clinical-module-content">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <Activity className="text-purple-500" size={20} />
                            Timeline Unificada
                        </h3>
                        {data.timeline.length === 0 && data.encounters.length === 0 ? (
                            <p className="text-gray-500 italic">Nenhum evento registrado.</p>
                        ) : (
                            <div className="relative">
                                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                                <div className="space-y-4">
                                    {[...data.timeline, ...data.encounters.map((e: any) => ({
                                        id: e.id,
                                        type: 'encounter',
                                        date: e.period?.start || e.date,
                                        title: e.type?.[0]?.coding?.[0]?.display || 'Atendimento',
                                        description: e.reasonCode?.[0]?.text || '',
                                        icon: '🏥',
                                        status: e.status
                                    }))]
                                        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                                        .slice(0, 10)
                                        .map((event: any) => (
                                            <div key={event.id} className="flex gap-4 relative">
                                                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-lg z-10">
                                                    {event.icon || '📋'}
                                                </div>
                                                <div className="flex-1 pb-4">
                                                    <p className="font-medium">{event.title}</p>
                                                    <p className="text-sm text-gray-500">{event.description}</p>
                                                    <p className="text-xs text-gray-400">{formatDate(event.date)}</p>
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        )}
                    </div>
                );

            case 'vitals':
                return (
                    <div className="clinical-module-content">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <BarChart3 className="text-emerald-500" size={20} />
                            Histórico de Sinais Vitais
                        </h3>
                        {Object.keys(data.latestVitals).length === 0 ? (
                            <p className="text-gray-500 italic">Nenhum sinal vital registrado.</p>
                        ) : (
                            <div className="grid grid-cols-2 gap-3">
                                {Object.entries(data.latestVitals).map(([key, vital]) => (
                                    <div key={key} className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                                        <p className="text-sm text-gray-600">{vital.display}</p>
                                        <p className="text-xl font-bold text-gray-800">
                                            {vital.value} <span className="text-sm font-normal">{vital.unit}</span>
                                        </p>
                                        <p className="text-xs text-gray-400">{formatDate(vital.date)}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                        {data.vitalSigns.length > 0 && (
                            <p className="text-sm text-gray-500 mt-4">
                                Total de {data.vitalSigns.length} registros de sinais vitais
                            </p>
                        )}
                    </div>
                );

            case 'medications':
                return (
                    <div className="clinical-module-content">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <Pill className="text-amber-500" size={20} />
                            Medicamentos
                        </h3>
                        {data.medications.length === 0 ? (
                            <p className="text-gray-500 italic">Nenhum medicamento prescrito.</p>
                        ) : (
                            <div className="space-y-3">
                                {data.medications.map(med => (
                                    <div key={med.id} className={`p-3 rounded-lg border ${med.status === 'active' ? 'bg-green-50 border-green-100' :
                                            med.status === 'stopped' ? 'bg-red-50 border-red-100' :
                                                'bg-gray-50 border-gray-100'
                                        }`}>
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p className="font-medium">{med.name}</p>
                                                <p className="text-sm text-gray-600">{med.dosage} - {med.frequency}</p>
                                                {med.route && <p className="text-sm text-gray-500">{med.route}</p>}
                                            </div>
                                            <span className={`text-xs px-2 py-1 rounded-full ${med.status === 'active' ? 'bg-green-100 text-green-700' :
                                                    med.status === 'stopped' ? 'bg-red-100 text-red-700' :
                                                        'bg-gray-100 text-gray-700'
                                                }`}>
                                                {med.status === 'active' ? 'Ativo' :
                                                    med.status === 'stopped' ? 'Parado' :
                                                        med.status === 'completed' ? 'Concluído' : med.status}
                                            </span>
                                        </div>
                                        {med.startDate && (
                                            <p className="text-xs text-gray-400 mt-1">
                                                Início: {formatDate(med.startDate)}
                                                {med.endDate && ` - Fim: ${formatDate(med.endDate)}`}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
                <Activity size={20} className="text-blue-600" />
                <h2 className="font-semibold text-gray-800">Módulos Clínicos</h2>
                {loading && <span className="text-sm text-gray-400">(carregando...)</span>}
            </div>

            {/* Module buttons */}
            <div className="flex flex-wrap gap-2 mb-4">
                {modules.map(mod => (
                    <button
                        key={mod.id}
                        onClick={() => setActiveModule(activeModule === mod.id ? null : mod.id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium transition-all ${activeModule === mod.id
                                ? 'text-white shadow-md'
                                : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                            }`}
                        style={activeModule === mod.id ? { backgroundColor: mod.color } : {}}
                    >
                        <mod.icon size={16} />
                        {mod.label}
                        {mod.count > 0 && (
                            <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs ${activeModule === mod.id ? 'bg-white/20' : 'bg-gray-100'
                                }`}>
                                {mod.count}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Active module content */}
            {activeModule && (
                <div className="border-t pt-4">
                    <div className="flex justify-between items-center mb-3">
                        <button
                            onClick={refresh}
                            className="text-sm text-blue-600 hover:underline"
                        >
                            Atualizar dados
                        </button>
                        <button
                            onClick={() => setActiveModule(null)}
                            className="text-gray-400 hover:text-gray-600"
                        >
                            <X size={18} />
                        </button>
                    </div>
                    {renderModuleContent()}
                </div>
            )}
        </Card>
    );
};

export default ClinicalModulesPanel;

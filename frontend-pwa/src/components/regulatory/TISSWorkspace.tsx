/**
 * TISSWorkspace - Interface para Guias TISS/ANS
 * 
 * Permite criar e gerenciar guias TISS para faturamento:
 * - Guia de Consulta
 * - Guia SP/SADT (Serviços Profissionais / SADT)
 * - Guia de Internação
 * - Guia de Honorários
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import {
    FileSpreadsheet,
    Plus,
    Send,
    Clock,
    CheckCircle,
    AlertTriangle,
    Search,
    Filter,
    Download,
    RefreshCw,
    Building2,
    User,
    Calendar,
    DollarSign,
    FileText,
    Printer
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface TISSWorkspaceProps {
    patientId?: string;
    encounterId?: string;
}

type GuideType = 'consulta' | 'sp_sadt' | 'internacao' | 'honorarios';
type GuideStatus = 'draft' | 'pending' | 'authorized' | 'denied' | 'cancelled';

interface TISSGuide {
    id: string;
    numero_guia: string;
    tipo: GuideType;
    status: GuideStatus;
    paciente_nome: string;
    operadora: string;
    valor_total: number;
    data_emissao: string;
    data_autorizacao?: string;
    procedures: string[];
}

const GUIDE_TYPES: Record<GuideType, { label: string; icon: string; color: string }> = {
    consulta: { label: 'Consulta', icon: '👨‍⚕️', color: '#3b82f6' },
    sp_sadt: { label: 'SP/SADT', icon: '🔬', color: '#8b5cf6' },
    internacao: { label: 'Internação', icon: '🏥', color: '#ef4444' },
    honorarios: { label: 'Honorários', icon: '💰', color: '#10b981' },
};

const STATUS_CONFIG: Record<GuideStatus, { label: string; color: string; bgColor: string }> = {
    draft: { label: 'Rascunho', color: '#6b7280', bgColor: '#f3f4f6' },
    pending: { label: 'Aguardando', color: '#f59e0b', bgColor: '#fef3c7' },
    authorized: { label: 'Autorizada', color: '#10b981', bgColor: '#d1fae5' },
    denied: { label: 'Negada', color: '#ef4444', bgColor: '#fee2e2' },
    cancelled: { label: 'Cancelada', color: '#6b7280', bgColor: '#e5e7eb' },
};

const TISSWorkspace: React.FC<TISSWorkspaceProps> = ({ patientId, encounterId }) => {
    const { token } = useAuth();
    const [guides, setGuides] = useState<TISSGuide[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [selectedType, setSelectedType] = useState<GuideType>('consulta');
    const [filterStatus, setFilterStatus] = useState<GuideStatus | 'all'>('all');
    const [searchTerm, setSearchTerm] = useState('');

    // Form state
    const [formData, setFormData] = useState({
        operadora_codigo: '',
        operadora_nome: '',
        beneficiario_carteira: '',
        beneficiario_nome: patientId ? '' : '',
        procedimentos: [''],
        data_atendimento: new Date().toISOString().split('T')[0],
        tipo_atendimento: 'eletivo',
        carater_atendimento: 'eletivo',
        observacoes: ''
    });

    useEffect(() => {
        fetchGuides();
    }, [patientId]);

    const fetchGuides = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (patientId) params.append('patient_id', patientId);

            const response = await axios.get(`${API_URL}/tiss/guides/?${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setGuides(response.data.guides || []);
        } catch (err) {
            console.error('Erro ao carregar guias TISS:', err);
            // Mock data for demo
            setGuides([
                {
                    id: '1',
                    numero_guia: 'TISS-2024-001234',
                    tipo: 'consulta',
                    status: 'authorized',
                    paciente_nome: 'Maria Silva',
                    operadora: 'Unimed',
                    valor_total: 250.00,
                    data_emissao: '2024-12-10',
                    data_autorizacao: '2024-12-10',
                    procedures: ['Consulta em consultório']
                },
                {
                    id: '2',
                    numero_guia: 'TISS-2024-001235',
                    tipo: 'sp_sadt',
                    status: 'pending',
                    paciente_nome: 'João Santos',
                    operadora: 'Bradesco Saúde',
                    valor_total: 1250.00,
                    data_emissao: '2024-12-12',
                    procedures: ['Hemograma completo', 'Glicemia', 'Colesterol total']
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateGuide = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await axios.post(
                `${API_URL}/tiss/${selectedType}/`,
                {
                    ...formData,
                    patient_id: patientId,
                    encounter_id: encounterId,
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setGuides(prev => [response.data, ...prev]);
            setShowForm(false);
            resetForm();
            alert('Guia TISS criada com sucesso!');
        } catch (err: any) {
            alert(err.response?.data?.error || 'Erro ao criar guia TISS');
        }
    };

    const resetForm = () => {
        setFormData({
            operadora_codigo: '',
            operadora_nome: '',
            beneficiario_carteira: '',
            beneficiario_nome: '',
            procedimentos: [''],
            data_atendimento: new Date().toISOString().split('T')[0],
            tipo_atendimento: 'eletivo',
            carater_atendimento: 'eletivo',
            observacoes: ''
        });
    };

    const addProcedure = () => {
        setFormData(prev => ({
            ...prev,
            procedimentos: [...prev.procedimentos, '']
        }));
    };

    const updateProcedure = (index: number, value: string) => {
        setFormData(prev => ({
            ...prev,
            procedimentos: prev.procedimentos.map((p, i) => i === index ? value : p)
        }));
    };

    const removeProcedure = (index: number) => {
        if (formData.procedimentos.length > 1) {
            setFormData(prev => ({
                ...prev,
                procedimentos: prev.procedimentos.filter((_, i) => i !== index)
            }));
        }
    };

    const filteredGuides = guides.filter(g => {
        if (filterStatus !== 'all' && g.status !== filterStatus) return false;
        if (searchTerm && !g.numero_guia.toLowerCase().includes(searchTerm.toLowerCase()) &&
            !g.paciente_nome.toLowerCase().includes(searchTerm.toLowerCase())) return false;
        return true;
    });

    const formatCurrency = (value: number) => {
        return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    };

    return (
        <div className="tiss-workspace space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center flex-wrap gap-4">
                <div>
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <FileSpreadsheet className="text-indigo-600" />
                        Guias TISS/ANS
                    </h2>
                    <p className="text-gray-500">Gerenciamento de guias para faturamento</p>
                </div>

                <div className="flex gap-2">
                    <Button variant="secondary" onClick={fetchGuides}>
                        <RefreshCw size={16} className="mr-1" />
                        Atualizar
                    </Button>
                    <Button onClick={() => setShowForm(!showForm)}>
                        <Plus size={16} className="mr-1" />
                        Nova Guia
                    </Button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(GUIDE_TYPES).map(([type, config]) => {
                    const count = guides.filter(g => g.tipo === type).length;
                    return (
                        <Card key={type} className="p-4">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{config.icon}</span>
                                <div>
                                    <p className="text-2xl font-bold" style={{ color: config.color }}>{count}</p>
                                    <p className="text-sm text-gray-500">{config.label}</p>
                                </div>
                            </div>
                        </Card>
                    );
                })}
            </div>

            {/* Form */}
            {showForm && (
                <Card className="p-6 bg-indigo-50 border-indigo-200">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Plus size={18} />
                        Nova Guia TISS
                    </h3>

                    <form onSubmit={handleCreateGuide} className="space-y-4">
                        {/* Tipo de guia */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Guia</label>
                            <div className="flex gap-2 flex-wrap">
                                {Object.entries(GUIDE_TYPES).map(([type, config]) => (
                                    <button
                                        key={type}
                                        type="button"
                                        onClick={() => setSelectedType(type as GuideType)}
                                        className={`px-4 py-2 rounded-lg border-2 flex items-center gap-2 transition-all ${selectedType === type
                                                ? 'border-indigo-500 bg-white'
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <span>{config.icon}</span>
                                        {config.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Operadora */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Código Operadora ANS</label>
                                <input
                                    type="text"
                                    value={formData.operadora_codigo}
                                    onChange={(e) => setFormData({ ...formData, operadora_codigo: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    placeholder="Ex: 359955"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nome da Operadora</label>
                                <input
                                    type="text"
                                    value={formData.operadora_nome}
                                    onChange={(e) => setFormData({ ...formData, operadora_nome: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    placeholder="Ex: Unimed"
                                    required
                                />
                            </div>
                        </div>

                        {/* Beneficiário */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nº Carteira</label>
                                <input
                                    type="text"
                                    value={formData.beneficiario_carteira}
                                    onChange={(e) => setFormData({ ...formData, beneficiario_carteira: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    placeholder="Número da carteira do plano"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Data do Atendimento</label>
                                <input
                                    type="date"
                                    value={formData.data_atendimento}
                                    onChange={(e) => setFormData({ ...formData, data_atendimento: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    required
                                />
                            </div>
                        </div>

                        {/* Procedimentos */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Procedimentos (TUSS)
                            </label>
                            {formData.procedimentos.map((proc, index) => (
                                <div key={index} className="flex gap-2 mb-2">
                                    <input
                                        type="text"
                                        value={proc}
                                        onChange={(e) => updateProcedure(index, e.target.value)}
                                        className="flex-1 p-2 border border-gray-300 rounded-lg"
                                        placeholder="Código TUSS ou descrição"
                                        required
                                    />
                                    {formData.procedimentos.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeProcedure(index)}
                                            className="px-3 py-2 text-red-500 hover:bg-red-50 rounded-lg"
                                        >
                                            ✕
                                        </button>
                                    )}
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={addProcedure}
                                className="text-sm text-indigo-600 hover:underline flex items-center gap-1"
                            >
                                <Plus size={14} /> Adicionar procedimento
                            </button>
                        </div>

                        {/* Observações */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                            <textarea
                                value={formData.observacoes}
                                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                                className="w-full p-2 border border-gray-300 rounded-lg"
                                rows={2}
                                placeholder="Observações adicionais..."
                            />
                        </div>

                        {/* Botões */}
                        <div className="flex justify-end gap-2 pt-4">
                            <Button variant="secondary" type="button" onClick={() => setShowForm(false)}>
                                Cancelar
                            </Button>
                            <Button type="submit">
                                <Send size={16} className="mr-1" />
                                Criar Guia
                            </Button>
                        </div>
                    </form>
                </Card>
            )}

            {/* Filters */}
            <div className="flex gap-4 flex-wrap">
                <div className="relative flex-1 min-w-[200px]">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Buscar por número ou paciente..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
                    />
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value as GuideStatus | 'all')}
                    className="px-4 py-2 border border-gray-300 rounded-lg"
                    aria-label="Filtrar por status"
                >
                    <option value="all">Todos os status</option>
                    {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                        <option key={status} value={status}>{config.label}</option>
                    ))}
                </select>
            </div>

            {/* Lista de guias */}
            <div className="space-y-3">
                {loading ? (
                    <p className="text-center text-gray-500 py-8">Carregando guias...</p>
                ) : filteredGuides.length === 0 ? (
                    <p className="text-center text-gray-500 py-8 italic">Nenhuma guia encontrada</p>
                ) : (
                    filteredGuides.map(guide => (
                        <Card key={guide.id} className="p-4 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start flex-wrap gap-4">
                                <div className="flex items-start gap-4">
                                    <span className="text-3xl">{GUIDE_TYPES[guide.tipo].icon}</span>
                                    <div>
                                        <p className="font-semibold text-gray-800">{guide.numero_guia}</p>
                                        <p className="text-sm text-gray-500 flex items-center gap-2">
                                            <User size={14} /> {guide.paciente_nome}
                                        </p>
                                        <p className="text-sm text-gray-500 flex items-center gap-2">
                                            <Building2 size={14} /> {guide.operadora}
                                        </p>
                                        <p className="text-sm text-gray-400 mt-1">
                                            {guide.procedures.join(', ')}
                                        </p>
                                    </div>
                                </div>

                                <div className="text-right">
                                    <span
                                        className="inline-block px-3 py-1 rounded-full text-sm font-medium"
                                        style={{
                                            backgroundColor: STATUS_CONFIG[guide.status].bgColor,
                                            color: STATUS_CONFIG[guide.status].color
                                        }}
                                    >
                                        {STATUS_CONFIG[guide.status].label}
                                    </span>
                                    <p className="text-lg font-bold text-gray-800 mt-2">
                                        {formatCurrency(guide.valor_total)}
                                    </p>
                                    <p className="text-xs text-gray-400">
                                        <Calendar size={12} className="inline mr-1" />
                                        {new Date(guide.data_emissao).toLocaleDateString('pt-BR')}
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-2 mt-4 pt-4 border-t">
                                <Button variant="secondary" className="text-sm">
                                    <FileText size={14} className="mr-1" /> Ver Detalhes
                                </Button>
                                <Button variant="secondary" className="text-sm">
                                    <Printer size={14} className="mr-1" /> Imprimir
                                </Button>
                                <Button variant="secondary" className="text-sm">
                                    <Download size={14} className="mr-1" /> XML
                                </Button>
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
};

export default TISSWorkspace;

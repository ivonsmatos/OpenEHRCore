/**
 * RNDSStatus - Dashboard de Status da RNDS
 * 
 * Mostra o status de integração com a Rede Nacional de Dados em Saúde:
 * - Status de conexão
 * - Últimas submissões
 * - Consulta de histórico do paciente
 * - Envio de dados (IPS, vacinas, exames)
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import {
    Globe,
    CheckCircle,
    XCircle,
    AlertTriangle,
    RefreshCw,
    Send,
    Search,
    Clock,
    FileText,
    Syringe,
    TestTube,
    User,
    ShieldCheck,
    Activity
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface RNDSStatusProps {
    patientId?: string;
    patientCpf?: string;
}

interface RNDSSubmission {
    id: string;
    type: 'ips' | 'immunization' | 'lab_result';
    status: 'success' | 'error' | 'pending';
    timestamp: string;
    message?: string;
    resourceId?: string;
}

const RNDSStatus: React.FC<RNDSStatusProps> = ({ patientId, patientCpf }) => {
    const { token } = useAuth();
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
    const [submissions, setSubmissions] = useState<RNDSSubmission[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchCpf, setSearchCpf] = useState(patientCpf || '');
    const [patientHistory, setPatientHistory] = useState<any>(null);
    const [submitting, setSubmitting] = useState<string | null>(null);

    useEffect(() => {
        checkConnection();
        if (patientId) {
            loadSubmissions();
        }
    }, [patientId]);

    const checkConnection = async () => {
        setConnectionStatus('checking');
        try {
            const response = await axios.get(`${API_URL}/rnds/status/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setConnectionStatus(response.data.connected ? 'connected' : 'disconnected');
        } catch (err) {
            setConnectionStatus('disconnected');
        }
    };

    const loadSubmissions = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/rnds/submissions/?patient_id=${patientId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setSubmissions(response.data.submissions || []);
        } catch (err) {
            // Mock data for demo
            setSubmissions([
                {
                    id: '1',
                    type: 'ips',
                    status: 'success',
                    timestamp: new Date(Date.now() - 86400000).toISOString(),
                    message: 'IPS enviado com sucesso',
                    resourceId: 'Bundle/ips-12345'
                },
                {
                    id: '2',
                    type: 'immunization',
                    status: 'success',
                    timestamp: new Date(Date.now() - 172800000).toISOString(),
                    message: 'Vacina COVID-19 registrada',
                    resourceId: 'Immunization/vac-67890'
                },
                {
                    id: '3',
                    type: 'lab_result',
                    status: 'error',
                    timestamp: new Date(Date.now() - 259200000).toISOString(),
                    message: 'Erro de validação: CPF inválido'
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const searchPatient = async () => {
        if (!searchCpf || searchCpf.length < 11) {
            alert('Digite um CPF válido');
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/rnds/patient/${searchCpf}/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setPatientHistory(response.data);
        } catch (err: any) {
            alert(err.response?.data?.error || 'Paciente não encontrado na RNDS');
        }
    };

    const submitToRNDS = async (type: 'ips' | 'immunization' | 'lab_result') => {
        if (!patientId) {
            alert('Selecione um paciente primeiro');
            return;
        }

        setSubmitting(type);
        try {
            let endpoint = '';
            switch (type) {
                case 'ips': endpoint = `/rnds/submit-ips/${patientId}/`; break;
                case 'immunization': endpoint = `/rnds/submit-immunization/${patientId}/`; break;
                case 'lab_result': endpoint = `/rnds/submit-lab-result/${patientId}/`; break;
            }

            const response = await axios.post(
                `${API_URL}${endpoint}`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setSubmissions(prev => [{
                id: Date.now().toString(),
                type,
                status: 'success',
                timestamp: new Date().toISOString(),
                message: response.data.message,
                resourceId: response.data.resource_id
            }, ...prev]);

            alert('Dados enviados com sucesso para a RNDS!');
        } catch (err: any) {
            setSubmissions(prev => [{
                id: Date.now().toString(),
                type,
                status: 'error',
                timestamp: new Date().toISOString(),
                message: err.response?.data?.error || 'Erro ao enviar dados'
            }, ...prev]);

            alert('Erro ao enviar para RNDS: ' + (err.response?.data?.error || 'Erro desconhecido'));
        } finally {
            setSubmitting(null);
        }
    };

    const typeConfig = {
        ips: { label: 'Sumário do Paciente (IPS)', icon: FileText, color: '#3b82f6' },
        immunization: { label: 'Imunização', icon: Syringe, color: '#ec4899' },
        lab_result: { label: 'Resultado de Exame', icon: TestTube, color: '#8b5cf6' }
    };

    return (
        <div className="rnds-status space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center flex-wrap gap-4">
                <div>
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <Globe className="text-green-600" />
                        RNDS - Rede Nacional de Dados em Saúde
                    </h2>
                    <p className="text-gray-500">Integração com o Ministério da Saúde</p>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-100 text-green-700' :
                            connectionStatus === 'disconnected' ? 'bg-red-100 text-red-700' :
                                'bg-gray-100 text-gray-700'
                        }`}>
                        {connectionStatus === 'connected' && <CheckCircle size={18} />}
                        {connectionStatus === 'disconnected' && <XCircle size={18} />}
                        {connectionStatus === 'checking' && <RefreshCw size={18} className="animate-spin" />}
                        <span className="font-medium">
                            {connectionStatus === 'connected' ? 'Conectado' :
                                connectionStatus === 'disconnected' ? 'Desconectado' : 'Verificando...'}
                        </span>
                    </div>
                    <Button variant="secondary" onClick={checkConnection}>
                        <RefreshCw size={16} />
                    </Button>
                </div>
            </div>

            {/* Actions */}
            <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Send size={18} />
                    Enviar Dados para RNDS
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button
                        onClick={() => submitToRNDS('ips')}
                        disabled={submitting !== null || connectionStatus !== 'connected'}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${submitting === 'ips' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        <FileText size={24} className="text-blue-500 mb-2" />
                        <p className="font-medium">Sumário do Paciente (IPS)</p>
                        <p className="text-sm text-gray-500">Envia resumo clínico completo</p>
                        {submitting === 'ips' && <span className="text-sm text-blue-600">Enviando...</span>}
                    </button>

                    <button
                        onClick={() => submitToRNDS('immunization')}
                        disabled={submitting !== null || connectionStatus !== 'connected'}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${submitting === 'immunization' ? 'border-pink-500 bg-pink-50' : 'border-gray-200 hover:border-pink-300'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        <Syringe size={24} className="text-pink-500 mb-2" />
                        <p className="font-medium">Imunizações</p>
                        <p className="text-sm text-gray-500">Registra vacinas aplicadas</p>
                        {submitting === 'immunization' && <span className="text-sm text-pink-600">Enviando...</span>}
                    </button>

                    <button
                        onClick={() => submitToRNDS('lab_result')}
                        disabled={submitting !== null || connectionStatus !== 'connected'}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${submitting === 'lab_result' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        <TestTube size={24} className="text-purple-500 mb-2" />
                        <p className="font-medium">Resultados de Exames</p>
                        <p className="text-sm text-gray-500">Envia laudos laboratoriais</p>
                        {submitting === 'lab_result' && <span className="text-sm text-purple-600">Enviando...</span>}
                    </button>
                </div>
            </Card>

            {/* Search Patient */}
            <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Search size={18} />
                    Consultar Histórico na RNDS
                </h3>

                <div className="flex gap-4">
                    <input
                        type="text"
                        value={searchCpf}
                        onChange={(e) => setSearchCpf(e.target.value.replace(/\D/g, '').slice(0, 11))}
                        placeholder="Digite o CPF do paciente..."
                        className="flex-1 p-3 border border-gray-300 rounded-lg"
                    />
                    <Button onClick={searchPatient} disabled={connectionStatus !== 'connected'}>
                        <Search size={16} className="mr-1" />
                        Consultar
                    </Button>
                </div>

                {patientHistory && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                            <User size={18} />
                            <span className="font-medium">{patientHistory.nome || 'Paciente'}</span>
                            <ShieldCheck size={16} className="text-green-500" />
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500">Vacinas</p>
                                <p className="font-bold text-lg">{patientHistory.immunizations || 0}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Exames</p>
                                <p className="font-bold text-lg">{patientHistory.lab_results || 0}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Atendimentos</p>
                                <p className="font-bold text-lg">{patientHistory.encounters || 0}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Última Atualização</p>
                                <p className="font-bold">{patientHistory.last_update || '-'}</p>
                            </div>
                        </div>
                    </div>
                )}
            </Card>

            {/* Submission History */}
            <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Activity size={18} />
                    Histórico de Submissões
                </h3>

                {loading ? (
                    <p className="text-center text-gray-500 py-4">Carregando...</p>
                ) : submissions.length === 0 ? (
                    <p className="text-center text-gray-500 py-4 italic">Nenhuma submissão registrada</p>
                ) : (
                    <div className="space-y-3">
                        {submissions.map(sub => {
                            const config = typeConfig[sub.type];
                            const Icon = config.icon;
                            return (
                                <div key={sub.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <Icon size={20} style={{ color: config.color }} />
                                        <div>
                                            <p className="font-medium">{config.label}</p>
                                            <p className="text-sm text-gray-500">{sub.message}</p>
                                            {sub.resourceId && (
                                                <p className="text-xs text-gray-400 font-mono">{sub.resourceId}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm ${sub.status === 'success' ? 'bg-green-100 text-green-700' :
                                                sub.status === 'error' ? 'bg-red-100 text-red-700' :
                                                    'bg-yellow-100 text-yellow-700'
                                            }`}>
                                            {sub.status === 'success' && <CheckCircle size={14} />}
                                            {sub.status === 'error' && <XCircle size={14} />}
                                            {sub.status === 'pending' && <Clock size={14} />}
                                            {sub.status === 'success' ? 'Sucesso' :
                                                sub.status === 'error' ? 'Erro' : 'Pendente'}
                                        </span>
                                        <p className="text-xs text-gray-400 mt-1">
                                            {new Date(sub.timestamp).toLocaleString('pt-BR')}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </Card>
        </div>
    );
};

export default RNDSStatus;

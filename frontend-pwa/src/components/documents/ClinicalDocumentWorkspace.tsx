
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { FileText, Plus, FileSearch, Printer, Trash2 } from 'lucide-react';

import { useAuth } from '../../hooks/useAuth';
import { usePatients } from '../../hooks/usePatients';
import Button from '../base/Button';
import Card from '../base/Card';

const AnamnesisForm = ({ onCancel, onSuccess }: { onCancel: () => void, onSuccess: () => void }) => {
    const { token } = useAuth();
    const { patients, loading: loadingPatients, fetchPatients } = usePatients();
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    const [formData, setFormData] = useState({
        doc_type: 'anamnese',
        title: '',
        text_content: '',
        patient_id: '',
        practitioner_id: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        fetchPatients();
    }, []);

    // Set default patient if list loads and selection is empty
    useEffect(() => {
        if (patients.length > 0 && !formData.patient_id) {
            setFormData(prev => ({ ...prev, patient_id: patients[0].id }));
        }
    }, [patients]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.patient_id) {
            alert("Selecione um paciente");
            return;
        }

        setIsSubmitting(true);
        try {
            await axios.post(`${API_URL}/documents/`, formData, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            alert('Documento criado com sucesso!');
            onSuccess();
        } catch (error) {
            console.error(error);
            if (axios.isAxiosError(error) && error.response) {
                alert(`Erro ao criar documento: ${error.response.data?.error || error.response.statusText}`);
            } else {
                alert('Erro ao criar documento.');
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="font-semibold text-xl mb-4 text-slate-800">Novo Documento Clínico</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Paciente</label>
                    {loadingPatients ? (
                        <p className="text-sm text-gray-500">Carregando pacientes...</p>
                    ) : (
                        <select
                            className="w-full p-2 border rounded-md"
                            value={formData.patient_id}
                            onChange={e => setFormData({ ...formData, patient_id: e.target.value })}
                            required
                        >
                            <option value="">Selecione um paciente</option>
                            {patients.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                        </select>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Documento</label>
                    <select
                        className="w-full p-2 border rounded-md"
                        value={formData.doc_type}
                        onChange={e => setFormData({ ...formData, doc_type: e.target.value })}
                    >
                        <option value="anamnese">Anamnese</option>
                        <option value="evolucao">Evolução</option>
                        <option value="receita">Receita</option>
                        <option value="atestado">Atestado</option>
                    </select>
                </div>

                <div className="col-span-1 md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700 mb-1">Título</label>
                    <input
                        type="text"
                        required
                        className="w-full p-2 border rounded-md"
                        placeholder="Ex: Anamnese Inicial, Evolução Diária..."
                        value={formData.title}
                        onChange={e => setFormData({ ...formData, title: e.target.value })}
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Conteúdo (História Clínica)</label>
                <textarea
                    required
                    rows={10}
                    className="w-full p-2 border rounded-md font-mono text-sm"
                    placeholder="Descreva a queixa principal, história da moléstia atual, conduta, etc..."
                    value={formData.text_content}
                    onChange={e => setFormData({ ...formData, text_content: e.target.value })}
                />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="secondary" onClick={onCancel} type="button">Cancelar</Button>
                <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Salvando...' : 'Salvar Documento'}
                </Button>
            </div>
        </form>
    );
};

interface Document {
    id: string;
    title: string;
    date: string;
    author: string;
    type: string;
    status: string;
}

const ClinicalDocumentWorkspace: React.FC = () => {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'list' | 'create'>('list');
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    const fetchDocuments = async () => {
        setLoading(true);
        console.log("Fetching documents... Token:", !!token);
        try {
            const response = await axios.get(`${API_URL}/documents/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            console.log("Documents response:", response.data);
            if (Array.isArray(response.data)) {
                setDocuments(response.data);
            } else {
                console.error("Expected array but got:", response.data);
                setDocuments([]);
            }
        } catch (error) {
            console.error("Erro ao buscar documentos:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (viewMode === 'list') {
            fetchDocuments();
        }
    }, [viewMode]);

    const handlePrintPDF = async (docId: string) => {
        try {
            const response = await axios.get(`${API_URL}/documents/${docId}/pdf/`, {
                responseType: 'blob',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
            const pdfUrl = window.URL.createObjectURL(pdfBlob);
            window.open(pdfUrl, '_blank');

        } catch (error) {
            console.error("Erro ao abrir PDF", error);
            if (axios.isAxiosError(error) && error.response?.status === 404) {
                alert("Documento não encontrado no servidor.");
            } else if (axios.isAxiosError(error) && error.response?.status === 401) {
                alert("Erro de permissão (401). Tente fazer login novamente.");
            } else {
                alert("Erro ao abrir PDF. Verifique o console.");
            }
        }
    };

    const handleDeleteDocument = async (docId: string) => {
        if (!confirm('Tem certeza que deseja excluir este documento?')) return;

        try {
            await axios.delete(`${API_URL}/documents/${docId}/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            alert('Documento excluído com sucesso.');
            fetchDocuments(); // Reload list
        } catch (error) {
            console.error("Erro ao excluir", error);
            alert("Erro ao excluir documento.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="mb-4">
                <Button variant="secondary" size="sm" onClick={() => navigate('/')}>
                    ← Voltar para Dashboard
                </Button>
            </div>

            <header className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                        <FileText className="text-indigo-600" />
                        Documentos Clínicos
                    </h1>
                    <p className="text-slate-600">Gestão de prontuário, evoluções e atestados.</p>
                </div>
                <div className="flex gap-2">
                    {viewMode === 'list' && (
                        <>
                            <Button variant="secondary" onClick={fetchDocuments}>
                                🔄
                            </Button>
                            <Button onClick={() => setViewMode('create')}>
                                <Plus size={20} className="mr-2" />
                                Novo Documento
                            </Button>
                        </>
                    )}
                </div>
            </header>

            {viewMode === 'list' ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {loading ? (
                        <p className="text-gray-500 col-span-full text-center py-8">Carregando documentos...</p>
                    ) : documents.map((doc) => (
                        <Card key={doc.id} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-indigo-500">
                            <div className="p-4 flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <FileText size={16} className="text-gray-400" />
                                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{doc.type}</span>
                                    </div>
                                    <h3 className="font-semibold text-lg text-slate-800">{doc.title}</h3>
                                    <p className="text-sm text-slate-500 mt-1">Autor: {doc.author}</p>
                                    <p className="text-xs text-slate-400 mt-1">{doc.date}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full"
                                        title="Visualizar"
                                        onClick={() => handlePrintPDF(doc.id)}
                                    >
                                        <FileSearch size={18} />
                                    </button>
                                    <button
                                        className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full"
                                        title="Imprimir PDF"
                                        onClick={() => handlePrintPDF(doc.id)}
                                    >
                                        <Printer size={18} />
                                    </button>
                                    <button
                                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full"
                                        title="Excluir"
                                        onClick={() => handleDeleteDocument(doc.id)}
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>
                        </Card>
                    ))}

                    {!loading && documents.length === 0 && (
                        <div className="col-span-full py-12 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                            <FileText size={48} className="mx-auto mb-4 opacity-20" />
                            <p>Nenhum documento encontrado.</p>
                            <Button variant="secondary" className="mt-4" onClick={() => setViewMode('create')}>
                                Criar Primeiro Documento
                            </Button>
                        </div>
                    )}
                </div>
            ) : (
                <Card>
                    <div className="p-6">
                        <AnamnesisForm
                            onCancel={() => setViewMode('list')}
                            onSuccess={() => setViewMode('list')}
                        />
                    </div>
                </Card>
            )}
        </div>
    );
};

export default ClinicalDocumentWorkspace;

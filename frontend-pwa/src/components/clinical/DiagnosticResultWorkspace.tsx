
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import { FileText, Plus, Calendar, Activity } from 'lucide-react';

interface DiagnosticReport {
    id: string;
    name: string;
    date: string;
    conclusion: string;
    status: string;
}

const DiagnosticResultWorkspace = () => {
    const { id: patientId } = useParams();
    const { token } = useAuth();
    const [reports, setReports] = useState<DiagnosticReport[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        date: new Date().toISOString().split('T')[0],
        conclusion: ''
    });

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    useEffect(() => {
        fetchReports();
    }, [patientId]);

    const fetchReports = async () => {
        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/diagnostic-reports/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setReports(response.data);
        } catch (error) {
            console.error("Error fetching reports:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post(`${API_URL}/diagnostic-reports/`, {
                patient_id: patientId,
                name: formData.name,
                code: "88", // Mock code
                date: formData.date,
                conclusion: formData.conclusion
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setShowForm(false);
            setFormData({ name: '', code: '', date: '', conclusion: '' });
            fetchReports();
        } catch (error) {
            alert("Erro ao salvar resultado.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                        <Activity className="text-indigo-600" />
                        Resultados de Exames
                    </h2>
                    <p className="text-slate-600">Laudos e resultados laboratoriais</p>
                </div>
                <Button onClick={() => setShowForm(!showForm)}>
                    <Plus size={16} className="mr-2" />
                    Novo Resultado
                </Button>
            </div>

            {showForm && (
                <Card className="p-6 bg-slate-50 border-indigo-100">
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-slate-700">Nome do Exame</label>
                                <input
                                    type="text"
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ex: Hemograma Completo"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Data do Resultado</label>
                                <input
                                    type="date"
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={formData.date}
                                    onChange={e => setFormData({ ...formData, date: e.target.value })}
                                />
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-slate-700">Conclusão / Laudo</label>
                                <textarea
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    rows={3}
                                    value={formData.conclusion}
                                    onChange={e => setFormData({ ...formData, conclusion: e.target.value })}
                                    placeholder="Descreva o resultado ou conclusão..."
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button variant="ghost" onClick={() => setShowForm(false)} type="button">Cancelar</Button>
                            <Button type="submit">Salvar Resultado</Button>
                        </div>
                    </form>
                </Card>
            )}

            <div className="grid gap-4">
                {loading ? (
                    <p>Carregando...</p>
                ) : reports.length === 0 ? (
                    <p className="text-slate-500 italic">Nenhum resultado registrado.</p>
                ) : (
                    reports.map((rep) => (
                        <Card key={rep.id} className="p-4 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start">
                                <div className="flex items-start gap-4">
                                    <div className="p-3 bg-indigo-100 rounded-lg text-indigo-600">
                                        <FileText size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-slate-900">{rep.name}</h3>
                                        <p className="text-sm text-slate-500 flex items-center gap-2 mb-2">
                                            <Calendar size={14} /> {rep.date}
                                        </p>
                                        <p className="text-sm text-slate-700 bg-slate-50 p-2 rounded border border-slate-100">
                                            <strong>Laudo:</strong> {rep.conclusion}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
};

export default DiagnosticResultWorkspace;

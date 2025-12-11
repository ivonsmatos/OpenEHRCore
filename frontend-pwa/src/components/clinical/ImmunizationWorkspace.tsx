
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import { Syringe, Plus, Calendar, CheckCircle } from 'lucide-react';

interface Immunization {
    id: string;
    vaccine_name: string;
    date: string;
    status: string;
    lot_number?: string;
}

const ImmunizationWorkspace = () => {
    const { id: patientId } = useParams();
    const { token } = useAuth();
    const [immunizations, setImmunizations] = useState<Immunization[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Form State
    const [formData, setFormData] = useState({
        vaccine_name: '',
        vaccine_code: '', // Simplified: user types name, we map to mock code for now
        date: new Date().toISOString().split('T')[0],
        lot_number: ''
    });

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    useEffect(() => {
        fetchImmunizations();
    }, [patientId]);

    const fetchImmunizations = async () => {
        try {
            const response = await axios.get(`${API_URL}/patients/${patientId}/immunizations/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setImmunizations(response.data);
        } catch (error) {
            console.error("Error fetching immunizations:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post(`${API_URL}/immunizations/`, {
                patient_id: patientId,
                vaccine_name: formData.vaccine_name,
                vaccine_code: "99", // Mock code
                date: formData.date,
                lot_number: formData.lot_number
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setShowForm(false);
            setFormData({ vaccine_name: '', vaccine_code: '', date: '', lot_number: '' });
            fetchImmunizations();
        } catch (error) {
            alert("Erro ao salvar vacina.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                        <Syringe className="text-pink-600" />
                        Carteira de Vacinação
                    </h2>
                    <p className="text-slate-600">Histórico de imunizações do paciente</p>
                </div>
                <Button onClick={() => setShowForm(!showForm)}>
                    <Plus size={16} className="mr-2" />
                    Nova Vacina
                </Button>
            </div>

            {showForm && (
                <Card className="p-6 bg-slate-50 border-pink-100">
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Nome da Vacina</label>
                                <input
                                    type="text"
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={formData.vaccine_name}
                                    onChange={e => setFormData({ ...formData, vaccine_name: e.target.value })}
                                    placeholder="Ex: Gripe (Influenza)"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Data da Aplicação</label>
                                <input
                                    type="date"
                                    required
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={formData.date}
                                    onChange={e => setFormData({ ...formData, date: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Lote (Opcional)</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={formData.lot_number}
                                    onChange={e => setFormData({ ...formData, lot_number: e.target.value })}
                                    placeholder="Ex: AB1234"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button variant="ghost" onClick={() => setShowForm(false)} type="button">Cancelar</Button>
                            <Button type="submit">Registrar Vacina</Button>
                        </div>
                    </form>
                </Card>
            )}

            <div className="grid gap-4">
                {loading ? (
                    <p>Carregando...</p>
                ) : immunizations.length === 0 ? (
                    <p className="text-slate-500 italic">Nenhuma vacina registrada.</p>
                ) : (
                    immunizations.map((imm) => (
                        <Card key={imm.id} className="p-4 flex justify-between items-center hover:shadow-md transition-shadow">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-pink-100 rounded-full text-pink-600">
                                    <Syringe size={20} />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-900">{imm.vaccine_name}</h3>
                                    <p className="text-sm text-slate-500 flex items-center gap-2">
                                        <Calendar size={14} /> {imm.date}
                                        {imm.lot_number && <span className="text-slate-400">| Lote: {imm.lot_number}</span>}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm font-medium">
                                <CheckCircle size={14} />
                                Aplicada
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
};

export default ImmunizationWorkspace;

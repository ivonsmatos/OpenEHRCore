import React, { useState } from 'react';
import axios from 'axios';
import { CreditCard, Save, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface CoverageFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

const CoverageForm: React.FC<CoverageFormProps> = ({ onSuccess, onCancel }) => {
    const { user } = useAuth();
    const [formData, setFormData] = useState({
        payor_name: '',
        subscriber_id: '',
        status: 'active'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await axios.post('/financial/coverage/', {
                patient_id: user?.id || 'patient-1', // Fallback for dev/demo
                ...formData
            });
            onSuccess();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.error || "Erro ao criar convênio.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-medium text-slate-900 mb-4 flex items-center gap-2">
                <CreditCard size={20} />
                Novo Convênio
            </h3>

            {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Seguradora / Convênio
                    </label>
                    <input
                        type="text"
                        name="payor_name"
                        required
                        placeholder="Ex: Unimed, Bradesco Saúde"
                        value={formData.payor_name}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Número da Carteirinha
                    </label>
                    <input
                        type="text"
                        name="subscriber_id"
                        required
                        placeholder="Ex: 000.123.456.789"
                        value={formData.subscriber_id}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Status
                    </label>
                    <select
                        name="status"
                        value={formData.status}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="active">Ativo</option>
                        <option value="cancelled">Cancelado</option>
                        <option value="draft">Rascunho</option>
                    </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-4 py-2 text-slate-700 hover:bg-slate-50 border border-slate-300 rounded-lg flex items-center gap-2"
                        disabled={loading}
                    >
                        <X size={18} />
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg flex items-center gap-2"
                    >
                        {loading ? 'Salvando...' : <><Save size={18} /> Salvar</>}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default CoverageForm;

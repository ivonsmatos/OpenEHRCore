import React, { useState } from 'react';
import axios from 'axios';
import { FileText, Save, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface InvoiceFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

const InvoiceForm: React.FC<InvoiceFormProps> = ({ onSuccess, onCancel }) => {
    const { user } = useAuth();
    const [formData, setFormData] = useState({
        total_gross: '',
        status: 'issued',
        description: '' // Not used in backend yet explicitly but good for future
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
            // Auto-create Account if needed or just link to user
            // Ideally we'd list accounts and pick one, but for simplicity let's assume auto-account creation in backend or optional
            await axios.post('/financial/invoices/', {
                patient_id: user?.id || 'patient-1',
                total_gross: parseFloat(formData.total_gross),
                status: formData.status
            });
            onSuccess();
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.error || "Erro ao criar fatura.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-medium text-slate-900 mb-4 flex items-center gap-2">
                <FileText size={20} />
                Nova Fatura
            </h3>

            {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Valor Total (R$)
                    </label>
                    <input
                        type="number"
                        name="total_gross"
                        step="0.01"
                        required
                        placeholder="0.00"
                        value={formData.total_gross}
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
                        <option value="issued">Emitida (Pendente)</option>
                        <option value="balanced">Paga</option>
                        <option value="cancelled">Cancelada</option>
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

export default InvoiceForm;

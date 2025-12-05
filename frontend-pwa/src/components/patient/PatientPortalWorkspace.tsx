import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { theme } from '../../theme/colors';
import { Button } from '../base/Button';
import Calendar from 'lucide-react/dist/esm/icons/calendar';
import Video from 'lucide-react/dist/esm/icons/video';
import FileText from 'lucide-react/dist/esm/icons/file-text';
import Activity from 'lucide-react/dist/esm/icons/activity';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Appointment {
    id: string;
    start: string;
    end: string;
    status: string;
    description?: string;
}

interface ExamResult {
    id: string;
    code: { text: string };
    valueQuantity?: { value: number; unit: string };
    effectiveDateTime: string;
}

export const PatientPortalWorkspace: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<{ appointments: Appointment[], exam_results: ExamResult[] } | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchDashboard();
    }, []);

    const fetchDashboard = async () => {
        try {
            // Assuming the token is already set in axios default headers or localStorage
            // For this specific view, we might need to ensure we are using the patient token
            // But let's assume the context switch happens globally
            const response = await axios.get(`${API_URL}/patient/dashboard/`);
            setData(response.data);
        } catch (err) {
            console.error(err);
            setError('Falha ao carregar dados do portal. Verifique se você está logado como paciente.');
        } finally {
            setLoading(false);
        }
    };

    const joinTelemedicine = (appointmentId: string) => {
        // In a real app, this would be a real video link.
        // For now, we simulate opening a Meet link
        window.open(`https://meet.google.com/new?authuser=${appointmentId}`, '_blank');
    };

    if (loading) return <div className="p-8 text-center text-neutral-dark">Carregando portal...</div>;
    if (error) return <div className="p-8 text-center text-alert-critical">{error}</div>;

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-8">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-dark to-primary-medium p-8 rounded-2xl shadow-lg text-white">
                <h1 className="text-3xl font-bold mb-2">Olá, Paciente! 👋</h1>
                <p className="opacity-90">Bem-vindo ao seu portal de saúde pessoal.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Appointments Section */}
                <section className="bg-white rounded-xl shadow-sm border border-border-light p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 bg-primary-light/10 rounded-lg text-primary-medium">
                            <Calendar size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-neutral-darkest">Seus Agendamentos</h2>
                    </div>

                    <div className="space-y-4">
                        {data?.appointments && data.appointments.length > 0 ? (
                            data.appointments.map((appt) => (
                                <div key={appt.id} className="group p-4 rounded-lg border border-border-default hover:border-primary-light transition-colors relative">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="font-semibold text-neutral-darkest">Consulta Geral</p>
                                            <p className="text-sm text-neutral-base">
                                                {new Date(appt.start).toLocaleString()}
                                            </p>
                                            <span className="inline-block mt-2 px-2 py-1 rounded text-xs font-medium bg-neutral-light text-neutral-dark">
                                                {appt.status}
                                            </span>
                                        </div>

                                        {/* Telemedicine Logic: Show button if it's a remote consulation (simulated) */}
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={() => joinTelemedicine(appt.id)}
                                            className="flex items-center gap-2"
                                        >
                                            <Video size={16} />
                                            Entrar na Sala
                                        </Button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="text-neutral-base italic">Nenhum agendamento futuro.</p>
                        )}
                    </div>
                </section>

                {/* Exams Section */}
                <section className="bg-white rounded-xl shadow-sm border border-border-light p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 bg-accent-primary/10 rounded-lg text-accent-primary">
                            <Activity size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-neutral-darkest">Resultados Recentes</h2>
                    </div>

                    <div className="space-y-4">
                        {data?.exam_results && data.exam_results.length > 0 ? (
                            data.exam_results.map((exam) => (
                                <div key={exam.id} className="p-4 rounded-lg bg-neutral-light/50 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <FileText size={20} className="text-neutral-base" />
                                        <div>
                                            <p className="font-medium text-neutral-darkest">{exam.code?.text || 'Exame'}</p>
                                            <p className="text-xs text-neutral-base">{new Date(exam.effectiveDateTime).toLocaleDateString()}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold text-primary-dark">
                                            {exam.valueQuantity ? `${exam.valueQuantity.value} ${exam.valueQuantity.unit}` : 'Ver laudo'}
                                        </p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="text-neutral-base italic">Nenhum resultado recente.</p>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
};

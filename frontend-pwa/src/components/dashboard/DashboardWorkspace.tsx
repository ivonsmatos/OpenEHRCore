
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Users, Calendar, FileText, DollarSign, Activity,
    TrendingUp, Plus
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import { useNavigate } from 'react-router-dom';

const StatsCard = ({ title, value, icon: Icon, trend, color }: any) => (
    <Card className="border-l-4 w-full min-w-0" style={{ borderLeftColor: color }}>
        <div className="p-4 flex justify-between items-start">
            <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1 truncate">{value}</h3>
                {trend && (
                    <span className="inline-flex items-center text-xs font-medium text-green-600 mt-2 bg-green-50 px-2 py-1 rounded-full">
                        <TrendingUp size={12} className="mr-1" />
                        {trend}
                    </span>
                )}
            </div>
            <div className={`p-3 rounded-full bg-opacity-10 flex-shrink-0`} style={{ backgroundColor: `${color}20` }}>
                <Icon size={24} style={{ color: color }} />
            </div>
        </div>
    </Card>
);

const DashboardWorkspace = () => {
    const { token, user } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    // Mock data for charts (backend service for this is complex, simulating for UI)
    const lineData = [
        { name: 'Seg', atendimentos: 4 },
        { name: 'Ter', atendimentos: 3 },
        { name: 'Qua', atendimentos: 7 },
        { name: 'Qui', atendimentos: 5 },
        { name: 'Sex', atendimentos: 8 },
    ];

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await axios.get(`${API_URL}/analytics/dashboard/`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                setStats(response.data);
            } catch (error) {
                console.error("Error fetching dashboard stats:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, [token]);

    if (loading) return <div className="p-8 text-center text-gray-500">Carregando painel...</div>;

    return (
        <div className="space-y-6 w-full max-w-full overflow-hidden">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Olá, Dr. {user?.username}</h1>
                    <p className="text-slate-600">Aqui está o resumo da sua clínica hoje.</p>
                </div>
                <div className="flex gap-2">
                    <Button size="sm" onClick={() => navigate('/appointments')}>
                        <Plus size={16} className="mr-1" />
                        Agendar
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                <StatsCard
                    title="Pacientes Ativos"
                    value={stats?.stats?.patients || 0}
                    icon={Users}
                    color="#4F46E5" // Indigo
                    trend={stats?.trends?.patients}
                />
                <StatsCard
                    title="Consultas Hoje"
                    value={stats?.stats?.appointments_today || 0}
                    icon={Calendar}
                    color="#0EA5E9" // Sky
                />
                <StatsCard
                    title="Documentos"
                    value={stats?.stats?.documents || 0}
                    icon={FileText}
                    color="#8B5CF6" // Violet
                />
                <StatsCard
                    title="Faturas Geradas"
                    value={stats?.stats?.invoices_count || 0}
                    icon={DollarSign}
                    color="#10B981" // Emerald
                    trend={stats?.trends?.revenue}
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
                <div className="lg:col-span-2 w-full min-w-0">
                    <Card className="h-96 flex flex-col w-full">
                        <div className="p-4 border-b">
                            <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                                <Activity size={18} className="text-indigo-600" />
                                Evolução de Atendimentos (Semanal)
                            </h3>
                        </div>
                        <div className="flex-1 p-4 w-full overflow-hidden" style={{ minHeight: 280 }}>
                            <ResponsiveContainer width="100%" height="100%" minHeight={250}>
                                <LineChart data={lineData} margin={{ left: 0, right: 10, top: 5, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B' }} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B' }} />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="atendimentos"
                                        stroke="#4F46E5"
                                        strokeWidth={3}
                                        dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
                                        activeDot={{ r: 6 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </Card>
                </div>

                <div className="w-full min-w-0">
                    <Card className="h-96">
                        <div className="p-4 border-b">
                            <h3 className="font-semibold text-slate-800">Acesso Rápido</h3>
                        </div>
                        <div className="p-4 space-y-3">
                            <button
                                onClick={() => navigate('/patients')}
                                className="w-full text-left p-3 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all group"
                            >
                                <h4 className="font-medium text-slate-900 group-hover:text-indigo-600">Novo Paciente</h4>
                                <p className="text-xs text-slate-500">Cadastrar ficha completa</p>
                            </button>
                            <button
                                onClick={() => navigate('/documents')}
                                className="w-full text-left p-3 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all group"
                            >
                                <h4 className="font-medium text-slate-900 group-hover:text-indigo-600">Novo Atestado/Receita</h4>
                                <p className="text-xs text-slate-500">Emitir documento rápido</p>
                            </button>
                            <button
                                onClick={() => navigate('/financial')}
                                className="w-full text-left p-3 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all group"
                            >
                                <h4 className="font-medium text-slate-900 group-hover:text-indigo-600">Lançar Pagamento</h4>
                                <p className="text-xs text-slate-500">Registrar nova fatura</p>
                            </button>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default DashboardWorkspace;

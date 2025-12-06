
import React, { useEffect, useState } from 'react';
import {
    AreaChart, Area,
    LineChart, Line,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { colors, spacing } from '../../theme/colors';
import Card from '../base/Card';
import { Activity, Users, Clipboard, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import LoadingVitalSign from '../base/LoadingVitalSign';

const MedicalDashboard: React.FC = () => {
    const navigate = useNavigate();
    const { token } = useAuth();
    const [kpiData, setKpiData] = useState<any>(null);
    const [surveyData, setSurveyData] = useState<any>(null);
    const [clinicalData, setClinicalData] = useState<any>(null);
    const [admissionsData, setAdmissionsData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const headers = {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/json'
                };

                const API_BASE = 'http://localhost:8000/api/v1';
                const [resKpi, resSurvey, resClin] = await Promise.all([
                    fetch(`${API_BASE}/analytics/kpi/`, { headers }),
                    fetch(`${API_BASE}/analytics/survey/`, { headers }),
                    fetch(`${API_BASE}/analytics/clinical/`, { headers })
                ]);

                if (resKpi.status === 401) {
                    console.warn("Unauthorized! Redirecting...");
                    window.location.href = '/login';
                    return;
                }

                if (resKpi.ok) {
                    const text = await resKpi.text();
                    try {
                        setKpiData(JSON.parse(text));
                    } catch (e) {
                        console.error("KPI JSON Parse Error. Response:", text.substring(0, 200));
                    }
                }
                if (resSurvey.ok) {
                    try {
                        setSurveyData(await resSurvey.json());
                    } catch (e) { console.error("Survey JSON Error", e); }
                }
                if (resClin.ok) {
                    try {
                        setClinicalData(await resClin.json());
                    } catch (e) { console.error("Clinical JSON Error", e); }
                }

                // Fetch Admissions
                const resAdm = await fetch(`${API_BASE}/analytics/admissions/`, { headers });
                if (resAdm.ok) {
                    setAdmissionsData(await resAdm.json());
                }
            } catch (err) {
                console.error("Failed to load dashboard data", err);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) return <LoadingVitalSign text="Sincronizando dados hospitalares..." />;

    // Data for charts
    const surveyChartData = surveyData?.labels.map((label: string, index: number) => ({
        name: label,
        patients: surveyData.series[0].data[index],
        recovery: surveyData.series[1].data[index]
    })) || [];

    const conditionsData = clinicalData?.top_conditions || [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>

            {/* Header Section */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: colors.text.primary, marginBottom: '4px' }}>Dashboard</h1>
                    <p style={{ fontSize: '0.875rem', color: colors.text.tertiary }}>Bem-vindo ao Sistema de Gestão Hospitalar</p>
                </div>
                <div style={{ display: 'flex', gap: spacing.sm }}>
                    <button style={{ padding: '8px 16px', backgroundColor: '#EFF6FF', color: colors.primary.medium, border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Home</button>
                    <button style={{ padding: '8px 16px', backgroundColor: 'transparent', color: colors.text.secondary, border: 'none', cursor: 'pointer' }}>Dashboard</button>
                </div>
            </div>

            {/* Top KPI Cards Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: spacing.lg }}>

                {/* New Patients */}
                <Card padding="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: colors.text.primary }}>Novos Pacientes</h3>
                            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#10B981', marginTop: spacing.sm }}>{kpiData?.new_patients || 0}</div>
                        </div>
                        <div style={{ padding: '10px', backgroundColor: '#D1FAE5', borderRadius: '50%', color: '#10B981' }}>
                            <UserPlus size={20} />
                        </div>
                    </div>
                    <div style={{ marginTop: spacing.md, height: '4px', background: '#E5E7EB', borderRadius: '2px' }}>
                        <div style={{ width: '65%', height: '100%', background: '#10B981', borderRadius: '2px' }}></div>
                    </div>
                </Card>

                {/* OPD Patients */}
                <Card padding="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: colors.text.primary }}>Pacientes Ambulatório</h3>
                            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#F59E0B', marginTop: spacing.sm }}>{kpiData?.opd_patients || 0}</div>
                        </div>
                        <div style={{ padding: '10px', backgroundColor: '#FEF3C7', borderRadius: '50%', color: '#F59E0B' }}>
                            <Clipboard size={20} />
                        </div>
                    </div>
                    <div style={{ marginTop: spacing.md, height: '4px', background: '#E5E7EB', borderRadius: '2px' }}>
                        <div style={{ width: '45%', height: '100%', background: '#F59E0B', borderRadius: '2px' }}></div>
                    </div>
                </Card>

                {/* Operations */}
                <Card padding="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: colors.text.primary }}>Cirurgias Hoje</h3>
                            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#EF4444', marginTop: spacing.sm }}>{kpiData?.todays_operations || 0}</div>
                        </div>
                        <div style={{ padding: '10px', backgroundColor: '#FEE2E2', borderRadius: '50%', color: '#EF4444' }}>
                            <Activity size={20} />
                        </div>
                    </div>
                    <div style={{ marginTop: spacing.md, height: '4px', background: '#E5E7EB', borderRadius: '2px' }}>
                        <div style={{ width: '30%', height: '100%', background: '#EF4444', borderRadius: '2px' }}></div>
                    </div>
                </Card>

                {/* Visitors */}
                <Card padding="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: colors.text.primary }}>Visitantes</h3>
                            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#3B82F6', marginTop: spacing.sm }}>{kpiData?.visitors || 0}</div>
                        </div>
                        <div style={{ padding: '10px', backgroundColor: '#DBEAFE', borderRadius: '50%', color: '#3B82F6' }}>
                            <Users size={20} />
                        </div>
                    </div>
                    <div style={{ marginTop: spacing.md, height: '4px', background: '#E5E7EB', borderRadius: '2px' }}>
                        <div style={{ width: '80%', height: '100%', background: '#3B82F6', borderRadius: '2px' }}></div>
                    </div>
                </Card>
            </div>

            {/* Main Charts Section */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: spacing.lg }}>

                {/* Hospital Survey Chart */}
                <Card padding="lg">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: spacing.lg }}>
                        <h3 style={{ fontWeight: 600, color: colors.text.primary }}>Pesquisa Hospitalar</h3>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            {/* Legend placeholders */}
                        </div>
                    </div>
                    <div style={{ height: '300px', width: '100%', minHeight: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={surveyChartData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} dy={10} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} />
                                <Line type="monotone" dataKey="patients" stroke="#6366F1" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                                <Line type="monotone" dataKey="recovery" stroke="#A5B4FC" strokeWidth={3} strokeDasharray="5 5" dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </Card>

                {/* Heart Surgeries / Clinical Stats */}
                <Card padding="lg">
                    <h3 style={{ fontWeight: 600, color: colors.text.primary, marginBottom: spacing.lg }}>Tratamentos Médicos (Top Condições)</h3>
                    <div style={{ height: '300px', width: '100%', minHeight: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={conditionsData}>
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="name" hide />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                                <Tooltip />
                                <Area type="monotone" dataKey="value" stroke="#10B981" fillOpacity={1} fill="url(#colorValue)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </Card>
            </div>

            {/* Admit Patient List (Placeholder for now, can be populated with real Encounter data later) */}
            <Card padding="lg">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md }}>
                    <h3 style={{ fontWeight: 600, color: colors.text.primary }}>Lista de Admissão de Pacientes</h3>
                </div>
                {/* Mock Table purely for visual compliance with request */}
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #E5E7EB', textAlign: 'left', color: colors.text.tertiary }}>
                            <th style={{ padding: '12px' }}>No</th>
                            <th style={{ padding: '12px' }}>Nome</th>
                            <th style={{ padding: '12px' }}>Médico</th>
                            <th style={{ padding: '12px' }}>Data Admissão</th>
                            <th style={{ padding: '12px' }}>Motivo</th>
                            <th style={{ padding: '12px' }}>Quarto</th>
                            <th style={{ padding: '12px' }}>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        {admissionsData.length > 0 ? admissionsData.map((adm: any) => (
                            <tr key={adm.id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                                <td style={{ padding: '12px' }}>{adm.no}</td>
                                <td style={{ padding: '12px', fontWeight: 500 }}>{adm.name}</td>
                                <td style={{ padding: '12px' }}>{adm.doctor}</td>
                                <td style={{ padding: '12px' }}>{adm.date}</td>
                                <td style={{ padding: '12px' }}>
                                    <span style={{ padding: '4px 8px', borderRadius: '4px', backgroundColor: '#D1FAE5', color: '#065F46', fontSize: '0.75rem' }}>
                                        {adm.condition}
                                    </span>
                                </td>
                                <td style={{ padding: '12px' }}>{adm.room}</td>
                                <td style={{ padding: '12px', cursor: 'pointer' }} onClick={() => navigate(`/patients/${adm.patient_id}`)}>✏️</td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan={7} style={{ padding: '20px', textAlign: 'center', color: '#9CA3AF' }}>Nenhuma admissão recente encontrada.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </Card>

        </div>
    );
};

export const DashboardWorkspace = MedicalDashboard;

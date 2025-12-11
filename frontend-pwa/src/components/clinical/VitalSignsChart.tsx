import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Area,
    AreaChart,
} from 'recharts';
import { Activity, TrendingUp, Calendar, ChevronDown } from 'lucide-react';
import Card from '../base/Card';
import './VitalSignsChart.css';

interface VitalSignsChartProps {
    patientId: string;
}

interface VitalReading {
    date: string;
    dateDisplay: string;
    systolic?: number;
    diastolic?: number;
    heartRate?: number;
    temperature?: number;
    spo2?: number;
    respiratoryRate?: number;
    weight?: number;
}

type ChartType = 'bloodPressure' | 'heartRate' | 'temperature' | 'spo2' | 'respiratory' | 'weight';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * VitalSignsChart - Gráficos de evolução dos sinais vitais
 * 
 * Exibe gráficos de linha para visualizar a evolução temporal de:
 * - Pressão arterial (sistólica/diastólica)
 * - Frequência cardíaca
 * - Temperatura
 * - Saturação O2
 * - Frequência respiratória
 * - Peso
 */
export const VitalSignsChart: React.FC<VitalSignsChartProps> = ({ patientId }) => {
    const [observations, setObservations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedChart, setSelectedChart] = useState<ChartType>('bloodPressure');
    const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

    useEffect(() => {
        const fetchVitals = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('access_token');
                const response = await axios.get(
                    `${API_BASE}/patients/${patientId}/observations/`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                setObservations(response.data || []);
                setError(null);
            } catch (err) {
                console.error('Erro ao buscar vitais:', err);
                setError('Não foi possível carregar os sinais vitais');
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchVitals();
        }
    }, [patientId]);

    // Processar observações para formato de gráfico
    const chartData = useMemo(() => {
        const dataMap = new Map<string, VitalReading>();

        observations.forEach((obs: any) => {
            const date = obs.effectiveDateTime?.split('T')[0];
            if (!date) return;

            const existing: VitalReading = dataMap.get(date) || {
                date,
                dateDisplay: new Date(date).toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: 'short'
                }),
            };

            const code = obs.code?.coding?.[0]?.code || '';
            const value = obs.valueQuantity?.value;

            // Mapear códigos LOINC para propriedades
            if (code.includes('85354-9') || code.includes('blood-pressure')) {
                // Blood pressure - pode ter componentes
                obs.component?.forEach((comp: any) => {
                    const compCode = comp.code?.coding?.[0]?.code || '';
                    if (compCode.includes('8480-6') || compCode.includes('systolic')) {
                        existing.systolic = comp.valueQuantity?.value;
                    }
                    if (compCode.includes('8462-4') || compCode.includes('diastolic')) {
                        existing.diastolic = comp.valueQuantity?.value;
                    }
                });
            } else if (code.includes('8867-4') || code.includes('heart')) {
                existing.heartRate = value;
            } else if (code.includes('8310-5') || code.includes('temperature')) {
                existing.temperature = value;
            } else if (code.includes('59408-5') || code.includes('spo2') || code.includes('oxygen')) {
                existing.spo2 = value;
            } else if (code.includes('9279-1') || code.includes('respiratory')) {
                existing.respiratoryRate = value;
            } else if (code.includes('29463-7') || code.includes('weight')) {
                existing.weight = value;
            }

            dataMap.set(date, existing);
        });

        // Ordenar por data
        return Array.from(dataMap.values())
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .filter((item) => {
                if (dateRange === 'all') return true;
                const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90;
                const cutoff = new Date();
                cutoff.setDate(cutoff.getDate() - days);
                return new Date(item.date) >= cutoff;
            });
    }, [observations, dateRange]);

    const chartOptions: { key: ChartType; label: string; available: boolean }[] = [
        { key: 'bloodPressure', label: 'Pressão Arterial', available: chartData.some(d => d.systolic) },
        { key: 'heartRate', label: 'Freq. Cardíaca', available: chartData.some(d => d.heartRate) },
        { key: 'temperature', label: 'Temperatura', available: chartData.some(d => d.temperature) },
        { key: 'spo2', label: 'Saturação O₂', available: chartData.some(d => d.spo2) },
        { key: 'respiratory', label: 'Freq. Respiratória', available: chartData.some(d => d.respiratoryRate) },
        { key: 'weight', label: 'Peso', available: chartData.some(d => d.weight) },
    ];

    const renderChart = () => {
        if (chartData.length === 0) {
            return (
                <div className="chart-empty">
                    <Activity size={48} />
                    <p>Nenhum dado disponível para o período selecionado</p>
                </div>
            );
        }

        switch (selectedChart) {
            case 'bloodPressure':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis domain={[40, 200]} stroke="#6b7280" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                                }}
                            />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="systolic"
                                name="Sistólica"
                                stroke="#ef4444"
                                strokeWidth={2}
                                dot={{ fill: '#ef4444', r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="diastolic"
                                name="Diastólica"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={{ fill: '#3b82f6', r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'heartRate':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis domain={[40, 140]} stroke="#6b7280" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px'
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="heartRate"
                                name="Freq. Cardíaca (bpm)"
                                stroke="#ef4444"
                                fill="rgba(239, 68, 68, 0.2)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                );

            case 'temperature':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis domain={[35, 41]} stroke="#6b7280" fontSize={12} />
                            <Tooltip />
                            <Line
                                type="monotone"
                                dataKey="temperature"
                                name="Temperatura (°C)"
                                stroke="#f59e0b"
                                strokeWidth={2}
                                dot={{ fill: '#f59e0b', r: 4 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'spo2':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis domain={[85, 100]} stroke="#6b7280" fontSize={12} />
                            <Tooltip />
                            <Area
                                type="monotone"
                                dataKey="spo2"
                                name="SpO₂ (%)"
                                stroke="#3b82f6"
                                fill="rgba(59, 130, 246, 0.2)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                );

            case 'respiratory':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis domain={[8, 30]} stroke="#6b7280" fontSize={12} />
                            <Tooltip />
                            <Line
                                type="monotone"
                                dataKey="respiratoryRate"
                                name="Freq. Respiratória (rpm)"
                                stroke="#10b981"
                                strokeWidth={2}
                                dot={{ fill: '#10b981', r: 4 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                );

            case 'weight':
                return (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis dataKey="dateDisplay" stroke="#6b7280" fontSize={12} />
                            <YAxis stroke="#6b7280" fontSize={12} />
                            <Tooltip />
                            <Area
                                type="monotone"
                                dataKey="weight"
                                name="Peso (kg)"
                                stroke="#8b5cf6"
                                fill="rgba(139, 92, 246, 0.2)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                );

            default:
                return null;
        }
    };

    if (loading) {
        return (
            <Card className="vitals-chart-card">
                <div className="chart-loading">
                    <TrendingUp size={32} className="loading-icon" />
                    <p>Carregando gráficos...</p>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="vitals-chart-card">
                <div className="chart-error">{error}</div>
            </Card>
        );
    }

    return (
        <Card className="vitals-chart-card">
            <div className="chart-header">
                <div className="chart-title">
                    <TrendingUp size={20} />
                    <h3>Evolução dos Sinais Vitais</h3>
                </div>

                <div className="chart-controls">
                    <div className="date-range-selector">
                        <Calendar size={16} />
                        <select
                            value={dateRange}
                            onChange={(e) => setDateRange(e.target.value as any)}
                            aria-label="Período de análise"
                        >
                            <option value="7d">Últimos 7 dias</option>
                            <option value="30d">Últimos 30 dias</option>
                            <option value="90d">Últimos 90 dias</option>
                            <option value="all">Todo o histórico</option>
                        </select>
                        <ChevronDown size={14} />
                    </div>
                </div>
            </div>

            <div className="chart-tabs">
                {chartOptions.map((opt) => (
                    <button
                        key={opt.key}
                        className={`chart-tab ${selectedChart === opt.key ? 'active' : ''} ${!opt.available ? 'disabled' : ''}`}
                        onClick={() => opt.available && setSelectedChart(opt.key)}
                        disabled={!opt.available}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            <div className="chart-container">
                {renderChart()}
            </div>

            {chartData.length > 0 && (
                <div className="chart-stats">
                    <div className="stat-item">
                        <span className="stat-label">Período</span>
                        <span className="stat-value">
                            {chartData[0]?.dateDisplay} - {chartData[chartData.length - 1]?.dateDisplay}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Medições</span>
                        <span className="stat-value">{chartData.length}</span>
                    </div>
                </div>
            )}
        </Card>
    );
};

export default VitalSignsChart;

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
    Calendar,
    Activity,
    Pill,
    Stethoscope,
    FileText,
    AlertCircle,
    ChevronDown,
    ChevronUp,
    Filter,
    Clock
} from 'lucide-react';
import { colors } from '../../theme/colors';
import './PatientTimeline.css';

interface TimelineEvent {
    id: string;
    type: 'encounter' | 'observation' | 'condition' | 'medication' | 'procedure' | 'immunization';
    date: string;
    title: string;
    description?: string;
    status?: string;
    data: Record<string, unknown>;
}

interface PatientTimelineProps {
    patientId: string;
    patientName?: string;
}

const EVENT_ICONS: Record<string, typeof Activity> = {
    encounter: Calendar,
    observation: Activity,
    condition: AlertCircle,
    medication: Pill,
    procedure: Stethoscope,
    immunization: FileText
};

const EVENT_COLORS: Record<string, string> = {
    encounter: '#3b82f6',  // blue
    observation: '#10b981', // green
    condition: '#f59e0b',   // amber
    medication: '#8b5cf6',  // purple
    procedure: '#ec4899',   // pink
    immunization: '#06b6d4' // cyan
};

const EVENT_LABELS: Record<string, string> = {
    encounter: 'Consulta',
    observation: 'Observação',
    condition: 'Condição',
    medication: 'Medicação',
    procedure: 'Procedimento',
    immunization: 'Imunização'
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function PatientTimeline({ patientId, patientName }: PatientTimelineProps) {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>('all');
    const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
    const [showFilters, setShowFilters] = useState(false);

    const parseDate = (resource: Record<string, unknown>): string => {
        // Tentar diferentes campos de data comuns em recursos FHIR
        const dateFields = [
            'effectiveDateTime',
            'performedDateTime',
            'occurrenceDateTime',
            'recordedDate',
            'authoredOn',
            'onsetDateTime',
            'period.start',
            'meta.lastUpdated'
        ];

        for (const field of dateFields) {
            if (field.includes('.')) {
                const [parent, child] = field.split('.');
                const parentObj = resource[parent] as Record<string, unknown> | undefined;
                if (parentObj?.[child]) return parentObj[child] as string;
            } else if (resource[field]) {
                return resource[field] as string;
            }
        }

        return new Date().toISOString();
    };

    const getTitle = (resource: Record<string, unknown>, type: string): string => {
        switch (type) {
            case 'encounter': {
                const typeArr = resource.type as Array<{ text?: string; coding?: Array<{ display?: string }> }> | undefined;
                return typeArr?.[0]?.text || typeArr?.[0]?.coding?.[0]?.display || 'Consulta';
            }
            case 'observation': {
                const code = resource.code as { text?: string; coding?: Array<{ display?: string }> } | undefined;
                return code?.text || code?.coding?.[0]?.display || 'Observação';
            }
            case 'condition': {
                const code = resource.code as { text?: string; coding?: Array<{ display?: string }> } | undefined;
                return code?.text || code?.coding?.[0]?.display || 'Condição';
            }
            case 'medication': {
                const med = resource.medicationCodeableConcept as { text?: string; coding?: Array<{ display?: string }> } | undefined;
                return med?.text || med?.coding?.[0]?.display || 'Medicação';
            }
            case 'procedure': {
                const code = resource.code as { text?: string; coding?: Array<{ display?: string }> } | undefined;
                return code?.text || code?.coding?.[0]?.display || 'Procedimento';
            }
            case 'immunization': {
                const vaccine = resource.vaccineCode as { text?: string; coding?: Array<{ display?: string }> } | undefined;
                return vaccine?.text || vaccine?.coding?.[0]?.display || 'Vacina';
            }
            default:
                return 'Evento';
        }
    };

    const getDescription = (resource: Record<string, unknown>, type: string): string | undefined => {
        switch (type) {
            case 'observation': {
                const value = resource.valueQuantity as { value?: number; unit?: string } | undefined;
                if (value) return `${value.value} ${value.unit || ''}`;
                const valueStr = resource.valueString as string | undefined;
                return valueStr;
            }
            case 'medication': {
                const dosage = resource.dosageInstruction as Array<{ text?: string }> | undefined;
                return dosage?.[0]?.text;
            }
            case 'condition': {
                const clinStatus = resource.clinicalStatus as { coding?: Array<{ code?: string }> } | undefined;
                return clinStatus?.coding?.[0]?.code;
            }
            default:
                return undefined;
        }
    };

    const fetchTimelineData = useCallback(async () => {
        if (!patientId) return;

        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            // Buscar todos os tipos de recursos em paralelo
            const [
                encountersRes,
                observationsRes,
                conditionsRes,
                medicationsRes,
                proceduresRes,
                immunizationsRes
            ] = await Promise.allSettled([
                axios.get(`${API_BASE}/patients/${patientId}/encounters/`, { headers }),
                axios.get(`${API_BASE}/patients/${patientId}/observations/`, { headers }),
                axios.get(`${API_BASE}/patients/${patientId}/conditions/`, { headers }),
                axios.get(`${API_BASE}/patients/${patientId}/medications/`, { headers }),
                axios.get(`${API_BASE}/patients/${patientId}/procedures/`, { headers }),
                axios.get(`${API_BASE}/patients/${patientId}/immunizations/`, { headers })
            ]);

            const allEvents: TimelineEvent[] = [];

            // Processar encounters
            if (encountersRes.status === 'fulfilled') {
                const data = encountersRes.value.data.encounters || encountersRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `encounter-${r.id}`,
                        type: 'encounter',
                        date: parseDate(r),
                        title: getTitle(r, 'encounter'),
                        status: r.status as string,
                        data: r
                    });
                });
            }

            // Processar observations
            if (observationsRes.status === 'fulfilled') {
                const data = observationsRes.value.data.observations || observationsRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `observation-${r.id}`,
                        type: 'observation',
                        date: parseDate(r),
                        title: getTitle(r, 'observation'),
                        description: getDescription(r, 'observation'),
                        status: r.status as string,
                        data: r
                    });
                });
            }

            // Processar conditions
            if (conditionsRes.status === 'fulfilled') {
                const data = conditionsRes.value.data.conditions || conditionsRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `condition-${r.id}`,
                        type: 'condition',
                        date: parseDate(r),
                        title: getTitle(r, 'condition'),
                        description: getDescription(r, 'condition'),
                        data: r
                    });
                });
            }

            // Processar medications
            if (medicationsRes.status === 'fulfilled') {
                const data = medicationsRes.value.data.medications || medicationsRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `medication-${r.id}`,
                        type: 'medication',
                        date: parseDate(r),
                        title: getTitle(r, 'medication'),
                        description: getDescription(r, 'medication'),
                        status: r.status as string,
                        data: r
                    });
                });
            }

            // Processar procedures
            if (proceduresRes.status === 'fulfilled') {
                const data = proceduresRes.value.data.procedures || proceduresRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `procedure-${r.id}`,
                        type: 'procedure',
                        date: parseDate(r),
                        title: getTitle(r, 'procedure'),
                        status: r.status as string,
                        data: r
                    });
                });
            }

            // Processar immunizations
            if (immunizationsRes.status === 'fulfilled') {
                const data = immunizationsRes.value.data.immunizations || immunizationsRes.value.data || [];
                data.forEach((r: Record<string, unknown>) => {
                    allEvents.push({
                        id: `immunization-${r.id}`,
                        type: 'immunization',
                        date: parseDate(r),
                        title: getTitle(r, 'immunization'),
                        status: r.status as string,
                        data: r
                    });
                });
            }

            // Ordenar por data (mais recente primeiro)
            allEvents.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

            setEvents(allEvents);
        } catch (err) {
            setError('Erro ao carregar timeline do paciente');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [patientId]);

    useEffect(() => {
        fetchTimelineData();
    }, [fetchTimelineData]);

    const filteredEvents = filter === 'all'
        ? events
        : events.filter(e => e.type === filter);

    const toggleExpand = (id: string) => {
        const newExpanded = new Set(expandedEvents);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedEvents(newExpanded);
    };

    const formatDate = (dateStr: string): string => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    };

    const groupEventsByMonth = (events: TimelineEvent[]): Map<string, TimelineEvent[]> => {
        const groups = new Map<string, TimelineEvent[]>();

        events.forEach(event => {
            const date = new Date(event.date);
            const key = date.toLocaleDateString('pt-BR', { year: 'numeric', month: 'long' });

            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key)!.push(event);
        });

        return groups;
    };

    const groupedEvents = groupEventsByMonth(filteredEvents);

    return (
        <div className="patient-timeline">
            <header className="timeline-header">
                <div className="header-info">
                    <Clock size={24} color={colors.primary.medium} />
                    <div>
                        <h2>Timeline Clínica</h2>
                        {patientName && <span className="patient-name">{patientName}</span>}
                    </div>
                </div>

                <button
                    className="filter-toggle"
                    onClick={() => setShowFilters(!showFilters)}
                    aria-expanded={showFilters ? 'true' : 'false'}
                >
                    <Filter size={18} />
                    Filtros
                    {showFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
            </header>

            {showFilters && (
                <div className="filters-panel">
                    <button
                        className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        Todos ({events.length})
                    </button>
                    {Object.entries(EVENT_LABELS).map(([key, label]) => {
                        const count = events.filter(e => e.type === key).length;
                        if (count === 0) return null;
                        return (
                            <button
                                key={key}
                                className={`filter-btn ${filter === key ? 'active' : ''}`}
                                onClick={() => setFilter(key)}
                                style={{ '--event-color': EVENT_COLORS[key] } as React.CSSProperties}
                            >
                                {label} ({count})
                            </button>
                        );
                    })}
                </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <div className="timeline-content">
                {loading ? (
                    <div className="loading">
                        <div className="loading-spinner" />
                        Carregando timeline...
                    </div>
                ) : filteredEvents.length === 0 ? (
                    <div className="empty-state">
                        <Clock size={48} />
                        <p>Nenhum evento encontrado</p>
                    </div>
                ) : (
                    Array.from(groupedEvents.entries()).map(([month, monthEvents]) => (
                        <div key={month} className="timeline-month">
                            <h3 className="month-header">{month}</h3>
                            <div className="timeline-events">
                                {monthEvents.map(event => {
                                    const Icon = EVENT_ICONS[event.type] || Activity;
                                    const color = EVENT_COLORS[event.type] || colors.primary.medium;
                                    const isExpanded = expandedEvents.has(event.id);

                                    return (
                                        <div
                                            key={event.id}
                                            className="timeline-event"
                                            style={{ '--event-color': color } as React.CSSProperties}
                                        >
                                            <div className="event-marker">
                                                <div className="marker-icon" style={{ backgroundColor: color }}>
                                                    <Icon size={16} color="white" />
                                                </div>
                                                <div className="marker-line" />
                                            </div>

                                            <div className="event-content" onClick={() => toggleExpand(event.id)}>
                                                <div className="event-header">
                                                    <div className="event-info">
                                                        <span className="event-type" style={{ color }}>
                                                            {EVENT_LABELS[event.type]}
                                                        </span>
                                                        <h4 className="event-title">{event.title}</h4>
                                                        {event.description && (
                                                            <p className="event-description">{event.description}</p>
                                                        )}
                                                    </div>
                                                    <div className="event-meta">
                                                        <span className="event-date">{formatDate(event.date)}</span>
                                                        {event.status && (
                                                            <span className={`event-status status-${event.status}`}>
                                                                {event.status}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>

                                                {isExpanded && (
                                                    <div className="event-details">
                                                        <pre>{JSON.stringify(event.data, null, 2)}</pre>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default PatientTimeline;

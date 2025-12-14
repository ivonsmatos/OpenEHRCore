import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Header from '../base/Header';
import Button from '../base/Button';
import Card from '../base/Card';
import CalendarView from './CalendarView';
import { AvailabilityManager } from './AvailabilityManager';
import { useScheduling } from '../../hooks/useScheduling';
import { usePractitioners } from '../../hooks/usePractitioners';
import { usePatients } from '../../hooks/usePatients';
import { useIsMobile } from '../../hooks/useMediaQuery';
import { colors, spacing } from '../../theme/colors';
import { Calendar, Clock, User, Plus } from 'lucide-react';

interface Practitioner {
    id: string;
    name: string;
    specialty?: string;
}

interface Patient {
    id: string;
    name: string;
}

const SchedulingWorkspace: React.FC = () => {
    const { slots, fetchSlots, createSchedule, createSlot, createAppointment, loading } = useScheduling();
    const { fetchPractitioners, loading: loadingPractitioners } = usePractitioners();
    const { fetchPatients, loading: loadingPatients } = usePatients();
    const isMobile = useIsMobile();
    
    const [searchParams] = useSearchParams();
    const [activeTab, setActiveTab] = useState<'calendar' | 'availability' | 'new-appointment'>('new-appointment');
    
    // Form state
    const [selectedPractitioner, setSelectedPractitioner] = useState<string>('');
    const [selectedPatient, setSelectedPatient] = useState<string>('');
    const [appointmentDate, setAppointmentDate] = useState('');
    const [appointmentTime, setAppointmentTime] = useState('');
    const [appointmentDuration, setAppointmentDuration] = useState('30');
    const [appointmentReason, setAppointmentReason] = useState('');
    const [practitionersList, setPractitionersList] = useState<Practitioner[]>([]);
    const [patientsList, setPatientsList] = useState<Patient[]>([]);

    useEffect(() => {
        const loadData = async () => {
            // Load slots
            fetchSlots();
            
            // Load practitioners
            try {
                const response = await fetchPractitioners();
                const practitioners = response.results || response.practitioners || [];
                
                const pracs = practitioners.map((p: any) => {
                    const resource = p.resource || p;
                    const id = resource.id;
                    
                    let name = 'Profissional';
                    if (resource.name && resource.name[0]) {
                        const n = resource.name[0];
                        const given = n.given?.join(' ') || '';
                        const family = n.family || '';
                        name = `${given} ${family}`.trim() || `Dr(a). ${id}`;
                    }
                    
                    let specialty = '';
                    if (resource.qualification && resource.qualification[0]) {
                        specialty = resource.qualification[0].code?.text ||
                            resource.qualification[0].code?.coding?.[0]?.display || '';
                    }
                    
                    return { id, name, specialty };
                });
                
                setPractitionersList(pracs);
                
                // Check URL param for pre-selected practitioner
                const practitionerParam = searchParams.get('practitioner');
                if (practitionerParam) {
                    setSelectedPractitioner(practitionerParam);
                }
            } catch (error) {
                console.error('Error loading practitioners:', error);
            }
            
            // Load patients
            try {
                const response = await fetchPatients(1, 100, {});
                if (response && response.results) {
                    const patients = response.results;
                    
                    const pats = patients.map((p: any) => {
                        const resource = p.resource || p;
                        const id = resource.id;
                        
                        let name = 'Paciente';
                        if (resource.name && resource.name[0]) {
                            const n = resource.name[0];
                            const given = n.given?.join(' ') || '';
                            const family = n.family || '';
                            name = `${given} ${family}`.trim() || `Paciente ${id}`;
                        }
                        
                        return { id, name };
                    });
                    
                    setPatientsList(pats);
                }
            } catch (error) {
                console.error('Error loading patients:', error);
            }
        };
        
        loadData();
    }, []);

    const handleCreateAppointment = async () => {
        if (!selectedPractitioner || !selectedPatient || !appointmentDate || !appointmentTime) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }

        try {
            const startDateTime = `${appointmentDate}T${appointmentTime}:00`;
            const start = new Date(startDateTime);
            const end = new Date(start.getTime() + parseInt(appointmentDuration) * 60000);

            await createAppointment({
                practitionerId: selectedPractitioner,
                patientId: selectedPatient,
                start: start.toISOString(),
                end: end.toISOString(),
                reason: appointmentReason || 'Consulta médica'
            });

            alert('Consulta agendada com sucesso!');
            
            // Reset form
            setSelectedPatient('');
            setAppointmentDate('');
            setAppointmentTime('');
            setAppointmentReason('');
            
            // Refresh slots
            fetchSlots();
        } catch (error) {
            console.error('Error creating appointment:', error);
            alert('Erro ao agendar consulta. Tente novamente.');
        }
    };

    // Converter Slots FHIR para Eventos do FullCalendar
    const events = slots.map(slot => ({
        id: slot.id,
        title: slot.status === 'free' ? 'Livre' : 'Ocupado',
        start: slot.start,
        end: slot.end,
        backgroundColor: slot.status === 'free' ? colors.alert.success : colors.alert.critical,
        borderColor: slot.status === 'free' ? colors.alert.success : colors.alert.critical,
    }));

    const selectedPractitionerData = practitionersList.find(p => p.id === selectedPractitioner);

    return (
        <div style={{ backgroundColor: colors.background.surface, minHeight: '100vh' }}>
            <Header
                title="Agendamento de Consultas"
                subtitle="Agende consultas com nossos profissionais"
            />

            <main style={{ 
                maxWidth: '1200px', 
                margin: '0 auto', 
                padding: isMobile ? spacing.md : spacing.lg
            }}>
                {/* Tabs */}
                <div style={{ 
                    display: 'flex', 
                    gap: '12px', 
                    marginBottom: spacing.lg,
                    overflowX: 'auto',
                    WebkitOverflowScrolling: 'touch',
                    paddingBottom: '8px',
                    msOverflowStyle: 'none',
                    scrollbarWidth: 'none',
                    flexWrap: isMobile ? 'nowrap' : 'wrap'
                }}>
                    <button
                        onClick={() => setActiveTab('new-appointment')}
                        style={{
                            padding: isMobile ? '10px 16px' : '12px 24px',
                            background: activeTab === 'new-appointment' ? colors.primary.medium : 'white',
                            color: activeTab === 'new-appointment' ? 'white' : colors.text.primary,
                            border: `2px solid ${activeTab === 'new-appointment' ? colors.primary.medium : colors.border.default}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            fontSize: isMobile ? '0.875rem' : '1rem',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            flexShrink: 0,
                            boxShadow: activeTab === 'new-appointment' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'
                        }}
                    >
                        <Plus size={18} />
                        Nova Consulta
                    </button>
                    <button
                        onClick={() => setActiveTab('calendar')}
                        style={{
                            padding: isMobile ? '10px 16px' : '12px 24px',
                            background: activeTab === 'calendar' ? colors.primary.medium : 'white',
                            color: activeTab === 'calendar' ? 'white' : colors.text.primary,
                            border: `2px solid ${activeTab === 'calendar' ? colors.primary.medium : colors.border.default}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            fontSize: isMobile ? '0.875rem' : '1rem',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            flexShrink: 0,
                            boxShadow: activeTab === 'calendar' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'
                        }}
                    >
                        <span style={{ fontSize: '1.1em' }}>📅</span>
                        Calendário
                    </button>
                    <button
                        onClick={() => setActiveTab('availability')}
                        style={{
                            padding: isMobile ? '10px 16px' : '12px 24px',
                            background: activeTab === 'availability' ? colors.primary.medium : 'white',
                            color: activeTab === 'availability' ? 'white' : colors.text.primary,
                            border: `2px solid ${activeTab === 'availability' ? colors.primary.medium : colors.border.default}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            fontSize: isMobile ? '0.875rem' : '1rem',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',                            flexShrink: 0,                            boxShadow: activeTab === 'availability' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'
                        }}
                    >
                        <span style={{ fontSize: '1.1em' }}>⏰</span>
                        Disponibilidade
                    </button>
                </div>

                {activeTab === 'new-appointment' && (
                    <Card padding="lg">
                        <h2 style={{ margin: 0, marginBottom: spacing.lg, color: colors.text.primary }}>
                            Agendar Nova Consulta
                        </h2>

                        <div style={{ display: 'grid', gap: spacing.lg }}>
                            {/* Practitioner Selection */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                    <User size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
                                    Profissional *
                                </label>
                                <select
                                    value={selectedPractitioner}
                                    onChange={(e) => setSelectedPractitioner(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        border: `1px solid ${colors.border.default}`,
                                        borderRadius: '8px',
                                        fontSize: isMobile ? '16px' : '0.95rem',
                                        boxSizing: 'border-box'
                                    }}
                                    disabled={loadingPractitioners}
                                >
                                    <option value="">Selecione um profissional</option>
                                    {practitionersList.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name} {p.specialty ? `- ${p.specialty}` : ''}
                                        </option>
                                    ))}
                                </select>
                                {selectedPractitionerData && (
                                    <p style={{ margin: '8px 0 0 0', fontSize: '0.875rem', color: colors.text.secondary }}>
                                        {selectedPractitionerData.specialty || 'Especialidade não especificada'}
                                    </p>
                                )}
                            </div>

                            {/* Patient Selection */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                    <User size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
                                    Paciente *
                                </label>
                                <select
                                    value={selectedPatient}
                                    onChange={(e) => setSelectedPatient(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        border: `1px solid ${colors.border.default}`,
                                        borderRadius: '8px',
                                        fontSize: isMobile ? '16px' : '0.95rem',
                                        boxSizing: 'border-box'
                                    }}
                                    disabled={loadingPatients}
                                >
                                    <option value="">Selecione um paciente</option>
                                    {patientsList.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Date and Time */}
                            <div style={{ 
                                display: 'grid', 
                                gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', 
                                gap: spacing.md 
                            }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                        <Calendar size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
                                        Data *
                                    </label>
                                    <input
                                        type="date"
                                        value={appointmentDate}
                                        onChange={(e) => setAppointmentDate(e.target.value)}
                                        min={new Date().toISOString().split('T')[0]}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            border: `1px solid ${colors.border.default}`,
                                            borderRadius: '8px',
                                            fontSize: isMobile ? '16px' : '0.95rem',
                                            boxSizing: 'border-box'
                                        }}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                        <Clock size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
                                        Horário *
                                    </label>
                                    <input
                                        type="time"
                                        value={appointmentTime}
                                        onChange={(e) => setAppointmentTime(e.target.value)}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            border: `1px solid ${colors.border.default}`,
                                            borderRadius: '8px',
                                            fontSize: isMobile ? '16px' : '0.95rem',
                                            boxSizing: 'border-box'
                                        }}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                        Duração (min)
                                    </label>
                                    <select
                                        value={appointmentDuration}
                                        onChange={(e) => setAppointmentDuration(e.target.value)}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            border: `1px solid ${colors.border.default}`,
                                            borderRadius: '8px',
                                            fontSize: isMobile ? '16px' : '0.95rem',
                                            boxSizing: 'border-box'
                                        }}
                                    >
                                        <option value="15">15 min</option>
                                        <option value="30">30 min</option>
                                        <option value="45">45 min</option>
                                        <option value="60">60 min</option>
                                    </select>
                                </div>
                            </div>

                            {/* Reason */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, color: colors.text.primary }}>
                                    Motivo da Consulta
                                </label>
                                <textarea
                                    value={appointmentReason}
                                    onChange={(e) => setAppointmentReason(e.target.value)}
                                    placeholder="Ex: Consulta de rotina, dor abdominal, check-up..."
                                    rows={3}
                                    style={{
                                        width: '100%',
                                        padding: '12px',
                                        border: `1px solid ${colors.border.default}`,
                                        borderRadius: '8px',
                                        fontSize: isMobile ? '16px' : '0.95rem',
                                        fontFamily: 'inherit',
                                        resize: 'vertical',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>

                            {/* Submit Button */}
                            <Button
                                onClick={handleCreateAppointment}
                                isLoading={loading}
                                disabled={!selectedPractitioner || !selectedPatient || !appointmentDate || !appointmentTime}
                                style={{ 
                                    marginTop: spacing.md,
                                    width: isMobile ? '100%' : 'auto'
                                }}
                            >
                                Agendar Consulta
                            </Button>
                        </div>
                    </Card>
                )}

                {activeTab === 'calendar' && (
                    <CalendarView
                        events={events}
                        onEventClick={(info) => alert(`Slot clicado: ${info.event.title}`)}
                    />
                )}
                
                {activeTab === 'availability' && (
                    <AvailabilityManager
                        practitionerId="demo-practitioner"
                        practitionerName="Dr. Demo (Clínico Geral)"
                    />
                )}
            </main>
        </div>
    );
};

export default SchedulingWorkspace;
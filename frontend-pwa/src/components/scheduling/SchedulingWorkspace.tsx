import React, { useEffect, useState } from 'react';
import Header from '../base/Header';
import Button from '../base/Button';
import CalendarView from './CalendarView';
import { AvailabilityManager } from './AvailabilityManager';
import { useScheduling } from '../../hooks/useScheduling';
import { colors, spacing } from '../../theme/colors';

const SchedulingWorkspace: React.FC = () => {
    const { slots, fetchSlots, createSchedule, createSlot, loading } = useScheduling();
    const [activeTab, setActiveTab] = useState<'calendar' | 'availability'>('calendar');

    useEffect(() => {
        // Carregar slots ao iniciar
        fetchSlots();
    }, [fetchSlots]);

    const handleGenerateTestSlots = async () => {
        try {
            // 1. Criar Schedule (se não existir - simplificado para demo)
            const schedule = await createSchedule('practitioner-1', 'Dr. House', 'Agenda Principal');

            // 2. Criar Slots para hoje (UTC)
            const today = new Date().toISOString().split('T')[0];
            await createSlot(schedule.id, `${today}T09:00:00Z`, `${today}T09:30:00Z`);
            await createSlot(schedule.id, `${today}T09:30:00Z`, `${today}T10:00:00Z`);
            await createSlot(schedule.id, `${today}T10:00:00Z`, `${today}T10:30:00Z`);

            alert('Slots de teste gerados com sucesso!');
            fetchSlots();
        } catch (error) {
            console.error(error);
            alert('Erro ao gerar slots');
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

    return (
        <div style={{ backgroundColor: colors.background.surface, minHeight: '100vh' }}>
            <Header
                title="Gestão de Agendamento"
                subtitle="Visualize e gerencie a agenda da clínica"
            >
                <Button onClick={handleGenerateTestSlots} isLoading={loading}>
                    ⚙️ Gerar Horários (Demo)
                </Button>
            </Header>

            <main style={{ maxWidth: '1200px', margin: '0 auto', padding: spacing.lg }}>
                {/* Tabs */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: spacing.lg }}>
                    <button
                        onClick={() => setActiveTab('calendar')}
                        style={{
                            padding: '10px 20px',
                            background: activeTab === 'calendar' ? colors.primary.medium : 'white',
                            color: activeTab === 'calendar' ? 'white' : colors.text.primary,
                            border: `1px solid ${activeTab === 'calendar' ? colors.primary.medium : colors.border.default}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            transition: 'all 0.15s'
                        }}
                    >
                        📅 Calendário
                    </button>
                    <button
                        onClick={() => setActiveTab('availability')}
                        style={{
                            padding: '10px 20px',
                            background: activeTab === 'availability' ? colors.primary.medium : 'white',
                            color: activeTab === 'availability' ? 'white' : colors.text.primary,
                            border: `1px solid ${activeTab === 'availability' ? colors.primary.medium : colors.border.default}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            transition: 'all 0.15s'
                        }}
                    >
                        ⏰ Configurar Disponibilidade
                    </button>
                </div>

                {activeTab === 'calendar' ? (
                    <CalendarView
                        events={events}
                        onEventClick={(info) => alert(`Slot clicado: ${info.event.title}`)}
                    />
                ) : (
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


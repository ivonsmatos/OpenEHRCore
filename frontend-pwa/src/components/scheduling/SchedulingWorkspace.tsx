import React, { useEffect } from 'react';
import Header from '../base/Header';
import Button from '../base/Button';
import CalendarView from './CalendarView';
import { useScheduling } from '../../hooks/useScheduling';
import { colors, spacing } from '../../theme/colors';

const SchedulingWorkspace: React.FC = () => {
    const { slots, fetchSlots, createSchedule, createSlot, loading } = useScheduling();

    useEffect(() => {
        // Carregar slots ao iniciar
        // TODO: Passar range de datas baseado na view atual
        fetchSlots();
    }, [fetchSlots]);

    const handleGenerateTestSlots = async () => {
        try {
            // 1. Criar Schedule (se não existir - simplificado para demo)
            const schedule = await createSchedule('practitioner-1', 'Dr. House', 'Agenda Principal');

            // 2. Criar Slots para hoje
            const today = new Date().toISOString().split('T')[0];
            await createSlot(schedule.id, `${today}T09:00:00`, `${today}T09:30:00`);
            await createSlot(schedule.id, `${today}T09:30:00`, `${today}T10:00:00`);
            await createSlot(schedule.id, `${today}T10:00:00`, `${today}T10:30:00`);

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
                <CalendarView
                    events={events}
                    onEventClick={(info) => alert(`Slot clicado: ${info.event.title}`)}
                />
            </main>
        </div>
    );
};

export default SchedulingWorkspace;

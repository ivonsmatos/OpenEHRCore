import React from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { colors } from '../../theme/colors';

interface CalendarEvent {
    id: string;
    title: string;
    start: string;
    end: string;
    backgroundColor?: string;
    borderColor?: string;
}

interface CalendarViewProps {
    events: CalendarEvent[];
    onDateClick?: (arg: any) => void;
    onEventClick?: (arg: any) => void;
}

const CalendarView: React.FC<CalendarViewProps> = ({ events, onDateClick, onEventClick }) => {
    return (
        <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            fontFamily: "'Inter', sans-serif"
        }}>
            <FullCalendar
                plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                initialView="timeGridWeek"
                headerToolbar={{
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                }}
                events={events}
                dateClick={onDateClick}
                eventClick={onEventClick}
                slotMinTime="07:00:00"
                slotMaxTime="20:00:00"
                allDaySlot={false}
                locale="pt-br"
                height="auto"
                eventColor={colors.primary.medium}
            />
        </div>
    );
};

export default CalendarView;

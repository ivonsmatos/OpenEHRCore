import React, { useState, useEffect } from 'react';
import {
    Calendar,
    Clock,
    Plus,
    Trash2,
    Save,
    ChevronDown,
    User
} from 'lucide-react';
import Card from '../base/Card';
import Button from '../base/Button';
import './AvailabilityManager.css';

interface TimeSlot {
    id: string;
    dayOfWeek: number;
    startTime: string;
    endTime: string;
    slotDuration: number; // minutos
}

interface AvailabilityManagerProps {
    practitionerId?: string;
    practitionerName?: string;
    onSave?: (slots: TimeSlot[]) => void;
}

const DAYS = [
    { value: 0, label: 'Domingo' },
    { value: 1, label: 'Segunda-feira' },
    { value: 2, label: 'Terça-feira' },
    { value: 3, label: 'Quarta-feira' },
    { value: 4, label: 'Quinta-feira' },
    { value: 5, label: 'Sexta-feira' },
    { value: 6, label: 'Sábado' }
];

/**
 * AvailabilityManager - Gestão de disponibilidade de profissionais
 * 
 * Permite configurar horários de atendimento por dia da semana,
 * duração de consultas e geração de slots.
 */
export const AvailabilityManager: React.FC<AvailabilityManagerProps> = ({
    practitionerId,
    practitionerName = 'Profissional',
    onSave
}) => {
    const [slots, setSlots] = useState<TimeSlot[]>([]);
    const [saving, setSaving] = useState(false);

    // Carregar configuração existente
    useEffect(() => {
        // TODO: Carregar do backend quando disponível
        // Por agora, criar configuração padrão
        const defaultSlots: TimeSlot[] = [
            { id: '1', dayOfWeek: 1, startTime: '08:00', endTime: '12:00', slotDuration: 30 },
            { id: '2', dayOfWeek: 1, startTime: '14:00', endTime: '18:00', slotDuration: 30 },
            { id: '3', dayOfWeek: 2, startTime: '08:00', endTime: '12:00', slotDuration: 30 },
            { id: '4', dayOfWeek: 2, startTime: '14:00', endTime: '18:00', slotDuration: 30 },
            { id: '5', dayOfWeek: 3, startTime: '08:00', endTime: '12:00', slotDuration: 30 },
            { id: '6', dayOfWeek: 4, startTime: '08:00', endTime: '12:00', slotDuration: 30 },
            { id: '7', dayOfWeek: 5, startTime: '08:00', endTime: '12:00', slotDuration: 30 },
        ];
        setSlots(defaultSlots);
    }, [practitionerId]);

    const addSlot = (dayOfWeek: number) => {
        const newSlot: TimeSlot = {
            id: `new-${Date.now()}`,
            dayOfWeek,
            startTime: '09:00',
            endTime: '12:00',
            slotDuration: 30
        };
        setSlots([...slots, newSlot]);
    };

    const updateSlot = (id: string, field: keyof TimeSlot, value: any) => {
        setSlots(slots.map(slot =>
            slot.id === id ? { ...slot, [field]: value } : slot
        ));
    };

    const removeSlot = (id: string) => {
        setSlots(slots.filter(slot => slot.id !== id));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            // TODO: Salvar no backend
            if (onSave) {
                onSave(slots);
            }
            alert('Disponibilidade salva com sucesso!');
        } catch (err) {
            alert('Erro ao salvar disponibilidade');
        } finally {
            setSaving(false);
        }
    };

    const getSlotsForDay = (dayOfWeek: number) =>
        slots.filter(slot => slot.dayOfWeek === dayOfWeek);

    const calculateSlotsCount = (startTime: string, endTime: string, duration: number) => {
        const [startH, startM] = startTime.split(':').map(Number);
        const [endH, endM] = endTime.split(':').map(Number);
        const totalMinutes = (endH * 60 + endM) - (startH * 60 + startM);
        return Math.floor(totalMinutes / duration);
    };

    return (
        <Card className="availability-manager">
            <div className="am-header">
                <div className="am-title">
                    <Calendar size={24} />
                    <div>
                        <h3>Configurar Disponibilidade</h3>
                        <p className="am-subtitle">
                            <User size={14} />
                            {practitionerName}
                        </p>
                    </div>
                </div>
                <Button onClick={handleSave} disabled={saving}>
                    <Save size={16} />
                    {saving ? 'Salvando...' : 'Salvar'}
                </Button>
            </div>

            <div className="am-days">
                {DAYS.map(day => {
                    const daySlots = getSlotsForDay(day.value);
                    const hasSlots = daySlots.length > 0;

                    return (
                        <div key={day.value} className={`am-day ${hasSlots ? 'active' : ''}`}>
                            <div className="am-day-header">
                                <span className="day-name">{day.label}</span>
                                <button
                                    className="add-slot-btn"
                                    onClick={() => addSlot(day.value)}
                                    title="Adicionar período"
                                >
                                    <Plus size={16} />
                                </button>
                            </div>

                            {!hasSlots ? (
                                <div className="no-slots">
                                    <span>Sem atendimento</span>
                                </div>
                            ) : (
                                <div className="am-day-slots">
                                    {daySlots.map(slot => (
                                        <div key={slot.id} className="slot-config">
                                            <div className="slot-times">
                                                <div className="time-input">
                                                    <Clock size={14} />
                                                    <input
                                                        type="time"
                                                        value={slot.startTime}
                                                        onChange={(e) => updateSlot(slot.id, 'startTime', e.target.value)}
                                                        aria-label="Horário início"
                                                    />
                                                </div>
                                                <span className="time-separator">às</span>
                                                <div className="time-input">
                                                    <input
                                                        type="time"
                                                        value={slot.endTime}
                                                        onChange={(e) => updateSlot(slot.id, 'endTime', e.target.value)}
                                                        aria-label="Horário término"
                                                    />
                                                </div>
                                            </div>

                                            <div className="slot-duration">
                                                <select
                                                    value={slot.slotDuration}
                                                    onChange={(e) => updateSlot(slot.id, 'slotDuration', Number(e.target.value))}
                                                    aria-label="Duração da consulta"
                                                >
                                                    <option value={15}>15 min</option>
                                                    <option value={20}>20 min</option>
                                                    <option value={30}>30 min</option>
                                                    <option value={45}>45 min</option>
                                                    <option value={60}>1 hora</option>
                                                </select>
                                                <ChevronDown size={14} />
                                            </div>

                                            <div className="slot-count">
                                                {calculateSlotsCount(slot.startTime, slot.endTime, slot.slotDuration)} vagas
                                            </div>

                                            <button
                                                className="remove-slot-btn"
                                                onClick={() => removeSlot(slot.id)}
                                                title="Remover período"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="am-summary">
                <div className="summary-item">
                    <span className="summary-label">Total de períodos</span>
                    <span className="summary-value">{slots.length}</span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Dias ativos</span>
                    <span className="summary-value">
                        {new Set(slots.map(s => s.dayOfWeek)).size}
                    </span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Vagas/semana</span>
                    <span className="summary-value">
                        {slots.reduce((sum, slot) =>
                            sum + calculateSlotsCount(slot.startTime, slot.endTime, slot.slotDuration),
                            0)}
                    </span>
                </div>
            </div>
        </Card>
    );
};

export default AvailabilityManager;

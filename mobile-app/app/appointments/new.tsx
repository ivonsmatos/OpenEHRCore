/**
 * Sprint 26: New Appointment Scheduling Screen
 * 
 * Form to schedule a new appointment
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';
import { format, addDays, setHours, setMinutes } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Specialty {
    id: string;
    name: string;
    icon: keyof typeof Ionicons.glyphMap;
}

interface Practitioner {
    id: string;
    name: string;
    specialty: string;
    photo?: string;
    nextAvailable: string;
}

interface TimeSlot {
    time: string;
    available: boolean;
}

const specialties: Specialty[] = [
    { id: 'general', name: 'Clínico Geral', icon: 'person-outline' },
    { id: 'cardio', name: 'Cardiologia', icon: 'heart-outline' },
    { id: 'derma', name: 'Dermatologia', icon: 'body-outline' },
    { id: 'neuro', name: 'Neurologia', icon: 'pulse-outline' },
    { id: 'ortho', name: 'Ortopedia', icon: 'fitness-outline' },
    { id: 'gyno', name: 'Ginecologia', icon: 'female-outline' },
];

const mockPractitioners: Practitioner[] = [
    { id: '1', name: 'Dr. Carlos Silva', specialty: 'Clínico Geral', nextAvailable: 'Hoje, 14:30' },
    { id: '2', name: 'Dra. Maria Santos', specialty: 'Cardiologia', nextAvailable: 'Amanhã, 09:00' },
    { id: '3', name: 'Dr. João Oliveira', specialty: 'Dermatologia', nextAvailable: 'Seg, 10:00' },
];

const generateTimeSlots = (): TimeSlot[] => {
    const slots: TimeSlot[] = [];
    for (let hour = 8; hour <= 18; hour++) {
        slots.push({ time: `${hour.toString().padStart(2, '0')}:00`, available: Math.random() > 0.3 });
        if (hour < 18) {
            slots.push({ time: `${hour.toString().padStart(2, '0')}:30`, available: Math.random() > 0.3 });
        }
    }
    return slots;
};

const generateDates = () => {
    const dates = [];
    for (let i = 0; i < 14; i++) {
        const date = addDays(new Date(), i);
        dates.push({
            date,
            day: format(date, 'dd'),
            weekday: format(date, 'EEE', { locale: ptBR }),
            month: format(date, 'MMM', { locale: ptBR }),
            isToday: i === 0,
        });
    }
    return dates;
};

type Step = 'specialty' | 'practitioner' | 'date' | 'time' | 'type' | 'confirm';

export default function NewAppointmentScreen() {
    const router = useRouter();
    const [step, setStep] = useState<Step>('specialty');
    const [selectedSpecialty, setSelectedSpecialty] = useState<Specialty | null>(null);
    const [selectedPractitioner, setSelectedPractitioner] = useState<Practitioner | null>(null);
    const [selectedDate, setSelectedDate] = useState<typeof dates[0] | null>(null);
    const [selectedTime, setSelectedTime] = useState<string | null>(null);
    const [appointmentType, setAppointmentType] = useState<'in-person' | 'telemedicine' | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const dates = generateDates();
    const timeSlots = generateTimeSlots();

    const handleConfirm = async () => {
        setIsLoading(true);

        // Simulate API call
        setTimeout(() => {
            setIsLoading(false);
            Alert.alert(
                'Consulta Agendada!',
                `Sua consulta com ${selectedPractitioner?.name} foi agendada para ${selectedDate?.day}/${selectedDate?.month} às ${selectedTime}.`,
                [{ text: 'OK', onPress: () => router.back() }]
            );
        }, 1500);
    };

    const goBack = () => {
        const steps: Step[] = ['specialty', 'practitioner', 'date', 'time', 'type', 'confirm'];
        const currentIndex = steps.indexOf(step);
        if (currentIndex > 0) {
            setStep(steps[currentIndex - 1]);
        } else {
            router.back();
        }
    };

    const renderStepIndicator = () => (
        <View style={styles.stepIndicator}>
            {['specialty', 'practitioner', 'date', 'time', 'type', 'confirm'].map((s, index) => (
                <View
                    key={s}
                    style={[
                        styles.stepDot,
                        step === s && styles.stepDotActive,
                        ['specialty', 'practitioner', 'date', 'time', 'type', 'confirm'].indexOf(step) > index && styles.stepDotCompleted
                    ]}
                />
            ))}
        </View>
    );

    return (
        <>
            <Stack.Screen
                options={{
                    title: 'Nova Consulta',
                    headerLeft: () => (
                        <TouchableOpacity onPress={goBack} style={{ marginLeft: 8 }}>
                            <Ionicons name="arrow-back" size={24} color="#fff" />
                        </TouchableOpacity>
                    ),
                }}
            />

            <View style={styles.container}>
                {renderStepIndicator()}

                <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                    {/* Step 1: Specialty */}
                    {step === 'specialty' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Escolha a especialidade</Text>
                            <View style={styles.specialtiesGrid}>
                                {specialties.map((specialty) => (
                                    <TouchableOpacity
                                        key={specialty.id}
                                        style={[
                                            styles.specialtyCard,
                                            selectedSpecialty?.id === specialty.id && styles.specialtyCardSelected
                                        ]}
                                        onPress={() => {
                                            setSelectedSpecialty(specialty);
                                            setStep('practitioner');
                                        }}
                                    >
                                        <View style={[
                                            styles.specialtyIcon,
                                            selectedSpecialty?.id === specialty.id && styles.specialtyIconSelected
                                        ]}>
                                            <Ionicons
                                                name={specialty.icon}
                                                size={28}
                                                color={selectedSpecialty?.id === specialty.id ? '#fff' : colors.primary[600]}
                                            />
                                        </View>
                                        <Text style={styles.specialtyName}>{specialty.name}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        </View>
                    )}

                    {/* Step 2: Practitioner */}
                    {step === 'practitioner' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Escolha o profissional</Text>
                            {mockPractitioners.map((practitioner) => (
                                <TouchableOpacity
                                    key={practitioner.id}
                                    style={[
                                        styles.practitionerCard,
                                        selectedPractitioner?.id === practitioner.id && styles.practitionerCardSelected
                                    ]}
                                    onPress={() => {
                                        setSelectedPractitioner(practitioner);
                                        setStep('date');
                                    }}
                                >
                                    <View style={styles.practitionerAvatar}>
                                        <Ionicons name="person" size={24} color={colors.primary[600]} />
                                    </View>
                                    <View style={styles.practitionerInfo}>
                                        <Text style={styles.practitionerName}>{practitioner.name}</Text>
                                        <Text style={styles.practitionerSpecialty}>{practitioner.specialty}</Text>
                                        <Text style={styles.practitionerAvailable}>
                                            Próximo horário: {practitioner.nextAvailable}
                                        </Text>
                                    </View>
                                    <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
                                </TouchableOpacity>
                            ))}
                        </View>
                    )}

                    {/* Step 3: Date */}
                    {step === 'date' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Escolha a data</Text>
                            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.datesScroll}>
                                {dates.map((d) => (
                                    <TouchableOpacity
                                        key={d.date.toISOString()}
                                        style={[
                                            styles.dateCard,
                                            selectedDate?.date.toISOString() === d.date.toISOString() && styles.dateCardSelected
                                        ]}
                                        onPress={() => {
                                            setSelectedDate(d);
                                            setStep('time');
                                        }}
                                    >
                                        <Text style={[
                                            styles.dateWeekday,
                                            selectedDate?.date.toISOString() === d.date.toISOString() && styles.dateTextSelected
                                        ]}>
                                            {d.isToday ? 'Hoje' : d.weekday}
                                        </Text>
                                        <Text style={[
                                            styles.dateDay,
                                            selectedDate?.date.toISOString() === d.date.toISOString() && styles.dateTextSelected
                                        ]}>
                                            {d.day}
                                        </Text>
                                        <Text style={[
                                            styles.dateMonth,
                                            selectedDate?.date.toISOString() === d.date.toISOString() && styles.dateTextSelected
                                        ]}>
                                            {d.month}
                                        </Text>
                                    </TouchableOpacity>
                                ))}
                            </ScrollView>
                        </View>
                    )}

                    {/* Step 4: Time */}
                    {step === 'time' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Escolha o horário</Text>
                            <View style={styles.timeSlotsGrid}>
                                {timeSlots.map((slot) => (
                                    <TouchableOpacity
                                        key={slot.time}
                                        style={[
                                            styles.timeSlot,
                                            !slot.available && styles.timeSlotUnavailable,
                                            selectedTime === slot.time && styles.timeSlotSelected
                                        ]}
                                        disabled={!slot.available}
                                        onPress={() => {
                                            setSelectedTime(slot.time);
                                            setStep('type');
                                        }}
                                    >
                                        <Text style={[
                                            styles.timeSlotText,
                                            !slot.available && styles.timeSlotTextUnavailable,
                                            selectedTime === slot.time && styles.timeSlotTextSelected
                                        ]}>
                                            {slot.time}
                                        </Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        </View>
                    )}

                    {/* Step 5: Type */}
                    {step === 'type' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Tipo de atendimento</Text>
                            <TouchableOpacity
                                style={[
                                    styles.typeCard,
                                    appointmentType === 'in-person' && styles.typeCardSelected
                                ]}
                                onPress={() => {
                                    setAppointmentType('in-person');
                                    setStep('confirm');
                                }}
                            >
                                <View style={styles.typeIcon}>
                                    <Ionicons name="location" size={32} color={colors.primary[600]} />
                                </View>
                                <View style={styles.typeInfo}>
                                    <Text style={styles.typeName}>Presencial</Text>
                                    <Text style={styles.typeDescription}>
                                        Atendimento na unidade de saúde
                                    </Text>
                                </View>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={[
                                    styles.typeCard,
                                    appointmentType === 'telemedicine' && styles.typeCardSelected
                                ]}
                                onPress={() => {
                                    setAppointmentType('telemedicine');
                                    setStep('confirm');
                                }}
                            >
                                <View style={styles.typeIcon}>
                                    <Ionicons name="videocam" size={32} color={colors.primary[600]} />
                                </View>
                                <View style={styles.typeInfo}>
                                    <Text style={styles.typeName}>Teleconsulta</Text>
                                    <Text style={styles.typeDescription}>
                                        Atendimento por vídeo chamada
                                    </Text>
                                </View>
                            </TouchableOpacity>
                        </View>
                    )}

                    {/* Step 6: Confirm */}
                    {step === 'confirm' && (
                        <View style={styles.stepContent}>
                            <Text style={styles.stepTitle}>Confirme sua consulta</Text>

                            <View style={styles.confirmCard}>
                                <View style={styles.confirmRow}>
                                    <Ionicons name="medical" size={20} color={colors.primary[600]} />
                                    <View style={styles.confirmInfo}>
                                        <Text style={styles.confirmLabel}>Especialidade</Text>
                                        <Text style={styles.confirmValue}>{selectedSpecialty?.name}</Text>
                                    </View>
                                </View>

                                <View style={styles.confirmDivider} />

                                <View style={styles.confirmRow}>
                                    <Ionicons name="person" size={20} color={colors.primary[600]} />
                                    <View style={styles.confirmInfo}>
                                        <Text style={styles.confirmLabel}>Profissional</Text>
                                        <Text style={styles.confirmValue}>{selectedPractitioner?.name}</Text>
                                    </View>
                                </View>

                                <View style={styles.confirmDivider} />

                                <View style={styles.confirmRow}>
                                    <Ionicons name="calendar" size={20} color={colors.primary[600]} />
                                    <View style={styles.confirmInfo}>
                                        <Text style={styles.confirmLabel}>Data e Hora</Text>
                                        <Text style={styles.confirmValue}>
                                            {selectedDate?.day}/{selectedDate?.month} às {selectedTime}
                                        </Text>
                                    </View>
                                </View>

                                <View style={styles.confirmDivider} />

                                <View style={styles.confirmRow}>
                                    <Ionicons
                                        name={appointmentType === 'telemedicine' ? 'videocam' : 'location'}
                                        size={20}
                                        color={colors.primary[600]}
                                    />
                                    <View style={styles.confirmInfo}>
                                        <Text style={styles.confirmLabel}>Tipo</Text>
                                        <Text style={styles.confirmValue}>
                                            {appointmentType === 'telemedicine' ? 'Teleconsulta' : 'Presencial'}
                                        </Text>
                                    </View>
                                </View>
                            </View>

                            <TouchableOpacity
                                style={[styles.confirmButton, isLoading && styles.confirmButtonDisabled]}
                                onPress={handleConfirm}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <ActivityIndicator color="#fff" />
                                ) : (
                                    <>
                                        <Ionicons name="checkmark-circle" size={20} color="#fff" />
                                        <Text style={styles.confirmButtonText}>Confirmar Agendamento</Text>
                                    </>
                                )}
                            </TouchableOpacity>
                        </View>
                    )}
                </ScrollView>
            </View>
        </>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    stepIndicator: {
        flexDirection: 'row',
        justifyContent: 'center',
        paddingVertical: 16,
        backgroundColor: '#fff',
        gap: 8,
    },
    stepDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.gray[200],
    },
    stepDotActive: {
        backgroundColor: colors.primary[600],
        width: 24,
    },
    stepDotCompleted: {
        backgroundColor: colors.success[500],
    },
    content: {
        flex: 1,
    },
    stepContent: {
        padding: 20,
    },
    stepTitle: {
        fontFamily: 'Inter-Bold',
        fontSize: 22,
        color: colors.gray[900],
        marginBottom: 20,
    },
    specialtiesGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
    },
    specialtyCard: {
        width: '48%',
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 20,
        alignItems: 'center',
        marginBottom: 12,
        borderWidth: 2,
        borderColor: 'transparent',
    },
    specialtyCardSelected: {
        borderColor: colors.primary[600],
    },
    specialtyIcon: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 12,
    },
    specialtyIconSelected: {
        backgroundColor: colors.primary[600],
    },
    specialtyName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
        color: colors.gray[800],
        textAlign: 'center',
    },
    practitionerCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 16,
        marginBottom: 12,
        borderWidth: 2,
        borderColor: 'transparent',
    },
    practitionerCardSelected: {
        borderColor: colors.primary[600],
    },
    practitionerAvatar: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 14,
    },
    practitionerInfo: {
        flex: 1,
    },
    practitionerName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: colors.gray[900],
    },
    practitionerSpecialty: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginTop: 2,
    },
    practitionerAvailable: {
        fontFamily: 'Inter-Medium',
        fontSize: 13,
        color: colors.success[600],
        marginTop: 4,
    },
    datesScroll: {
        marginHorizontal: -20,
        paddingHorizontal: 20,
    },
    dateCard: {
        backgroundColor: '#fff',
        borderRadius: 16,
        paddingVertical: 16,
        paddingHorizontal: 14,
        marginRight: 10,
        alignItems: 'center',
        minWidth: 70,
        borderWidth: 2,
        borderColor: 'transparent',
    },
    dateCardSelected: {
        backgroundColor: colors.primary[600],
        borderColor: colors.primary[600],
    },
    dateWeekday: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        color: colors.gray[500],
        textTransform: 'capitalize',
    },
    dateDay: {
        fontFamily: 'Inter-Bold',
        fontSize: 22,
        color: colors.gray[900],
        marginVertical: 4,
    },
    dateMonth: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        color: colors.gray[500],
        textTransform: 'uppercase',
    },
    dateTextSelected: {
        color: '#fff',
    },
    timeSlotsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
    },
    timeSlot: {
        backgroundColor: '#fff',
        paddingVertical: 12,
        paddingHorizontal: 18,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: colors.gray[200],
    },
    timeSlotUnavailable: {
        backgroundColor: colors.gray[100],
        opacity: 0.5,
    },
    timeSlotSelected: {
        backgroundColor: colors.primary[600],
        borderColor: colors.primary[600],
    },
    timeSlotText: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.gray[700],
    },
    timeSlotTextUnavailable: {
        color: colors.gray[400],
    },
    timeSlotTextSelected: {
        color: '#fff',
    },
    typeCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 20,
        borderRadius: 16,
        marginBottom: 12,
        borderWidth: 2,
        borderColor: 'transparent',
    },
    typeCardSelected: {
        borderColor: colors.primary[600],
    },
    typeIcon: {
        width: 64,
        height: 64,
        borderRadius: 16,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 16,
    },
    typeInfo: {
        flex: 1,
    },
    typeName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 18,
        color: colors.gray[900],
    },
    typeDescription: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginTop: 4,
    },
    confirmCard: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 20,
        marginBottom: 24,
    },
    confirmRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    confirmInfo: {
        marginLeft: 14,
        flex: 1,
    },
    confirmLabel: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
    },
    confirmValue: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[900],
        marginTop: 2,
    },
    confirmDivider: {
        height: 1,
        backgroundColor: colors.gray[100],
        marginVertical: 14,
    },
    confirmButton: {
        flexDirection: 'row',
        backgroundColor: colors.primary[600],
        paddingVertical: 16,
        borderRadius: 14,
        justifyContent: 'center',
        alignItems: 'center',
        gap: 8,
    },
    confirmButtonDisabled: {
        opacity: 0.7,
    },
    confirmButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: '#fff',
    },
});

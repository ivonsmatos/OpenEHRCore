/**
 * Sprint 26: Appointment Detail Screen
 * 
 * View appointment details with actions
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Linking } from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

interface AppointmentDetail {
    id: string;
    practitioner: {
        name: string;
        specialty: string;
        crm: string;
        photo?: string;
    };
    date: string;
    time: string;
    endTime: string;
    status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
    type: 'in-person' | 'telemedicine';
    location?: {
        name: string;
        address: string;
        room: string;
    };
    notes?: string;
    meetingUrl?: string;
}

// Mock data - in real app would fetch from API
const getMockAppointment = (id: string): AppointmentDetail => ({
    id,
    practitioner: {
        name: 'Dr. Carlos Silva',
        specialty: 'Clínico Geral',
        crm: 'CRM/SP 123456',
    },
    date: '15 de Dezembro, 2024',
    time: '14:30',
    endTime: '15:00',
    status: 'confirmed',
    type: 'in-person',
    location: {
        name: 'Clínica Central',
        address: 'Av. Paulista, 1000 - São Paulo, SP',
        room: 'Sala 201 - 2º Andar',
    },
    notes: 'Trazer exames recentes de sangue.',
});

const statusConfig = {
    scheduled: { color: colors.warning[500], label: 'Agendado', icon: 'time' as const },
    confirmed: { color: colors.success[500], label: 'Confirmado', icon: 'checkmark-circle' as const },
    completed: { color: colors.gray[400], label: 'Realizado', icon: 'checkmark-done' as const },
    cancelled: { color: colors.error[500], label: 'Cancelado', icon: 'close-circle' as const },
};

export default function AppointmentDetailScreen() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const router = useRouter();
    const appointment = getMockAppointment(id || '1');
    const status = statusConfig[appointment.status];

    const handleCancel = () => {
        Alert.alert(
            'Cancelar Consulta',
            'Tem certeza que deseja cancelar esta consulta?',
            [
                { text: 'Não', style: 'cancel' },
                {
                    text: 'Sim, Cancelar',
                    style: 'destructive',
                    onPress: () => {
                        // API call to cancel
                        Alert.alert('Consulta Cancelada', 'Sua consulta foi cancelada com sucesso.');
                        router.back();
                    }
                },
            ]
        );
    };

    const handleReschedule = () => {
        router.push('/appointments/new');
    };

    const handleAddToCalendar = () => {
        Alert.alert('Adicionado', 'Consulta adicionada ao seu calendário.');
    };

    const handleOpenMaps = () => {
        if (appointment.location) {
            const url = `https://maps.google.com/maps?q=${encodeURIComponent(appointment.location.address)}`;
            Linking.openURL(url);
        }
    };

    const handleJoinCall = () => {
        if (appointment.meetingUrl) {
            Linking.openURL(appointment.meetingUrl);
        }
    };

    return (
        <>
            <Stack.Screen
                options={{
                    title: 'Detalhes',
                    headerRight: () => (
                        <TouchableOpacity onPress={handleAddToCalendar} style={{ marginRight: 8 }}>
                            <Ionicons name="calendar-outline" size={24} color="#fff" />
                        </TouchableOpacity>
                    ),
                }}
            />

            <ScrollView style={styles.container}>
                {/* Status Badge */}
                <View style={[styles.statusBanner, { backgroundColor: status.color + '15' }]}>
                    <Ionicons name={status.icon} size={20} color={status.color} />
                    <Text style={[styles.statusText, { color: status.color }]}>{status.label}</Text>
                </View>

                {/* Practitioner Card */}
                <View style={styles.card}>
                    <View style={styles.practitionerHeader}>
                        <View style={styles.practitionerAvatar}>
                            <Ionicons name="person" size={32} color={colors.primary[600]} />
                        </View>
                        <View style={styles.practitionerInfo}>
                            <Text style={styles.practitionerName}>{appointment.practitioner.name}</Text>
                            <Text style={styles.practitionerSpecialty}>{appointment.practitioner.specialty}</Text>
                            <Text style={styles.practitionerCrm}>{appointment.practitioner.crm}</Text>
                        </View>
                    </View>
                </View>

                {/* Date & Time */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>Data e Horário</Text>
                    <View style={styles.infoRow}>
                        <Ionicons name="calendar" size={20} color={colors.primary[600]} />
                        <Text style={styles.infoText}>{appointment.date}</Text>
                    </View>
                    <View style={styles.infoRow}>
                        <Ionicons name="time" size={20} color={colors.primary[600]} />
                        <Text style={styles.infoText}>{appointment.time} - {appointment.endTime}</Text>
                    </View>
                </View>

                {/* Location or Telemedicine */}
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>
                        {appointment.type === 'telemedicine' ? 'Teleconsulta' : 'Local'}
                    </Text>

                    {appointment.type === 'in-person' && appointment.location ? (
                        <>
                            <View style={styles.infoRow}>
                                <Ionicons name="business" size={20} color={colors.primary[600]} />
                                <Text style={styles.infoText}>{appointment.location.name}</Text>
                            </View>
                            <View style={styles.infoRow}>
                                <Ionicons name="location" size={20} color={colors.primary[600]} />
                                <Text style={styles.infoText}>{appointment.location.address}</Text>
                            </View>
                            <View style={styles.infoRow}>
                                <Ionicons name="navigate" size={20} color={colors.primary[600]} />
                                <Text style={styles.infoText}>{appointment.location.room}</Text>
                            </View>
                            <TouchableOpacity style={styles.mapButton} onPress={handleOpenMaps}>
                                <Ionicons name="map" size={18} color={colors.primary[600]} />
                                <Text style={styles.mapButtonText}>Abrir no Mapa</Text>
                            </TouchableOpacity>
                        </>
                    ) : (
                        <>
                            <View style={styles.infoRow}>
                                <Ionicons name="videocam" size={20} color={colors.primary[600]} />
                                <Text style={styles.infoText}>Atendimento por vídeo chamada</Text>
                            </View>
                            {appointment.status === 'confirmed' && (
                                <TouchableOpacity style={styles.joinButton} onPress={handleJoinCall}>
                                    <Ionicons name="videocam" size={20} color="#fff" />
                                    <Text style={styles.joinButtonText}>Entrar na Consulta</Text>
                                </TouchableOpacity>
                            )}
                        </>
                    )}
                </View>

                {/* Notes */}
                {appointment.notes && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Observações</Text>
                        <Text style={styles.notesText}>{appointment.notes}</Text>
                    </View>
                )}

                {/* Actions */}
                {appointment.status !== 'completed' && appointment.status !== 'cancelled' && (
                    <View style={styles.actions}>
                        <TouchableOpacity style={styles.rescheduleButton} onPress={handleReschedule}>
                            <Ionicons name="calendar-outline" size={18} color={colors.primary[600]} />
                            <Text style={styles.rescheduleButtonText}>Reagendar</Text>
                        </TouchableOpacity>

                        <TouchableOpacity style={styles.cancelButton} onPress={handleCancel}>
                            <Ionicons name="close-circle-outline" size={18} color={colors.error[600]} />
                            <Text style={styles.cancelButtonText}>Cancelar</Text>
                        </TouchableOpacity>
                    </View>
                )}

                <View style={{ height: 40 }} />
            </ScrollView>
        </>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    statusBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 12,
        gap: 8,
    },
    statusText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
    },
    card: {
        backgroundColor: '#fff',
        marginHorizontal: 16,
        marginTop: 16,
        borderRadius: 16,
        padding: 20,
    },
    cardTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: colors.gray[800],
        marginBottom: 16,
    },
    practitionerHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    practitionerAvatar: {
        width: 70,
        height: 70,
        borderRadius: 35,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 16,
    },
    practitionerInfo: {
        flex: 1,
    },
    practitionerName: {
        fontFamily: 'Inter-Bold',
        fontSize: 18,
        color: colors.gray[900],
    },
    practitionerSpecialty: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.primary[600],
        marginTop: 2,
    },
    practitionerCrm: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 2,
    },
    infoRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
        gap: 12,
    },
    infoText: {
        fontFamily: 'Inter-Regular',
        fontSize: 15,
        color: colors.gray[700],
        flex: 1,
    },
    mapButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 12,
        borderRadius: 10,
        backgroundColor: colors.primary[50],
        marginTop: 8,
        gap: 8,
    },
    mapButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
        color: colors.primary[600],
    },
    joinButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        borderRadius: 12,
        backgroundColor: colors.success[500],
        marginTop: 8,
        gap: 8,
    },
    joinButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: '#fff',
    },
    notesText: {
        fontFamily: 'Inter-Regular',
        fontSize: 15,
        color: colors.gray[600],
        lineHeight: 22,
    },
    actions: {
        flexDirection: 'row',
        marginHorizontal: 16,
        marginTop: 24,
        gap: 12,
    },
    rescheduleButton: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        borderRadius: 12,
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: colors.primary[200],
        gap: 8,
    },
    rescheduleButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
        color: colors.primary[600],
    },
    cancelButton: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        borderRadius: 12,
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: colors.error[200],
        gap: 8,
    },
    cancelButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
        color: colors.error[600],
    },
});

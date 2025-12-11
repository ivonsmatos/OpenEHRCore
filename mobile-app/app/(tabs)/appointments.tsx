/**
 * Sprint 26: Appointments Screen
 * 
 * Patient appointments list and scheduling
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';
import { format, parseISO, isAfter } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Appointment {
    id: string;
    practitioner: string;
    specialty: string;
    date: string;
    time: string;
    status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
    type: 'in-person' | 'telemedicine';
    location?: string;
}

const mockAppointments: Appointment[] = [
    {
        id: '1',
        practitioner: 'Dr. Carlos Silva',
        specialty: 'Clínico Geral',
        date: '2024-12-15',
        time: '14:30',
        status: 'confirmed',
        type: 'in-person',
        location: 'Sala 201',
    },
    {
        id: '2',
        practitioner: 'Dra. Maria Santos',
        specialty: 'Cardiologia',
        date: '2024-12-20',
        time: '09:00',
        status: 'scheduled',
        type: 'telemedicine',
    },
    {
        id: '3',
        practitioner: 'Dr. João Oliveira',
        specialty: 'Dermatologia',
        date: '2024-11-10',
        time: '16:00',
        status: 'completed',
        type: 'in-person',
        location: 'Sala 105',
    },
];

const statusConfig: Record<string, { color: string; label: string; icon: keyof typeof Ionicons.glyphMap }> = {
    scheduled: { color: colors.warning[500], label: 'Agendado', icon: 'time-outline' },
    confirmed: { color: colors.success[500], label: 'Confirmado', icon: 'checkmark-circle-outline' },
    completed: { color: colors.gray[400], label: 'Realizado', icon: 'checkmark-done-outline' },
    cancelled: { color: colors.error[500], label: 'Cancelado', icon: 'close-circle-outline' },
};

export default function AppointmentsScreen() {
    const router = useRouter();
    const [refreshing, setRefreshing] = useState(false);
    const [filter, setFilter] = useState<'upcoming' | 'past'>('upcoming');

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    }, []);

    const filteredAppointments = mockAppointments.filter(apt => {
        const isPast = !isAfter(parseISO(apt.date), new Date());
        return filter === 'past' ? isPast : !isPast;
    });

    const renderAppointment = ({ item }: { item: Appointment }) => {
        const status = statusConfig[item.status];
        const dateObj = parseISO(item.date);

        return (
            <TouchableOpacity
                style={styles.appointmentCard}
                onPress={() => router.push(`/appointments/${item.id}`)}
            >
                <View style={styles.dateBlock}>
                    <Text style={styles.dateDay}>{format(dateObj, 'dd')}</Text>
                    <Text style={styles.dateMonth}>{format(dateObj, 'MMM', { locale: ptBR })}</Text>
                </View>

                <View style={styles.appointmentContent}>
                    <View style={styles.appointmentHeader}>
                        <Text style={styles.practitionerName}>{item.practitioner}</Text>
                        <View style={[styles.statusBadge, { backgroundColor: status.color + '20' }]}>
                            <Ionicons name={status.icon} size={12} color={status.color} />
                            <Text style={[styles.statusText, { color: status.color }]}>
                                {status.label}
                            </Text>
                        </View>
                    </View>

                    <Text style={styles.specialty}>{item.specialty}</Text>

                    <View style={styles.appointmentDetails}>
                        <View style={styles.detailItem}>
                            <Ionicons name="time-outline" size={14} color={colors.gray[500]} />
                            <Text style={styles.detailText}>{item.time}</Text>
                        </View>
                        <View style={styles.detailItem}>
                            <Ionicons
                                name={item.type === 'telemedicine' ? 'videocam-outline' : 'location-outline'}
                                size={14}
                                color={colors.gray[500]}
                            />
                            <Text style={styles.detailText}>
                                {item.type === 'telemedicine' ? 'Teleconsulta' : item.location}
                            </Text>
                        </View>
                    </View>
                </View>

                <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            {/* Filter Tabs */}
            <View style={styles.filterTabs}>
                <TouchableOpacity
                    style={[styles.filterTab, filter === 'upcoming' && styles.filterTabActive]}
                    onPress={() => setFilter('upcoming')}
                >
                    <Text style={[styles.filterTabText, filter === 'upcoming' && styles.filterTabTextActive]}>
                        Próximas
                    </Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.filterTab, filter === 'past' && styles.filterTabActive]}
                    onPress={() => setFilter('past')}
                >
                    <Text style={[styles.filterTabText, filter === 'past' && styles.filterTabTextActive]}>
                        Histórico
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Appointments List */}
            <FlatList
                data={filteredAppointments}
                renderItem={renderAppointment}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
                ListEmptyComponent={
                    <View style={styles.emptyState}>
                        <Ionicons name="calendar-outline" size={64} color={colors.gray[300]} />
                        <Text style={styles.emptyTitle}>Nenhuma consulta</Text>
                        <Text style={styles.emptyText}>
                            {filter === 'upcoming'
                                ? 'Você não tem consultas agendadas'
                                : 'Nenhuma consulta no histórico'}
                        </Text>
                    </View>
                }
            />

            {/* FAB - New Appointment */}
            <TouchableOpacity
                style={styles.fab}
                onPress={() => router.push('/appointments/new')}
            >
                <Ionicons name="add" size={28} color="#fff" />
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    filterTabs: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        padding: 8,
        marginHorizontal: 16,
        marginTop: 16,
        borderRadius: 12,
    },
    filterTab: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 8,
    },
    filterTabActive: {
        backgroundColor: colors.primary[50],
    },
    filterTabText: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.gray[500],
    },
    filterTabTextActive: {
        color: colors.primary[600],
    },
    listContent: {
        padding: 16,
        paddingBottom: 100,
    },
    appointmentCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 16,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.03,
        shadowRadius: 4,
        elevation: 1,
    },
    dateBlock: {
        backgroundColor: colors.primary[50],
        paddingHorizontal: 12,
        paddingVertical: 10,
        borderRadius: 12,
        alignItems: 'center',
        marginRight: 14,
    },
    dateDay: {
        fontFamily: 'Inter-Bold',
        fontSize: 20,
        color: colors.primary[600],
    },
    dateMonth: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        color: colors.primary[600],
        textTransform: 'uppercase',
    },
    appointmentContent: {
        flex: 1,
    },
    appointmentHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 4,
    },
    practitionerName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: colors.gray[900],
        flex: 1,
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
        marginLeft: 8,
    },
    statusText: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        marginLeft: 4,
    },
    specialty: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginBottom: 8,
    },
    appointmentDetails: {
        flexDirection: 'row',
        gap: 16,
    },
    detailItem: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    detailText: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginLeft: 4,
    },
    emptyState: {
        alignItems: 'center',
        paddingTop: 60,
    },
    emptyTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 18,
        color: colors.gray[700],
        marginTop: 16,
    },
    emptyText: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginTop: 8,
        textAlign: 'center',
    },
    fab: {
        position: 'absolute',
        right: 20,
        bottom: 20,
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: colors.primary[600],
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: colors.primary[600],
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 8,
    },
});

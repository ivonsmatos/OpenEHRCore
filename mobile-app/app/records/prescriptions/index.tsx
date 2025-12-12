/**
 * Sprint 26: Prescriptions List Screen
 * 
 * View patient prescriptions/recipes
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

interface Prescription {
    id: string;
    medication: string;
    dosage: string;
    practitioner: string;
    date: string;
    validUntil: string;
    status: 'active' | 'expired' | 'used';
}

const mockPrescriptions: Prescription[] = [
    {
        id: '1',
        medication: 'Losartana 50mg',
        dosage: '1 comprimido ao dia',
        practitioner: 'Dra. Maria Santos',
        date: '05/12/2024',
        validUntil: '05/03/2025',
        status: 'active',
    },
    {
        id: '2',
        medication: 'Sinvastatina 20mg',
        dosage: '1 comprimido à noite',
        practitioner: 'Dra. Maria Santos',
        date: '05/12/2024',
        validUntil: '05/03/2025',
        status: 'active',
    },
    {
        id: '3',
        medication: 'Amoxicilina 500mg',
        dosage: '1 cápsula de 8/8h por 7 dias',
        practitioner: 'Dr. Carlos Silva',
        date: '15/11/2024',
        validUntil: '22/11/2024',
        status: 'used',
    },
    {
        id: '4',
        medication: 'Ibuprofeno 600mg',
        dosage: 'Se dor, máximo 3x ao dia',
        practitioner: 'Dr. João Oliveira',
        date: '01/10/2024',
        validUntil: '01/01/2025',
        status: 'expired',
    },
];

const statusConfig = {
    active: { color: colors.success[500], label: 'Ativa', icon: 'checkmark-circle' as const },
    expired: { color: colors.error[500], label: 'Expirada', icon: 'alert-circle' as const },
    used: { color: colors.gray[400], label: 'Utilizada', icon: 'checkmark-done' as const },
};

export default function PrescriptionsScreen() {
    const router = useRouter();
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    }, []);

    const renderPrescription = ({ item }: { item: Prescription }) => {
        const status = statusConfig[item.status];

        return (
            <TouchableOpacity
                style={styles.prescriptionCard}
                onPress={() => router.push(`/records/prescriptions/${item.id}`)}
            >
                <View style={[styles.statusIndicator, { backgroundColor: status.color }]} />

                <View style={styles.prescriptionContent}>
                    <View style={styles.prescriptionHeader}>
                        <Text style={styles.medicationName} numberOfLines={1}>{item.medication}</Text>
                        <View style={[styles.statusBadge, { backgroundColor: status.color + '15' }]}>
                            <Ionicons name={status.icon} size={12} color={status.color} />
                            <Text style={[styles.statusText, { color: status.color }]}>{status.label}</Text>
                        </View>
                    </View>

                    <Text style={styles.dosage}>{item.dosage}</Text>

                    <View style={styles.prescriptionMeta}>
                        <View style={styles.metaItem}>
                            <Ionicons name="person-outline" size={12} color={colors.gray[400]} />
                            <Text style={styles.metaText}>{item.practitioner}</Text>
                        </View>
                        <View style={styles.metaItem}>
                            <Ionicons name="calendar-outline" size={12} color={colors.gray[400]} />
                            <Text style={styles.metaText}>Válida até {item.validUntil}</Text>
                        </View>
                    </View>
                </View>

                <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
            </TouchableOpacity>
        );
    };

    return (
        <>
            <Stack.Screen options={{ title: 'Receitas' }} />

            <View style={styles.container}>
                <FlatList
                    data={mockPrescriptions}
                    renderItem={renderPrescription}
                    keyExtractor={(item) => item.id}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                    }
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <Ionicons name="medkit-outline" size={64} color={colors.gray[300]} />
                            <Text style={styles.emptyTitle}>Nenhuma receita</Text>
                            <Text style={styles.emptyText}>
                                Suas receitas médicas aparecerão aqui
                            </Text>
                        </View>
                    }
                />
            </View>
        </>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    listContent: {
        padding: 16,
    },
    prescriptionCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        borderRadius: 14,
        marginBottom: 10,
        overflow: 'hidden',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.02,
        shadowRadius: 2,
        elevation: 1,
    },
    statusIndicator: {
        width: 4,
        height: '100%',
    },
    prescriptionContent: {
        flex: 1,
        padding: 16,
    },
    prescriptionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 4,
    },
    medicationName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[900],
        flex: 1,
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 10,
        marginLeft: 8,
        gap: 4,
    },
    statusText: {
        fontFamily: 'Inter-Medium',
        fontSize: 11,
    },
    dosage: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[600],
        marginBottom: 8,
    },
    prescriptionMeta: {
        flexDirection: 'row',
        gap: 16,
    },
    metaItem: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    metaText: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.gray[400],
    },
    emptyState: {
        alignItems: 'center',
        paddingTop: 80,
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
});

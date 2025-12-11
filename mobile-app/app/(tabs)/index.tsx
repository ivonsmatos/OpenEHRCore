/**
 * Sprint 26: Home Screen (Patient Portal Dashboard)
 * 
 * Main dashboard for the patient portal
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/store/AuthContext';
import { colors } from '@/theme/colors';

interface QuickActionProps {
    icon: keyof typeof Ionicons.glyphMap;
    label: string;
    onPress: () => void;
    color: string;
}

const QuickAction = ({ icon, label, onPress, color }: QuickActionProps) => (
    <TouchableOpacity style={styles.quickAction} onPress={onPress}>
        <View style={[styles.quickActionIcon, { backgroundColor: color }]}>
            <Ionicons name={icon} size={24} color="#fff" />
        </View>
        <Text style={styles.quickActionLabel}>{label}</Text>
    </TouchableOpacity>
);

interface InfoCardProps {
    title: string;
    value: string;
    subtitle?: string;
    icon: keyof typeof Ionicons.glyphMap;
}

const InfoCard = ({ title, value, subtitle, icon }: InfoCardProps) => (
    <View style={styles.infoCard}>
        <View style={styles.infoCardHeader}>
            <Ionicons name={icon} size={20} color={colors.primary[600]} />
            <Text style={styles.infoCardTitle}>{title}</Text>
        </View>
        <Text style={styles.infoCardValue}>{value}</Text>
        {subtitle && <Text style={styles.infoCardSubtitle}>{subtitle}</Text>}
    </View>
);

export default function HomeScreen() {
    const router = useRouter();
    const { user } = useAuth();
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        // Reload data
        setTimeout(() => setRefreshing(false), 1000);
    }, []);

    return (
        <ScrollView
            style={styles.container}
            refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
        >
            {/* Welcome Header */}
            <View style={styles.welcomeCard}>
                <View style={styles.welcomeContent}>
                    <Text style={styles.welcomeText}>Olá,</Text>
                    <Text style={styles.welcomeName}>{user?.name || 'Paciente'}</Text>
                </View>
                <View style={styles.avatarContainer}>
                    <Ionicons name="person-circle" size={50} color={colors.primary[600]} />
                </View>
            </View>

            {/* Quick Actions */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Acesso Rápido</Text>
                <View style={styles.quickActionsGrid}>
                    <QuickAction
                        icon="calendar"
                        label="Agendar"
                        color={colors.primary[500]}
                        onPress={() => router.push('/appointments/new')}
                    />
                    <QuickAction
                        icon="document-text"
                        label="Exames"
                        color={colors.success[500]}
                        onPress={() => router.push('/records/exams')}
                    />
                    <QuickAction
                        icon="medkit"
                        label="Receitas"
                        color={colors.warning[500]}
                        onPress={() => router.push('/records/prescriptions')}
                    />
                    <QuickAction
                        icon="chatbubbles"
                        label="Mensagem"
                        color={colors.info[500]}
                        onPress={() => router.push('/messages')}
                    />
                </View>
            </View>

            {/* Upcoming Appointment */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Próxima Consulta</Text>
                <TouchableOpacity
                    style={styles.appointmentCard}
                    onPress={() => router.push('/appointments')}
                >
                    <View style={styles.appointmentDate}>
                        <Text style={styles.appointmentDay}>15</Text>
                        <Text style={styles.appointmentMonth}>DEZ</Text>
                    </View>
                    <View style={styles.appointmentInfo}>
                        <Text style={styles.appointmentDoctor}>Dr. Carlos Silva</Text>
                        <Text style={styles.appointmentSpecialty}>Clínico Geral</Text>
                        <Text style={styles.appointmentTime}>14:30 - Presencial</Text>
                    </View>
                    <Ionicons name="chevron-forward" size={24} color={colors.gray[400]} />
                </TouchableOpacity>
            </View>

            {/* Health Summary */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Resumo de Saúde</Text>
                <View style={styles.infoCardsRow}>
                    <InfoCard
                        title="Pressão"
                        value="120/80"
                        subtitle="mmHg"
                        icon="heart"
                    />
                    <InfoCard
                        title="Peso"
                        value="72.5"
                        subtitle="kg"
                        icon="fitness"
                    />
                </View>
                <View style={styles.infoCardsRow}>
                    <InfoCard
                        title="Glicemia"
                        value="95"
                        subtitle="mg/dL"
                        icon="water"
                    />
                    <InfoCard
                        title="Vacinas"
                        value="Em dia"
                        icon="shield-checkmark"
                    />
                </View>
            </View>

            {/* Bottom spacing */}
            <View style={{ height: 20 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    welcomeCard: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#fff',
        margin: 16,
        padding: 20,
        borderRadius: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 2,
    },
    welcomeContent: {},
    welcomeText: {
        fontFamily: 'Inter-Regular',
        fontSize: 16,
        color: colors.gray[500],
    },
    welcomeName: {
        fontFamily: 'Inter-Bold',
        fontSize: 24,
        color: colors.gray[900],
        marginTop: 4,
    },
    avatarContainer: {},
    section: {
        marginHorizontal: 16,
        marginBottom: 24,
    },
    sectionTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 18,
        color: colors.gray[800],
        marginBottom: 12,
    },
    quickActionsGrid: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    quickAction: {
        alignItems: 'center',
        width: '22%',
    },
    quickActionIcon: {
        width: 56,
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 8,
    },
    quickActionLabel: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        color: colors.gray[700],
        textAlign: 'center',
    },
    appointmentCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 2,
    },
    appointmentDate: {
        backgroundColor: colors.primary[50],
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 12,
        alignItems: 'center',
        marginRight: 16,
    },
    appointmentDay: {
        fontFamily: 'Inter-Bold',
        fontSize: 24,
        color: colors.primary[600],
    },
    appointmentMonth: {
        fontFamily: 'Inter-Medium',
        fontSize: 12,
        color: colors.primary[600],
    },
    appointmentInfo: {
        flex: 1,
    },
    appointmentDoctor: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: colors.gray[900],
    },
    appointmentSpecialty: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginTop: 2,
    },
    appointmentTime: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.primary[600],
        marginTop: 4,
    },
    infoCardsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 12,
    },
    infoCard: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        width: '48%',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.03,
        shadowRadius: 4,
        elevation: 1,
    },
    infoCardHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    infoCardTitle: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.gray[500],
        marginLeft: 8,
    },
    infoCardValue: {
        fontFamily: 'Inter-Bold',
        fontSize: 24,
        color: colors.gray[900],
    },
    infoCardSubtitle: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.gray[400],
    },
});

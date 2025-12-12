/**
 * Sprint 26: Exams List Screen
 * 
 * View patient exam results
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useState, useCallback } from 'react';
import { useRouter, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

interface Exam {
    id: string;
    name: string;
    date: string;
    lab: string;
    status: 'pending' | 'available' | 'viewed';
    category: string;
}

const mockExams: Exam[] = [
    {
        id: '1',
        name: 'Hemograma Completo',
        date: '10/12/2024',
        lab: 'Laboratório São Lucas',
        status: 'available',
        category: 'Sangue',
    },
    {
        id: '2',
        name: 'Glicemia de Jejum',
        date: '10/12/2024',
        lab: 'Laboratório São Lucas',
        status: 'available',
        category: 'Sangue',
    },
    {
        id: '3',
        name: 'Raio-X Tórax',
        date: '05/12/2024',
        lab: 'Centro de Imagem',
        status: 'viewed',
        category: 'Imagem',
    },
    {
        id: '4',
        name: 'Eletrocardiograma',
        date: '01/12/2024',
        lab: 'Cardiologia SP',
        status: 'viewed',
        category: 'Cardiologia',
    },
    {
        id: '5',
        name: 'Ultrassom Abdominal',
        date: '15/11/2024',
        lab: 'Centro de Imagem',
        status: 'viewed',
        category: 'Imagem',
    },
];

const statusConfig = {
    pending: { color: colors.warning[500], label: 'Aguardando', icon: 'time-outline' as const },
    available: { color: colors.success[500], label: 'Disponível', icon: 'checkmark-circle' as const },
    viewed: { color: colors.gray[400], label: 'Visualizado', icon: 'eye-outline' as const },
};

export default function ExamsScreen() {
    const router = useRouter();
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    }, []);

    const renderExam = ({ item }: { item: Exam }) => {
        const status = statusConfig[item.status];

        return (
            <TouchableOpacity
                style={styles.examCard}
                onPress={() => router.push(`/records/exams/${item.id}`)}
            >
                <View style={styles.examIcon}>
                    <Ionicons name="document-text" size={24} color={colors.primary[600]} />
                </View>

                <View style={styles.examContent}>
                    <View style={styles.examHeader}>
                        <Text style={styles.examName} numberOfLines={1}>{item.name}</Text>
                        {item.status === 'available' && (
                            <View style={styles.newBadge}>
                                <Text style={styles.newBadgeText}>NOVO</Text>
                            </View>
                        )}
                    </View>
                    <Text style={styles.examCategory}>{item.category}</Text>
                    <View style={styles.examMeta}>
                        <Text style={styles.examLab}>{item.lab}</Text>
                        <Text style={styles.examDate}>{item.date}</Text>
                    </View>
                </View>

                <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
            </TouchableOpacity>
        );
    };

    return (
        <>
            <Stack.Screen
                options={{
                    title: 'Exames',
                    headerSearchBarOptions: {
                        placeholder: 'Buscar exame...',
                    },
                }}
            />

            <View style={styles.container}>
                <FlatList
                    data={mockExams}
                    renderItem={renderExam}
                    keyExtractor={(item) => item.id}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                    }
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <Ionicons name="document-text-outline" size={64} color={colors.gray[300]} />
                            <Text style={styles.emptyTitle}>Nenhum exame</Text>
                            <Text style={styles.emptyText}>
                                Seus resultados de exames aparecerão aqui
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
    examCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 14,
        marginBottom: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.02,
        shadowRadius: 2,
        elevation: 1,
    },
    examIcon: {
        width: 48,
        height: 48,
        borderRadius: 12,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 14,
    },
    examContent: {
        flex: 1,
    },
    examHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    examName: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[900],
        flex: 1,
    },
    newBadge: {
        backgroundColor: colors.success[500],
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 10,
        marginLeft: 8,
    },
    newBadgeText: {
        fontFamily: 'Inter-Bold',
        fontSize: 10,
        color: '#fff',
    },
    examCategory: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 2,
    },
    examMeta: {
        flexDirection: 'row',
        marginTop: 6,
    },
    examLab: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.gray[400],
    },
    examDate: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.gray[400],
        marginLeft: 8,
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

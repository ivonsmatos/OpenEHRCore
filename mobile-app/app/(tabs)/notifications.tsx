/**
 * Sprint 26: Notifications Screen
 * 
 * Push notifications and in-app alerts
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Notification {
    id: string;
    type: 'appointment' | 'result' | 'prescription' | 'message' | 'reminder' | 'system';
    title: string;
    body: string;
    timestamp: string;
    read: boolean;
    actionRoute?: string;
}

const mockNotifications: Notification[] = [
    {
        id: '1',
        type: 'appointment',
        title: 'Lembrete de Consulta',
        body: 'Sua consulta com Dr. Carlos Silva é amanhã às 14:30.',
        timestamp: '2024-12-11T10:00:00Z',
        read: false,
        actionRoute: '/appointments/1',
    },
    {
        id: '2',
        type: 'result',
        title: 'Resultado de Exame Disponível',
        body: 'Os resultados do seu Hemograma Completo já estão disponíveis.',
        timestamp: '2024-12-10T15:30:00Z',
        read: false,
        actionRoute: '/records/exams/1',
    },
    {
        id: '3',
        type: 'prescription',
        title: 'Nova Receita',
        body: 'Dra. Maria Santos emitiu uma nova receita para você.',
        timestamp: '2024-12-05T09:00:00Z',
        read: true,
        actionRoute: '/records/prescriptions/1',
    },
    {
        id: '4',
        type: 'reminder',
        title: 'Hora do Medicamento',
        body: 'Lembre-se de tomar Losartana 50mg.',
        timestamp: '2024-12-04T08:00:00Z',
        read: true,
    },
    {
        id: '5',
        type: 'system',
        title: 'Atualização de Segurança',
        body: 'Suas configurações de privacidade foram atualizadas.',
        timestamp: '2024-12-01T12:00:00Z',
        read: true,
    },
];

const notificationConfig: Record<string, { icon: keyof typeof Ionicons.glyphMap; color: string }> = {
    appointment: { icon: 'calendar', color: colors.primary[500] },
    result: { icon: 'document-text', color: colors.success[500] },
    prescription: { icon: 'medkit', color: colors.warning[500] },
    message: { icon: 'chatbubble', color: colors.info[500] },
    reminder: { icon: 'alarm', color: colors.purple[500] },
    system: { icon: 'settings', color: colors.gray[500] },
};

export default function NotificationsScreen() {
    const [notifications, setNotifications] = useState(mockNotifications);
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        setTimeout(() => setRefreshing(false), 1000);
    }, []);

    const markAsRead = (id: string) => {
        setNotifications(prev =>
            prev.map(n => n.id === id ? { ...n, read: true } : n)
        );
    };

    const markAllAsRead = () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    };

    const unreadCount = notifications.filter(n => !n.read).length;

    const renderNotification = ({ item }: { item: Notification }) => {
        const config = notificationConfig[item.type];
        const timeAgo = formatDistanceToNow(parseISO(item.timestamp), {
            addSuffix: true,
            locale: ptBR
        });

        return (
            <TouchableOpacity
                style={[
                    styles.notificationCard,
                    !item.read && styles.notificationUnread
                ]}
                onPress={() => markAsRead(item.id)}
            >
                <View style={[styles.iconContainer, { backgroundColor: config.color + '15' }]}>
                    <Ionicons name={config.icon} size={22} color={config.color} />
                </View>

                <View style={styles.content}>
                    <View style={styles.header}>
                        <Text style={styles.title} numberOfLines={1}>
                            {item.title}
                        </Text>
                        {!item.read && <View style={styles.unreadDot} />}
                    </View>
                    <Text style={styles.body} numberOfLines={2}>
                        {item.body}
                    </Text>
                    <Text style={styles.timestamp}>{timeAgo}</Text>
                </View>
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            {/* Header Actions */}
            {unreadCount > 0 && (
                <View style={styles.headerBar}>
                    <Text style={styles.unreadText}>
                        {unreadCount} não lida{unreadCount > 1 ? 's' : ''}
                    </Text>
                    <TouchableOpacity onPress={markAllAsRead}>
                        <Text style={styles.markAllText}>Marcar todas como lidas</Text>
                    </TouchableOpacity>
                </View>
            )}

            {/* Notifications List */}
            <FlatList
                data={notifications}
                renderItem={renderNotification}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
                ListEmptyComponent={
                    <View style={styles.emptyState}>
                        <Ionicons name="notifications-off-outline" size={64} color={colors.gray[300]} />
                        <Text style={styles.emptyTitle}>Sem notificações</Text>
                        <Text style={styles.emptyText}>
                            Você não tem notificações no momento
                        </Text>
                    </View>
                }
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    headerBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: colors.gray[100],
    },
    unreadText: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.gray[600],
    },
    markAllText: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.primary[600],
    },
    listContent: {
        padding: 16,
    },
    notificationCard: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        marginBottom: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.02,
        shadowRadius: 2,
        elevation: 1,
    },
    notificationUnread: {
        backgroundColor: colors.primary[50],
        borderLeftWidth: 3,
        borderLeftColor: colors.primary[500],
    },
    iconContainer: {
        width: 44,
        height: 44,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    content: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    title: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[800],
        flex: 1,
    },
    unreadDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.primary[500],
        marginLeft: 8,
    },
    body: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[600],
        marginTop: 4,
        lineHeight: 20,
    },
    timestamp: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.gray[400],
        marginTop: 8,
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

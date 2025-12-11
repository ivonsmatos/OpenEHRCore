/**
 * Sprint 26: Tab Navigation Layout
 * 
 * Main tab navigation for authenticated users
 */

import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

type IconName = keyof typeof Ionicons.glyphMap;

export default function TabsLayout() {
    return (
        <Tabs
            screenOptions={{
                tabBarActiveTintColor: colors.primary[600],
                tabBarInactiveTintColor: colors.gray[400],
                tabBarStyle: {
                    backgroundColor: '#fff',
                    borderTopWidth: 1,
                    borderTopColor: colors.gray[200],
                    paddingTop: 8,
                    paddingBottom: 8,
                    height: 60,
                },
                tabBarLabelStyle: {
                    fontFamily: 'Inter-Medium',
                    fontSize: 12,
                },
                headerStyle: {
                    backgroundColor: colors.primary[600],
                },
                headerTintColor: '#fff',
                headerTitleStyle: {
                    fontFamily: 'Inter-SemiBold',
                },
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: 'Início',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="home-outline" size={size} color={color} />
                    ),
                    headerTitle: 'Portal do Paciente',
                }}
            />
            <Tabs.Screen
                name="appointments"
                options={{
                    title: 'Consultas',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="calendar-outline" size={size} color={color} />
                    ),
                    headerTitle: 'Minhas Consultas',
                }}
            />
            <Tabs.Screen
                name="records"
                options={{
                    title: 'Prontuário',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="document-text-outline" size={size} color={color} />
                    ),
                    headerTitle: 'Meu Prontuário',
                }}
            />
            <Tabs.Screen
                name="notifications"
                options={{
                    title: 'Avisos',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="notifications-outline" size={size} color={color} />
                    ),
                    headerTitle: 'Notificações',
                }}
            />
            <Tabs.Screen
                name="profile"
                options={{
                    title: 'Perfil',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="person-outline" size={size} color={color} />
                    ),
                    headerTitle: 'Meu Perfil',
                }}
            />
        </Tabs>
    );
}

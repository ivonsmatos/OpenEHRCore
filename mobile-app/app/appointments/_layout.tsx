/**
 * Sprint 26: Appointments Stack Layout
 */

import { Stack } from 'expo-router';
import { colors } from '@/theme/colors';

export default function AppointmentsLayout() {
    return (
        <Stack
            screenOptions={{
                headerStyle: {
                    backgroundColor: colors.primary[600],
                },
                headerTintColor: '#fff',
                headerTitleStyle: {
                    fontFamily: 'Inter-SemiBold',
                },
            }}
        >
            <Stack.Screen
                name="new"
                options={{
                    title: 'Nova Consulta',
                    presentation: 'modal',
                }}
            />
            <Stack.Screen
                name="[id]"
                options={{
                    title: 'Detalhes da Consulta',
                }}
            />
        </Stack>
    );
}

/**
 * Sprint 26: Records Stack Layout
 */

import { Stack } from 'expo-router';
import { colors } from '@/theme/colors';

export default function RecordsLayout() {
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
            <Stack.Screen name="exams/index" options={{ title: 'Exames' }} />
            <Stack.Screen name="exams/[id]" options={{ title: 'Resultado' }} />
            <Stack.Screen name="prescriptions/index" options={{ title: 'Receitas' }} />
            <Stack.Screen name="prescriptions/[id]" options={{ title: 'Receita' }} />
        </Stack>
    );
}

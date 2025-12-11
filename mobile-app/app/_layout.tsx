/**
 * Sprint 26: Root Layout
 * 
 * Main navigation structure with authentication state
 */

import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { AuthProvider } from '@/store/AuthContext';
import { NotificationProvider } from '@/store/NotificationContext';
import { colors } from '@/theme/colors';

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
    const [fontsLoaded] = useFonts({
        'Inter-Regular': require('../assets/fonts/Inter-Regular.ttf'),
        'Inter-Medium': require('../assets/fonts/Inter-Medium.ttf'),
        'Inter-SemiBold': require('../assets/fonts/Inter-SemiBold.ttf'),
        'Inter-Bold': require('../assets/fonts/Inter-Bold.ttf'),
    });

    useEffect(() => {
        if (fontsLoaded) {
            SplashScreen.hideAsync();
        }
    }, [fontsLoaded]);

    if (!fontsLoaded) {
        return null;
    }

    return (
        <AuthProvider>
            <NotificationProvider>
                <StatusBar style="auto" />
                <Stack
                    screenOptions={{
                        headerStyle: {
                            backgroundColor: colors.primary[600],
                        },
                        headerTintColor: '#fff',
                        headerTitleStyle: {
                            fontFamily: 'Inter-SemiBold',
                        },
                        contentStyle: {
                            backgroundColor: colors.background,
                        },
                    }}
                >
                    <Stack.Screen
                        name="(auth)"
                        options={{ headerShown: false }}
                    />
                    <Stack.Screen
                        name="(tabs)"
                        options={{ headerShown: false }}
                    />
                </Stack>
            </NotificationProvider>
        </AuthProvider>
    );
}

/**
 * Sprint 26: Push Notification Context
 * 
 * Handles push notification registration and handling
 */

import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { Platform } from 'react-native';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';
import { api } from '@/services/api';

// Configure notification behavior
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

interface NotificationContextType {
    expoPushToken: string | null;
    notification: Notifications.Notification | null;
    sendLocalNotification: (title: string, body: string, data?: object) => Promise<void>;
    scheduleMedicationReminder: (medication: string, time: Date) => Promise<string>;
    scheduleAppointmentReminder: (appointmentId: string, datetime: Date, practitioner: string) => Promise<string>;
    cancelNotification: (id: string) => Promise<void>;
    setBadgeCount: (count: number) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
    children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
    const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
    const [notification, setNotification] = useState<Notifications.Notification | null>(null);
    const notificationListener = useRef<Notifications.Subscription>();
    const responseListener = useRef<Notifications.Subscription>();
    const router = useRouter();

    useEffect(() => {
        // Register for push notifications
        registerForPushNotificationsAsync().then(token => {
            if (token) {
                setExpoPushToken(token);
                // Send token to backend
                sendTokenToBackend(token);
            }
        });

        // Listen for incoming notifications
        notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
            setNotification(notification);
        });

        // Listen for notification responses (when user taps)
        responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
            handleNotificationResponse(response);
        });

        return () => {
            if (notificationListener.current) {
                Notifications.removeNotificationSubscription(notificationListener.current);
            }
            if (responseListener.current) {
                Notifications.removeNotificationSubscription(responseListener.current);
            }
        };
    }, []);

    const handleNotificationResponse = (response: Notifications.NotificationResponse) => {
        const data = response.notification.request.content.data;

        // Navigate based on notification type
        if (data?.route) {
            router.push(data.route as any);
        } else if (data?.type === 'appointment') {
            router.push(`/appointments/${data.appointmentId}`);
        } else if (data?.type === 'result') {
            router.push(`/records/exams/${data.examId}`);
        } else if (data?.type === 'prescription') {
            router.push(`/records/prescriptions/${data.prescriptionId}`);
        }
    };

    const sendTokenToBackend = async (token: string) => {
        try {
            await api.post('/notifications/register-device', {
                push_token: token,
                platform: Platform.OS,
                device_name: Device.modelName,
            });
        } catch (error) {
            console.error('Failed to register push token:', error);
        }
    };

    const sendLocalNotification = async (title: string, body: string, data?: object) => {
        await Notifications.scheduleNotificationAsync({
            content: {
                title,
                body,
                data: data || {},
                sound: 'default',
            },
            trigger: null, // Send immediately
        });
    };

    const scheduleMedicationReminder = async (medication: string, time: Date): Promise<string> => {
        const id = await Notifications.scheduleNotificationAsync({
            content: {
                title: 'Hora do Medicamento 💊',
                body: `Lembre-se de tomar ${medication}`,
                data: { type: 'medication', medication },
                sound: 'default',
            },
            trigger: {
                date: time,
            },
        });
        return id;
    };

    const scheduleAppointmentReminder = async (
        appointmentId: string,
        datetime: Date,
        practitioner: string
    ): Promise<string> => {
        // Schedule reminder 1 day before
        const reminderTime = new Date(datetime);
        reminderTime.setDate(reminderTime.getDate() - 1);
        reminderTime.setHours(9, 0, 0, 0);

        const id = await Notifications.scheduleNotificationAsync({
            content: {
                title: 'Lembrete de Consulta 📅',
                body: `Sua consulta com ${practitioner} é amanhã`,
                data: {
                    type: 'appointment',
                    appointmentId,
                    route: `/appointments/${appointmentId}`
                },
                sound: 'default',
            },
            trigger: {
                date: reminderTime,
            },
        });
        return id;
    };

    const cancelNotification = async (id: string) => {
        await Notifications.cancelScheduledNotificationAsync(id);
    };

    const setBadgeCount = async (count: number) => {
        await Notifications.setBadgeCountAsync(count);
    };

    return (
        <NotificationContext.Provider
            value={{
                expoPushToken,
                notification,
                sendLocalNotification,
                scheduleMedicationReminder,
                scheduleAppointmentReminder,
                cancelNotification,
                setBadgeCount,
            }}
        >
            {children}
        </NotificationContext.Provider>
    );
}

export function useNotifications() {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
}

// Helper function to register for push notifications
async function registerForPushNotificationsAsync(): Promise<string | null> {
    let token: string | null = null;

    if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#3b82f6',
        });
    }

    if (Device.isDevice) {
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.log('Failed to get push token for push notification!');
            return null;
        }

        const projectId = Constants.expoConfig?.extra?.eas?.projectId;
        token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
    } else {
        console.log('Must use physical device for Push Notifications');
    }

    return token;
}

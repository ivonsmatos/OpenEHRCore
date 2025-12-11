/**
 * Sprint 26: Profile Screen
 * 
 * User profile and settings
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/store/AuthContext';
import { colors } from '@/theme/colors';

interface MenuItem {
    id: string;
    icon: keyof typeof Ionicons.glyphMap;
    title: string;
    subtitle?: string;
    route?: string;
    action?: () => void;
    color?: string;
}

export default function ProfileScreen() {
    const router = useRouter();
    const { user, logout } = useAuth();

    const menuSections: { title: string; items: MenuItem[] }[] = [
        {
            title: 'Conta',
            items: [
                {
                    id: 'personal',
                    icon: 'person-outline',
                    title: 'Dados Pessoais',
                    subtitle: 'Nome, CPF, data de nascimento',
                    route: '/profile/personal',
                },
                {
                    id: 'contact',
                    icon: 'call-outline',
                    title: 'Contato',
                    subtitle: 'Telefone, email, endereço',
                    route: '/profile/contact',
                },
                {
                    id: 'emergency',
                    icon: 'alert-circle-outline',
                    title: 'Contato de Emergência',
                    route: '/profile/emergency',
                },
            ],
        },
        {
            title: 'Saúde',
            items: [
                {
                    id: 'insurance',
                    icon: 'card-outline',
                    title: 'Plano de Saúde',
                    subtitle: 'Gerenciar convênios',
                    route: '/profile/insurance',
                },
                {
                    id: 'medications',
                    icon: 'medkit-outline',
                    title: 'Medicamentos em Uso',
                    route: '/profile/medications',
                },
                {
                    id: 'allergies',
                    icon: 'warning-outline',
                    title: 'Alergias',
                    route: '/profile/allergies',
                },
            ],
        },
        {
            title: 'Preferências',
            items: [
                {
                    id: 'notifications',
                    icon: 'notifications-outline',
                    title: 'Notificações',
                    subtitle: 'Gerenciar alertas',
                    route: '/profile/notifications',
                },
                {
                    id: 'privacy',
                    icon: 'shield-checkmark-outline',
                    title: 'Privacidade (LGPD)',
                    subtitle: 'Consentimentos e dados',
                    route: '/profile/privacy',
                },
                {
                    id: 'security',
                    icon: 'lock-closed-outline',
                    title: 'Segurança',
                    subtitle: 'Senha e biometria',
                    route: '/profile/security',
                },
            ],
        },
        {
            title: 'Ajuda',
            items: [
                {
                    id: 'help',
                    icon: 'help-circle-outline',
                    title: 'Central de Ajuda',
                    route: '/profile/help',
                },
                {
                    id: 'terms',
                    icon: 'document-text-outline',
                    title: 'Termos de Uso',
                    route: '/profile/terms',
                },
                {
                    id: 'about',
                    icon: 'information-circle-outline',
                    title: 'Sobre o App',
                    subtitle: 'Versão 1.0.0',
                    route: '/profile/about',
                },
            ],
        },
        {
            title: '',
            items: [
                {
                    id: 'logout',
                    icon: 'log-out-outline',
                    title: 'Sair',
                    color: colors.error[500],
                    action: () => {
                        Alert.alert(
                            'Sair',
                            'Deseja realmente sair da sua conta?',
                            [
                                { text: 'Cancelar', style: 'cancel' },
                                { text: 'Sair', style: 'destructive', onPress: logout },
                            ]
                        );
                    },
                },
            ],
        },
    ];

    const handleMenuPress = (item: MenuItem) => {
        if (item.action) {
            item.action();
        } else if (item.route) {
            router.push(item.route as any);
        }
    };

    return (
        <ScrollView style={styles.container}>
            {/* Profile Header */}
            <View style={styles.profileHeader}>
                <View style={styles.avatarContainer}>
                    {user?.avatar ? (
                        <Image source={{ uri: user.avatar }} style={styles.avatar} />
                    ) : (
                        <View style={styles.avatarPlaceholder}>
                            <Text style={styles.avatarInitial}>
                                {user?.name?.charAt(0) || 'P'}
                            </Text>
                        </View>
                    )}
                    <TouchableOpacity style={styles.editAvatarButton}>
                        <Ionicons name="camera" size={14} color="#fff" />
                    </TouchableOpacity>
                </View>
                <Text style={styles.userName}>{user?.name || 'Paciente'}</Text>
                <Text style={styles.userEmail}>{user?.email || 'email@exemplo.com'}</Text>
            </View>

            {/* Menu Sections */}
            {menuSections.map((section) => (
                <View key={section.title || 'logout'} style={styles.section}>
                    {section.title && (
                        <Text style={styles.sectionTitle}>{section.title}</Text>
                    )}
                    <View style={styles.menuCard}>
                        {section.items.map((item, index) => (
                            <View key={item.id}>
                                <TouchableOpacity
                                    style={styles.menuItem}
                                    onPress={() => handleMenuPress(item)}
                                >
                                    <View style={[
                                        styles.menuIcon,
                                        { backgroundColor: (item.color || colors.primary[500]) + '15' }
                                    ]}>
                                        <Ionicons
                                            name={item.icon}
                                            size={20}
                                            color={item.color || colors.primary[600]}
                                        />
                                    </View>
                                    <View style={styles.menuContent}>
                                        <Text style={[
                                            styles.menuTitle,
                                            item.color && { color: item.color }
                                        ]}>
                                            {item.title}
                                        </Text>
                                        {item.subtitle && (
                                            <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
                                        )}
                                    </View>
                                    {!item.action && (
                                        <Ionicons
                                            name="chevron-forward"
                                            size={18}
                                            color={colors.gray[300]}
                                        />
                                    )}
                                </TouchableOpacity>
                                {index < section.items.length - 1 && (
                                    <View style={styles.divider} />
                                )}
                            </View>
                        ))}
                    </View>
                </View>
            ))}

            {/* Bottom spacing */}
            <View style={{ height: 40 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    profileHeader: {
        alignItems: 'center',
        paddingVertical: 24,
        backgroundColor: '#fff',
        marginBottom: 8,
    },
    avatarContainer: {
        position: 'relative',
        marginBottom: 12,
    },
    avatar: {
        width: 80,
        height: 80,
        borderRadius: 40,
    },
    avatarPlaceholder: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: colors.primary[100],
        justifyContent: 'center',
        alignItems: 'center',
    },
    avatarInitial: {
        fontFamily: 'Inter-Bold',
        fontSize: 32,
        color: colors.primary[600],
    },
    editAvatarButton: {
        position: 'absolute',
        bottom: 0,
        right: 0,
        width: 28,
        height: 28,
        borderRadius: 14,
        backgroundColor: colors.primary[600],
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#fff',
    },
    userName: {
        fontFamily: 'Inter-Bold',
        fontSize: 20,
        color: colors.gray[900],
    },
    userEmail: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[500],
        marginTop: 4,
    },
    section: {
        marginTop: 16,
        marginHorizontal: 16,
    },
    sectionTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 14,
        color: colors.gray[500],
        marginBottom: 8,
        marginLeft: 4,
        textTransform: 'uppercase',
    },
    menuCard: {
        backgroundColor: '#fff',
        borderRadius: 16,
        overflow: 'hidden',
    },
    menuItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 14,
    },
    menuIcon: {
        width: 36,
        height: 36,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    menuContent: {
        flex: 1,
    },
    menuTitle: {
        fontFamily: 'Inter-Medium',
        fontSize: 15,
        color: colors.gray[800],
    },
    menuSubtitle: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 2,
    },
    divider: {
        height: 1,
        backgroundColor: colors.gray[100],
        marginLeft: 62,
    },
});

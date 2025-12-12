/**
 * Sprint 26: Reusable Card Component
 */

import { View, Text, StyleSheet, TouchableOpacity, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

interface CardProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    icon?: keyof typeof Ionicons.glyphMap;
    iconColor?: string;
    onPress?: () => void;
    style?: ViewStyle;
    noPadding?: boolean;
}

export function Card({
    children,
    title,
    subtitle,
    icon,
    iconColor = colors.primary[600],
    onPress,
    style,
    noPadding = false,
}: CardProps) {
    const Container = onPress ? TouchableOpacity : View;

    return (
        <Container
            style={[
                styles.card,
                !noPadding && styles.cardPadding,
                style,
            ]}
            onPress={onPress}
            activeOpacity={onPress ? 0.7 : 1}
        >
            {(title || icon) && (
                <View style={styles.header}>
                    {icon && (
                        <View style={[styles.iconContainer, { backgroundColor: iconColor + '15' }]}>
                            <Ionicons name={icon} size={20} color={iconColor} />
                        </View>
                    )}
                    <View style={styles.headerText}>
                        {title && <Text style={styles.title}>{title}</Text>}
                        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
                    </View>
                    {onPress && (
                        <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
                    )}
                </View>
            )}
            {children}
        </Container>
    );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.03,
        shadowRadius: 4,
        elevation: 1,
    },
    cardPadding: {
        padding: 16,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
    },
    iconContainer: {
        width: 40,
        height: 40,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    headerText: {
        flex: 1,
    },
    title: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: colors.gray[900],
    },
    subtitle: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 2,
    },
});

export default Card;

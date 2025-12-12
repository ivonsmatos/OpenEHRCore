/**
 * Sprint 26: Reusable Button Component
 */

import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, ViewStyle, TextStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
    title: string;
    onPress: () => void;
    variant?: ButtonVariant;
    size?: ButtonSize;
    icon?: keyof typeof Ionicons.glyphMap;
    iconPosition?: 'left' | 'right';
    loading?: boolean;
    disabled?: boolean;
    fullWidth?: boolean;
    style?: ViewStyle;
    textStyle?: TextStyle;
}

const variantStyles: Record<ButtonVariant, { bg: string; text: string; border?: string }> = {
    primary: { bg: colors.primary[600], text: '#fff' },
    secondary: { bg: colors.gray[100], text: colors.gray[700] },
    outline: { bg: 'transparent', text: colors.primary[600], border: colors.primary[600] },
    ghost: { bg: 'transparent', text: colors.primary[600] },
    danger: { bg: colors.error[500], text: '#fff' },
};

const sizeStyles: Record<ButtonSize, { padding: number; fontSize: number; iconSize: number }> = {
    sm: { padding: 10, fontSize: 13, iconSize: 16 },
    md: { padding: 14, fontSize: 15, iconSize: 18 },
    lg: { padding: 18, fontSize: 17, iconSize: 22 },
};

export function Button({
    title,
    onPress,
    variant = 'primary',
    size = 'md',
    icon,
    iconPosition = 'left',
    loading = false,
    disabled = false,
    fullWidth = false,
    style,
    textStyle,
}: ButtonProps) {
    const variantStyle = variantStyles[variant];
    const sizeStyle = sizeStyles[size];
    const isDisabled = disabled || loading;

    return (
        <TouchableOpacity
            style={[
                styles.button,
                {
                    backgroundColor: variantStyle.bg,
                    paddingVertical: sizeStyle.padding,
                    paddingHorizontal: sizeStyle.padding * 1.5,
                    borderWidth: variantStyle.border ? 1.5 : 0,
                    borderColor: variantStyle.border,
                    opacity: isDisabled ? 0.5 : 1,
                },
                fullWidth && styles.fullWidth,
                style,
            ]}
            onPress={onPress}
            disabled={isDisabled}
            activeOpacity={0.7}
        >
            {loading ? (
                <ActivityIndicator color={variantStyle.text} size="small" />
            ) : (
                <>
                    {icon && iconPosition === 'left' && (
                        <Ionicons
                            name={icon}
                            size={sizeStyle.iconSize}
                            color={variantStyle.text}
                            style={styles.iconLeft}
                        />
                    )}
                    <Text
                        style={[
                            styles.text,
                            { color: variantStyle.text, fontSize: sizeStyle.fontSize },
                            textStyle,
                        ]}
                    >
                        {title}
                    </Text>
                    {icon && iconPosition === 'right' && (
                        <Ionicons
                            name={icon}
                            size={sizeStyle.iconSize}
                            color={variantStyle.text}
                            style={styles.iconRight}
                        />
                    )}
                </>
            )}
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    button: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 12,
    },
    fullWidth: {
        width: '100%',
    },
    text: {
        fontFamily: 'Inter-SemiBold',
    },
    iconLeft: {
        marginRight: 8,
    },
    iconRight: {
        marginLeft: 8,
    },
});

export default Button;

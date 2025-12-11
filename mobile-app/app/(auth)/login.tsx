/**
 * Sprint 26: Login Screen
 * 
 * Patient authentication screen
 */

import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/store/AuthContext';
import { colors } from '@/theme/colors';

export default function LoginScreen() {
    const { login, isLoading } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

    const validate = () => {
        const newErrors: { email?: string; password?: string } = {};

        if (!email) {
            newErrors.email = 'E-mail é obrigatório';
        } else if (!/\S+@\S+\.\S+/.test(email)) {
            newErrors.email = 'E-mail inválido';
        }

        if (!password) {
            newErrors.password = 'Senha é obrigatória';
        } else if (password.length < 6) {
            newErrors.password = 'Senha deve ter no mínimo 6 caracteres';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleLogin = async () => {
        if (!validate()) return;

        try {
            await login(email, password);
        } catch (error: any) {
            Alert.alert('Erro', error.message || 'Falha ao fazer login');
        }
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
            <View style={styles.content}>
                {/* Logo */}
                <View style={styles.logoContainer}>
                    <View style={styles.logo}>
                        <Ionicons name="medical" size={48} color={colors.primary[600]} />
                    </View>
                    <Text style={styles.appName}>OpenEHRCore</Text>
                    <Text style={styles.appSubtitle}>Portal do Paciente</Text>
                </View>

                {/* Form */}
                <View style={styles.form}>
                    <View style={styles.inputContainer}>
                        <Ionicons
                            name="mail-outline"
                            size={20}
                            color={errors.email ? colors.error[500] : colors.gray[400]}
                            style={styles.inputIcon}
                        />
                        <TextInput
                            style={[styles.input, errors.email && styles.inputError]}
                            placeholder="E-mail"
                            placeholderTextColor={colors.gray[400]}
                            keyboardType="email-address"
                            autoCapitalize="none"
                            autoCorrect={false}
                            value={email}
                            onChangeText={(text) => {
                                setEmail(text);
                                if (errors.email) setErrors({ ...errors, email: undefined });
                            }}
                        />
                    </View>
                    {errors.email && (
                        <Text style={styles.errorText}>{errors.email}</Text>
                    )}

                    <View style={styles.inputContainer}>
                        <Ionicons
                            name="lock-closed-outline"
                            size={20}
                            color={errors.password ? colors.error[500] : colors.gray[400]}
                            style={styles.inputIcon}
                        />
                        <TextInput
                            style={[styles.input, errors.password && styles.inputError]}
                            placeholder="Senha"
                            placeholderTextColor={colors.gray[400]}
                            secureTextEntry={!showPassword}
                            value={password}
                            onChangeText={(text) => {
                                setPassword(text);
                                if (errors.password) setErrors({ ...errors, password: undefined });
                            }}
                        />
                        <TouchableOpacity
                            style={styles.passwordToggle}
                            onPress={() => setShowPassword(!showPassword)}
                        >
                            <Ionicons
                                name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                                size={20}
                                color={colors.gray[400]}
                            />
                        </TouchableOpacity>
                    </View>
                    {errors.password && (
                        <Text style={styles.errorText}>{errors.password}</Text>
                    )}

                    <TouchableOpacity style={styles.forgotPassword}>
                        <Text style={styles.forgotPasswordText}>Esqueceu a senha?</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
                        onPress={handleLogin}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <Text style={styles.loginButtonText}>Entrar</Text>
                        )}
                    </TouchableOpacity>
                </View>

                {/* Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>
                        Primeiro acesso?{' '}
                        <Text style={styles.footerLink}>Cadastre-se</Text>
                    </Text>
                </View>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    content: {
        flex: 1,
        paddingHorizontal: 24,
        justifyContent: 'center',
    },
    logoContainer: {
        alignItems: 'center',
        marginBottom: 48,
    },
    logo: {
        width: 80,
        height: 80,
        borderRadius: 20,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 16,
    },
    appName: {
        fontFamily: 'Inter-Bold',
        fontSize: 28,
        color: colors.gray[900],
    },
    appSubtitle: {
        fontFamily: 'Inter-Regular',
        fontSize: 16,
        color: colors.gray[500],
        marginTop: 4,
    },
    form: {
        marginBottom: 24,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.gray[50],
        borderRadius: 12,
        marginBottom: 4,
        borderWidth: 1,
        borderColor: colors.gray[200],
    },
    inputIcon: {
        marginLeft: 16,
    },
    input: {
        flex: 1,
        paddingVertical: 16,
        paddingHorizontal: 12,
        fontFamily: 'Inter-Regular',
        fontSize: 16,
        color: colors.gray[900],
    },
    inputError: {
        borderColor: colors.error[500],
    },
    passwordToggle: {
        padding: 16,
    },
    errorText: {
        fontFamily: 'Inter-Regular',
        fontSize: 12,
        color: colors.error[500],
        marginBottom: 12,
        marginLeft: 4,
    },
    forgotPassword: {
        alignSelf: 'flex-end',
        marginBottom: 24,
    },
    forgotPasswordText: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.primary[600],
    },
    loginButton: {
        backgroundColor: colors.primary[600],
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    loginButtonDisabled: {
        opacity: 0.7,
    },
    loginButtonText: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 16,
        color: '#fff',
    },
    footer: {
        alignItems: 'center',
    },
    footerText: {
        fontFamily: 'Inter-Regular',
        fontSize: 14,
        color: colors.gray[600],
    },
    footerLink: {
        fontFamily: 'Inter-SemiBold',
        color: colors.primary[600],
    },
});

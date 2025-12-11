/**
 * Sprint 26: Patient Records Screen
 * 
 * View patient health records, exams, prescriptions
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/theme/colors';

interface RecordCategory {
    id: string;
    title: string;
    icon: keyof typeof Ionicons.glyphMap;
    count: number;
    color: string;
    route: string;
}

const recordCategories: RecordCategory[] = [
    {
        id: 'consultations',
        title: 'Consultas',
        icon: 'medical-outline',
        count: 12,
        color: colors.primary[500],
        route: '/records/consultations',
    },
    {
        id: 'exams',
        title: 'Exames',
        icon: 'document-text-outline',
        count: 8,
        color: colors.success[500],
        route: '/records/exams',
    },
    {
        id: 'prescriptions',
        title: 'Receitas',
        icon: 'medkit-outline',
        count: 5,
        color: colors.warning[500],
        route: '/records/prescriptions',
    },
    {
        id: 'vaccines',
        title: 'Vacinas',
        icon: 'shield-checkmark-outline',
        count: 15,
        color: colors.info[500],
        route: '/records/vaccines',
    },
    {
        id: 'allergies',
        title: 'Alergias',
        icon: 'alert-circle-outline',
        count: 2,
        color: colors.error[500],
        route: '/records/allergies',
    },
    {
        id: 'conditions',
        title: 'Condições',
        icon: 'heart-outline',
        count: 3,
        color: colors.purple[500],
        route: '/records/conditions',
    },
];

interface RecentDocument {
    id: string;
    title: string;
    type: string;
    date: string;
    practitioner: string;
}

const recentDocuments: RecentDocument[] = [
    {
        id: '1',
        title: 'Hemograma Completo',
        type: 'Exame',
        date: '10/12/2024',
        practitioner: 'Lab. São Lucas',
    },
    {
        id: '2',
        title: 'Consulta Cardiológica',
        type: 'Consulta',
        date: '05/12/2024',
        practitioner: 'Dra. Maria Santos',
    },
    {
        id: '3',
        title: 'Receita - Losartana',
        type: 'Receita',
        date: '05/12/2024',
        practitioner: 'Dra. Maria Santos',
    },
];

export default function RecordsScreen() {
    const router = useRouter();

    return (
        <ScrollView style={styles.container}>
            {/* Categories Grid */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Categorias</Text>
                <View style={styles.categoriesGrid}>
                    {recordCategories.map((category) => (
                        <TouchableOpacity
                            key={category.id}
                            style={styles.categoryCard}
                            onPress={() => router.push(category.route as any)}
                        >
                            <View style={[styles.categoryIcon, { backgroundColor: category.color + '15' }]}>
                                <Ionicons name={category.icon} size={24} color={category.color} />
                            </View>
                            <Text style={styles.categoryTitle}>{category.title}</Text>
                            <Text style={styles.categoryCount}>{category.count} registros</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            {/* Recent Documents */}
            <View style={styles.section}>
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Documentos Recentes</Text>
                    <TouchableOpacity>
                        <Text style={styles.seeAll}>Ver todos</Text>
                    </TouchableOpacity>
                </View>

                {recentDocuments.map((doc) => (
                    <TouchableOpacity
                        key={doc.id}
                        style={styles.documentCard}
                        onPress={() => router.push(`/records/document/${doc.id}`)}
                    >
                        <View style={styles.documentIcon}>
                            <Ionicons name="document-outline" size={24} color={colors.primary[600]} />
                        </View>
                        <View style={styles.documentContent}>
                            <Text style={styles.documentTitle}>{doc.title}</Text>
                            <Text style={styles.documentMeta}>
                                {doc.type} • {doc.date}
                            </Text>
                            <Text style={styles.documentPractitioner}>{doc.practitioner}</Text>
                        </View>
                        <Ionicons name="chevron-forward" size={20} color={colors.gray[300]} />
                    </TouchableOpacity>
                ))}
            </View>

            {/* LGPD Actions */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Privacidade (LGPD)</Text>
                <View style={styles.lgpdCard}>
                    <TouchableOpacity style={styles.lgpdAction}>
                        <Ionicons name="download-outline" size={20} color={colors.primary[600]} />
                        <Text style={styles.lgpdActionText}>Exportar meus dados</Text>
                    </TouchableOpacity>
                    <View style={styles.lgpdDivider} />
                    <TouchableOpacity style={styles.lgpdAction}>
                        <Ionicons name="eye-outline" size={20} color={colors.primary[600]} />
                        <Text style={styles.lgpdActionText}>Histórico de acessos</Text>
                    </TouchableOpacity>
                    <View style={styles.lgpdDivider} />
                    <TouchableOpacity style={styles.lgpdAction}>
                        <Ionicons name="settings-outline" size={20} color={colors.primary[600]} />
                        <Text style={styles.lgpdActionText}>Gerenciar consentimentos</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Bottom spacing */}
            <View style={{ height: 20 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.gray[50],
    },
    section: {
        marginHorizontal: 16,
        marginTop: 20,
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    sectionTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 18,
        color: colors.gray[800],
        marginBottom: 12,
    },
    seeAll: {
        fontFamily: 'Inter-Medium',
        fontSize: 14,
        color: colors.primary[600],
        marginBottom: 12,
    },
    categoriesGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
    },
    categoryCard: {
        backgroundColor: '#fff',
        width: '48%',
        padding: 16,
        borderRadius: 16,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.03,
        shadowRadius: 4,
        elevation: 1,
    },
    categoryIcon: {
        width: 48,
        height: 48,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 12,
    },
    categoryTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[800],
    },
    categoryCount: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 4,
    },
    documentCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        marginBottom: 10,
    },
    documentIcon: {
        width: 44,
        height: 44,
        borderRadius: 10,
        backgroundColor: colors.primary[50],
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    documentContent: {
        flex: 1,
    },
    documentTitle: {
        fontFamily: 'Inter-SemiBold',
        fontSize: 15,
        color: colors.gray[800],
    },
    documentMeta: {
        fontFamily: 'Inter-Regular',
        fontSize: 13,
        color: colors.gray[500],
        marginTop: 2,
    },
    documentPractitioner: {
        fontFamily: 'Inter-Medium',
        fontSize: 13,
        color: colors.gray[600],
        marginTop: 2,
    },
    lgpdCard: {
        backgroundColor: '#fff',
        borderRadius: 16,
        overflow: 'hidden',
    },
    lgpdAction: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
    },
    lgpdActionText: {
        fontFamily: 'Inter-Medium',
        fontSize: 15,
        color: colors.gray[700],
        marginLeft: 12,
    },
    lgpdDivider: {
        height: 1,
        backgroundColor: colors.gray[100],
        marginHorizontal: 16,
    },
});

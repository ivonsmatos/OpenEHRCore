/**
 * Practitioner Edit Page
 * Wrapper for PractitionerForm with edit mode
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePractitioners } from '../../hooks/usePractitioners';
import PractitionerForm from './PractitionerForm';
import { PractitionerFormData } from '../../types/practitioner';
import Card from '../base/Card';
import { colors, spacing } from '../../theme/colors';
import { ArrowLeft } from 'lucide-react';
import Button from '../base/Button';

// Loading spinner styles
const spinnerStyles = `
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
`;

const PractitionerEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { getPractitioner, updatePractitioner } = usePractitioners();
    const [practitioner, setPractitioner] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [initialData, setInitialData] = useState<Partial<PractitionerFormData> | undefined>(undefined);

    useEffect(() => {
        const fetchPractitioner = async () => {
            if (!id) return;

            try {
                setLoading(true);
                const data = await getPractitioner(id);
                setPractitioner(data);

                // Convert FHIR resource to form data
                const formData: Partial<PractitionerFormData> = {};

                // Name
                if (data.name && data.name[0]) {
                    const name = data.name[0];
                    formData.family_name = name.family || '';
                    formData.given_names = name.given || [''];
                    formData.prefix = name.prefix?.[0] || '';
                }

                // Gender
                formData.gender = data.gender || 'unknown';

                // BirthDate
                formData.birthDate = data.birthDate || '';

                // Telecom
                if (data.telecom) {
                    const phone = data.telecom.find((t: any) => t.system === 'phone');
                    const email = data.telecom.find((t: any) => t.system === 'email');
                    formData.phone = phone?.value || '';
                    formData.email = email?.value || '';
                }

                // Identifiers (CRM)
                if (data.identifier) {
                    const crm = data.identifier.find((i: any) => 
                        i.system?.includes('crm') || i.type?.text?.toLowerCase().includes('crm')
                    );
                    if (crm) {
                        formData.crm = crm.value || '';
                        (formData as any).numero_conselho = crm.value || '';
                        (formData as any).conselho = 'CRM';
                        // Try to extract UF from system
                        if (crm.system) {
                            const match = crm.system.match(/crm[/-]([A-Z]{2})/i);
                            if (match) {
                                (formData as any).uf_conselho = match[1].toUpperCase();
                            }
                        }
                    }
                }

                // Qualification
                if (data.qualification && data.qualification[0]) {
                    const qual = data.qualification[0];
                    formData.qualification_code = qual.code?.coding?.[0]?.code || 'MD';
                    formData.qualification_display = qual.code?.text || 
                        qual.code?.coding?.[0]?.display || '';
                    
                    // CBO code
                    const cboCode = qual.code?.coding?.find((c: any) => 
                        c.system?.includes('cbo') || c.system?.includes('CBO')
                    );
                    if (cboCode) {
                        (formData as any).codigo_cbo = cboCode.code || '';
                    }
                }

                setInitialData(formData);
            } catch (err) {
                console.error('Error fetching practitioner:', err);
                setError('Não foi possível carregar os dados do profissional.');
            } finally {
                setLoading(false);
            }
        };

        fetchPractitioner();
    }, [id, getPractitioner]);

    const handleSubmit = async (data: PractitionerFormData) => {
        if (!id) return;

        try {
            await updatePractitioner(id, data);
            alert('Profissional atualizado com sucesso!');
            navigate(`/practitioners/${id}`);
        } catch (err) {
            console.error('Error updating practitioner:', err);
            alert('Erro ao atualizar profissional. Tente novamente.');
            throw err;
        }
    };

    const handleCancel = () => {
        navigate(`/practitioners/${id}`);
    };

    if (loading) {
        return (
            <>
                <style>{spinnerStyles}</style>
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100vh',
                    backgroundColor: colors.background.default,
                    gap: spacing.md
                }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        border: `4px solid ${colors.primary.medium}`,
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <p style={{ 
                        color: colors.text.secondary,
                        fontSize: '1rem'
                    }}>Carregando dados do profissional...</p>
                </div>
            </>
        );
    }

    if (error || !practitioner) {
        return (
            <div style={{
                padding: spacing.xl,
                backgroundColor: colors.background.default,
                minHeight: '100vh'
            }}>
                <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                    <Card padding="lg">
                        <div style={{
                            textAlign: 'center',
                            padding: spacing.lg
                        }}>
                            <div style={{
                                width: '64px',
                                height: '64px',
                                margin: '0 auto',
                                marginBottom: spacing.lg,
                                borderRadius: '50%',
                                backgroundColor: colors.alert.critical + '20',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}>
                                <span style={{
                                    fontSize: '2rem',
                                    color: colors.alert.critical
                                }}>⚠️</span>
                            </div>
                            
                            <h2 style={{
                                margin: 0,
                                marginBottom: spacing.sm,
                                fontSize: '1.5rem',
                                color: colors.text.primary
                            }}>
                                Erro ao Carregar
                            </h2>
                            
                            <p style={{ 
                                color: colors.text.secondary,
                                marginBottom: spacing.lg,
                                fontSize: '1rem'
                            }}>
                                {error || 'Profissional não encontrado.'}
                            </p>
                            
                            <Button 
                                onClick={() => navigate('/practitioners')} 
                                leftIcon={<ArrowLeft size={20} />}
                            >
                                Voltar para lista
                            </Button>
                        </div>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div style={{
            padding: spacing.xl,
            backgroundColor: colors.background.default,
            minHeight: '100vh'
        }}>
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                {/* Header with back button */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: spacing.lg,
                    gap: spacing.md
                }}>
                    <Button
                        variant="ghost"
                        onClick={handleCancel}
                        leftIcon={<ArrowLeft size={20} />}
                        aria-label="Voltar"
                    >
                        Voltar
                    </Button>
                    
                    <div>
                        <h1 style={{
                            margin: 0,
                            fontSize: '2rem',
                            fontWeight: 600,
                            color: colors.text.primary
                        }}>
                            Editar Profissional
                        </h1>
                        {practitioner && practitioner.name && practitioner.name[0] && (
                            <p style={{
                                margin: 0,
                                marginTop: spacing.xs,
                                fontSize: '1rem',
                                color: colors.text.secondary
                            }}>
                                {practitioner.name[0].given?.join(' ')} {practitioner.name[0].family}
                            </p>
                        )}
                    </div>
                </div>

                {/* Form card */}
                <Card padding="lg">
                    <PractitionerForm
                        onSubmit={handleSubmit}
                        onCancel={handleCancel}
                        initialData={initialData}
                    />
                </Card>
            </div>
        </div>
    );
};

export default PractitionerEdit;

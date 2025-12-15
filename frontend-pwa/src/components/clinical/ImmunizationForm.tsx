import React, { useState } from 'react';
import { useEncounters } from '../../hooks/useEncounters';
import { Syringe, Calendar, Building2, User } from 'lucide-react';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Button from '../base/Button';
import { colors, spacing } from '../../theme/colors';

interface ImmunizationFormProps {
    patientId?: string;
    encounterId: string | null;
}

interface ImmunizationData {
    vaccineCode: string;
    vaccineName: string;
    occurrenceDateTime: string;
    lotNumber: string;
    manufacturer: string;
    site: string;
    route: string;
    doseQuantity: string;
    performer: string;
    notes: string;
}

const VACCINES = [
    { code: '207', name: 'COVID-19, mRNA, LNP-S' },
    { code: '208', name: 'COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL' },
    { code: '03', name: 'MMR (Sarampo, Caxumba, Rubéola)' },
    { code: '21', name: 'Varicela' },
    { code: '08', name: 'Hepatite B' },
    { code: '20', name: 'DTaP (Difteria, Tétano, Coqueluche)' },
    { code: '49', name: 'Hib (Haemophilus influenzae tipo b)' },
    { code: '10', name: 'Poliomielite (IPV)' },
    { code: '89', name: 'Poliomielite (OPV)' },
    { code: '88', name: 'Influenza (Gripe)' },
    { code: '33', name: 'Pneumocócica' },
    { code: '116', name: 'Rotavírus' },
    { code: '62', name: 'HPV' },
    { code: '141', name: 'Influenza H1N1' },
    { code: '114', name: 'Meningocócica (MenACWY)' },
    { code: '136', name: 'Meningocócica B' },
    { code: '133', name: 'Pneumocócica 13-valente' },
    { code: '43', name: 'Hepatite A' },
    { code: '52', name: 'Hepatite A + B' }
];

const ADMINISTRATION_SITES = [
    { value: 'LA', label: 'Braço Esquerdo' },
    { value: 'RA', label: 'Braço Direito' },
    { value: 'LT', label: 'Coxa Esquerda' },
    { value: 'RT', label: 'Coxa Direita' }
];

const ROUTES = [
    { value: 'IM', label: 'Intramuscular' },
    { value: 'SC', label: 'Subcutânea' },
    { value: 'ID', label: 'Intradérmica' },
    { value: 'PO', label: 'Oral' },
    { value: 'NASINHL', label: 'Inalação Nasal' }
];

const ImmunizationForm: React.FC<ImmunizationFormProps> = ({ encounterId, patientId }) => {
    const { createImmunization, loading: hookLoading } = useEncounters(patientId);
    const isMobile = useIsMobile();

    const [formData, setFormData] = useState<ImmunizationData>({
        vaccineCode: '',
        vaccineName: '',
        occurrenceDateTime: new Date().toISOString().split('T')[0],
        lotNumber: '',
        manufacturer: '',
        site: 'LA',
        route: 'IM',
        doseQuantity: '0.5',
        performer: '',
        notes: ''
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleVaccineChange = (code: string) => {
        const vaccine = VACCINES.find(v => v.code === code);
        setFormData({
            ...formData,
            vaccineCode: code,
            vaccineName: vaccine?.name || ''
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccessMessage(null);

        if (!patientId) {
            setError('ID do paciente não encontrado');
            setLoading(false);
            return;
        }

        if (!formData.vaccineCode || !formData.vaccineName) {
            setError('Selecione uma vacina');
            setLoading(false);
            return;
        }

        try {
            const token = localStorage.getItem('access_token');

            const payload = {
                resourceType: 'Immunization',
                status: 'completed',
                vaccineCode: {
                    coding: [{
                        system: 'http://hl7.org/fhir/sid/cvx',
                        code: formData.vaccineCode,
                        display: formData.vaccineName
                    }],
                    text: formData.vaccineName
                },
                patient: {
                    reference: `Patient/${patientId}`
                },
                encounter: encounterId ? {
                    reference: `Encounter/${encounterId}`
                } : undefined,
                occurrenceDateTime: formData.occurrenceDateTime,
                lotNumber: formData.lotNumber || undefined,
                manufacturer: formData.manufacturer ? {
                    display: formData.manufacturer
                } : undefined,
                site: {
                    coding: [{
                        system: 'http://terminology.hl7.org/CodeSystem/v3-ActSite',
                        code: formData.site,
                        display: ADMINISTRATION_SITES.find(s => s.value === formData.site)?.label
                    }]
                },
                route: {
                    coding: [{
                        system: 'http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration',
                        code: formData.route,
                        display: ROUTES.find(r => r.value === formData.route)?.label
                    }]
                },
                doseQuantity: {
                    value: parseFloat(formData.doseQuantity),
                    unit: 'mL',
                    system: 'http://unitsofmeasure.org',
                    code: 'mL'
                },
                performer: formData.performer ? [{
                    actor: {
                        display: formData.performer
                    }
                }] : undefined,
                note: formData.notes ? [{
                    text: formData.notes
                }] : undefined
            };

            await createImmunization({
                vaccine_code: formData.vaccineCode,
                vaccine_name: formData.vaccineName,
                occurrence_date_time: formData.occurrenceDateTime,
                lot_number: formData.lotNumber,
                manufacturer: formData.manufacturer,
                site: formData.site,
                route: formData.route,
                dose_quantity: formData.doseQuantity,
                performer: formData.performer,
                notes: formData.notes,
                encounter_id: encounterId,
                status: 'completed'
            });

            setSuccessMessage('Vacina registrada com sucesso!');
            
            // Reset form
            setFormData({
                vaccineCode: '',
                vaccineName: '',
                occurrenceDateTime: new Date().toISOString().split('T')[0],
                lotNumber: '',
                manufacturer: '',
                site: 'LA',
                route: 'IM',
                doseQuantity: '0.5',
                performer: '',
                notes: ''
            });

            setTimeout(() => setSuccessMessage(null), 3000);

        } catch (err: any) {
            console.error('Erro ao salvar vacina:', err);
            setError(err.response?.data?.message || 'Erro ao salvar vacina. Tente novamente.');
        } finally {
            setLoading(false);
        }
    };

    const inputStyle = {
        width: '100%',
        padding: spacing.sm,
        border: `1px solid ${colors.border.default}`,
        borderRadius: '8px',
        fontSize: isMobile ? '16px' : '0.95rem',
        boxSizing: 'border-box' as const
    };

    const labelStyle = {
        display: 'block',
        marginBottom: spacing.xs,
        fontWeight: 600,
        fontSize: isMobile ? '0.9rem' : '0.875rem',
        color: colors.text.primary
    };

    return (
        <div style={{ 
            maxWidth: '100%',
            padding: isMobile ? spacing.sm : 0
        }}>
            <h3 style={{ 
                margin: 0, 
                marginBottom: spacing.lg, 
                color: colors.text.primary, 
                display: 'flex', 
                alignItems: 'center', 
                gap: spacing.sm,
                fontSize: isMobile ? '1.1rem' : '1.25rem'
            }}>
                <Syringe size={isMobile ? 20 : 24} />
                Registro de Vacinação
            </h3>

            {error && (
                <div style={{
                    padding: spacing.md,
                    backgroundColor: `${colors.alert.critical}15`,
                    border: `1px solid ${colors.alert.critical}`,
                    borderRadius: '8px',
                    color: colors.alert.critical,
                    marginBottom: spacing.md,
                    fontSize: isMobile ? '0.875rem' : '0.9rem'
                }}>
                    {error}
                </div>
            )}

            {successMessage && (
                <div style={{
                    padding: spacing.md,
                    backgroundColor: `${colors.alert.success}20`,
                    border: `1px solid ${colors.alert.success}`,
                    borderRadius: '8px',
                    color: colors.alert.success,
                    marginBottom: spacing.md,
                    fontSize: isMobile ? '0.875rem' : '0.9rem'
                }}>
                    ✓ {successMessage}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', 
                    gap: spacing.md, 
                    marginBottom: spacing.md 
                }}>
                    <div>
                        <label style={labelStyle}>
                            Vacina *
                        </label>
                        <select
                            value={formData.vaccineCode}
                            onChange={(e) => handleVaccineChange(e.target.value)}
                            required
                            style={inputStyle}
                        >
                            <option value="">Selecione uma vacina...</option>
                            {VACCINES.map(vaccine => (
                                <option key={vaccine.code} value={vaccine.code}>
                                    {vaccine.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label style={labelStyle}>
                            <Calendar size={14} style={{ display: 'inline', marginRight: '4px' }} />
                            Data de Aplicação *
                        </label>
                        <input
                            type="date"
                            value={formData.occurrenceDateTime}
                            onChange={(e) => setFormData({ ...formData, occurrenceDateTime: e.target.value })}
                            required
                            style={inputStyle}
                        />
                    </div>
                </div>

                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', 
                    gap: spacing.md, 
                    marginBottom: spacing.md 
                }}>
                    <div>
                        <label style={labelStyle}>
                            Número do Lote
                        </label>
                        <input
                            type="text"
                            value={formData.lotNumber}
                            onChange={(e) => setFormData({ ...formData, lotNumber: e.target.value })}
                            placeholder="Ex: L123456"
                            style={inputStyle}
                        />
                    </div>

                    <div>
                        <label style={labelStyle}>
                            <Building2 size={14} style={{ display: 'inline', marginRight: '4px' }} />
                            Fabricante
                        </label>
                        <input
                            type="text"
                            value={formData.manufacturer}
                            onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                            placeholder="Ex: Pfizer, AstraZeneca"
                            style={inputStyle}
                        />
                    </div>
                </div>

                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', 
                    gap: spacing.md, 
                    marginBottom: spacing.md 
                }}>
                    <div>
                        <label style={labelStyle}>
                            Local de Aplicação *
                        </label>
                        <select
                            value={formData.site}
                            onChange={(e) => setFormData({ ...formData, site: e.target.value })}
                            required
                            style={inputStyle}
                        >
                            {ADMINISTRATION_SITES.map(site => (
                                <option key={site.value} value={site.value}>
                                    {site.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label style={labelStyle}>
                            Via de Administração *
                        </label>
                        <select
                            value={formData.route}
                            onChange={(e) => setFormData({ ...formData, route: e.target.value })}
                            required
                            style={inputStyle}
                        >
                            {ROUTES.map(route => (
                                <option key={route.value} value={route.value}>
                                    {route.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label style={labelStyle}>
                            Dose (mL) *
                        </label>
                        <input
                            type="number"
                            step="0.1"
                            value={formData.doseQuantity}
                            onChange={(e) => setFormData({ ...formData, doseQuantity: e.target.value })}
                            required
                            style={inputStyle}
                        />
                    </div>
                </div>

                <div style={{ marginBottom: spacing.md }}>
                    <label style={labelStyle}>
                        <User size={14} style={{ display: 'inline', marginRight: '4px' }} />
                        Profissional Aplicador
                    </label>
                    <input
                        type="text"
                        value={formData.performer}
                        onChange={(e) => setFormData({ ...formData, performer: e.target.value })}
                        placeholder="Nome do profissional"
                        style={inputStyle}
                    />
                </div>

                <div style={{ marginBottom: spacing.lg }}>
                    <label style={labelStyle}>
                        Observações
                    </label>
                    <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        placeholder="Reações adversas, observações gerais..."
                        rows={3}
                        style={{
                            ...inputStyle,
                            fontFamily: 'inherit',
                            resize: 'vertical' as const,
                            minHeight: isMobile ? '80px' : '100px'
                        }}
                    />
                </div>

                <div style={{ 
                    display: 'flex', 
                    justifyContent: isMobile ? 'stretch' : 'flex-end', 
                    gap: spacing.sm 
                }}>
                    <Button 
                        type="submit" 
                        variant="primary" 
                        disabled={loading}
                        style={{ 
                            width: isMobile ? '100%' : 'auto',
                            padding: spacing.md,
                            fontSize: isMobile ? '1rem' : '0.95rem'
                        }}
                    >
                        {loading ? 'Salvando...' : 'Salvar Vacinação'}
                    </Button>
                </div>
            </form>
        </div>
    );
};

export default ImmunizationForm;

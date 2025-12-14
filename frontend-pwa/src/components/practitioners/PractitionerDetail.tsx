/**
 * Practitioner Detail Page
 * 
 * Shows full profile of a practitioner with option to start chat
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Card from '../base/Card';
import Button from '../base/Button';
import { ArrowLeft, MessageCircle, Phone, Mail, Edit, Calendar } from 'lucide-react';
import { usePractitioners } from '../../hooks/usePractitioners';
import './PractitionerDetail.css';

interface Practitioner {
    id: string;
    name?: {
        prefix?: string[];
        given?: string[];
        family?: string;
    }[];
    identifier?: {
        system?: string;
        value?: string;
    }[];
    qualification?: {
        code?: {
            text?: string;
            coding?: { display?: string }[];
        };
    }[];
    telecom?: {
        system?: string;
        value?: string;
    }[];
    active?: boolean;
    gender?: string;
    birthDate?: string;
    address?: {
        line?: string[];
        city?: string;
        state?: string;
        postalCode?: string;
    }[];
}

const PractitionerDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { getPractitioner } = usePractitioners();
    const [practitioner, setPractitioner] = useState<Practitioner | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchPractitioner = async () => {
            if (!id) return;

            try {
                setLoading(true);
                const data = await getPractitioner(id);
                setPractitioner(data as Practitioner);
            } catch (err) {
                console.error('Error fetching practitioner:', err);
                setError('Não foi possível carregar os dados do profissional.');
            } finally {
                setLoading(false);
            }
        };

        fetchPractitioner();
    }, [id, getPractitioner]);

    const handleStartChat = () => {
        if (!practitioner) return;

        // Navigate directly to the DM channel for this practitioner
        // The channel ID format is 'dm-{practitionerId}'
        navigate(`/chat?channel=dm-${practitioner.id}`);
    };

    const handleScheduleAppointment = () => {
        // Navigate to scheduling with practitioner pre-selected
        navigate(`/scheduling?practitioner=${id}`);
    };

    const handleEdit = () => {
        navigate(`/practitioners/${id}/edit`);
    };

    // Helper functions
    const getFullName = () => {
        if (!practitioner?.name?.[0]) return 'Profissional';
        const n = practitioner.name[0];
        const prefix = n.prefix?.[0] || '';
        const given = n.given?.join(' ') || '';
        const family = n.family || '';
        return `${prefix} ${given} ${family}`.trim();
    };

    const getCRM = () => {
        return practitioner?.identifier?.find(i =>
            i.system?.includes('crm')
        )?.value || null;
    };

    const getSpecialty = () => {
        const qual = practitioner?.qualification?.[0];
        return qual?.code?.text || qual?.code?.coding?.[0]?.display || 'Não especificado';
    };

    const getPhone = () => {
        return practitioner?.telecom?.find(t => t.system === 'phone')?.value || null;
    };

    const getEmail = () => {
        return practitioner?.telecom?.find(t => t.system === 'email')?.value || null;
    };

    if (loading) {
        return (
            <div className="practitioner-detail">
                <div className="practitioner-detail__loading">
                    <p>Carregando perfil...</p>
                </div>
            </div>
        );
    }

    if (error || !practitioner) {
        return (
            <div className="practitioner-detail">
                <Card className="practitioner-detail__error">
                    <p>{error || 'Profissional não encontrado.'}</p>
                    <Button onClick={() => navigate('/profissionais')}>
                        <ArrowLeft size={18} /> Voltar
                    </Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="practitioner-detail">
            {/* Header with back button */}
            <div className="practitioner-detail__header">
                <Button
                    variant="ghost"
                    onClick={() => navigate('/profissionais')}
                    className="back-button"
                >
                    <ArrowLeft size={20} />
                    Voltar para lista
                </Button>
            </div>

            {/* Main Profile Card */}
            <Card className="practitioner-detail__profile">
                <div className="profile-header">
                    {/* Avatar */}
                    <div className="profile-avatar">
                        <span className="avatar-initials">
                            {(practitioner.name?.[0]?.given?.[0]?.[0] || 'P').toUpperCase()}
                            {(practitioner.name?.[0]?.family?.[0] || '').toUpperCase()}
                        </span>
                    </div>

                    {/* Basic Info */}
                    <div className="profile-info">
                        <h1 className="profile-name">{getFullName()}</h1>
                        <p className="profile-specialty">{getSpecialty()}</p>
                        {getCRM() && (
                            <span className="profile-crm">{getCRM()}</span>
                        )}
                        <span className={`profile-status ${practitioner.active !== false ? 'active' : 'inactive'}`}>
                            {practitioner.active !== false ? '● Ativo' : '○ Inativo'}
                        </span>
                    </div>

                    {/* Action Buttons */}
                    <div className="profile-actions">
                        <Button
                            onClick={handleStartChat}
                            className="action-button action-button--primary"
                            leftIcon={<MessageCircle size={20} />}
                        >
                            Iniciar Chat
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={handleScheduleAppointment}
                            className="action-button"
                            leftIcon={<Calendar size={20} />}
                        >
                            Agendar Consulta
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={handleEdit}
                            className="action-button"
                            leftIcon={<Edit size={20} />}
                        >
                            Editar
                        </Button>
                    </div>
                </div>
            </Card>

            {/* Contact Information */}
            <div className="practitioner-detail__grid">
                <Card className="info-card">
                    <h2 className="info-card__title">Contato</h2>
                    <div className="info-card__content">
                        {getPhone() && (
                            <div className="info-item">
                                <Phone size={16} className="info-icon" />
                                <span>{getPhone()}</span>
                            </div>
                        )}
                        {getEmail() && (
                            <div className="info-item">
                                <Mail size={16} className="info-icon" />
                                <span>{getEmail()}</span>
                            </div>
                        )}
                        {!getPhone() && !getEmail() && (
                            <p className="info-empty">Nenhum contato cadastrado</p>
                        )}
                    </div>
                </Card>

                <Card className="info-card">
                    <h2 className="info-card__title">Informações Pessoais</h2>
                    <div className="info-card__content">
                        {practitioner.gender && (
                            <div className="info-row">
                                <span className="info-label">Gênero:</span>
                                <span className="info-value">
                                    {practitioner.gender === 'male' ? 'Masculino' :
                                        practitioner.gender === 'female' ? 'Feminino' :
                                            practitioner.gender}
                                </span>
                            </div>
                        )}
                        {practitioner.birthDate && (
                            <div className="info-row">
                                <span className="info-label">Data de Nascimento:</span>
                                <span className="info-value">
                                    {new Date(practitioner.birthDate).toLocaleDateString('pt-BR')}
                                </span>
                            </div>
                        )}
                        {practitioner.address?.[0] && (
                            <div className="info-row">
                                <span className="info-label">Endereço:</span>
                                <span className="info-value">
                                    {practitioner.address[0].line?.join(', ')},
                                    {practitioner.address[0].city} - {practitioner.address[0].state}
                                </span>
                            </div>
                        )}
                    </div>
                </Card>

                <Card className="info-card">
                    <h2 className="info-card__title">Qualificações</h2>
                    <div className="info-card__content">
                        {practitioner.qualification?.map((qual, idx) => (
                            <div key={idx} className="qualification-item">
                                <span className="qualification-badge">
                                    {qual.code?.text || qual.code?.coding?.[0]?.display || 'Qualificação'}
                                </span>
                            </div>
                        ))}
                        {(!practitioner.qualification || practitioner.qualification.length === 0) && (
                            <p className="info-empty">Nenhuma qualificação cadastrada</p>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default PractitionerDetail;

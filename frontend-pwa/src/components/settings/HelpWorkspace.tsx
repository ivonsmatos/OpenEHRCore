import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    HelpCircle,
    Book,
    FileText,
    MessageCircle,
    Mail,
    ExternalLink,
    ArrowLeft,
    Search
} from 'lucide-react';
import Card from '../base/Card';
import Button from '../base/Button';
import './HelpWorkspace.css';

/**
 * Workspace de Ajuda e Suporte
 * FAQ, documentação e contato
 */
export const HelpWorkspace: React.FC = () => {
    const navigate = useNavigate();

    const faqItems = [
        {
            category: 'Geral',
            questions: [
                {
                    q: 'Como cadastro um novo paciente?',
                    a: 'Vá para Pacientes > Novo Paciente e preencha os dados obrigatórios (Nome, CPF, Data de Nascimento e Gênero).'
                },
                {
                    q: 'Como agendar uma consulta?',
                    a: 'Acesse Agendamentos > Nova Consulta, selecione o profissional, paciente, data e horário desejados.'
                },
                {
                    q: 'Como alterar minha senha?',
                    a: 'Clique no seu avatar > Segurança & Privacidade > Alterar Senha.'
                }
            ]
        },
        {
            category: 'FHIR',
            questions: [
                {
                    q: 'O que é FHIR?',
                    a: 'FHIR (Fast Healthcare Interoperability Resources) é um padrão internacional para troca de dados de saúde eletrônicos, desenvolvido pela HL7.'
                },
                {
                    q: 'Quais recursos FHIR são suportados?',
                    a: 'Suportamos Patient, Practitioner, Organization, Encounter, Observation, Condition, AllergyIntolerance, MedicationRequest, Appointment, entre outros.'
                },
                {
                    q: 'Como exportar dados FHIR?',
                    a: 'Na página de detalhes de um paciente, clique em "Exportar" para baixar os dados em formato FHIR JSON.'
                }
            ]
        },
        {
            category: 'Financeiro',
            questions: [
                {
                    q: 'Como visualizar o faturamento?',
                    a: 'Acesse o módulo Financeiro no menu lateral para ver KPIs, gráficos e relatórios detalhados.'
                },
                {
                    q: 'Como gerenciar convênios?',
                    a: 'Vá para Organizações e cadastre os convênios como recursos FHIR Organization.'
                }
            ]
        }
    ];

    const documentationLinks = [
        {
            title: 'Documentação FHIR R4',
            description: 'Especificação oficial do FHIR R4',
            url: 'https://hl7.org/fhir/R4/',
            icon: <Book size={18} />
        },
        {
            title: 'Guia do Usuário OpenEHRCore',
            description: 'Manual completo do sistema',
            url: '#',
            icon: <FileText size={18} />
        },
        {
            title: 'API Documentation',
            description: 'Referência da API REST',
            url: '#',
            icon: <FileText size={18} />
        }
    ];

    const supportChannels = [
        {
            title: 'Email',
            description: 'suporte@openehrcore.com',
            icon: <Mail size={20} />,
            action: () => window.location.href = 'mailto:suporte@openehrcore.com'
        },
        {
            title: 'Chat',
            description: 'Suporte em tempo real',
            icon: <MessageCircle size={20} />,
            action: () => alert('Chat em breve!')
        }
    ];

    return (
        <div className="help-workspace">
            <div className="help-header">
                <button className="back-button" onClick={() => navigate(-1)}>
                    <ArrowLeft size={20} />
                    Voltar
                </button>
                <div className="header-content">
                    <h1>
                        <HelpCircle size={28} />
                        Ajuda & Suporte
                    </h1>
                    <p>Documentação, FAQ e canais de suporte</p>
                </div>
            </div>

            <div className="help-content">
                {/* Search */}
                <Card className="search-card">
                    <div className="search-box">
                        <Search size={20} />
                        <input
                            type="text"
                            placeholder="Buscar na documentação..."
                        />
                    </div>
                </Card>

                {/* FAQ */}
                <section className="faq-section">
                    <h2>Perguntas Frequentes</h2>
                    {faqItems.map((category, idx) => (
                        <div key={idx} className="faq-category">
                            <h3>{category.category}</h3>
                            {category.questions.map((item, qIdx) => (
                                <Card key={qIdx} className="faq-item">
                                    <details>
                                        <summary>{item.q}</summary>
                                        <p>{item.a}</p>
                                    </details>
                                </Card>
                            ))}
                        </div>
                    ))}
                </section>

                {/* Documentation */}
                <section className="docs-section">
                    <h2>Documentação</h2>
                    <div className="docs-grid">
                        {documentationLinks.map((doc, idx) => (
                            <Card key={idx} className="doc-card">
                                <div className="doc-icon">{doc.icon}</div>
                                <h3>{doc.title}</h3>
                                <p>{doc.description}</p>
                                <a
                                    href={doc.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="doc-link"
                                >
                                    Acessar <ExternalLink size={14} />
                                </a>
                            </Card>
                        ))}
                    </div>
                </section>

                {/* Support */}
                <section className="support-section">
                    <h2>Canais de Suporte</h2>
                    <div className="support-grid">
                        {supportChannels.map((channel, idx) => (
                            <Card key={idx} className="support-card">
                                <div className="support-icon">{channel.icon}</div>
                                <h3>{channel.title}</h3>
                                <p>{channel.description}</p>
                                <Button variant="secondary" onClick={channel.action}>
                                    Contatar
                                </Button>
                            </Card>
                        ))}
                    </div>
                </section>

                {/* Footer */}
                <Card className="version-info">
                    <div className="version-details">
                        <p><strong>OpenEHRCore</strong> v1.0</p>
                        <p>FHIR R4 • RNDS compliant</p>
                        <p>© 2025 OpenEHRCore. Todos os direitos reservados.</p>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default HelpWorkspace;

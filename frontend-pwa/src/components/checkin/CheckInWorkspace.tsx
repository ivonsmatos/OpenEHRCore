import React, { useState } from 'react';
import Header from '../base/Header';
import Button from '../base/Button';
import { useCheckIn, QuestionnaireItem } from '../../hooks/useCheckIn';
import { colors, spacing } from '../../theme/colors';

const CheckInWorkspace: React.FC = () => {
    const { createQuestionnaire, submitResponse, loading } = useCheckIn();
    const [activeQuestionnaireId, setActiveQuestionnaireId] = useState<string | null>(null);
    const [answers, setAnswers] = useState<{ [key: string]: string }>({});

    // Mock de questionário de triagem
    const triageItems: QuestionnaireItem[] = [
        { linkId: "1", text: "Você teve febre nas últimas 24 horas?", type: "string" },
        { linkId: "2", text: "Está sentindo falta de ar?", type: "string" },
        { linkId: "3", text: "Teve contato com alguém doente recentemente?", type: "string" }
    ];

    const handleCreateTriage = async () => {
        try {
            const result = await createQuestionnaire("Triagem Inicial COVID-19", triageItems);
            setActiveQuestionnaireId(result.id);
            alert(`Questionário criado! ID: ${result.id}`);
        } catch (error) {
            console.error(error);
            alert('Erro ao criar questionário');
        }
    };

    const handleSubmit = async () => {
        if (!activeQuestionnaireId) return;

        const formattedAnswers = Object.keys(answers).map(key => ({
            linkId: key,
            text: triageItems.find(i => i.linkId === key)?.text || "",
            valueString: answers[key]
        }));

        try {
            // Usando ID fixo de paciente para demo
            await submitResponse(activeQuestionnaireId, "patient-1", formattedAnswers);
            alert('Check-in realizado com sucesso!');
            setAnswers({});
            setActiveQuestionnaireId(null);
        } catch (error) {
            console.error(error);
            alert('Erro ao enviar check-in');
        }
    };

    return (
        <div style={{ backgroundColor: colors.background.surface, minHeight: '100vh' }}>
            <Header
                title="Check-in Digital"
                subtitle="Triagem e formulários pré-consulta"
            >
                <Button onClick={handleCreateTriage} isLoading={loading} disabled={!!activeQuestionnaireId}>
                    📝 Iniciar Nova Triagem
                </Button>
            </Header>

            <main style={{ maxWidth: '800px', margin: '0 auto', padding: spacing.lg }}>
                {activeQuestionnaireId ? (
                    <div style={{
                        backgroundColor: 'white',
                        padding: spacing.lg,
                        borderRadius: '8px',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }}>
                        <h2 style={{ marginBottom: spacing.md }}>Triagem Inicial</h2>
                        {triageItems.map(item => (
                            <div key={item.linkId} style={{ marginBottom: spacing.md }}>
                                <label style={{ display: 'block', marginBottom: spacing.xs, fontWeight: 500 }}>
                                    {item.text}
                                </label>
                                <input
                                    type="text"
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        borderRadius: '4px',
                                        border: `1px solid ${colors.neutral.lighter}`
                                    }}
                                    placeholder="Sua resposta..."
                                    value={answers[item.linkId] || ''}
                                    onChange={(e) => setAnswers({ ...answers, [item.linkId]: e.target.value })}
                                />
                            </div>
                        ))}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: spacing.lg }}>
                            <Button onClick={handleSubmit} isLoading={loading}>
                                ✅ Enviar Respostas
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', color: colors.text.secondary, marginTop: spacing.xl }}>
                        <p>Nenhuma triagem ativa. Clique em "Iniciar Nova Triagem" para começar.</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default CheckInWorkspace;

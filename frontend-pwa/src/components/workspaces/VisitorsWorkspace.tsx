import React, { useState, useEffect } from 'react';
import { colors, spacing } from '../../theme/colors';
import { useAuth } from '../../hooks/useAuth';
import { useIsMobile } from '../../hooks/useMediaQuery';
import Card from '../base/Card';
import { UserPlus, X, LogIn, LogOut } from 'lucide-react';

interface Visitor {
    id: string;
    name: string;
    relationship: string;
    contact: string;
    patient_id: string;
}

const VisitorsWorkspace: React.FC = () => {
    const { token } = useAuth();
    const isMobile = useIsMobile();
    const [visitors, setVisitors] = useState<Visitor[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Form State
    const [newName, setNewName] = useState('');
    const [newPhone, setNewPhone] = useState('');
    const [newRelation, setNewRelation] = useState('Visitante');
    const [targetPatientId, setTargetPatientId] = useState('');

    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

    useEffect(() => {
        fetchVisitors();
    }, [token]);

    const fetchVisitors = async () => {
        try {
            const res = await fetch(`${API_BASE}/visitors/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setVisitors(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateVisitor = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_BASE}/visitors/create/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: newName,
                    phone: newPhone,
                    relationship: newRelation,
                    patient_id: targetPatientId
                })
            });

            if (res.ok) {
                alert('Visitante registrado com sucesso!');
                setShowModal(false);
                fetchVisitors();
                // Reset form
                setNewName('');
                setNewPhone('');
            } else {
                alert('Erro ao registrar visitante.');
            }
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div style={{ padding: isMobile ? spacing.md : spacing.xl }}>
            <div style={{ 
                display: 'flex', 
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between', 
                alignItems: isMobile ? 'stretch' : 'center',
                marginBottom: spacing.lg,
                gap: spacing.md
            }}>
                <h1 style={{ fontSize: isMobile ? '1.25rem' : '1.5rem', fontWeight: 700, color: colors.text.primary }}>Módulo de Visitantes</h1>
                <button
                    onClick={() => setShowModal(true)}
                    style={{
                        display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'center',
                        backgroundColor: colors.primary.medium, color: '#fff',
                        padding: '10px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                        width: isMobile ? '100%' : 'auto'
                    }}
                >
                    <UserPlus size={18} />
                    Registrar Visitante
                </button>
            </div>

            {loading ? <p>Carregando...</p> : (
                isMobile ? (
                    // Mobile: Card Layout
                    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
                        {visitors.length === 0 ? (
                            <Card>
                                <p style={{ padding: spacing.lg, textAlign: 'center', color: colors.text.secondary }}>Nenhum visitante registrado.</p>
                            </Card>
                        ) : visitors.map(v => (
                            <Card key={v.id} style={{ padding: spacing.md }}>
                                <div style={{ marginBottom: spacing.sm }}>
                                    <div style={{ fontWeight: 600, fontSize: '1rem', color: colors.text.primary, marginBottom: '4px' }}>{v.name}</div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.xs, marginBottom: '4px' }}>
                                        <span style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Relação:</span>
                                        <span style={{ backgroundColor: '#EFF6FF', color: colors.primary.dark, padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 500 }}>
                                            {v.relationship}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '4px' }}>
                                        <strong>Contato:</strong> {v.contact}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: colors.text.secondary }}>
                                        <strong>Paciente ID:</strong> {v.patient_id.substring(0, 8)}...
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: spacing.sm, marginTop: spacing.sm, paddingTop: spacing.sm, borderTop: `1px solid ${colors.border.default}` }}>
                                    <button 
                                        title="Registrar Entrada" 
                                        style={{ 
                                            flex: 1, padding: '8px', cursor: 'pointer', border: `1px solid #22c55e`, background: 'white', color: '#22c55e', borderRadius: '6px',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontSize: '0.875rem', fontWeight: 500
                                        }}
                                    >
                                        <LogIn size={16} /> Entrada
                                    </button>
                                    <button 
                                        title="Registrar Saída" 
                                        style={{ 
                                            flex: 1, padding: '8px', cursor: 'pointer', border: `1px solid #ef4444`, background: 'white', color: '#ef4444', borderRadius: '6px',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontSize: '0.875rem', fontWeight: 500
                                        }}
                                    >
                                        <LogOut size={16} /> Saída
                                    </button>
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    // Desktop: Table Layout
                    <Card>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid ' + colors.border }}>
                                <th style={{ textAlign: 'left', padding: spacing.md }}>Nome</th>
                                <th style={{ textAlign: 'left', padding: spacing.md }}>Relação</th>
                                <th style={{ textAlign: 'left', padding: spacing.md }}>Contato</th>
                                <th style={{ textAlign: 'left', padding: spacing.md }}>Paciente (Ref)</th>
                                <th style={{ textAlign: 'left', padding: spacing.md }}>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {visitors.length === 0 ? (
                                <tr><td colSpan={5} style={{ padding: spacing.lg, textAlign: 'center' }}>Nenhum visitante registrado.</td></tr>
                            ) : visitors.map(v => (
                                <tr key={v.id} style={{ borderBottom: '1px solid ' + colors.border }}>
                                    <td style={{ padding: spacing.md }}>{v.name}</td>
                                    <td style={{ padding: spacing.md }}>
                                        <span style={{ backgroundColor: '#EFF6FF', color: colors.primary.dark, padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem' }}>
                                            {v.relationship}
                                        </span>
                                    </td>
                                    <td style={{ padding: spacing.md }}>{v.contact}</td>
                                    <td style={{ padding: spacing.md }}>{v.patient_id}</td>
                                    <td style={{ padding: spacing.md, display: 'flex', gap: '8px' }}>
                                        <button title="Registrar Entrada" style={{ cursor: 'pointer', border: 'none', background: 'none', color: 'green' }}><LogIn size={18} /></button>
                                        <button title="Registrar Saída" style={{ cursor: 'pointer', border: 'none', background: 'none', color: 'red' }}><LogOut size={18} /></button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </Card>
                )
            )}

            {/* Modal de Criação Simples */}
            {showModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000,
                    padding: isMobile ? spacing.md : 0
                }}>
                    <div style={{ 
                        backgroundColor: '#fff', 
                        padding: isMobile ? spacing.md : spacing.xl, 
                        borderRadius: '8px', 
                        width: isMobile ? '100%' : '400px',
                        maxWidth: '100%',
                        maxHeight: isMobile ? '90vh' : 'auto',
                        overflowY: 'auto'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: spacing.md }}>
                            <h3 style={{ margin: 0 }}>Novo Visitante</h3>
                            <button onClick={() => setShowModal(false)} style={{ border: 'none', background: 'none', cursor: 'pointer' }}><X /></button>
                        </div>
                        <form onSubmit={handleCreateVisitor} style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.9rem' }}>Nome Completo</label>
                                <input required value={newName} onChange={e => setNewName(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontSize: isMobile ? '16px' : '0.9rem', boxSizing: 'border-box' }} />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.9rem' }}>Telefone</label>
                                <input value={newPhone} onChange={e => setNewPhone(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontSize: isMobile ? '16px' : '0.9rem', boxSizing: 'border-box' }} />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.9rem' }}>Relação</label>
                                <select value={newRelation} onChange={e => setNewRelation(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontSize: isMobile ? '16px' : '0.9rem', boxSizing: 'border-box' }}>
                                    <option value="Visitante">Visitante</option>
                                    <option value="Familiar">Familiar</option>
                                    <option value="Acompanhante">Acompanhante</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.9rem' }}>ID do Paciente (UUID)</label>
                                <input required value={targetPatientId} onChange={e => setTargetPatientId(e.target.value)} placeholder="Cole o ID do paciente aqui" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd', fontSize: isMobile ? '16px' : '0.9rem', boxSizing: 'border-box' }} />
                                <small style={{ color: '#666' }}>Copie o ID da URL do detalhe do paciente.</small>
                            </div>

                            <button type="submit" style={{ marginTop: spacing.sm, padding: '10px', backgroundColor: colors.primary.medium, color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>Salvar</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VisitorsWorkspace;

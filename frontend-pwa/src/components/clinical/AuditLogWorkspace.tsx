
import React, { useEffect, useState } from 'react';
import Card from "../base/Card";
import { colors, spacing } from "../../theme/colors";
import { ShieldCheck } from "lucide-react";

interface AuditLogWorkspaceProps {
    patientId: string;
}

interface Provenance {
    resourceType: "Provenance";
    id: string;
    recorded: string;
    reason?: { text: string }[];
    agent?: { who: { display: string } }[];
    target: { reference: string }[];
}

const AuditLogWorkspace: React.FC<AuditLogWorkspaceProps> = ({ patientId }) => {
    const [logs, setLogs] = useState<Provenance[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchLogs = async () => {
            setLoading(true);
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`${import.meta.env.VITE_API_URL}/audit/logs/?target=Patient/${patientId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) throw new Error("Failed to fetch audit logs");
                const data = await response.json();
                setLogs(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Algo deu errado");
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchLogs();
        }
    }, [patientId]);

    if (loading) return <div className="p-4 text-center text-slate-500">Carregando auditoria...</div>;
    if (error) return <div className="p-4 text-red-500 bg-red-50 rounded">Erro: {error}</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
            <header className="flex items-center gap-3 mb-4">
                <ShieldCheck size={28} className="text-emerald-600" />
                <div>
                    <h2 className="text-xl font-bold text-slate-800">Trilha de Auditoria (Provenance)</h2>
                    <p className="text-sm text-slate-500">Histórico imutável de alterações deste prontuário.</p>
                </div>
            </header>

            {logs.length === 0 ? (
                <Card padding="lg">
                    <div className="text-center text-slate-500">Nenhum registro de auditoria encontrado.</div>
                </Card>
            ) : (
                <div className="space-y-3">
                    {logs.map(log => (
                        <div key={log.id} style={{
                            backgroundColor: 'white',
                            padding: spacing.md,
                            borderRadius: '8px',
                            borderLeft: `4px solid ${colors.primary.medium}`,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <div>
                                <div className="font-semibold text-slate-800 flex items-center gap-2">
                                    {log.reason?.[0]?.text || "AÇÃO DESCONHECIDA"}
                                </div>
                                <div className="text-sm text-slate-500 mt-1">
                                    Agente: <b>{log.agent?.[0]?.who?.display || "Sistema"}</b>
                                </div>
                            </div>
                            <div className="text-right text-sm text-slate-400 font-mono">
                                {new Date(log.recorded).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AuditLogWorkspace;

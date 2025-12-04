import React, { useEffect, useState } from "react";
import axios from "axios";
import { AlertCircle, CheckCircle } from "lucide-react";
import Card from "../base/Card";
import { colors, spacing } from "../../theme/colors";
import {
    FHIRCondition,
    getConditionName,
    getConditionStatus,
} from "../../utils/fhirParser";

interface ProblemListProps {
    patientId: string;
}

const ProblemList: React.FC<ProblemListProps> = ({ patientId }) => {
    const [conditions, setConditions] = useState<FHIRCondition[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const VITE_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

    useEffect(() => {
        const fetchConditions = async () => {
            try {
                const response = await axios.get(
                    `${VITE_API_URL}/patients/${patientId}/conditions/`
                );
                setConditions(response.data);
            } catch (err) {
                console.error("Erro ao buscar condições:", err);
                setError("Não foi possível carregar a lista de problemas.");
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchConditions();
        }
    }, [patientId, VITE_API_URL]);

    if (loading) return <div>Carregando problemas...</div>;
    if (error) return <div style={{ color: colors.alert.critical }}>{error}</div>;
    if (conditions.length === 0) {
        return (
            <Card padding="lg">
                <div style={{ textAlign: "center", color: colors.text.tertiary }}>
                    Nenhum problema ativo registrado.
                </div>
            </Card>
        );
    }

    return (
        <Card padding="none">
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {conditions.map((cond, idx) => {
                    const name = getConditionName(cond);
                    const status = getConditionStatus(cond);
                    const isActive = status === "active" || status === "recurrence" || status === "relapse";

                    return (
                        <li
                            key={cond.id}
                            style={{
                                padding: spacing.md,
                                borderBottom:
                                    idx !== conditions.length - 1
                                        ? `1px solid ${colors.border.light}`
                                        : "none",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                                {isActive ? (
                                    <AlertCircle size={20} color={colors.alert.warning} />
                                ) : (
                                    <CheckCircle size={20} color={colors.alert.success} />
                                )}
                                <span style={{ fontWeight: 500, color: colors.text.primary }}>
                                    {name}
                                </span>
                            </div>
                            <span
                                style={{
                                    fontSize: "0.75rem",
                                    padding: "2px 8px",
                                    borderRadius: "12px",
                                    backgroundColor: isActive
                                        ? `${colors.alert.warning}20`
                                        : `${colors.alert.success}20`,
                                    color: isActive ? colors.alert.warning : colors.alert.success,
                                    textTransform: "uppercase",
                                    fontWeight: 600,
                                }}
                            >
                                {status}
                            </span>
                        </li>
                    );
                })}
            </ul>
        </Card>
    );
};

export default ProblemList;

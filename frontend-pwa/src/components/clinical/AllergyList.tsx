import React, { useEffect, useState } from "react";
import axios from "axios";
import { ShieldAlert } from "lucide-react";
import Card from "../base/Card";
import { colors, spacing } from "../../theme/colors";
import {
    FHIRAllergyIntolerance,
    getAllergyName,
    getAllergyCriticality,
} from "../../utils/fhirParser";

interface AllergyListProps {
    patientId: string;
}

const AllergyList: React.FC<AllergyListProps> = ({ patientId }) => {
    const [allergies, setAllergies] = useState<FHIRAllergyIntolerance[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const VITE_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

    useEffect(() => {
        const fetchAllergies = async () => {
            try {
                const response = await axios.get(
                    `${VITE_API_URL}/patients/${patientId}/allergies/`
                );
                setAllergies(response.data);
            } catch (err) {
                console.error("Erro ao buscar alergias:", err);
                setError("Não foi possível carregar a lista de alergias.");
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchAllergies();
        }
    }, [patientId, VITE_API_URL]);

    if (loading) return <div>Carregando alergias...</div>;
    if (error) return <div style={{ color: colors.alert.critical }}>{error}</div>;
    if (allergies.length === 0) {
        return (
            <Card padding="lg">
                <div style={{ textAlign: "center", color: colors.text.tertiary }}>
                    Nenhuma alergia conhecida.
                </div>
            </Card>
        );
    }

    return (
        <Card padding="none">
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {allergies.map((allergy, idx) => {
                    const name = getAllergyName(allergy);
                    const criticality = getAllergyCriticality(allergy);
                    const isHighRisk = criticality === "Alta";

                    return (
                        <li
                            key={allergy.id}
                            style={{
                                padding: spacing.md,
                                borderBottom:
                                    idx !== allergies.length - 1
                                        ? `1px solid ${colors.border.light}`
                                        : "none",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                                <ShieldAlert
                                    size={20}
                                    color={isHighRisk ? colors.alert.critical : colors.alert.warning}
                                />
                                <span style={{ fontWeight: 500, color: colors.text.primary }}>
                                    {name}
                                </span>
                            </div>
                            <span
                                style={{
                                    fontSize: "0.75rem",
                                    padding: "2px 8px",
                                    borderRadius: "12px",
                                    backgroundColor: isHighRisk
                                        ? `${colors.alert.critical}20`
                                        : `${colors.alert.warning}20`,
                                    color: isHighRisk
                                        ? colors.alert.critical
                                        : colors.alert.warning,
                                    textTransform: "uppercase",
                                    fontWeight: 600,
                                }}
                            >
                                {criticality}
                            </span>
                        </li>
                    );
                })}
            </ul>
        </Card>
    );
};

export default AllergyList;

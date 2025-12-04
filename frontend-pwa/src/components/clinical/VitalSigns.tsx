import React, { useEffect, useState } from "react";
import axios from "axios";
import { Activity, Thermometer, Heart, Weight, Ruler } from "lucide-react";
import Card from "../base/Card";
import { colors, spacing } from "../../theme/colors";
import {
    FHIRObservation,
    getObservationName,
    getObservationValue,
    formatObservationDate,
} from "../../utils/fhirParser";

interface VitalSignsProps {
    patientId: string;
}

const VitalSigns: React.FC<VitalSignsProps> = ({ patientId }) => {
    const [observations, setObservations] = useState<FHIRObservation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const VITE_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

    useEffect(() => {
        const fetchObservations = async () => {
            try {
                const response = await axios.get(
                    `${VITE_API_URL}/patients/${patientId}/observations/`
                );
                setObservations(response.data);
            } catch (err) {
                console.error("Erro ao buscar sinais vitais:", err);
                setError("Não foi possível carregar os sinais vitais.");
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchObservations();
        }
    }, [patientId, VITE_API_URL]);

    if (loading) return <div>Carregando sinais vitais...</div>;
    if (error) return <div style={{ color: colors.alert.critical }}>{error}</div>;
    if (observations.length === 0) {
        return (
            <Card padding="lg">
                <div style={{ textAlign: "center", color: colors.text.tertiary }}>
                    Nenhum sinal vital registrado.
                </div>
            </Card>
        );
    }

    // Helper para escolher ícone baseado no código ou nome
    const getIcon = (name: string) => {
        const lower = name.toLowerCase();
        if (lower.includes("pressure")) return <Activity size={24} />;
        if (lower.includes("temperature")) return <Thermometer size={24} />;
        if (lower.includes("heart") || lower.includes("pulse")) return <Heart size={24} />;
        if (lower.includes("weight")) return <Weight size={24} />;
        if (lower.includes("height")) return <Ruler size={24} />;
        return <Activity size={24} />;
    };

    return (
        <div
            style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: spacing.md,
            }}
        >
            {observations.map((obs) => {
                const name = getObservationName(obs);
                const value = getObservationValue(obs);
                const date = formatObservationDate(obs.effectiveDateTime);

                return (
                    <Card key={obs.id} padding="md">
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: spacing.sm,
                                marginBottom: spacing.sm,
                                color: colors.primary.medium,
                            }}
                        >
                            {getIcon(name)}
                            <span
                                style={{
                                    fontWeight: 600,
                                    fontSize: "0.875rem",
                                    color: colors.text.secondary,
                                }}
                            >
                                {name}
                            </span>
                        </div>
                        <div
                            style={{
                                fontSize: "1.5rem",
                                fontWeight: 700,
                                color: colors.text.primary,
                                marginBottom: "4px",
                            }}
                        >
                            {value}
                        </div>
                        <div
                            style={{
                                fontSize: "0.75rem",
                                color: colors.text.tertiary,
                            }}
                        >
                            {date}
                        </div>
                    </Card>
                );
            })}
        </div>
    );
};

export default VitalSigns;

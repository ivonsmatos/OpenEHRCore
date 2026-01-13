import React, { useEffect, useState } from "react";
import axios from "axios";
import {
    Activity,
    Thermometer,
    Heart,
    Weight,
    Ruler,
    Droplets,
    Wind,
    Gauge,
    Candy
} from "lucide-react";
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
            } catch (err: any) {
                if (err.response?.status === 429) {
                    // Erro 429 - Too Many Requests, tentar novamente em 2s
                    setTimeout(fetchObservations, 2000);
                } else {
                    console.error("Erro ao buscar sinais vitais:", err);
                    setError("Não foi possível carregar os sinais vitais.");
                }
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

    // Helper para escolher ícone baseado no nome do sinal vital
    const getIcon = (name: string) => {
        const lower = name.toLowerCase();

        // Temperatura
        if (lower.includes("temperatura")) return <Thermometer size={24} color="#FF6B6B" />;

        // Frequência Cardíaca
        if (lower.includes("cardíaca") || lower.includes("cardiaca") || lower.includes("coração"))
            return <Heart size={24} color="#FF4757" />;

        // Frequência Respiratória
        if (lower.includes("respiratória") || lower.includes("respiratoria"))
            return <Wind size={24} color="#00D2D3" />;

        // Pressão Arterial
        if (lower.includes("pressão") || lower.includes("pressao") || lower.includes("arterial"))
            return <Gauge size={24} color="#EE5A24" />;

        // Saturação de Oxigênio
        if (lower.includes("saturação") || lower.includes("saturacao") || lower.includes("oxigênio") || lower.includes("spo2"))
            return <Droplets size={24} color="#5F27CD" />;

        // Peso
        if (lower.includes("peso")) return <Weight size={24} color="#10AC84" />;

        // Altura
        if (lower.includes("altura")) return <Ruler size={24} color="#01A3A4" />;

        // IMC
        if (lower.includes("imc")) return <Activity size={24} color="#F79F1F" />;

        // Glicemia
        if (lower.includes("glicemia") || lower.includes("glicose"))
            return <Candy size={24} color="#6C5CE7" />;

        // Default
        return <Activity size={24} color={colors.primary.medium} />;
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

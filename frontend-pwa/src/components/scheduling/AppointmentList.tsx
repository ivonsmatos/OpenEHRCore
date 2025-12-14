import React, { useEffect, useState } from "react";
import axios from "axios";
import { Calendar, Clock } from "lucide-react";
import Card from "../base/Card";
import { colors, spacing } from "../../theme/colors";
import {
    FHIRAppointment,
    getAppointmentDescription,
    formatAppointmentDate,
    getAppointmentStatusLabel,
} from "../../utils/fhirParser";

interface AppointmentListProps {
    patientId: string;
}

const AppointmentList: React.FC<AppointmentListProps> = ({ patientId }) => {
    const [appointments, setAppointments] = useState<FHIRAppointment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const VITE_API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

    useEffect(() => {
        const fetchAppointments = async () => {
            try {
                const response = await axios.get(
                    `${VITE_API_URL}/patients/${patientId}/appointments/`
                );
                setAppointments(response.data);
            } catch (err: any) {
                if (err.response?.status === 429) {
                    // Erro 429 - Too Many Requests, tentar novamente em 2s
                    setTimeout(fetchAppointments, 2000);
                } else {
                    console.error("Erro ao buscar agendamentos:", err);
                    setError("Não foi possível carregar a agenda.");
                }
            } finally {
                setLoading(false);
            }
        };

        if (patientId) {
            fetchAppointments();
        }
    }, [patientId, VITE_API_URL]);

    if (loading) return <div>Carregando agenda...</div>;
    if (error) return <div style={{ color: colors.alert.critical }}>{error}</div>;
    if (appointments.length === 0) {
        return (
            <Card padding="lg">
                <div style={{ textAlign: "center", color: colors.text.tertiary }}>
                    Nenhum agendamento futuro.
                </div>
            </Card>
        );
    }

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
            {appointments.map((appt) => {
                const description = getAppointmentDescription(appt);
                const date = formatAppointmentDate(appt.start);
                const status = getAppointmentStatusLabel(appt.status);

                return (
                    <Card key={appt.id} padding="md">
                        <div
                            style={{
                                display: "flex",
                                alignItems: "flex-start",
                                justifyContent: "space-between",
                            }}
                        >
                            <div>
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: spacing.sm,
                                        marginBottom: spacing.xs,
                                    }}
                                >
                                    <Calendar size={18} color={colors.primary.medium} />
                                    <span
                                        style={{
                                            fontWeight: 600,
                                            color: colors.text.primary,
                                            fontSize: "1rem",
                                        }}
                                    >
                                        {description}
                                    </span>
                                </div>
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: spacing.sm,
                                        color: colors.text.secondary,
                                        fontSize: "0.875rem",
                                    }}
                                >
                                    <Clock size={16} />
                                    {date}
                                </div>
                            </div>
                            <span
                                style={{
                                    fontSize: "0.75rem",
                                    padding: "4px 12px",
                                    borderRadius: "16px",
                                    backgroundColor: colors.background.muted,
                                    color: colors.text.secondary,
                                    fontWeight: 600,
                                    textTransform: "uppercase",
                                }}
                            >
                                {status}
                            </span>
                        </div>
                    </Card>
                );
            })}
        </div>
    );
};

export default AppointmentList;

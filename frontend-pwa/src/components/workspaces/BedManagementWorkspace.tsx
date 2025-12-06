
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../base/Card';
import { colors, spacing, borderRadius } from '../../theme/colors';
import { User, Bed, Activity, CheckCircle, Clock } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import BedDetailsModal from './BedDetailsModal';

// API Base
const API_BASE = 'http://localhost:8000/api/v1';

interface LocationNode {
    id: string;
    resourceType: string;
    name: string;
    status_code: string; // 'O', 'U', 'C'
    physicalType?: { coding: { code: string, display: string }[] };
    children?: LocationNode[];
}

interface Patient {
    id: string;
    name: string;
}

const BedManagementWorkspace: React.FC = () => {
    const navigate = useNavigate();
    const { token, logout } = useAuth(); // Use auth hook
    const [locations, setLocations] = useState<LocationNode[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ total: 0, occupied: 0, free: 0, cleaning: 0, occupancy_rate: 0 });

    // Admission Modal State
    const [selectedBed, setSelectedBed] = useState<LocationNode | null>(null);
    const [showAdmitModal, setShowAdmitModal] = useState(false);
    const [showDetailsModal, setShowDetailsModal] = useState(false);

    const [patients, setPatients] = useState<Patient[]>([]);
    const [selectedPatientId, setSelectedPatientId] = useState('');

    useEffect(() => {
        if (token) {
            fetchLocations();
            fetchStats();
            fetchPatients();
        }
    }, [token]);

    const fetchLocations = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/ipd/locations/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setLocations(data);
                setError(null);
            } else {
                setError(`Erro ao carregar locais: ${res.status} ${res.statusText}`);
                if (res.status === 401) {
                    alert("Sessão expirada. Por favor, faça login novamente.");
                    logout();
                }
            }
        } catch (error) {
            console.error("Error fetching locations", error);
            setError("Erro de conexão com o servidor.");
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/ipd/occupancy/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) return; // Handled by fetchLocations usually
            if (res.ok) setStats(await res.json());
        } catch (err) { console.error(err); }
    };

    const fetchPatients = async () => {
        try {
            const res = await fetch(`${API_BASE}/patients/?page=1`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) return;
            if (res.ok) {
                const data = await res.json();
                setPatients(data.results.map((p: any) => ({
                    id: p.id,
                    name: p.name || `Desconhecido`
                })));
            }
        } catch (err) { console.error(err); }
    };

    const handleBedClick = (bed: LocationNode) => {
        setSelectedBed(bed);
        setShowDetailsModal(true);
    };

    const openAdmission = () => {
        setShowDetailsModal(false);
        setShowAdmitModal(true);
    };

    const handleAdmit = async () => {
        if (!selectedBed || !selectedPatientId) return;
        try {
            const res = await fetch(`${API_BASE}/ipd/admit/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location_id: selectedBed.id,
                    patient_id: selectedPatientId
                })
            });

            if (res.ok) {
                alert("Paciente internado com sucesso!");
                setShowAdmitModal(false);
                setSelectedPatientId('');
                fetchLocations(); // Refresh
                fetchStats();
            } else {
                if (res.status === 401) {
                    alert("Sessão expirada.");
                    logout();
                    return;
                }
                alert("Erro ao internar");
            }
        } catch (err) { console.error(err); }
    };

    const getBedColor = (status: string) => {
        switch (status) {
            case 'O': return '#ef4444'; // Red (Occupied)
            case 'C': return '#f59e0b'; // Yellow (Cleaning)
            case 'U': return '#10b981'; // Green (Free)
            default: return '#9ca3af';
        }
    };

    const renderBed = (bed: LocationNode) => (
        <div
            key={bed.id}
            onClick={() => handleBedClick(bed)}
            style={{
                width: '80px',
                height: '100px',
                backgroundColor: 'white',
                border: `2px solid ${getBedColor(bed.status_code)}`,
                borderRadius: borderRadius.md,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                margin: spacing.sm,
                cursor: 'pointer',
                position: 'relative'
            }}
        >
            <Bed size={24} color={getBedColor(bed.status_code)} />
            <span style={{ fontSize: '0.75rem', marginTop: 4, textAlign: 'center' }}>{bed.name.replace('Leito ', '')}</span>
            {bed.status_code === 'O' && <User size={12} style={{ position: 'absolute', top: 4, right: 4 }} />}
        </div>
    );

    const renderRoom = (room: LocationNode) => (
        <div key={room.id} style={{ margin: spacing.md, padding: spacing.md, backgroundColor: '#f9fafb', borderRadius: borderRadius.md }}>
            <h4 style={{ marginBottom: spacing.sm }}>{room.name}</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                {room.children?.map(child => {
                    // Check if child is a Bed by code 'bd' or name convention as fallback
                    const isBed = child.physicalType?.coding?.some(c => c.code === 'bd') || child.name.startsWith('Leito');
                    if (isBed) return renderBed(child);
                    // Nested rooms? Unlikely but recursion is safe
                    return renderBed(child);
                })}
            </div>
        </div>
    );

    const renderWard = (ward: LocationNode) => (
        <Card key={ward.id} title={ward.name} style={{ marginBottom: spacing.lg }}>
            <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                {ward.children?.map(child => {
                    const isRoom = child.physicalType?.coding?.some(c => c.code === 'ro') || child.name.startsWith('Quarto');
                    if (isRoom) return renderRoom(child);
                    // Ward might have direct beds
                    return renderBed(child);
                })}
            </div>
        </Card>
    );

    return (
        <div style={{ padding: spacing.lg }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.lg }}>
                {/* Header content */}
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Gestão de Leitos</h1>
                    <p style={{ color: colors.text.secondary }}>Visualização em tempo real da ocupação hospitalar</p>
                </div>

                {/* Stats Summary */}
                <div style={{ display: 'flex', gap: spacing.md }}>
                    <Card style={{ padding: spacing.sm, minWidth: 100, textAlign: 'center' }}>
                        <div style={{ color: '#10b981', fontWeight: 'bold' }}>{stats.free}</div>
                        <div style={{ fontSize: '0.8rem' }}>Livres</div>
                    </Card>
                    <Card style={{ padding: spacing.sm, minWidth: 100, textAlign: 'center' }}>
                        <div style={{ color: '#ef4444', fontWeight: 'bold' }}>{stats.occupied}</div>
                        <div style={{ fontSize: '0.8rem' }}>Ocupados</div>
                    </Card>
                    <Card style={{ padding: spacing.sm, minWidth: 100, textAlign: 'center' }}>
                        <div style={{ color: '#f59e0b', fontWeight: 'bold' }}>{stats.cleaning}</div>
                        <div style={{ fontSize: '0.8rem' }}>Limpeza</div>
                    </Card>
                    <Card style={{ padding: spacing.sm, minWidth: 100, textAlign: 'center' }}>
                        <div style={{ fontWeight: 'bold' }}>{stats.occupancy_rate}%</div>
                        <div style={{ fontSize: '0.8rem' }}>Taxa Ocup.</div>
                    </Card>
                </div>
            </div>

            {error && (
                <div style={{ padding: spacing.md, backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: borderRadius.md, marginBottom: spacing.md }}>
                    {error}
                </div>
            )}

            {loading ? <p>Carregando mapa...</p> : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.xl }}>
                    {/* Render by Groups */}
                    {(() => {
                        const getAllBeds = (nodes: LocationNode[]): LocationNode[] => {
                            let beds: LocationNode[] = [];
                            nodes.forEach(node => {
                                const isBed = node.physicalType?.coding?.some(c => c.code === 'bd') || node.name.startsWith('Leito');
                                if (isBed) beds.push(node);
                                if (node.children) beds = [...beds, ...getAllBeds(node.children)];
                            });
                            return beds;
                        };
                        const allBeds = getAllBeds(locations);
                        const occupied = allBeds.filter(b => b.status_code === 'O');
                        const cleaning = allBeds.filter(b => b.status_code === 'K');
                        const free = allBeds.filter(b => b.status_code === 'U');

                        const renderSection = (title: string, color: string, list: LocationNode[]) => (
                            <Card style={{ marginBottom: spacing.lg }}>
                                <h3 style={{ color, borderBottom: `2px solid ${color}`, paddingBottom: spacing.sm, marginBottom: spacing.md }}>
                                    {title} ({list.length})
                                </h3>
                                <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                                    {list.length > 0 ? list.map(bed => renderBed(bed)) : <p style={{ padding: spacing.md, color: colors.text.secondary }}>Nenhum leito nesta categoria.</p>}
                                </div>
                            </Card>
                        );

                        return (
                            <>
                                {renderSection('Em Uso / Ocupados', '#ef4444', occupied)}
                                {renderSection('Em Higienização', '#f59e0b', cleaning)}
                                {renderSection('Liberados / Livres', '#10b981', free)}
                            </>
                        );
                    })()}
                </div>
            )}

            {/* Bed Details Modal */}
            {showDetailsModal && selectedBed && (
                <BedDetailsModal
                    locationId={selectedBed.id}
                    onClose={() => setShowDetailsModal(false)}
                    onAdmit={openAdmission}
                />
            )}

            {/* Admission Modal */}
            {showAdmitModal && selectedBed && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center',
                    zIndex: 1000
                }}>
                    <div style={{ backgroundColor: 'white', padding: spacing.lg, borderRadius: borderRadius.md, width: '400px' }}>
                        <h3>Internar Paciente</h3>
                        <p>Leito: <b>{selectedBed.name}</b></p>

                        <div style={{ margin: `${spacing.md} 0` }}>
                            <label>Selecione o Paciente:</label>
                            <select
                                style={{ width: '100%', padding: spacing.sm, marginTop: spacing.xs }}
                                value={selectedPatientId}
                                onChange={(e) => setSelectedPatientId(e.target.value)}
                            >
                                <option value="">Selecione...</option>
                                {patients.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: spacing.sm }}>
                            <button onClick={() => setShowAdmitModal(false)} style={{ padding: spacing.sm }}>Cancelar</button>
                            <button
                                onClick={handleAdmit}
                                style={{ padding: spacing.sm, backgroundColor: colors.primary.medium, color: 'white', border: 'none', borderRadius: borderRadius.sm }}
                            >
                                Confirmar Internação
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BedManagementWorkspace;

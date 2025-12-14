import React, { useState, useEffect } from 'react';
import Card from '../base/Card';
import { colors, spacing, borderRadius } from '../../theme/colors';
import { User, Bed, Activity } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useIsMobile } from '../../hooks/useMediaQuery';
import BedDetailsModal from './BedDetailsModal';

// API Base
const API_BASE = 'http://localhost:8000/api/v1';

interface LocationNode {
    id: string;
    resourceType: string;
    name: string;
    status_code: string; // 'O', 'U', 'K', 'I'
    physicalType?: { coding: { code: string, display: string }[] };
    children?: LocationNode[];
}

interface Patient {
    id: string;
    name: string;
}

type StatusFilter = 'all' | 'O' | 'U' | 'K' | 'I';

const BedManagementWorkspace: React.FC = () => {
    const { token, logout } = useAuth();
    const isMobile = useIsMobile();
    const [locations, setLocations] = useState<LocationNode[]>([]);
    const [_error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ total: 0, occupied: 0, free: 0, cleaning: 0, occupancy_rate: 0 });
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

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
            if (res.ok) setStats(await res.json());
        } catch (err) { console.error(err); }
    };

    const fetchPatients = async () => {
        try {
            const res = await fetch(`${API_BASE}/patients/?page=1`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
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
                alert("Erro ao internar");
            }
        } catch (err) { console.error(err); }
    };

    const getBedColor = (status: string) => {
        switch (status) {
            case 'O': return '#ef4444'; // Red (Occupied)
            case 'K': return '#f59e0b'; // Yellow (Cleaning)
            case 'U': return '#10b981'; // Green (Free)
            case 'I': return '#6b7280'; // Gray (Inactive/Blocked)
            default: return '#9ca3af';
        }
    };

    const renderBed = (bed: LocationNode) => {
        const color = getBedColor(bed.status_code || 'U');
        return (
            <div
                key={bed.id}
                onClick={() => handleBedClick(bed)}
                style={{
                    width: 100,
                    height: 120,
                    margin: spacing.sm,
                    border: `2px solid ${color}`,
                    borderRadius: borderRadius.md,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    backgroundColor: 'white',
                    position: 'relative'
                }}
            >
                <div style={{ position: 'absolute', top: 5, right: 5 }}>
                    {bed.status_code === 'O' && <User size={14} color={color} />}
                    {bed.status_code === 'K' && <Activity size={14} color={color} />}
                </div>

                <Bed size={32} color={color} style={{ marginBottom: spacing.xs }} />
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: colors.text.primary, textAlign: 'center' }}>
                    {bed.name.replace('Leito ', '')}
                </span>
                <span style={{ fontSize: '0.7rem', color: colors.text.secondary }}>
                    {bed.status_code === 'O' ? 'OCUPADO' : bed.status_code === 'K' ? 'LIMPEZA' : bed.status_code === 'I' ? 'BLOQ.' : 'LIVRE'}
                </span>
            </div>
        );
    };

    return (
        <div style={{ padding: isMobile ? spacing.md : spacing.xl }}>
            {/* Header and Stats */}
            <div style={{ 
                display: 'flex', 
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between', 
                alignItems: isMobile ? 'flex-start' : 'center', 
                marginBottom: spacing.xl,
                gap: spacing.md
            }}>
                <div>
                    <h1 style={{ fontSize: isMobile ? '1.5rem' : '1.8rem', fontWeight: 700, color: colors.text.primary }}>Gestão de Leitos</h1>
                    <p style={{ color: colors.text.secondary, fontSize: isMobile ? '0.875rem' : '1rem' }}>Visualização em tempo real da ocupação hospitalar</p>
                </div>
                <div style={{ 
                    display: 'grid',
                    gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(5, 1fr)',
                    gap: spacing.sm,
                    width: isMobile ? '100%' : 'auto'
                }}>
                    <Card 
                        style={{ 
                            padding: spacing.sm, 
                            minWidth: isMobile ? 'auto' : 100, 
                            textAlign: 'center',
                            cursor: 'pointer',
                            border: `2px solid ${statusFilter === 'U' ? '#10b981' : 'transparent'}`,
                            transform: statusFilter === 'U' ? 'scale(1.05)' : 'scale(1)',
                            transition: 'all 0.2s'
                        }}
                        onClick={() => setStatusFilter(statusFilter === 'U' ? 'all' : 'U')}
                    >
                        <div style={{ color: '#10b981', fontWeight: 'bold', fontSize: isMobile ? '1.25rem' : '1.5rem' }}>{stats.free}</div>
                        <div style={{ fontSize: isMobile ? '0.7rem' : '0.8rem' }}>Livres</div>
                    </Card>
                    <Card 
                        style={{ 
                            padding: spacing.sm, 
                            minWidth: isMobile ? 'auto' : 100, 
                            textAlign: 'center',
                            cursor: 'pointer',
                            border: `2px solid ${statusFilter === 'O' ? '#ef4444' : 'transparent'}`,
                            transform: statusFilter === 'O' ? 'scale(1.05)' : 'scale(1)',
                            transition: 'all 0.2s'
                        }}
                        onClick={() => setStatusFilter(statusFilter === 'O' ? 'all' : 'O')}
                    >
                        <div style={{ color: '#ef4444', fontWeight: 'bold', fontSize: isMobile ? '1.25rem' : '1.5rem' }}>{stats.occupied}</div>
                        <div style={{ fontSize: isMobile ? '0.7rem' : '0.8rem' }}>Ocupados</div>
                    </Card>
                    <Card 
                        style={{ 
                            padding: spacing.sm, 
                            minWidth: isMobile ? 'auto' : 100, 
                            textAlign: 'center',
                            cursor: 'pointer',
                            border: `2px solid ${statusFilter === 'K' ? '#f59e0b' : 'transparent'}`,
                            transform: statusFilter === 'K' ? 'scale(1.05)' : 'scale(1)',
                            transition: 'all 0.2s'
                        }}
                        onClick={() => setStatusFilter(statusFilter === 'K' ? 'all' : 'K')}
                    >
                        <div style={{ color: '#f59e0b', fontWeight: 'bold', fontSize: isMobile ? '1.25rem' : '1.5rem' }}>{stats.cleaning}</div>
                        <div style={{ fontSize: isMobile ? '0.7rem' : '0.8rem' }}>Limpeza</div>
                    </Card>
                    <Card 
                        style={{ 
                            padding: spacing.sm, 
                            minWidth: isMobile ? 'auto' : 100, 
                            textAlign: 'center',
                            cursor: 'pointer',
                            border: `2px solid ${statusFilter === 'I' ? '#6b7280' : 'transparent'}`,
                            transform: statusFilter === 'I' ? 'scale(1.05)' : 'scale(1)',
                            transition: 'all 0.2s'
                        }}
                        onClick={() => setStatusFilter(statusFilter === 'I' ? 'all' : 'I')}
                    >
                        <div style={{ color: '#6b7280', fontWeight: 'bold', fontSize: isMobile ? '1.25rem' : '1.5rem' }}>{stats.total - (stats.free + stats.occupied + stats.cleaning)}</div>
                        <div style={{ fontSize: isMobile ? '0.7rem' : '0.8rem' }}>Bloqueados</div>
                    </Card>
                    <Card 
                        style={{ 
                            padding: spacing.sm, 
                            minWidth: isMobile ? 'auto' : 100, 
                            textAlign: 'center',
                            gridColumn: isMobile ? 'span 2' : 'auto'
                        }}
                    >
                        <div style={{ fontWeight: 'bold', fontSize: isMobile ? '1.25rem' : '1.5rem' }}>{stats.occupancy_rate}%</div>
                        <div style={{ fontSize: isMobile ? '0.7rem' : '0.8rem' }}>Taxa Ocup.</div>
                    </Card>
                </div>
            </div>

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
                        const blocked = allBeds.filter(b => b.status_code === 'I');

                        // Apply filter
                        const getFilteredBeds = () => {
                            if (statusFilter === 'all') return allBeds;
                            return allBeds.filter(b => b.status_code === statusFilter);
                        };

                        const filteredBeds = getFilteredBeds();

                        const renderSection = (title: string, color: string, list: LocationNode[]) => (
                            <Card style={{ marginBottom: spacing.lg }}>
                                <h3 style={{ color, borderBottom: `2px solid ${color}`, paddingBottom: spacing.sm, marginBottom: spacing.md, fontSize: isMobile ? '1rem' : '1.25rem' }}>
                                    {title} ({list.length})
                                </h3>
                                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: isMobile ? 'center' : 'flex-start' }}>
                                    {list.length > 0 ? list.map(bed => renderBed(bed)) : <p style={{ padding: spacing.md, color: colors.text.secondary }}>Nenhum leito nesta categoria.</p>}
                                </div>
                            </Card>
                        );

                        // If filter is active, show only filtered beds in one section
                        if (statusFilter !== 'all') {
                            const filterTitle = 
                                statusFilter === 'O' ? 'Em Uso / Ocupados' :
                                statusFilter === 'K' ? 'Em Higienização' :
                                statusFilter === 'U' ? 'Liberados / Livres' :
                                'Bloqueados / Manutenção';
                            const filterColor = 
                                statusFilter === 'O' ? '#ef4444' :
                                statusFilter === 'K' ? '#f59e0b' :
                                statusFilter === 'U' ? '#10b981' :
                                '#6b7280';
                            
                            return (
                                <>
                                    <div style={{ marginBottom: spacing.md, padding: spacing.sm, backgroundColor: colors.background.surface, borderRadius: borderRadius.md, textAlign: 'center' }}>
                                        <span style={{ fontSize: isMobile ? '0.875rem' : '1rem', color: colors.text.secondary }}>
                                            Filtrando por: <strong style={{ color: filterColor }}>{filterTitle}</strong>
                                            <button 
                                                onClick={() => setStatusFilter('all')}
                                                style={{ 
                                                    marginLeft: spacing.md, 
                                                    padding: '4px 12px', 
                                                    backgroundColor: colors.primary.medium, 
                                                    color: 'white', 
                                                    border: 'none', 
                                                    borderRadius: borderRadius.soft,
                                                    cursor: 'pointer',
                                                    fontSize: '0.875rem'
                                                }}
                                            >
                                                Limpar Filtro
                                            </button>
                                        </span>
                                    </div>
                                    {renderSection(filterTitle, filterColor, filteredBeds)}
                                </>
                            );
                        }

                        return (
                            <>
                                {renderSection('Em Uso / Ocupados', '#ef4444', occupied)}
                                {renderSection('Em Higienização', '#f59e0b', cleaning)}
                                {renderSection('Liberados / Livres', '#10b981', free)}
                                {renderSection('Bloqueados / Manutenção', '#6b7280', blocked)}
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
                                style={{ padding: spacing.sm, backgroundColor: colors.primary.medium, color: 'white', border: 'none', borderRadius: borderRadius.soft }}
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

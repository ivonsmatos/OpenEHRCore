import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Building2, Plus, Edit2, Trash2, ChevronDown, ChevronRight, Search, Phone, Mail, MapPin } from 'lucide-react';
import { Button } from '../base/Button';
import { colors } from '../../theme/colors';
import './OrganizationWorkspace.css';

interface Organization {
    id: string;
    name: string;
    alias?: string[];
    active: boolean;
    type?: Array<{
        coding?: Array<{
            code: string;
            display: string;
        }>;
    }>;
    identifier?: Array<{
        system: string;
        value: string;
        type?: { text: string };
    }>;
    telecom?: Array<{
        system: string;
        value: string;
    }>;
    address?: Array<{
        line?: string[];
        city?: string;
        state?: string;
        postalCode?: string;
    }>;
    partOf?: {
        reference: string;
    };
}

interface OrganizationFormData {
    name: string;
    alias: string;
    type: string;
    cnpj: string;
    cnes: string;
    phone: string;
    email: string;
    address: {
        line: string;
        city: string;
        state: string;
        postalCode: string;
    };
    partOf: string;
}

const initialFormData: OrganizationFormData = {
    name: '',
    alias: '',
    type: 'prov',
    cnpj: '',
    cnes: '',
    phone: '',
    email: '',
    address: {
        line: '',
        city: '',
        state: '',
        postalCode: ''
    },
    partOf: ''
};

const ORG_TYPES = [
    { value: 'prov', label: 'Hospital/Clínica' },
    { value: 'dept', label: 'Departamento' },
    { value: 'team', label: 'Equipe' },
    { value: 'ins', label: 'Operadora de Saúde' },
    { value: 'govt', label: 'Órgão Governamental' },
    { value: 'edu', label: 'Instituição de Ensino' },
    { value: 'other', label: 'Outro' }
];

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function validateCNPJ(cnpj: string): boolean {
    const cleaned = cnpj.replace(/[^\d]/g, '');
    if (cleaned.length !== 14) return false;
    if (/^(\d)\1+$/.test(cleaned)) return false;

    // Validação dos dígitos verificadores
    let sum = 0;
    let weight = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    for (let i = 0; i < 12; i++) {
        sum += parseInt(cleaned[i]) * weight[i];
    }
    let digit1 = sum % 11 < 2 ? 0 : 11 - (sum % 11);
    if (parseInt(cleaned[12]) !== digit1) return false;

    sum = 0;
    weight = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    for (let i = 0; i < 13; i++) {
        sum += parseInt(cleaned[i]) * weight[i];
    }
    let digit2 = sum % 11 < 2 ? 0 : 11 - (sum % 11);
    return parseInt(cleaned[13]) === digit2;
}

function formatCNPJ(value: string): string {
    const cleaned = value.replace(/[^\d]/g, '');
    if (cleaned.length <= 2) return cleaned;
    if (cleaned.length <= 5) return `${cleaned.slice(0, 2)}.${cleaned.slice(2)}`;
    if (cleaned.length <= 8) return `${cleaned.slice(0, 2)}.${cleaned.slice(2, 5)}.${cleaned.slice(5)}`;
    if (cleaned.length <= 12) return `${cleaned.slice(0, 2)}.${cleaned.slice(2, 5)}.${cleaned.slice(5, 8)}/${cleaned.slice(8)}`;
    return `${cleaned.slice(0, 2)}.${cleaned.slice(2, 5)}.${cleaned.slice(5, 8)}/${cleaned.slice(8, 12)}-${cleaned.slice(12, 14)}`;
}

export function OrganizationWorkspace() {
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState<OrganizationFormData>(initialFormData);
    const [formErrors, setFormErrors] = useState<Record<string, string>>({});
    const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());

    const fetchOrganizations = useCallback(async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_BASE}/organizations/`, {
                headers: { Authorization: `Bearer ${token}` },
                params: searchTerm ? { name: searchTerm } : {}
            });
            setOrganizations(response.data.results || []);
            setError(null);
        } catch (err) {
            setError('Erro ao carregar organizações');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [searchTerm]);

    useEffect(() => {
        fetchOrganizations();
    }, [fetchOrganizations]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validação
        const errors: Record<string, string> = {};
        if (!formData.name.trim()) {
            errors.name = 'Nome é obrigatório';
        }
        if (formData.cnpj && !validateCNPJ(formData.cnpj)) {
            errors.cnpj = 'CNPJ inválido';
        }

        if (Object.keys(errors).length > 0) {
            setFormErrors(errors);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            const payload = {
                name: formData.name,
                alias: formData.alias ? formData.alias.split(',').map(a => a.trim()) : undefined,
                type: formData.type,
                cnpj: formData.cnpj || undefined,
                cnes: formData.cnes || undefined,
                phone: formData.phone || undefined,
                email: formData.email || undefined,
                address: formData.address.line ? {
                    line: [formData.address.line],
                    city: formData.address.city,
                    state: formData.address.state,
                    postalCode: formData.address.postalCode
                } : undefined,
                partOf: formData.partOf || undefined
            };

            if (editingId) {
                await axios.put(`${API_BASE}/organizations/${editingId}/`, payload, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            } else {
                await axios.post(`${API_BASE}/organizations/`, payload, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            }

            setShowForm(false);
            setEditingId(null);
            setFormData(initialFormData);
            setFormErrors({});
            fetchOrganizations();
        } catch (err) {
            setError('Erro ao salvar organização');
            console.error(err);
        }
    };

    const handleEdit = (org: Organization) => {
        const cnpjId = org.identifier?.find(i => i.type?.text === 'CNPJ');
        const cnesId = org.identifier?.find(i => i.type?.text === 'CNES');
        const phone = org.telecom?.find(t => t.system === 'phone');
        const email = org.telecom?.find(t => t.system === 'email');
        const addr = org.address?.[0];

        setFormData({
            name: org.name,
            alias: org.alias?.join(', ') || '',
            type: org.type?.[0]?.coding?.[0]?.code || 'prov',
            cnpj: cnpjId?.value || '',
            cnes: cnesId?.value || '',
            phone: phone?.value || '',
            email: email?.value || '',
            address: {
                line: addr?.line?.join(', ') || '',
                city: addr?.city || '',
                state: addr?.state || '',
                postalCode: addr?.postalCode || ''
            },
            partOf: org.partOf?.reference?.split('/')[1] || ''
        });
        setEditingId(org.id);
        setShowForm(true);
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Deseja realmente desativar esta organização?')) return;

        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${API_BASE}/organizations/${id}/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchOrganizations();
        } catch (err) {
            setError('Erro ao desativar organização');
            console.error(err);
        }
    };

    const toggleExpand = (id: string) => {
        const newExpanded = new Set(expandedOrgs);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedOrgs(newExpanded);
    };

    const getOrgTypeLabel = (org: Organization): string => {
        const code = org.type?.[0]?.coding?.[0]?.code;
        return ORG_TYPES.find(t => t.value === code)?.label || 'Organização';
    };

    const getCNPJ = (org: Organization): string | null => {
        const id = org.identifier?.find(i => i.type?.text === 'CNPJ');
        return id?.value || null;
    };

    return (
        <div className="organization-workspace">
            <header className="workspace-header">
                <div className="header-title">
                    <Building2 size={28} color={colors.primary.medium} />
                    <h1>Organizações</h1>
                </div>
                <Button variant="primary" onClick={() => { setShowForm(true); setEditingId(null); setFormData(initialFormData); }}>
                    <Plus size={18} />
                    Nova Organização
                </Button>
            </header>

            <div className="search-section">
                <div className="search-input-wrapper">
                    <Search size={18} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Buscar por nome..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-input"
                    />
                </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            {showForm && (
                <div className="form-modal-overlay">
                    <div className="form-modal">
                        <h2>{editingId ? 'Editar Organização' : 'Nova Organização'}</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Nome *</label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className={formErrors.name ? 'error' : ''}
                                    />
                                    {formErrors.name && <span className="error-text">{formErrors.name}</span>}
                                </div>
                                <div className="form-group">
                                    <label>Tipo</label>
                                    <select
                                        value={formData.type}
                                        onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                    >
                                        {ORG_TYPES.map(t => (
                                            <option key={t.value} value={t.value}>{t.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>CNPJ</label>
                                    <input
                                        type="text"
                                        value={formatCNPJ(formData.cnpj)}
                                        onChange={(e) => setFormData({ ...formData, cnpj: e.target.value.replace(/[^\d]/g, '') })}
                                        placeholder="00.000.000/0000-00"
                                        maxLength={18}
                                        className={formErrors.cnpj ? 'error' : ''}
                                    />
                                    {formErrors.cnpj && <span className="error-text">{formErrors.cnpj}</span>}
                                </div>
                                <div className="form-group">
                                    <label>CNES</label>
                                    <input
                                        type="text"
                                        value={formData.cnes}
                                        onChange={(e) => setFormData({ ...formData, cnes: e.target.value })}
                                        placeholder="Código CNES"
                                        maxLength={7}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Apelidos (separados por vírgula)</label>
                                <input
                                    type="text"
                                    value={formData.alias}
                                    onChange={(e) => setFormData({ ...formData, alias: e.target.value })}
                                    placeholder="Ex: HSP, Hospital Central"
                                />
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Telefone</label>
                                    <input
                                        type="tel"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        placeholder="(00) 0000-0000"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>E-mail</label>
                                    <input
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        placeholder="contato@hospital.com.br"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Endereço</label>
                                <input
                                    type="text"
                                    value={formData.address.line}
                                    onChange={(e) => setFormData({ ...formData, address: { ...formData.address, line: e.target.value } })}
                                    placeholder="Rua, número"
                                />
                            </div>

                            <div className="form-row triple">
                                <div className="form-group">
                                    <label>Cidade</label>
                                    <input
                                        type="text"
                                        value={formData.address.city}
                                        onChange={(e) => setFormData({ ...formData, address: { ...formData.address, city: e.target.value } })}
                                    />
                                </div>
                                <div className="form-group small">
                                    <label>UF</label>
                                    <input
                                        type="text"
                                        value={formData.address.state}
                                        onChange={(e) => setFormData({ ...formData, address: { ...formData.address, state: e.target.value } })}
                                        maxLength={2}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>CEP</label>
                                    <input
                                        type="text"
                                        value={formData.address.postalCode}
                                        onChange={(e) => setFormData({ ...formData, address: { ...formData.address, postalCode: e.target.value } })}
                                        placeholder="00000-000"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Organização Pai (ID)</label>
                                <input
                                    type="text"
                                    value={formData.partOf}
                                    onChange={(e) => setFormData({ ...formData, partOf: e.target.value })}
                                    placeholder="ID da organização pai (opcional)"
                                />
                            </div>

                            <div className="form-actions">
                                <Button variant="secondary" type="button" onClick={() => { setShowForm(false); setFormErrors({}); }}>
                                    Cancelar
                                </Button>
                                <Button variant="primary" type="submit">
                                    {editingId ? 'Salvar' : 'Criar'}
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="organizations-list">
                {loading ? (
                    <div className="loading">Carregando...</div>
                ) : organizations.length === 0 ? (
                    <div className="empty-state">
                        <Building2 size={48} color={colors.text.muted} />
                        <p>Nenhuma organização encontrada</p>
                    </div>
                ) : (
                    organizations.map(org => (
                        <div key={org.id} className={`org-card ${!org.active ? 'inactive' : ''}`}>
                            <div className="org-header" onClick={() => toggleExpand(org.id)}>
                                <div className="org-expand-icon">
                                    {expandedOrgs.has(org.id) ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                </div>
                                <div className="org-info">
                                    <h3>{org.name}</h3>
                                    <span className="org-type">{getOrgTypeLabel(org)}</span>
                                    {!org.active && <span className="inactive-badge">Inativo</span>}
                                </div>
                                <div className="org-actions">
                                    <button className="icon-btn" onClick={(e) => { e.stopPropagation(); handleEdit(org); }} aria-label="Editar">
                                        <Edit2 size={18} />
                                    </button>
                                    <button className="icon-btn danger" onClick={(e) => { e.stopPropagation(); handleDelete(org.id); }} aria-label="Excluir">
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>

                            {expandedOrgs.has(org.id) && (
                                <div className="org-details">
                                    {getCNPJ(org) && (
                                        <div className="detail-item">
                                            <strong>CNPJ:</strong> {formatCNPJ(getCNPJ(org) || '')}
                                        </div>
                                    )}
                                    {org.telecom?.map((t, i) => (
                                        <div key={i} className="detail-item">
                                            {t.system === 'phone' && <Phone size={14} />}
                                            {t.system === 'email' && <Mail size={14} />}
                                            <span>{t.value}</span>
                                        </div>
                                    ))}
                                    {org.address?.[0] && (
                                        <div className="detail-item">
                                            <MapPin size={14} />
                                            <span>
                                                {org.address[0].line?.join(', ')}
                                                {org.address[0].city && `, ${org.address[0].city}`}
                                                {org.address[0].state && ` - ${org.address[0].state}`}
                                            </span>
                                        </div>
                                    )}
                                    {org.alias && org.alias.length > 0 && (
                                        <div className="detail-item">
                                            <strong>Também conhecido como:</strong> {org.alias.join(', ')}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default OrganizationWorkspace;

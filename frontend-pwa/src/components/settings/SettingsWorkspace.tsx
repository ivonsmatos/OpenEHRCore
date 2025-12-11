import React, { useState, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import {
    User,
    Mail,
    Phone,
    MapPin,
    Shield,
    Save,
    ArrowLeft,
    Camera,
    Upload,
    X
} from 'lucide-react';
import Button from '../base/Button';
import Card from '../base/Card';
import { colors, spacing } from '../../theme/colors';
import './SettingsWorkspace.css';

/**
 * Workspace de Configurações do Usuário
 * Permite editar perfil, segurança, notificações e preferências
 */
export const SettingsWorkspace: React.FC<{ section?: string }> = ({ section = 'profile' }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [formData, setFormData] = useState({
        name: user?.name || '',
        email: user?.email || '',
        phone: '',
        address: '',
        specialty: '',
        crm: '',
    });

    const [avatarPreview, setAvatarPreview] = useState<string | null>(user?.photo || null);
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleAvatarClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validar tipo
        if (!file.type.startsWith('image/')) {
            alert('Por favor, selecione uma imagem.');
            return;
        }

        // Validar tamanho (máx 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Imagem muito grande. Máximo 5MB.');
            return;
        }

        setAvatarFile(file);

        // Criar preview
        const reader = new FileReader();
        reader.onloadend = () => {
            setAvatarPreview(reader.result as string);
        };
        reader.readAsDataURL(file);
    };

    const handleRemoveAvatar = () => {
        setAvatarPreview(null);
        setAvatarFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleSave = async () => {
        setSaveStatus('saving');

        // Se tem arquivo de avatar, fazer upload (simulado)
        if (avatarFile) {
            console.log('Uploading avatar:', avatarFile.name);
            // TODO: Implementar upload real para backend
            // const formData = new FormData();
            // formData.append('photo', avatarFile);
            // await axios.post('/api/v1/users/photo/', formData);
        }

        // Simulando save
        await new Promise(resolve => setTimeout(resolve, 1000));
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
    };

    const renderProfileSection = () => (
        <div className="settings-section">
            <h2 className="section-title">
                <User size={20} />
                Informações Pessoais
            </h2>

            <div className="profile-header">
                <div className="avatar-upload">
                    <div className="avatar-preview" onClick={handleAvatarClick}>
                        {avatarPreview ? (
                            <img src={avatarPreview} alt="Avatar" />
                        ) : (
                            <span>{user?.name?.[0] || 'U'}</span>
                        )}
                        <div className="avatar-overlay">
                            <Camera size={24} />
                        </div>
                    </div>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                    />

                    <div className="avatar-actions">
                        <button className="avatar-change" onClick={handleAvatarClick}>
                            <Upload size={16} />
                            {avatarPreview ? 'Trocar foto' : 'Subir foto'}
                        </button>
                        {avatarPreview && (
                            <button className="avatar-remove" onClick={handleRemoveAvatar}>
                                <X size={16} />
                                Remover
                            </button>
                        )}
                    </div>

                    <p className="avatar-hint">JPG, PNG ou GIF. Máximo 5MB.</p>
                </div>
            </div>

            <div className="form-grid">
                <div className="form-group">
                    <label>Nome Completo</label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="Seu nome completo"
                    />
                </div>

                <div className="form-group">
                    <label>Email</label>
                    <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="seu@email.com"
                    />
                </div>

                <div className="form-group">
                    <label>Telefone</label>
                    <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="(11) 99999-9999"
                    />
                </div>

                <div className="form-group">
                    <label>Endereço</label>
                    <input
                        type="text"
                        value={formData.address}
                        onChange={(e) => handleInputChange('address', e.target.value)}
                        placeholder="Cidade, Estado"
                    />
                </div>
            </div>

            <h3 className="subsection-title">Informações Profissionais (FHIR Practitioner)</h3>

            <div className="form-grid">
                <div className="form-group">
                    <label>Especialidade</label>
                    <select
                        value={formData.specialty}
                        onChange={(e) => handleInputChange('specialty', e.target.value)}
                    >
                        <option value="">Selecione...</option>
                        <option value="clinica-geral">Clínica Geral</option>
                        <option value="cardiologia">Cardiologia</option>
                        <option value="pediatria">Pediatria</option>
                        <option value="ginecologia">Ginecologia</option>
                        <option value="ortopedia">Ortopedia</option>
                        <option value="neurologia">Neurologia</option>
                        <option value="psiquiatria">Psiquiatria</option>
                        <option value="dermatologia">Dermatologia</option>
                        <option value="enfermagem">Enfermagem</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>CRM/COREN</label>
                    <input
                        type="text"
                        value={formData.crm}
                        onChange={(e) => handleInputChange('crm', e.target.value)}
                        placeholder="CRM-SP 123456"
                    />
                </div>
            </div>
        </div>
    );

    const renderSecuritySection = () => (
        <div className="settings-section">
            <h2 className="section-title">
                <Shield size={20} />
                Segurança & Privacidade
            </h2>

            <Card className="security-card">
                <h3>Alterar Senha</h3>
                <div className="form-grid">
                    <div className="form-group full-width">
                        <label>Senha Atual</label>
                        <input type="password" placeholder="••••••••" />
                    </div>
                    <div className="form-group">
                        <label>Nova Senha</label>
                        <input type="password" placeholder="••••••••" />
                    </div>
                    <div className="form-group">
                        <label>Confirmar Nova Senha</label>
                        <input type="password" placeholder="••••••••" />
                    </div>
                </div>
                <Button variant="secondary">Alterar Senha</Button>
            </Card>

            <Card className="security-card">
                <h3>Autenticação de Dois Fatores</h3>
                <p className="muted-text">Adicione uma camada extra de segurança à sua conta</p>
                <div className="toggle-row">
                    <span>2FA via Autenticador</span>
                    <label className="toggle">
                        <input type="checkbox" />
                        <span className="slider"></span>
                    </label>
                </div>
            </Card>

            <Card className="security-card">
                <h3>Sessões Ativas</h3>
                <p className="muted-text">Gerencie os dispositivos conectados à sua conta</p>
                <div className="session-list">
                    <div className="session-item">
                        <div>
                            <strong>Chrome - Windows</strong>
                            <span className="session-info">São Paulo, Brasil • Agora</span>
                        </div>
                        <span className="session-badge active">Atual</span>
                    </div>
                </div>
            </Card>
        </div>
    );

    const renderNotificationsSection = () => (
        <div className="settings-section">
            <h2 className="section-title">
                <Mail size={20} />
                Notificações
            </h2>

            <Card className="notification-card">
                <h3>Email</h3>
                <div className="toggle-list">
                    <div className="toggle-row">
                        <div>
                            <span className="toggle-label">Novos agendamentos</span>
                            <span className="toggle-desc">Receba email quando um paciente agendar consulta</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" defaultChecked />
                            <span className="slider"></span>
                        </label>
                    </div>
                    <div className="toggle-row">
                        <div>
                            <span className="toggle-label">Resultados de exames</span>
                            <span className="toggle-desc">Notificações sobre novos laudos</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" defaultChecked />
                            <span className="slider"></span>
                        </label>
                    </div>
                    <div className="toggle-row">
                        <div>
                            <span className="toggle-label">Newsletter</span>
                            <span className="toggle-desc">Atualizações e novidades do sistema</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" />
                            <span className="slider"></span>
                        </label>
                    </div>
                </div>
            </Card>

            <Card className="notification-card">
                <h3>Push</h3>
                <div className="toggle-list">
                    <div className="toggle-row">
                        <div>
                            <span className="toggle-label">Alertas de emergência</span>
                            <span className="toggle-desc">Notificações críticas do sistema</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" defaultChecked />
                            <span className="slider"></span>
                        </label>
                    </div>
                    <div className="toggle-row">
                        <div>
                            <span className="toggle-label">Chat</span>
                            <span className="toggle-desc">Mensagens de equipe médica</span>
                        </div>
                        <label className="toggle">
                            <input type="checkbox" defaultChecked />
                            <span className="slider"></span>
                        </label>
                    </div>
                </div>
            </Card>
        </div>
    );

    const renderPreferencesSection = () => (
        <div className="settings-section">
            <h2 className="section-title">
                <MapPin size={20} />
                Preferências
            </h2>

            <Card className="preference-card">
                <h3>Aparência</h3>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Tema</label>
                        <select defaultValue="light">
                            <option value="light">Claro</option>
                            <option value="dark">Escuro</option>
                            <option value="system">Sistema</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Tamanho da Fonte</label>
                        <select defaultValue="medium">
                            <option value="small">Pequena</option>
                            <option value="medium">Média</option>
                            <option value="large">Grande</option>
                        </select>
                    </div>
                </div>
            </Card>

            <Card className="preference-card">
                <h3>Regional</h3>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Idioma</label>
                        <select defaultValue="pt-BR">
                            <option value="pt-BR">Português (Brasil)</option>
                            <option value="en-US">English (US)</option>
                            <option value="es">Español</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Formato de Data</label>
                        <select defaultValue="DD/MM/YYYY">
                            <option value="DD/MM/YYYY">DD/MM/AAAA</option>
                            <option value="MM/DD/YYYY">MM/DD/AAAA</option>
                            <option value="YYYY-MM-DD">AAAA-MM-DD</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Fuso Horário</label>
                        <select defaultValue="America/Sao_Paulo">
                            <option value="America/Sao_Paulo">São Paulo (GMT-3)</option>
                            <option value="America/Manaus">Manaus (GMT-4)</option>
                            <option value="America/Noronha">Fernando de Noronha (GMT-2)</option>
                        </select>
                    </div>
                </div>
            </Card>
        </div>
    );

    const renderContent = () => {
        switch (section) {
            case 'security':
                return renderSecuritySection();
            case 'notifications':
                return renderNotificationsSection();
            case 'preferences':
                return renderPreferencesSection();
            default:
                return renderProfileSection();
        }
    };

    const menuItems = [
        { id: 'profile', label: 'Perfil', icon: <User size={18} /> },
        { id: 'security', label: 'Segurança', icon: <Shield size={18} /> },
        { id: 'notifications', label: 'Notificações', icon: <Mail size={18} /> },
        { id: 'preferences', label: 'Preferências', icon: <MapPin size={18} /> },
    ];

    return (
        <div className="settings-workspace">
            <div className="settings-header">
                <button className="back-button" onClick={() => navigate(-1)}>
                    <ArrowLeft size={20} />
                    Voltar
                </button>
                <h1>Configurações</h1>
            </div>

            <div className="settings-layout">
                <aside className="settings-sidebar">
                    {menuItems.map(item => (
                        <button
                            key={item.id}
                            className={`sidebar-item ${section === item.id ? 'active' : ''}`}
                            onClick={() => navigate(`/settings/${item.id}`)}
                        >
                            {item.icon}
                            {item.label}
                        </button>
                    ))}
                </aside>

                <main className="settings-content">
                    {renderContent()}

                    <div className="settings-actions">
                        <Button
                            onClick={handleSave}
                            disabled={saveStatus === 'saving'}
                        >
                            <Save size={16} />
                            {saveStatus === 'saving' ? 'Salvando...' :
                                saveStatus === 'saved' ? 'Salvo!' : 'Salvar Alterações'}
                        </Button>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default SettingsWorkspace;

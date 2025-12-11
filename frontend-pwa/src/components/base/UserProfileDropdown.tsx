import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    User,
    LogOut,
    UserCircle,
    Shield,
    Bell,
    Moon,
    HelpCircle,
    ChevronDown
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import './UserProfileDropdown.css';

interface UserProfileDropdownProps {
    compact?: boolean;
}

export const UserProfileDropdown: React.FC<UserProfileDropdownProps> = ({ compact = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    // Fechar dropdown ao clicar fora
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleMenuClick = (action: string) => {
        setIsOpen(false);

        switch (action) {
            case 'profile':
                navigate('/profile');
                break;
            case 'practitioner':
                // Navega para o Practitioner FHIR do usuário logado
                if (user?.practitionerId) {
                    navigate(`/practitioners/${user.practitionerId}`);
                } else {
                    navigate('/practitioners');
                }
                break;
            case 'preferences':
                navigate('/settings/preferences');
                break;
            case 'security':
                navigate('/settings/security');
                break;
            case 'notifications':
                navigate('/settings/notifications');
                break;
            case 'help':
                navigate('/help');
                break;
            case 'logout':
                logout();
                break;
            default:
                break;
        }
    };

    const menuItems = [
        {
            icon: <UserCircle size={18} />,
            label: 'Meu Perfil FHIR',
            action: 'practitioner',
            description: 'Recurso Practitioner'
        },
        {
            icon: <User size={18} />,
            label: 'Configurações de Conta',
            action: 'profile',
            description: 'Nome, email, senha'
        },
        { divider: true },
        {
            icon: <Shield size={18} />,
            label: 'Segurança & Privacidade',
            action: 'security',
            description: 'Autenticação, acessos'
        },
        {
            icon: <Bell size={18} />,
            label: 'Notificações',
            action: 'notifications',
            description: 'Alertas, lembretes'
        },
        {
            icon: <Moon size={18} />,
            label: 'Preferências',
            action: 'preferences',
            description: 'Tema, idioma, formato'
        },
        { divider: true },
        {
            icon: <HelpCircle size={18} />,
            label: 'Ajuda & Suporte',
            action: 'help',
            description: 'Documentação, FAQ'
        },
        {
            icon: <LogOut size={18} />,
            label: 'Sair',
            action: 'logout',
            danger: true
        },
    ];

    const getUserInitials = (): string => {
        if (!user?.name) return 'U';
        const parts = user.name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        }
        return parts[0][0].toUpperCase();
    };

    const getRoleLabel = (): string => {
        const role = user?.roles?.[0];
        const roleLabels: Record<string, string> = {
            'admin': 'Administrador',
            'doctor': 'Médico',
            'medico': 'Médico',
            'nurse': 'Enfermeiro(a)',
            'receptionist': 'Recepcionista',
            'staff': 'Colaborador'
        };
        return roleLabels[role?.toLowerCase() || ''] || role || 'Staff';
    };

    return (
        <div className="user-profile-dropdown" ref={dropdownRef}>
            <button
                className={`profile-trigger ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-expanded={isOpen ? 'true' : 'false'}
                aria-haspopup="true"
            >
                <div className="avatar">
                    {user?.photo ? (
                        <img src={user.photo} alt={user.name || 'Avatar'} />
                    ) : (
                        <span className="initials">{getUserInitials()}</span>
                    )}
                </div>

                {!compact && (
                    <div className="user-info">
                        <span className="user-name">{user?.name || 'Usuário'}</span>
                        <span className="user-role">{getRoleLabel()}</span>
                    </div>
                )}

                <ChevronDown
                    size={16}
                    className={`chevron ${isOpen ? 'rotated' : ''}`}
                />
            </button>

            {isOpen && (
                <div className="dropdown-menu">
                    {/* Header do dropdown */}
                    <div className="dropdown-header">
                        <div className="avatar-large">
                            {user?.photo ? (
                                <img src={user.photo} alt={user.name || 'Avatar'} />
                            ) : (
                                <span className="initials">{getUserInitials()}</span>
                            )}
                        </div>
                        <div className="header-info">
                            <span className="header-name">{user?.name || 'Usuário'}</span>
                            <span className="header-email">{user?.email || ''}</span>
                            <span className="header-role">{getRoleLabel()}</span>
                        </div>
                    </div>

                    {/* Menu items */}
                    <div className="dropdown-items">
                        {menuItems.map((item, index) => (
                            item.divider ? (
                                <div key={index} className="divider" />
                            ) : (
                                <button
                                    key={item.action}
                                    className={`menu-item ${item.danger ? 'danger' : ''}`}
                                    onClick={() => handleMenuClick(item.action!)}
                                >
                                    <span className="item-icon">{item.icon}</span>
                                    <div className="item-content">
                                        <span className="item-label">{item.label}</span>
                                        {item.description && (
                                            <span className="item-description">{item.description}</span>
                                        )}
                                    </div>
                                </button>
                            )
                        ))}
                    </div>

                    {/* Footer com versão */}
                    <div className="dropdown-footer">
                        <span>OpenEHRCore v1.0 • FHIR R4</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserProfileDropdown;

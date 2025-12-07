
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Users,
    Calendar,
    DollarSign,
    FileText,
    LogOut,
    Activity,
    Menu,
    UserPlus,
    MessageSquare,
    Bed,
    Stethoscope
} from 'lucide-react';
import { colors, spacing } from '../../theme/colors';
import { useAuth } from '../../hooks/useAuth';

interface SidebarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, toggleSidebar }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();
    const path = location.pathname;

    const menuItems = [
        { label: 'Dashboard', icon: <LayoutDashboard size={20} />, route: '/' },
        { label: 'Pacientes', icon: <Users size={20} />, route: '/patients' },
        { label: 'Profissionais', icon: <Stethoscope size={20} />, route: '/practitioners' },
        { label: 'Agenda', icon: <Calendar size={20} />, route: '/scheduling' },
        { label: 'Check-in', icon: <Activity size={20} />, route: '/checkin' },
        { label: 'Internação', icon: <Bed size={20} />, route: '/ipd' },
        { label: 'Financeiro', icon: <DollarSign size={20} />, route: '/finance' },

        { label: 'Documentos', icon: <FileText size={20} />, route: '/documents' },
        { label: 'Visitantes', icon: <UserPlus size={20} />, route: '/visitors' },
        { label: 'Chat', icon: <MessageSquare size={20} />, route: '/chat' },
        { label: 'Portal Paciente', icon: <Users size={20} />, route: '/portal' }, // Demo link
    ];

    return (
        <aside style={{
            backgroundColor: 'white',
            width: isOpen ? '260px' : '70px',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            borderRight: `1px solid ${colors.border.default}`,
            transition: 'width 0.3s ease',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            boxShadow: '4px 0 12px rgba(0,0,0,0.02)'
        }}>
            {/* Header do Sidebar */}
            <div style={{
                height: '64px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: isOpen ? 'space-between' : 'center',
                padding: isOpen ? `0 ${spacing.md}` : '0',
                borderBottom: `1px solid ${colors.border.default}`,
            }}>
                {isOpen && (
                    <div style={{ fontWeight: 'bold', fontSize: '1.25rem', color: colors.primary.dark, display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Activity size={24} color={colors.primary.medium} />
                        <span>OpenEHR</span>
                    </div>
                )}
                <button
                    onClick={toggleSidebar}
                    style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: colors.text.secondary,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '8px',
                        borderRadius: '4px',
                    }}
                >
                    <Menu size={20} />
                </button>
            </div>

            {/* Menu Navigation */}
            <nav style={{ flex: 1, padding: `${spacing.md} 0`, overflowY: 'auto' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {menuItems.map((item) => {
                        const isActive = path === item.route || (item.route !== '/' && path.startsWith(item.route));

                        return (
                            <li key={item.route} style={{ marginBottom: '4px', padding: `0 ${spacing.sm}` }}>
                                <button
                                    onClick={() => navigate(item.route)}
                                    title={!isOpen ? item.label : ''}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: isOpen ? 'flex-start' : 'center',
                                        padding: isOpen ? '12px 16px' : '12px',
                                        backgroundColor: isActive ? `${colors.primary.medium}15` : 'transparent',
                                        color: isActive ? colors.primary.dark : colors.text.secondary,
                                        border: 'none',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                        fontWeight: isActive ? 600 : 400,
                                        gap: isOpen ? '12px' : '0'
                                    }}
                                >
                                    {React.cloneElement(item.icon as React.ReactElement, { color: isActive ? colors.primary.medium : 'currentColor' })}
                                    {isOpen && <span>{item.label}</span>}
                                </button>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Footer / User Profile */}
            <div style={{
                padding: spacing.md,
                borderTop: `1px solid ${colors.border.default}`,
            }}>
                <button
                    onClick={logout}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: isOpen ? 'flex-start' : 'center',
                        padding: '12px',
                        backgroundColor: 'transparent',
                        color: colors.alert.critical,
                        border: `1px solid ${isOpen ? `${colors.alert.critical}30` : 'transparent'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        gap: isOpen ? '12px' : '0',
                        transition: 'all 0.2s'
                    }}
                >
                    <LogOut size={20} />
                    {isOpen && <span>Sair</span>}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;

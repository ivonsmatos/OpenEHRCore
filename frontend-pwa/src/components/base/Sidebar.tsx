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
    Stethoscope,
    Building2,
    Zap
} from 'lucide-react';
import { colors, spacing } from '../../theme/colors';
import { useAuth } from '../../hooks/useAuth';

interface SidebarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
    isMobile?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, toggleSidebar, isMobile = false }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();
    const path = location.pathname;

    const menuItems = [
        { label: 'Dashboard', icon: <LayoutDashboard size={20} />, route: '/' },
        { label: 'Pacientes', icon: <Users size={20} />, route: '/patients' },
        { label: 'Profissionais', icon: <Stethoscope size={20} />, route: '/practitioners' },
        { label: 'Organizações', icon: <Building2 size={20} />, route: '/organizations' },
        { label: 'Agenda', icon: <Calendar size={20} />, route: '/scheduling' },
        { label: 'Check-in', icon: <Activity size={20} />, route: '/checkin' },
        { label: 'Internação', icon: <Bed size={20} />, route: '/ipd' },
        { label: 'Prescrições', icon: <FileText size={20} />, route: '/prescriptions' },
        { label: 'Financeiro', icon: <DollarSign size={20} />, route: '/finance' },
        { label: 'Automações', icon: <Zap size={20} />, route: '/automation' },
        { label: 'Documentos', icon: <FileText size={20} />, route: '/documents' },
        { label: 'Visitantes', icon: <UserPlus size={20} />, route: '/visitors' },
        { label: 'Chat', icon: <MessageSquare size={20} />, route: '/chat' },
        { label: 'Portal Paciente', icon: <Users size={20} />, route: '/portal' },
    ];

    return (
        <aside style={{
            backgroundColor: 'white',
            width: isMobile ? (isOpen ? '80%' : '0') : (isOpen ? '260px' : '70px'),
            maxWidth: isMobile ? '300px' : 'none',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            borderRight: `1px solid ${colors.border.default}`,
            transition: 'width 0.3s ease, transform 0.3s ease',
            transform: isMobile ? (isOpen ? 'translateX(0)' : 'translateX(-100%)') : 'translateX(0)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            boxShadow: isMobile ? '4px 0 20px rgba(0,0,0,0.15)' : '4px 0 12px rgba(0,0,0,0.02)',
            overflowX: 'hidden'
        }}>
            {/* Header do Sidebar */}
            <div style={{
                height: '64px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: (isOpen || isMobile) ? 'space-between' : 'center',
                padding: (isOpen || isMobile) ? `0 ${spacing.md}` : '0',
                borderBottom: `1px solid ${colors.border.default}`,
            }}>
                {(isOpen || isMobile) && (
                    <div style={{ fontWeight: 'bold', fontSize: '1.25rem', color: colors.primary.dark, display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Activity size={24} color={colors.primary.medium} />
                        <span>OpenEHR</span>
                    </div>
                )}
                {!isMobile && (
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
                )}
            </div>

            {/* Menu Navigation */}
            <nav style={{ flex: 1, padding: `${spacing.md} 0`, overflowY: 'auto' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {menuItems.map((item) => {
                        const isActive = path === item.route || (item.route !== '/' && path.startsWith(item.route));

                        return (
                            <li key={item.route} style={{ marginBottom: '4px', padding: `0 ${spacing.sm}` }}>
                                <button
                                    onClick={() => {
                                        navigate(item.route);
                                        if (isMobile) toggleSidebar(); // Close sidebar on mobile after navigation
                                    }}
                                    title={(!isOpen && !isMobile) ? item.label : ''}
                                    style={{
                                        width: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: (isOpen || isMobile) ? 'flex-start' : 'center',
                                        padding: (isOpen || isMobile) ? '12px 16px' : '12px',
                                        backgroundColor: isActive ? `${colors.primary.medium}15` : 'transparent',
                                        color: isActive ? colors.primary.dark : colors.text.secondary,
                                        border: 'none',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                        fontWeight: isActive ? 600 : 400,
                                        gap: (isOpen || isMobile) ? '12px' : '0',
                                        fontSize: isMobile ? '0.95rem' : '1rem'
                                    }}
                                >
                                    {React.cloneElement(item.icon as React.ReactElement, { color: isActive ? colors.primary.medium : 'currentColor' })}
                                    {(isOpen || isMobile) && <span>{item.label}</span>}
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
                        justifyContent: (isOpen || isMobile) ? 'flex-start' : 'center',
                        padding: '12px',
                        backgroundColor: 'transparent',
                        color: colors.alert.critical,
                        border: `1px solid ${(isOpen || isMobile) ? `${colors.alert.critical}30` : 'transparent'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        gap: (isOpen || isMobile) ? '12px' : '0',
                        transition: 'all 0.2s'
                    }}
                >
                    <LogOut size={20} />
                    {(isOpen || isMobile) && <span>Sair</span>}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;

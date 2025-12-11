
import React, { useState } from 'react';
import Sidebar from './Sidebar';
import { colors, spacing } from '../../theme/colors';
import { Search, Bell } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Breadcrumbs from './Breadcrumbs';
import { UserProfileDropdown } from './UserProfileDropdown';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: colors.background.surface }}>
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Content Area */}
      <div style={{
        flex: 1,
        marginLeft: sidebarOpen ? '260px' : '70px',
        transition: 'margin-left 0.3s ease',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* TopBar / Header */}
        <header style={{
          height: '64px',
          backgroundColor: 'white',
          borderBottom: `1px solid ${colors.border.default}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: `0 ${spacing.xl}`,
          position: 'sticky',
          top: 0,
          zIndex: 900
        }}>
          {/* Global Search (Placeholder for future) */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: colors.background.surface,
            padding: '8px 16px',
            borderRadius: '20px',
            width: '300px',
            gap: '8px',
            border: `1px solid ${colors.border.default}`
          }}>
            <Search size={16} color={colors.text.tertiary} />
            <input
              type="text"
              placeholder="Buscar pacientes, prontuários..."
              style={{
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: '0.9rem',
                width: '100%',
                color: colors.text.primary
              }}
            />
          </div>

          {/* Right Actions: Notifications & Profile */}
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing.lg }}>
            <button style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              position: 'relative',
              color: colors.text.secondary
            }}>
              <Bell size={20} />
              <span style={{
                position: 'absolute',
                top: -2,
                right: -2,
                width: '8px',
                height: '8px',
                backgroundColor: colors.alert.critical,
                borderRadius: '50%'
              }} />
            </button>

            {/* User Profile Dropdown */}
            <UserProfileDropdown />
          </div>
        </header>

        {/* Content Body */}
        <main style={{
          padding: spacing.xl,
          flex: 1,
          maxWidth: '1600px', // Wider layout for dashboard look
          width: '100%',
          margin: '0 auto'
        }}>
          <Breadcrumbs />
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;

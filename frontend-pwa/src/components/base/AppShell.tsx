
import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { colors, spacing } from '../../theme/colors';
import { Search, Bell, Menu } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Breadcrumbs from './Breadcrumbs';
import { UserProfileDropdown } from './UserProfileDropdown';
import { useIsMobile, useIsTabletOrBelow } from '../../hooks/useMediaQuery';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const isMobile = useIsMobile();
  const isTabletOrBelow = useIsTabletOrBelow();
  const [sidebarOpen, setSidebarOpen] = useState(!isTabletOrBelow);
  useAuth(); // Keep hook for auth state

  // Close sidebar on mobile by default and when switching to mobile
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile]);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: colors.background.surface }}>
      {/* Sidebar Navigation */}
      <Sidebar 
        isOpen={sidebarOpen} 
        toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        isMobile={isMobile}
      />

      {/* Overlay for mobile when sidebar is open */}
      {isMobile && sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
            animation: 'fadeIn 0.2s ease'
          }}
        />
      )}

      {/* Main Content Area */}
      <div style={{
        flex: 1,
        marginLeft: isMobile ? '0' : (sidebarOpen ? '260px' : '70px'),
        transition: 'margin-left 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0 // Prevent flex overflow
      }}>
        {/* TopBar / Header */}
        <header style={{
          height: isMobile ? '56px' : '64px',
          backgroundColor: 'white',
          borderBottom: `1px solid ${colors.border.default}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? `0 ${spacing.md}` : `0 ${spacing.xl}`,
          position: 'sticky',
          top: 0,
          zIndex: 900
        }}>
          {/* Left side: Mobile menu + Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, flex: isMobile ? 1 : 'initial' }}>
            {/* Mobile Hamburger Menu */}
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: colors.text.secondary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: spacing.xs
                }}
              >
                <Menu size={24} />
              </button>
            )}

            {/* Global Search */}
            {!isMobile && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: colors.background.surface,
                padding: '8px 16px',
                borderRadius: '20px',
                width: isTabletOrBelow ? '200px' : '300px',
                gap: '8px',
                border: `1px solid ${colors.border.default}`
              }}>
                <Search size={16} color={colors.text.tertiary} />
                <input
                  type="text"
                  placeholder={isTabletOrBelow ? "Buscar..." : "Buscar pacientes, prontuários..."}
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
            )}
          </div>

          {/* Right Actions: Notifications & Profile */}
          <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? spacing.sm : spacing.lg }}>
            <button style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              position: 'relative',
              color: colors.text.secondary,
              padding: spacing.xs
            }}>
              <Bell size={isMobile ? 20 : 22} />
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
          padding: isMobile ? spacing.md : (isTabletOrBelow ? spacing.lg : spacing.xl),
          flex: 1,
          maxWidth: '1600px',
          width: '100%',
          margin: '0 auto',
          overflow: 'hidden', // Prevent horizontal scroll
          boxSizing: 'border-box'
        }}>
          <Breadcrumbs />
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;

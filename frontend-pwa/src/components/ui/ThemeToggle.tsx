/**
 * Theme Toggle Component
 * Sprint 28: UX Improvement
 */

import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import './ThemeToggle.css';

interface ThemeToggleProps {
    showLabel?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
    showLabel = false,
    size = 'md'
}) => {
    const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleTheme();
        }
    };

    return (
        <div className={`theme-toggle theme-toggle--${size}`}>
            <button
                className="theme-toggle__button"
                onClick={toggleTheme}
                onKeyDown={handleKeyDown}
                aria-label={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
                aria-pressed={resolvedTheme === 'dark'}
                title={`Current: ${resolvedTheme} mode. Click to toggle.`}
            >
                <span className="theme-toggle__icon theme-toggle__icon--sun" aria-hidden="true">
                    ☀️
                </span>
                <span className="theme-toggle__icon theme-toggle__icon--moon" aria-hidden="true">
                    🌙
                </span>
                <span className="theme-toggle__slider" />
            </button>

            {showLabel && (
                <span className="theme-toggle__label">
                    {resolvedTheme === 'dark' ? 'Dark' : 'Light'}
                </span>
            )}
        </div>
    );
};

// Theme selector dropdown for more options
export const ThemeSelector: React.FC = () => {
    const { theme, setTheme } = useTheme();

    return (
        <div className="theme-selector">
            <label htmlFor="theme-select" className="theme-selector__label">
                Theme
            </label>
            <select
                id="theme-select"
                className="theme-selector__select"
                value={theme}
                onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
            >
                <option value="light">☀️ Light</option>
                <option value="dark">🌙 Dark</option>
                <option value="system">💻 System</option>
            </select>
        </div>
    );
};

export default ThemeToggle;


import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { colors, spacing } from '../../theme/colors';

const routeNameMap: Record<string, string> = {
    'patients': 'Pacientes',
    'practitioners': 'Profissionais',
    'scheduling': 'Agenda',
    'checkin': 'Check-in',
    'finance': 'Financeiro',
    'documents': 'Documentos',
    'portal': 'Portal do Paciente',
    'new': 'Novo Cadastro',
    'edit': 'Editar',
    'audit': 'Auditoria',
};

// Helper to check if a segment is an ID (simple check: length > 2 and mixed/numbers)
const isId = (segment: string) => {
    // If segment is in the route map, it's a route name, not an ID
    if (routeNameMap[segment]) return false;
    // Check if it's a number or a short alphanumeric string (UUIDs, etc)
    return !isNaN(Number(segment)) || (segment.length <= 36 && /^[a-zA-Z0-9-]+$/.test(segment) && segment.length < 15);
};

const Breadcrumbs: React.FC = () => {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter((x) => x);

    // Don't show on dashboard/home
    if (pathnames.length === 0) return null;

    return (
        <nav style={{
            display: 'flex',
            alignItems: 'center',
            fontSize: '0.85rem',
            color: colors.text.tertiary,
            marginBottom: spacing.md,
            padding: `${spacing.sm} ${spacing.md}`,
            // background: 'white', // Optional: could be inside a card
            // borderRadius: '8px'
        }}>
            <Link to="/" style={{ display: 'flex', alignItems: 'center', color: colors.text.secondary, textDecoration: 'none' }}>
                <Home size={16} />
            </Link>

            {pathnames.map((value, index) => {
                const last = index === pathnames.length - 1;
                const to = `/${pathnames.slice(0, index + 1).join('/')}`;
                const previousSegment = index > 0 ? pathnames[index - 1] : null;

                // Resolve display name
                let displayName = routeNameMap[value] || value;
                
                // If current segment is an ID and previous is a known route, skip showing it
                // (to avoid "Profissionais > Profissionais" or similar duplications)
                if (isId(value) && previousSegment && routeNameMap[previousSegment]) {
                    // Only show this breadcrumb if it's a sub-action like 'edit', 'new', etc.
                    // Otherwise, the parent name is enough context
                    return null;
                }

                return (
                    <React.Fragment key={to}>
                        <ChevronRight size={14} style={{ margin: '0 8px' }} />
                        {last ? (
                            <span style={{ fontWeight: 600, color: colors.primary.dark }}>
                                {displayName}
                            </span>
                        ) : (
                            <Link to={to} style={{ color: colors.text.secondary, textDecoration: 'none' }}>
                                {displayName}
                            </Link>
                        )}
                    </React.Fragment>
                );
            })}
        </nav>
    );
};

export default Breadcrumbs;

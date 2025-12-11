/**
 * useRBAC - Role-Based Access Control Hook
 * 
 * Provides RBAC functionality for controlling access to features
 * based on user roles and permissions.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './useAuth';

// Role definitions
export type Role =
    | 'admin'           // Full access
    | 'doctor'          // Clinical access
    | 'nurse'           // Limited clinical access
    | 'receptionist'    // Scheduling/administrative
    | 'patient'         // Patient portal access
    | 'viewer';         // Read-only access

// Permission definitions
export type Permission =
    // Patient management
    | 'patients:read'
    | 'patients:write'
    | 'patients:delete'
    // Clinical data
    | 'clinical:read'
    | 'clinical:write'
    | 'clinical:sign'    // Sign off on clinical documents
    // Prescriptions
    | 'prescriptions:read'
    | 'prescriptions:write'
    // Scheduling
    | 'schedule:read'
    | 'schedule:write'
    | 'schedule:manage'  // Manage availability
    // Administration
    | 'users:read'
    | 'users:write'
    | 'settings:read'
    | 'settings:write'
    // Audit
    | 'audit:read'
    // Reports
    | 'reports:read'
    | 'reports:export';

// Role-Permission mapping
const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
    admin: [
        'patients:read', 'patients:write', 'patients:delete',
        'clinical:read', 'clinical:write', 'clinical:sign',
        'prescriptions:read', 'prescriptions:write',
        'schedule:read', 'schedule:write', 'schedule:manage',
        'users:read', 'users:write',
        'settings:read', 'settings:write',
        'audit:read',
        'reports:read', 'reports:export'
    ],
    doctor: [
        'patients:read', 'patients:write',
        'clinical:read', 'clinical:write', 'clinical:sign',
        'prescriptions:read', 'prescriptions:write',
        'schedule:read', 'schedule:write', 'schedule:manage',
        'reports:read', 'reports:export'
    ],
    nurse: [
        'patients:read', 'patients:write',
        'clinical:read', 'clinical:write',
        'prescriptions:read',
        'schedule:read',
        'reports:read'
    ],
    receptionist: [
        'patients:read', 'patients:write',
        'schedule:read', 'schedule:write',
        'reports:read'
    ],
    patient: [
        'patients:read',
        'clinical:read',
        'prescriptions:read',
        'schedule:read'
    ],
    viewer: [
        'patients:read',
        'clinical:read',
        'schedule:read'
    ]
};

// Role hierarchy - higher roles inherit permissions from lower roles
const ROLE_HIERARCHY: Record<Role, number> = {
    viewer: 1,
    patient: 2,
    receptionist: 3,
    nurse: 4,
    doctor: 5,
    admin: 6
};

interface UseRBACReturn {
    // User's current role
    role: Role | null;
    // All permissions the user has
    permissions: Permission[];
    // Check if user has a specific permission
    hasPermission: (permission: Permission) => boolean;
    // Check if user has any of the listed permissions
    hasAnyPermission: (permissions: Permission[]) => boolean;
    // Check if user has all listed permissions
    hasAllPermissions: (permissions: Permission[]) => boolean;
    // Check if user's role is at least the specified level
    hasRoleLevel: (role: Role) => boolean;
    // Check if user can perform an action on a resource
    canAccess: (resource: string, action: 'read' | 'write' | 'delete') => boolean;
    // Loading state
    loading: boolean;
}

export const useRBAC = (): UseRBACReturn => {
    const { token, user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [role, setRole] = useState<Role | null>(null);

    useEffect(() => {
        if (!token || !user) {
            setRole(null);
            setLoading(false);
            return;
        }

        // Extract role from Keycloak token claims
        // In production, this would come from the JWT token's realm_access.roles
        const extractedRole = extractRoleFromUser(user);
        setRole(extractedRole);
        setLoading(false);
    }, [token, user]);

    // Get all permissions for current role
    const permissions = useMemo<Permission[]>(() => {
        if (!role) return [];
        return ROLE_PERMISSIONS[role] || [];
    }, [role]);

    // Check single permission
    const hasPermission = useCallback((permission: Permission): boolean => {
        return permissions.includes(permission);
    }, [permissions]);

    // Check any permission
    const hasAnyPermission = useCallback((perms: Permission[]): boolean => {
        return perms.some(p => permissions.includes(p));
    }, [permissions]);

    // Check all permissions
    const hasAllPermissions = useCallback((perms: Permission[]): boolean => {
        return perms.every(p => permissions.includes(p));
    }, [permissions]);

    // Check role hierarchy level
    const hasRoleLevel = useCallback((requiredRole: Role): boolean => {
        if (!role) return false;
        return ROLE_HIERARCHY[role] >= ROLE_HIERARCHY[requiredRole];
    }, [role]);

    // Check resource access
    const canAccess = useCallback((resource: string, action: 'read' | 'write' | 'delete'): boolean => {
        const resourceMap: Record<string, Record<'read' | 'write' | 'delete', Permission>> = {
            patients: { read: 'patients:read', write: 'patients:write', delete: 'patients:delete' },
            clinical: { read: 'clinical:read', write: 'clinical:write', delete: 'clinical:write' },
            prescriptions: { read: 'prescriptions:read', write: 'prescriptions:write', delete: 'prescriptions:write' },
            schedule: { read: 'schedule:read', write: 'schedule:write', delete: 'schedule:manage' },
            users: { read: 'users:read', write: 'users:write', delete: 'users:write' },
            settings: { read: 'settings:read', write: 'settings:write', delete: 'settings:write' },
        };

        const resourcePerms = resourceMap[resource];
        if (!resourcePerms) return false;

        const requiredPerm = resourcePerms[action];
        return hasPermission(requiredPerm);
    }, [hasPermission]);

    return {
        role,
        permissions,
        hasPermission,
        hasAnyPermission,
        hasAllPermissions,
        hasRoleLevel,
        canAccess,
        loading
    };
};

// Helper to extract role from user object
function extractRoleFromUser(user: any): Role {
    // Check Keycloak realm_access.roles
    const roles = user?.realm_access?.roles || user?.roles || [];

    // Match against known roles in priority order
    if (roles.includes('admin') || roles.includes('administrator')) return 'admin';
    if (roles.includes('doctor') || roles.includes('medico') || roles.includes('physician')) return 'doctor';
    if (roles.includes('nurse') || roles.includes('enfermeiro')) return 'nurse';
    if (roles.includes('receptionist') || roles.includes('recepcionista')) return 'receptionist';
    if (roles.includes('patient') || roles.includes('paciente')) return 'patient';

    // Default to viewer for authenticated users without specific roles
    return 'viewer';
}

export default useRBAC;

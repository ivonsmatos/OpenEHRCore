/**
 * PermissionGate - Component for conditional rendering based on permissions
 * 
 * Wraps content and only renders it if the user has the required permissions.
 * Can show a fallback or nothing if permission is denied.
 */
import React from 'react';
import { useRBAC, Permission, Role } from '../../hooks/useRBAC';

interface PermissionGateProps {
    /** Required permission(s) to view the content */
    permissions?: Permission | Permission[];
    /** Require ALL permissions instead of ANY (default: false = ANY) */
    requireAll?: boolean;
    /** Required minimum role level */
    role?: Role;
    /** Content to render if permission is granted */
    children: React.ReactNode;
    /** Fallback content if permission is denied (optional) */
    fallback?: React.ReactNode;
    /** Show nothing instead of fallback when denied (default: true) */
    hideOnDeny?: boolean;
}

/**
 * PermissionGate - Controle de acesso baseado em permissões
 * 
 * @example
 * // Single permission
 * <PermissionGate permissions="patients:write">
 *   <Button>Editar Paciente</Button>
 * </PermissionGate>
 * 
 * @example
 * // Multiple permissions (ANY)
 * <PermissionGate permissions={['clinical:write', 'prescriptions:write']}>
 *   <ClinicalForm />
 * </PermissionGate>
 * 
 * @example
 * // Multiple permissions (ALL required)
 * <PermissionGate permissions={['clinical:write', 'clinical:sign']} requireAll>
 *   <SignOffButton />
 * </PermissionGate>
 * 
 * @example
 * // Role-based
 * <PermissionGate role="doctor">
 *   <PrescriptionPanel />
 * </PermissionGate>
 * 
 * @example
 * // With fallback
 * <PermissionGate permissions="reports:export" fallback={<p>Sem permissão</p>}>
 *   <ExportButton />
 * </PermissionGate>
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
    permissions,
    requireAll = false,
    role,
    children,
    fallback = null,
    hideOnDeny = true
}) => {
    const { hasPermission, hasAnyPermission, hasAllPermissions, hasRoleLevel, loading } = useRBAC();

    // While loading, don't render anything
    if (loading) {
        return null;
    }

    let hasAccess = true;

    // Check permissions if provided
    if (permissions) {
        const permArray = Array.isArray(permissions) ? permissions : [permissions];

        if (requireAll) {
            hasAccess = hasAllPermissions(permArray);
        } else {
            hasAccess = permArray.length === 1
                ? hasPermission(permArray[0])
                : hasAnyPermission(permArray);
        }
    }

    // Check role if provided (in addition to permissions)
    if (role && hasAccess) {
        hasAccess = hasRoleLevel(role);
    }

    // Render based on access
    if (hasAccess) {
        return <>{children}</>;
    }

    // Access denied
    if (hideOnDeny) {
        return null;
    }

    return <>{fallback}</>;
};

/**
 * Higher-order component version of PermissionGate
 */
export function withPermission<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    permissions: Permission | Permission[],
    options?: { requireAll?: boolean; role?: Role; fallback?: React.ReactNode }
) {
    return function WithPermissionComponent(props: P) {
        return (
            <PermissionGate
                permissions={permissions}
                requireAll={options?.requireAll}
                role={options?.role}
                fallback={options?.fallback}
            >
                <WrappedComponent {...props} />
            </PermissionGate>
        );
    };
}

export default PermissionGate;

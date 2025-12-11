/**
 * Sprint 24: LGPD Privacy Control Services API
 * 
 * TypeScript API client for LGPD endpoints
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface DataAccessLog {
    log_id: string;
    patient_id: string;
    resource_type: string;
    resource_id: string;
    action: 'read' | 'update' | 'delete' | 'export';
    user_id: string;
    user_name: string;
    timestamp: string;
    ip_address?: string;
    user_agent?: string;
    reason?: string;
}

export interface LGPDRequest {
    request_id: string;
    request_type: LGPDRequestType;
    patient_id: string;
    requester_name: string;
    requester_email: string;
    status: LGPDRequestStatus;
    created_at: string;
    updated_at: string;
    completed_at?: string;
    reason?: string;
    notes?: string;
    output_file?: string;
}

export type LGPDRequestType =
    | 'confirmation'
    | 'access'
    | 'correction'
    | 'anonymization'
    | 'blocking'
    | 'deletion'
    | 'portability'
    | 'info_sharing'
    | 'consent_revocation';

export type LGPDRequestStatus =
    | 'pending'
    | 'in_progress'
    | 'completed'
    | 'rejected'
    | 'expired';

export interface ConsentCheckResult {
    has_consent: boolean;
    consent_id?: string;
    purpose: string;
    valid_until?: string;
    error?: string;
}

export interface DataExportPreview {
    patient_id: string;
    export_date: string;
    statistics: {
        totalResources: number;
        resourceCounts: Record<string, number>;
    };
    available_formats: string[];
}

export interface LGPDReport {
    generated_at: string;
    patient_id: string;
    report_type: string;
    sections: {
        data_inventory: {
            resources: Record<string, { count: number; oldest?: string; newest?: string }>;
            total_records: number;
        };
        consents: {
            total: number;
            active: number;
            rejected: number;
            details: Array<{
                id: string;
                status: string;
                category?: string;
                date?: string;
            }>;
        };
        access_logs: {
            period: string;
            total_accesses: number;
            by_action: Record<string, number>;
            by_user: Record<string, number>;
            recent: DataAccessLog[];
        };
        lgpd_requests: {
            total: number;
            pending: number;
            completed: number;
            details: LGPDRequest[];
        };
        compliance_status: {
            has_active_consent: boolean;
            data_access_logged: boolean;
            pending_requests: number;
            last_access?: string;
        };
    };
}

export interface LGPDDashboard {
    summary: {
        total_requests: number;
        pending: number;
        in_progress: number;
        completed: number;
        by_type: Record<string, number>;
    };
    pending_requests: LGPDRequest[];
    recent_requests: LGPDRequest[];
    compliance_notes: string[];
}

// API Functions

/**
 * Get data access logs for a patient
 */
export async function getPatientAccessLogs(
    patientId: string,
    params?: {
        start_date?: string;
        end_date?: string;
        action?: string;
        limit?: number;
    }
): Promise<{ patient_id: string; total: number; logs: DataAccessLog[] }> {
    const response = await axios.get(
        `${API_URL}/patients/${patientId}/access-logs/`,
        { params }
    );
    return response.data;
}

/**
 * Log a data access event
 */
export async function logDataAccess(data: {
    patient_id: string;
    resource_type: string;
    resource_id: string;
    action: string;
    reason?: string;
}): Promise<{ message: string; log_id: string }> {
    const response = await axios.post(`${API_URL}/lgpd/log-access/`, data);
    return response.data;
}

/**
 * Preview data export for a patient
 */
export async function previewDataExport(patientId: string): Promise<DataExportPreview> {
    const response = await axios.get(
        `${API_URL}/patients/${patientId}/data-export/preview/`
    );
    return response.data;
}

/**
 * Request data export (download)
 */
export async function requestDataExport(
    patientId: string,
    format: 'json' | 'zip' = 'json',
    requesterEmail?: string
): Promise<Blob> {
    const response = await axios.post(
        `${API_URL}/patients/${patientId}/data-export/`,
        { format, requester_email: requesterEmail },
        { responseType: 'blob' }
    );
    return response.data;
}

/**
 * Request data deletion
 */
export async function requestDataDeletion(
    patientId: string,
    data: {
        reason?: string;
        soft_delete?: boolean;
        requester_email?: string;
    }
): Promise<{ request_id: string; result: any }> {
    const response = await axios.post(
        `${API_URL}/patients/${patientId}/data-deletion/`,
        data
    );
    return response.data;
}

/**
 * Check if patient has consent for a purpose
 */
export async function checkPatientConsent(
    patientId: string,
    purpose: string = 'treatment'
): Promise<ConsentCheckResult> {
    const response = await axios.get(
        `${API_URL}/patients/${patientId}/check-consent/`,
        { params: { purpose } }
    );
    return response.data;
}

/**
 * Get LGPD compliance report for a patient
 */
export async function getPatientLGPDReport(patientId: string): Promise<LGPDReport> {
    const response = await axios.get(
        `${API_URL}/patients/${patientId}/lgpd-report/`
    );
    return response.data;
}

/**
 * List LGPD requests
 */
export async function listLGPDRequests(params?: {
    patient_id?: string;
    status?: LGPDRequestStatus;
}): Promise<{ total: number; requests: LGPDRequest[] }> {
    const response = await axios.get(`${API_URL}/lgpd/requests/`, { params });
    return response.data;
}

/**
 * Create LGPD request
 */
export async function createLGPDRequest(data: {
    request_type: LGPDRequestType;
    patient_id: string;
    requester_name: string;
    requester_email: string;
    reason?: string;
}): Promise<LGPDRequest> {
    const response = await axios.post(`${API_URL}/lgpd/requests/`, data);
    return response.data;
}

/**
 * Get LGPD request details
 */
export async function getLGPDRequest(requestId: string): Promise<LGPDRequest> {
    const response = await axios.get(`${API_URL}/lgpd/requests/${requestId}/`);
    return response.data;
}

/**
 * Update LGPD request status
 */
export async function updateLGPDRequest(
    requestId: string,
    data: { status: LGPDRequestStatus; notes?: string }
): Promise<LGPDRequest> {
    const response = await axios.put(
        `${API_URL}/lgpd/requests/${requestId}/`,
        data
    );
    return response.data;
}

/**
 * Get LGPD dashboard
 */
export async function getLGPDDashboard(): Promise<LGPDDashboard> {
    const response = await axios.get(`${API_URL}/lgpd/dashboard/`);
    return response.data;
}

/**
 * Download patient data as file
 */
export function downloadPatientData(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}

export default {
    getPatientAccessLogs,
    logDataAccess,
    previewDataExport,
    requestDataExport,
    requestDataDeletion,
    checkPatientConsent,
    getPatientLGPDReport,
    listLGPDRequests,
    createLGPDRequest,
    getLGPDRequest,
    updateLGPDRequest,
    getLGPDDashboard,
    downloadPatientData
};

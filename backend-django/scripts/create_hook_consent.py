import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def create_consent_hook():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    
    content = """import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://45.151.122.234:8000/api/v1';

export interface Consent {
    resourceType: 'Consent';
    id?: string;
    status: 'active' | 'inactive' | 'rejected';
    patient: { reference: string; display?: string };
    dateTime: string;
    organization?: any[];
    policyRule?: any;
    provision?: any;
}

export const useConsents = () => {
    const [consents, setConsents] = useState<Consent[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchConsents = useCallback(async (patientId?: string) => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (patientId) params.append('patient', patientId);
            
            const response = await axios.get(`${API_URL}/consents/list/`, { params });
            
            if (response.data.results) {
                 setConsents(response.data.results);
            } else if (Array.isArray(response.data)) {
                 setConsents(response.data);
            } else {
                 setConsents([response.data]);
            }
        } catch (err) {
            console.error(err);
            setError('Error fetching consents');
        } finally {
            setLoading(false);
        }
    }, []);

    const createConsent = async (data: any) => {
        setLoading(true);
        try {
             // data: { patient_id: string }
             const res = await axios.post(`${API_URL}/consents/`, data);
             await fetchConsents(); 
             return res.data;
        } catch (err: any) {
             setError(err.message || 'Error creating consent');
             throw err;
        } finally {
             setLoading(false);
        }
    };

    return {
        consents,
        loading,
        error,
        fetchConsents,
        createConsent
    };
};
"""
    
    remote_path = "/opt/openehrcore/frontend-pwa/src/hooks/useConsents.ts"
    print(f"Uploading {remote_path}...")
    with sftp.open(remote_path, 'w') as f:
        f.write(content)
        
    sftp.close()
    t.close()

if __name__ == "__main__":
    create_consent_hook()

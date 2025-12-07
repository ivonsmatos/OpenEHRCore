import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def upload_sftp():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    
    hook_content = """import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://45.151.122.234:8000/api/v1';

export interface Patient {
    id: string;
    name: string;
    birthDate: string;
    gender: string;
    email?: string;
    phone?: string;
}

export const usePatients = () => {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [pagination, setPagination] = useState({
        current_page: 1,
        total_count: 0,
        total_pages: 1
    });

    const fetchPatients = useCallback(async (page = 1, search = '') => {
        setLoading(true);
        setError(null);
        try {
            // Use new list endpoint that supports filtering parameters
            const params = new URLSearchParams();
            params.append('page', page.toString());
            if (search) params.append('name', search);

            const response = await axios.get(`${API_URL}/patients/list/`, { params });

            // Check if backend returns paginated response
            if (response.data.results) {
                setPatients(response.data.results);
                setPagination({
                    current_page: response.data.current_page || page,
                    total_count: response.data.count || 0,
                    total_pages: response.data.total_pages || Math.ceil((response.data.count || 0) / (response.data.page_size || 10))
                });
            } else {
                // Fallback for flat list
                setPatients(response.data);
            }
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : 'Erro ao carregar pacientes');
        } finally {
            setLoading(false);
        }
    }, []);

    const nextPage = () => {
        if (pagination.current_page < pagination.total_pages) {
            fetchPatients(pagination.current_page + 1);
        }
    };

    const prevPage = () => {
        if (pagination.current_page > 1) {
            fetchPatients(pagination.current_page - 1);
        }
    };

    const createPatient = async (data: Partial<Patient>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_URL}/patients/`, data);
            await fetchPatients(pagination.current_page); // Recarregar página atual
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao criar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const updatePatient = async (id: string, data: Partial<Patient>) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.put(`${API_URL}/patients/${id}/`, data);
            await fetchPatients(pagination.current_page);
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao atualizar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const deletePatient = async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            await axios.delete(`${API_URL}/patients/${id}/`);
            await fetchPatients(pagination.current_page);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao excluir paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const getPatient = async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_URL}/patients/${id}/`);
            return response.data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar paciente');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPatients(1);
    }, []);

    return {
        patients,
        loading,
        error,
        pagination,
        fetchPatients,
        nextPage,
        prevPage,
        createPatient,
        updatePatient,
        deletePatient,
        getPatient,
    };
};
"""
    
    remote_path = "/opt/openehrcore/frontend-pwa/src/hooks/usePatients.ts"
    print(f"Uploading to {remote_path} via SFTP...")
    
    with sftp.open(remote_path, 'w') as f:
        f.write(hook_content)
        
    print("Done.")
    sftp.close()
    t.close()

if __name__ == "__main__":
    upload_sftp()

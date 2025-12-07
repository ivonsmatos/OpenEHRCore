import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def upload_hook():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Updated content
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
            // Use new list endpoint that supports filtering
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
    
    # Use python script on remote to write file to avoid shell escaping issues
    remote_writer = f"""
import os
with open('{remote_path}', 'w', encoding='utf-8') as f:
    f.write({repr(hook_content)})
print("Uploaded usePatients.ts")
"""
    client.exec_command("echo \"" + remote_writer.replace('"', '\\"') + "\" > /tmp/write_hook.py")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/write_hook.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    upload_hook()

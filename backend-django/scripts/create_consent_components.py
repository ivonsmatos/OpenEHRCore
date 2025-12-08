import paramiko
import sys

HOST = "45.151.122.234"
USER = "root"
PASS = "Protonsysdba@1986"

def create_consent_ui():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # Create directory
    client.exec_command("mkdir -p /opt/openehrcore/frontend-pwa/src/components/consents")
    
    # ConsentList
    list_content = """import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsents } from '../../hooks/useConsents';
import { colors, spacing } from '../../theme/colors';
import Card from '../base/Card';
import Button from '../base/Button';
import { HeartbeatLoader } from '../ui/HeartbeatLoader';

const ConsentList: React.FC = () => {
    const { consents, loading, error, fetchConsents } = useConsents();
    const navigate = useNavigate();

    useEffect(() => {
        fetchConsents();
    }, [fetchConsents]);

    if (loading && consents.length === 0) return <HeartbeatLoader fullScreen={false} label="Carregando consentimentos..." />;

    return (
        <div style={{ padding: spacing.xl }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: spacing.lg, alignItems: 'center' }}>
                <h1 style={{ margin: 0, color: colors.text.primary, fontSize: '1.5rem' }}>Gestão de Consentimentos (LGPD)</h1>
                <Button variant="primary" onClick={() => navigate('/consents/new')}>+ Novo Consentimento</Button>
            </div>
            
            {error && <div style={{ color: 'red', marginBottom: spacing.md }}>{error}</div>}
            
            <div style={{ display: 'grid', gap: spacing.md }}>
                {consents.length === 0 && !loading && (
                     <Card padding="xl" elevation="base">
                         <div style={{ textAlign: 'center', color: colors.text.secondary }}>
                             Nenhum consentimento registrado.
                         </div>
                     </Card>
                )}
                
                {consents.map((c: any, idx) => (
                    <Card key={c.id || idx} padding="md" elevation="base">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h3 style={{ margin: '0 0 8px 0' }}>
                                    {c.patient?.display || c.patient?.reference || 'Paciente Desconhecido'}
                                </h3>
                                <div style={{ fontSize: '0.9rem', color: colors.text.secondary }}>
                                    Status: <span style={{ 
                                        color: c.status === 'active' ? 'green' : 'gray', 
                                        fontWeight: 'bold' 
                                    }}>{c.status.toUpperCase()}</span>
                                </div>
                                <div style={{ fontSize: '0.8rem', color: colors.text.tertiary, marginTop: '4px' }}>
                                    ID: {c.id}
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.9rem' }}>
                                    {new Date(c.dateTime).toLocaleDateString()}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: colors.text.tertiary }}>
                                    {new Date(c.dateTime).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
export default ConsentList;
"""
    
    # ConsentForm
    form_content = """import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsents } from '../../hooks/useConsents';
import { colors, spacing } from '../../theme/colors';
import Card from '../base/Card';
import Button from '../base/Button';
import { HeartbeatLoader } from '../ui/HeartbeatLoader';

const ConsentForm: React.FC = () => {
    const { createConsent, loading } = useConsents();
    const navigate = useNavigate();
    const [patientId, setPatientId] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createConsent({
                patient_id: patientId
            });
            navigate('/consents');
        } catch (err) {
            alert('Erro ao criar consentimento: ' + err);
        }
    };

    if (loading) return <HeartbeatLoader fullScreen={false} label="Salvando..." />;

    return (
        <div style={{ padding: spacing.xl, maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ marginBottom: spacing.lg }}>
                <Button variant="secondary" onClick={() => navigate('/consents')}>← Voltar</Button>
            </div>
            
            <Card padding="lg">
                <h2 style={{ marginBottom: spacing.md, marginTop: 0 }}>Novo Consentimento LGPD</h2>
                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: spacing.md }}>
                        <label style={{ display: 'block', marginBottom: spacing.xs, fontWeight: 500 }}>ID do Paciente (ex: 123)</label>
                        <input 
                            type="text" 
                            value={patientId}
                            onChange={(e) => setPatientId(e.target.value)}
                            style={{ 
                                width: '100%', 
                                padding: '10px', 
                                border: '1px solid #ddd', 
                                borderRadius: '4px',
                                fontSize: '1rem'
                            }}
                            placeholder="Digite o ID do paciente..."
                            required
                        />
                        <p style={{ fontSize: '0.8rem', color: colors.text.tertiary, marginTop: '4px' }}>
                            O sistema irá vincular este consentimento ao registro do paciente existente.
                        </p>
                    </div>
                    
                    <div style={{ 
                        marginBottom: spacing.lg, 
                        padding: spacing.md, 
                        backgroundColor: '#f9fafb', 
                        borderRadius: '4px',
                        border: '1px solid #eee'
                    }}>
                        <h4 style={{ margin: '0 0 8px 0' }}>Termo de Consentimento</h4>
                        <p style={{ fontSize: '0.9rem', color: colors.text.secondary, margin: 0, lineHeight: 1.5 }}>
                            Ao salvar este registro, confirma-se que o paciente foi informado sobre a coleta e tratamento de seus dados sensíveis de saúde para fins de prestação de serviços médicos, conforme Art. 7º e 11 da LGPD (Lei 13.709/2018).
                            O paciente tem direito de revogar este consentimento a qualquer momento.
                        </p>
                    </div>

                    <div style={{ display: 'flex', gap: spacing.md, justifyContent: 'flex-end' }}>
                        <Button variant="secondary" onClick={() => navigate('/consents')} type="button">
                            Cancelar
                        </Button>
                        <Button variant="primary" type="submit" disabled={!patientId}>
                            Registrar Consentimento
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};
export default ConsentForm;
"""

    print("Uploading ConsentList.tsx...")
    with sftp.open("/opt/openehrcore/frontend-pwa/src/components/consents/ConsentList.tsx", 'w') as f:
        f.write(list_content)
        
    print("Uploading ConsentForm.tsx...")
    with sftp.open("/opt/openehrcore/frontend-pwa/src/components/consents/ConsentForm.tsx", 'w') as f:
        f.write(form_content)
        
    client.close()
    sftp.close()
    t.close()

if __name__ == "__main__":
    create_consent_ui()

/**
 * Document Manager - Gerenciamento de Documentos Médicos
 * 
 * Sprint 33: FHIR DocumentReference Implementation
 * Features:
 * - Upload de documentos (PDF, imagens)
 * - Visualização com preview
 * - Download seguro
 * - Filtros por tipo e data
 * - Mobile-first responsivo
 */

import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Image, 
  Download, 
  Eye, 
  Trash2,
  Filter,
  Calendar,
  User,
  Shield,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { colors } from '../../theme/colors';
import { useIsMobile } from '../../hooks/useMediaQuery';

interface Document {
  id: string;
  type: string;
  type_display: string;
  patient_name: string;
  author_name: string;
  date: string;
  description: string;
  status: string;
  security_label: string[];
  attachments: Attachment[];
}

interface Attachment {
  id: string;
  title: string;
  content_type: string;
  size: number;
  url: string;
  created_at: string;
}

interface DocumentManagerProps {
  patientId?: string;
  onDocumentSelect?: (doc: Document) => void;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({ 
  patientId, 
  onDocumentSelect 
}) => {
  const isMobile = useIsMobile();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtros
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  
  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const documentTypes = [
    { value: 'all', label: 'Todos os Tipos' },
    { value: 'lab-report', label: 'Resultado Laboratorial', icon: FileText },
    { value: 'imaging-report', label: 'Laudo de Imagem', icon: Image },
    { value: 'prescription', label: 'Prescrição', icon: FileText },
    { value: 'discharge-summary', label: 'Sumário de Alta', icon: FileText },
    { value: 'consent-form', label: 'Termo de Consentimento', icon: Shield },
    { value: 'other', label: 'Outro', icon: FileText },
  ];

  useEffect(() => {
    loadDocuments();
  }, [patientId, typeFilter]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const url = patientId 
        ? `/api/v1/documents/patient/${patientId}/${typeFilter !== 'all' ? `?type=${typeFilter}` : ''}`
        : `/api/v1/documents/${typeFilter !== 'all' ? `?type=${typeFilter}` : ''}`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) throw new Error('Erro ao carregar documentos');
      
      const data = await response.json();
      setDocuments(data.results || data);
      setError(null);
    } catch (err) {
      setError('Não foi possível carregar os documentos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !patientId) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    formData.append('type', typeFilter !== 'all' ? typeFilter : 'other');
    formData.append('title', file.name);

    try {
      setUploading(true);
      setUploadProgress(0);

      const xhr = new XMLHttpRequest();
      
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          setUploadProgress(progress);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 201) {
          loadDocuments();
          setUploadProgress(100);
          setTimeout(() => {
            setUploading(false);
            setUploadProgress(0);
          }, 1000);
        } else {
          throw new Error('Upload falhou');
        }
      };

      xhr.onerror = () => {
        setError('Erro no upload do arquivo');
        setUploading(false);
      };

      xhr.open('POST', '/api/v1/documents/upload/');
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('access_token')}`);
      xhr.send(formData);

    } catch (err) {
      setError('Erro ao fazer upload do arquivo');
      setUploading(false);
      console.error(err);
    }
  };

  const handleDownload = async (doc: Document, attachment: Attachment) => {
    try {
      const response = await fetch(
        `/api/v1/documents/${doc.id}/download/?attachment_id=${attachment.id}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      
      if (!response.ok) throw new Error('Erro no download');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.title;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Erro ao baixar o arquivo');
      console.error(err);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDocumentIcon = (type: string) => {
    const docType = documentTypes.find(t => t.value === type);
    return docType?.icon || FileText;
  };

  return (
    <div style={{ 
      padding: isMobile ? '16px' : '24px',
      backgroundColor: colors.background.surface 
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        justifyContent: 'space-between',
        alignItems: isMobile ? 'stretch' : 'center',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <h2 style={{ 
          fontSize: isMobile ? '1.5rem' : '1.75rem',
          fontWeight: 'bold',
          color: colors.text.primary,
          margin: 0
        }}>
          📄 Documentos Médicos
        </h2>

        {patientId && (
          <label style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            backgroundColor: colors.primary.medium,
            color: 'white',
            borderRadius: '8px',
            cursor: uploading ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            opacity: uploading ? 0.6 : 1,
            width: isMobile ? '100%' : 'auto',
            justifyContent: 'center'
          }}>
            <Upload size={20} />
            <span>{uploading ? `Enviando... ${uploadProgress.toFixed(0)}%` : 'Novo Documento'}</span>
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              accept=".pdf,.jpg,.jpeg,.png,.tiff,.dcm,.doc,.docx"
              style={{ display: 'none' }}
            />
          </label>
        )}
      </div>

      {/* Filtros */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '24px',
        border: `1px solid ${colors.border.default}`
      }}>
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '600',
            color: colors.primary.medium,
            width: '100%',
            justifyContent: 'space-between'
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={20} />
            Filtros
          </span>
          <span>{showFilters ? '▼' : '►'}</span>
        </button>

        {showFilters && (
          <div style={{
            marginTop: '16px',
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px'
          }}>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={{
                padding: '10px',
                borderRadius: '8px',
                border: `1px solid ${colors.border.default}`,
                fontSize: '0.875rem',
                backgroundColor: 'white'
              }}
            >
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div style={{
          backgroundColor: colors.status.info + '20',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px'
        }}>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: colors.background.surface,
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${uploadProgress}%`,
              height: '100%',
              backgroundColor: colors.primary.medium,
              transition: 'width 0.3s ease'
            }} />
          </div>
          <p style={{ 
            margin: '8px 0 0 0', 
            fontSize: '0.875rem',
            color: colors.text.secondary 
          }}>
            Enviando arquivo... {uploadProgress.toFixed(0)}%
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          backgroundColor: colors.status.error + '20',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={20} color={colors.status.error} />
          <span style={{ color: colors.status.error }}>{error}</span>
        </div>
      )}

      {/* Documents List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${colors.border.default}`,
            borderTop: `3px solid ${colors.primary.medium}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <p style={{ color: colors.text.secondary }}>Carregando documentos...</p>
        </div>
      ) : documents.length === 0 ? (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '48px',
          textAlign: 'center',
          border: `2px dashed ${colors.border.default}`
        }}>
          <FileText size={48} color={colors.text.tertiary} style={{ margin: '0 auto 16px' }} />
          <p style={{ color: colors.text.secondary, fontSize: '1rem' }}>
            Nenhum documento encontrado
          </p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '16px'
        }}>
          {documents.map(doc => {
            const Icon = getDocumentIcon(doc.type);
            const hasSecurityLabel = doc.security_label?.includes('R') || doc.security_label?.includes('V');

            return (
              <div
                key={doc.id}
                style={{
                  backgroundColor: 'white',
                  borderRadius: '12px',
                  padding: '16px',
                  border: `1px solid ${colors.border.default}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  ':hover': {
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    borderColor: colors.primary.medium
                  }
                }}
                onClick={() => onDocumentSelect?.(doc)}
              >
                {/* Header */}
                <div style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  marginBottom: '12px'
                }}>
                  <div style={{
                    padding: '12px',
                    backgroundColor: colors.primary.light + '40',
                    borderRadius: '8px'
                  }}>
                    <Icon size={24} color={colors.primary.medium} />
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: colors.text.primary,
                      margin: '0 0 4px 0',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {doc.type_display}
                    </h3>
                    <p style={{
                      fontSize: '0.875rem',
                      color: colors.text.secondary,
                      margin: 0
                    }}>
                      {formatDate(doc.date)}
                    </p>
                  </div>

                  {hasSecurityLabel && (
                    <Shield size={16} color={colors.status.warning} title="Documento restrito" />
                  )}
                </div>

                {/* Description */}
                {doc.description && (
                  <p style={{
                    fontSize: '0.875rem',
                    color: colors.text.secondary,
                    marginBottom: '12px',
                    lineHeight: '1.5'
                  }}>
                    {doc.description}
                  </p>
                )}

                {/* Metadata */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  paddingTop: '12px',
                  borderTop: `1px solid ${colors.border.light}`
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.75rem',
                    color: colors.text.tertiary
                  }}>
                    <User size={14} />
                    <span>{doc.author_name || 'Não informado'}</span>
                  </div>

                  {doc.attachments?.length > 0 && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '0.75rem',
                      color: colors.text.tertiary
                    }}>
                      <FileText size={14} />
                      <span>
                        {doc.attachments.length} arquivo(s) • {formatFileSize(doc.attachments[0].size)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  marginTop: '12px'
                }}>
                  {doc.attachments?.map(attachment => (
                    <button
                      key={attachment.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(doc, attachment);
                      }}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        backgroundColor: colors.primary.medium,
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Download size={16} />
                      Download
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DocumentManager;

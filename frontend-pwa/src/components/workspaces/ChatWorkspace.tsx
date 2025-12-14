/**
 * Chat Workspace - Internal FHIR-based Communication
 * 
 * Features:
 * - Loads all registered practitioners from FHIR
 * - Auto-refresh when new practitioners are registered
 * - Group channels and direct messages
 * - Real-time message polling
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import Card from '../base/Card';
import './ChatWorkspace.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const PRACTITIONER_REFRESH_INTERVAL = 30000; // 30 seconds
const MESSAGE_REFRESH_INTERVAL = 5000; // 5 seconds

interface Practitioner {
    id: string;
    name: string;
    specialty?: string;
    status: 'online' | 'offline' | 'away';
    avatar?: string;
}

interface Channel {
    id: string;
    name: string;
    type: 'group' | 'dm';
    description?: string;
    practitioner?: Practitioner;
}

interface Message {
    id: string;
    sender: string;
    senderName: string;
    content: string;
    timestamp: string;
    attachment?: {
        name: string;
        type: string;
        size: number;
        data?: string; // base64 encoded
    };
}

const ChatWorkspace: React.FC = () => {
    const [channels, setChannels] = useState<Channel[]>([]);
    const [practitioners, setPractitioners] = useState<Practitioner[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [loadingPractitioners, setLoadingPractitioners] = useState(false);
    const [attachment, setAttachment] = useState<{ name: string; type: string; size: number; data: string } | null>(null);
    const [imageModal, setImageModal] = useState<{ src: string; name: string } | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    // Get current user info
    const getCurrentUser = () => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                return JSON.parse(userStr);
            } catch {
                return null;
            }
        }
        return null;
    };

    // Fetch practitioners from FHIR server
    const fetchPractitioners = useCallback(async () => {
        setLoadingPractitioners(true);
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/practitioners/list/`, { headers });

            const practitionerList: Practitioner[] = [];
            const results = response.data?.results || response.data?.entry || response.data || [];

            results.forEach((p: any) => {
                // Handle FHIR resource format
                const resource = p.resource || p;
                const id = resource.id;

                // Extract name
                let name = 'Profissional';
                if (resource.name && resource.name[0]) {
                    const n = resource.name[0];
                    const given = n.given?.join(' ') || '';
                    const family = n.family || '';
                    name = `${given} ${family}`.trim() || `Dr(a). ${id}`;
                }

                // Extract specialty from qualification
                let specialty = '';
                if (resource.qualification && resource.qualification[0]) {
                    specialty = resource.qualification[0].code?.text ||
                        resource.qualification[0].code?.coding?.[0]?.display || '';
                }

                practitionerList.push({
                    id,
                    name,
                    specialty,
                    status: 'online', // TODO: implement real status
                    avatar: undefined
                });
            });

            setPractitioners(practitionerList);

            // Update channels with practitioners
            updateChannelsWithPractitioners(practitionerList);

        } catch (error) {
            console.error('Error fetching practitioners:', error);
        } finally {
            setLoadingPractitioners(false);
        }
    }, []);

    // Update channel list with practitioners
    const updateChannelsWithPractitioners = (practitionerList: Practitioner[]) => {
        const currentUser = getCurrentUser();
        const currentUserId = currentUser?.practitioner_id;

        // Base group channels
        const baseChannels: Channel[] = [
            { id: 'general', name: '#geral', type: 'group', description: 'Canal geral da equipe' },
            { id: 'urgencia', name: '#urgência', type: 'group', description: 'Casos urgentes' },
            { id: 'laboratorio', name: '#laboratório', type: 'group', description: 'Resultados de exames' },
        ];

        // Add practitioners as DM channels (exclude current user)
        practitionerList.forEach(p => {
            if (p.id !== currentUserId) {
                baseChannels.push({
                    id: `dm-${p.id}`,
                    name: p.name,
                    type: 'dm',
                    description: p.specialty,
                    practitioner: p
                });
            }
        });

        setChannels(baseChannels);

        // Select first channel if none selected
        if (!selectedChannel && baseChannels.length > 0) {
            setSelectedChannel(baseChannels[0].id);
        }
    };

    // Fetch messages for selected channel
    const fetchMessages = useCallback(async () => {
        if (!selectedChannel) return;

        try {
            const headers = getAuthHeaders();
            const response = await axios.get(
                `${API_URL}/chat/messages/?channel_id=${selectedChannel}`,
                { headers }
            );

            // Handle both array and {messages: []} response formats
            const messagesData = Array.isArray(response.data)
                ? response.data
                : (response.data?.messages || []);

            if (messagesData.length > 0) {
                setMessages(messagesData.map((m: any) => ({
                    id: m.id,
                    sender: m.sender_id || 'unknown',
                    senderName: m.sender_name || practitioners.find(p => p.id === m.sender_id)?.name || 'Sistema',
                    content: m.content || '',
                    timestamp: m.sent || new Date().toISOString(),
                    attachment: m.attachment
                })));
            }
            // Don't clear messages if empty - keep optimistic updates
        } catch (error) {
            console.error('Error fetching messages:', error);
            // Don't clear messages on error - keep optimistic updates
        }
    }, [selectedChannel, practitioners]);

    // Initial load
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            await fetchPractitioners();
            setLoading(false);

            // Check URL params first (priority)
            const channelParam = searchParams.get('channel');
            if (channelParam) {
                setSelectedChannel(channelParam);
                return;
            }

            // Check if coming from practitioner card click (fallback)
            const chatPractitioner = sessionStorage.getItem('chat-practitioner');
            if (chatPractitioner) {
                try {
                    const { id } = JSON.parse(chatPractitioner);
                    // Select the DM channel for this practitioner
                    setSelectedChannel(`dm-${id}`);
                    sessionStorage.removeItem('chat-practitioner');
                } catch (e) {
                    console.error('Error parsing chat practitioner:', e);
                }
            }
        };
        init();
    }, [fetchPractitioners, searchParams]);

    // Auto-refresh practitioners
    useEffect(() => {
        const interval = setInterval(() => {
            fetchPractitioners();
        }, PRACTITIONER_REFRESH_INTERVAL);

        return () => clearInterval(interval);
    }, [fetchPractitioners]);

    // Fetch messages when channel changes
    useEffect(() => {
        // Clear messages first to avoid showing wrong conversation
        setMessages([]);
        fetchMessages();
    }, [selectedChannel]);

    // Auto-refresh messages
    useEffect(() => {
        const interval = setInterval(() => {
            if (selectedChannel) {
                fetchMessages();
            }
        }, MESSAGE_REFRESH_INTERVAL);

        return () => clearInterval(interval);
    }, [selectedChannel, fetchMessages]);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Send message
    const sendMessage = async () => {
        if (!newMessage.trim() || !selectedChannel) return;

        const currentUser = getCurrentUser();
        const tempId = Date.now().toString();

        // Add message optimistically
        const optimisticMessage: Message = {
            id: tempId,
            sender: currentUser?.practitioner_id || 'you',
            senderName: currentUser?.name || 'Você',
            content: newMessage,
            timestamp: new Date().toISOString(),
            attachment: attachment ? {
                name: attachment.name,
                type: attachment.type,
                size: attachment.size,
                data: attachment.data
            } : undefined
        };

        setMessages(prev => [...prev, optimisticMessage]);
        setNewMessage('');

        // Clear attachment after adding to messages
        const attachmentToSend = attachment;
        setAttachment(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }

        try {
            const headers = getAuthHeaders();
            await axios.post(`${API_URL}/chat/send/`, {
                channel_id: selectedChannel,
                content: newMessage || null,
                recipient_id: selectedChannel.startsWith('dm-')
                    ? selectedChannel.replace('dm-', '')
                    : null,
                attachment: attachmentToSend ? {
                    name: attachmentToSend.name,
                    type: attachmentToSend.type,
                    size: attachmentToSend.size,
                    data: attachmentToSend.data
                } : null
            }, { headers });

            // Refresh to get server-assigned ID
            fetchMessages();
        } catch (error) {
            console.error('Error sending message:', error);
            // Message stays as optimistic update
        }
    };

    // Get status badge color
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'online': return '#10b981';
            case 'away': return '#f59e0b';
            case 'offline': return '#6b7280';
            default: return '#6b7280';
        }
    };

    // Handle attachment click
    const handleAttachmentClick = async (msg: Message) => {
        if (!msg.attachment) return;

        // If attachment has data (recent message), use it directly
        if (msg.attachment.data) {
            if (msg.attachment.type.startsWith('image/')) {
                // Open image in modal
                setImageModal({ src: msg.attachment.data, name: msg.attachment.name });
            } else {
                // Download file
                downloadFile(msg.attachment.data, msg.attachment.name);
            }
            return;
        }

        // Otherwise, fetch from backend
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(
                `${API_URL}/chat/attachment/${msg.id}/`,
                { headers }
            );

            const attachmentData = response.data;
            if (attachmentData.data) {
                const base64Data = `data:${attachmentData.type};base64,${attachmentData.data}`;
                
                if (attachmentData.type.startsWith('image/')) {
                    // Open image in modal
                    setImageModal({ src: base64Data, name: attachmentData.name });
                } else {
                    // Download file
                    downloadFile(base64Data, attachmentData.name);
                }
            }
        } catch (error) {
            console.error('Error downloading attachment:', error);
            alert('Erro ao baixar anexo');
        }
    };

    // Download file helper
    const downloadFile = (dataUrl: string, filename: string) => {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Compress image before uploading
    const compressImage = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;
                    
                    // Max dimensions 800x800
                    const maxSize = 800;
                    if (width > maxSize || height > maxSize) {
                        if (width > height) {
                            height = (height / width) * maxSize;
                            width = maxSize;
                        } else {
                            width = (width / height) * maxSize;
                            height = maxSize;
                        }
                    }
                    
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx?.drawImage(img, 0, 0, width, height);
                    
                    // Convert to JPEG with 0.7 quality for better compression
                    resolve(canvas.toDataURL('image/jpeg', 0.7));
                };
                img.onerror = reject;
                img.src = e.target?.result as string;
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    // Handle file selection
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Allow text files and images
        const allowedTypes = [
            // Text files
            'text/plain',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/csv',
            'application/json',
            'text/xml',
            'application/xml',
            // Images
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'image/bmp'
        ];

        const isAllowed = allowedTypes.includes(file.type) ||
            file.name.endsWith('.txt') ||
            file.type.startsWith('image/');

        if (!isAllowed) {
            alert('Apenas arquivos de texto e imagens são permitidos');
            return;
        }

        // Max 5MB
        if (file.size > 5 * 1024 * 1024) {
            alert('Arquivo muito grande. Máximo 5MB.');
            return;
        }

        try {
            let base64: string;
            let finalType = file.type || 'text/plain';
            
            // Compress images to avoid 431 errors
            if (file.type.startsWith('image/')) {
                base64 = await compressImage(file);
                finalType = 'image/jpeg'; // Always JPEG after compression
            } else {
                // Non-images: read as-is
                base64 = await new Promise<string>((resolve) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result as string);
                    reader.readAsDataURL(file);
                });
            }
            
            setAttachment({
                name: file.name,
                type: finalType,
                size: base64.length, // Update size to compressed size
                data: base64
            });
        } catch (error) {
            console.error('Error processing file:', error);
            alert('Erro ao processar arquivo');
        }
    };

    // Remove attachment
    const removeAttachment = () => {
        setAttachment(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Format file size
    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    // Get selected channel info
    const getSelectedChannelInfo = () => {
        return channels.find(c => c.id === selectedChannel);
    };

    if (loading) {
        return (
            <div className="chat-loading">
                <p>Carregando chat...</p>
            </div>
        );
    }

    const selectedChannelInfo = getSelectedChannelInfo();

    return (
        <div className="chat-workspace">
            {/* Header */}
            <div className="chat-header">
                <h1 className="chat-title">💬 Chat Clínico</h1>
                <p className="chat-subtitle">
                    Comunicação segura entre a equipe de saúde
                    {loadingPractitioners && <span className="loading-indicator"> (atualizando...)</span>}
                </p>
            </div>

            {/* Chat Layout */}
            <div className="chat-layout">
                {/* Channels Sidebar */}
                <Card className="chat-sidebar">
                    <h3 className="sidebar-title">Canais</h3>
                    {channels.filter(c => c.type === 'group').map(channel => (
                        <div
                            key={channel.id}
                            onClick={() => setSelectedChannel(channel.id)}
                            className={`channel-item ${selectedChannel === channel.id ? 'channel-item--selected' : ''}`}
                        >
                            <div className="channel-name">{channel.name}</div>
                            {channel.description && (
                                <div className="channel-description">{channel.description}</div>
                            )}
                        </div>
                    ))}

                    <h3 className="sidebar-title sidebar-title--dm">
                        Mensagens Diretas
                        <span className="practitioner-count">
                            ({channels.filter(c => c.type === 'dm').length})
                        </span>
                    </h3>

                    {channels.filter(c => c.type === 'dm').length === 0 ? (
                        <div className="no-practitioners">
                            <p>Nenhum profissional cadastrado</p>
                            <p className="no-practitioners-hint">Cadastre profissionais para iniciar conversas</p>
                        </div>
                    ) : (
                        <>
                            {/* Search Input */}
                            <div className="practitioner-search">
                                <input
                                    type="text"
                                    placeholder="Buscar profissional..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="search-input"
                                />
                                {searchQuery && (
                                    <button
                                        className="search-clear"
                                        onClick={() => setSearchQuery('')}
                                        type="button"
                                    >
                                        ×
                                    </button>
                                )}
                            </div>
                            
                            {channels
                                .filter(c => c.type === 'dm')
                                .filter(c => 
                                    !searchQuery || 
                                    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                    c.description?.toLowerCase().includes(searchQuery.toLowerCase())
                                )
                                .map(channel => (
                                <div
                                    key={channel.id}
                                    onClick={() => setSelectedChannel(channel.id)}
                                    className={`dm-item ${selectedChannel === channel.id ? 'dm-item--selected' : ''}`}
                                >
                                    <span
                                        className="status-dot"
                                        style={{ background: getStatusColor(channel.practitioner?.status || 'offline') }}
                                    />
                                    <div className="dm-info">
                                        <div className="dm-name">{channel.name}</div>
                                        {channel.description && (
                                            <div className="dm-specialty">{channel.description}</div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            
                            {/* No results message */}
                            {searchQuery && channels.filter(c => c.type === 'dm').filter(c => 
                                c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                c.description?.toLowerCase().includes(searchQuery.toLowerCase())
                            ).length === 0 && (
                                <div className="no-results">
                                    <p>🔍 Nenhum profissional encontrado</p>
                                    <button
                                        className="clear-search-button"
                                        onClick={() => setSearchQuery('')}
                                    >
                                        Limpar busca
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </Card>

                {/* Messages Area */}
                <Card className="chat-messages-area">
                    {/* Channel Header */}
                    {selectedChannelInfo && (
                        <div className="messages-header">
                            <div className="messages-header-info">
                                <h2 className="messages-header-title">
                                    {selectedChannelInfo.type === 'dm' ? '👤' : '💬'} {selectedChannelInfo.name}
                                </h2>
                                {selectedChannelInfo.description && (
                                    <p className="messages-header-subtitle">{selectedChannelInfo.description}</p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Messages List */}
                    <div className="messages-list">
                        {messages.length === 0 ? (
                            <div className="messages-empty">
                                <p>Nenhuma mensagem ainda.</p>
                                <p>Comece uma conversa!</p>
                            </div>
                        ) : (
                            messages.map(msg => (
                                <div key={msg.id} className="message-item">
                                    <div className="message-header">
                                        <span className="message-sender">{msg.senderName}</span>
                                        <span className="message-time">
                                            {new Date(msg.timestamp).toLocaleTimeString('pt-BR', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </span>
                                    </div>
                                    {msg.content && <p className="message-content">{msg.content}</p>}
                                    {msg.attachment && (
                                        <div 
                                            className="message-attachment"
                                            onClick={() => handleAttachmentClick(msg)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            {msg.attachment.type.startsWith('image/') ? (
                                                msg.attachment.data ? (
                                                    <img 
                                                        src={msg.attachment.data} 
                                                        alt={msg.attachment.name}
                                                        className="message-attachment-image"
                                                        title="Clique para ampliar"
                                                    />
                                                ) : (
                                                    <div className="message-attachment-file">
                                                        <span className="attachment-icon">🖼️</span>
                                                        <span className="attachment-name">{msg.attachment.name}</span>
                                                        <span className="attachment-size">({formatFileSize(msg.attachment.size)})</span>
                                                        <span className="attachment-hint">Clique para visualizar</span>
                                                    </div>
                                                )
                                            ) : (
                                                <div className="message-attachment-file">
                                                    <span className="attachment-icon">📎</span>
                                                    <span className="attachment-name">{msg.attachment.name}</span>
                                                    <span className="attachment-size">({formatFileSize(msg.attachment.size)})</span>
                                                    <span className="attachment-hint">Clique para baixar</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input */}
                    <div className="message-input-area">
                        {/* Hidden file input */}
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            accept=".txt,.pdf,.doc,.docx,.csv,.json,.xml,.jpg,.jpeg,.png,.gif,.webp,.bmp,image/*"
                            className="file-input-hidden"
                            title="Selecionar arquivo"
                        />

                        {/* Attachment preview */}
                        {attachment && (
                            <div className="attachment-preview">
                                {attachment.type.startsWith('image/') ? (
                                    <img
                                        src={attachment.data}
                                        alt={attachment.name}
                                        className="attachment-thumbnail"
                                    />
                                ) : (
                                    <span className="attachment-icon">📎</span>
                                )}
                                <span className="attachment-name">{attachment.name}</span>
                                <span className="attachment-size">({formatFileSize(attachment.size)})</span>
                                <button
                                    className="attachment-remove"
                                    onClick={removeAttachment}
                                    type="button"
                                >
                                    ✕
                                </button>
                            </div>
                        )}

                        <div className="message-input-row">
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="attach-button"
                                type="button"
                                title="Anexar arquivo"
                            >
                                📎
                            </button>
                            <input
                                type="text"
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                                placeholder="Digite uma mensagem..."
                                className="message-input"
                            />
                            <button
                                onClick={sendMessage}
                                className="send-button"
                                disabled={!newMessage.trim() && !attachment}
                            >
                                Enviar
                            </button>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Image Modal */}
            {imageModal && (
                <div 
                    className="image-modal"
                    onClick={() => setImageModal(null)}
                >
                    <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
                        <button 
                            className="image-modal-close"
                            onClick={() => setImageModal(null)}
                        >
                            ×
                        </button>
                        <img src={imageModal.src} alt={imageModal.name} />
                        <p className="image-modal-name">{imageModal.name}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatWorkspace;

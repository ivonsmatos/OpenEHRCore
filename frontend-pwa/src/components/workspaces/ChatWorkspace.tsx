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
import { useIsMobile } from '../../hooks/useMediaQuery';
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
    const [showSidebar, setShowSidebar] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const isMobile = useIsMobile();

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
        <div className="chat-workspace" style={{ 
            height: isMobile ? 'calc(100vh - 60px)' : 'calc(100vh - 120px)',
            display: 'flex',
            flexDirection: 'column'
        }}>
            {/* Header */}
            <div style={{ 
                marginBottom: isMobile ? '0.5rem' : '1rem',
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                alignItems: isMobile ? 'flex-start' : 'center',
                justifyContent: 'space-between',
                gap: isMobile ? '0.5rem' : '1rem'
            }}>
                <div style={{ flex: 1 }}>
                    <h1 style={{ 
                        margin: 0,
                        fontSize: isMobile ? '1.25rem' : '1.5rem',
                        color: '#1e3a5f'
                    }}>💬 Chat Clínico</h1>
                    <p style={{ 
                        margin: '0.25rem 0 0 0',
                        color: '#64748b',
                        fontSize: isMobile ? '0.8rem' : '0.875rem'
                    }}>
                        Comunicação segura entre a equipe de saúde
                        {loadingPractitioners && <span className="loading-indicator"> (atualizando...)</span>}
                    </p>
                </div>
                
                {isMobile && (
                    <button
                        onClick={() => setShowSidebar(!showSidebar)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: showSidebar ? '#3b82f6' : '#f1f5f9',
                            color: showSidebar ? 'white' : '#64748b',
                            border: showSidebar ? 'none' : '1px solid #e5e7eb',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            transition: 'all 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        {showSidebar ? '✕ Fechar Menu' : '☰ Abrir Menu'}
                    </button>
                )}
            </div>

            {/* Chat Layout */}
            <div style={{ 
                display: 'flex',
                flex: 1,
                gap: isMobile ? '0' : '1rem',
                overflow: 'hidden',
                position: 'relative'
            }}>
                {/* Channels Sidebar */}
                {(!isMobile || showSidebar) && (
                    <Card className="chat-sidebar" style={{
                        width: isMobile ? '100%' : '280px',
                        padding: '1rem',
                        overflow: 'auto',
                        position: isMobile ? 'absolute' : 'relative',
                        top: 0,
                        left: 0,
                        bottom: 0,
                        zIndex: isMobile ? 10 : 1,
                        boxShadow: isMobile ? '2px 0 8px rgba(0,0,0,0.1)' : 'none'
                    }}>
                        <h3 className="sidebar-title">Canais</h3>
                        {channels.filter(c => c.type === 'group').map(channel => (
                            <div
                                key={channel.id}
                                onClick={() => {
                                    setSelectedChannel(channel.id);
                                    if (isMobile) setShowSidebar(false);
                                }}
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
                                        style={{ fontSize: isMobile ? '16px' : '0.875rem' }}
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
                                        onClick={() => {
                                            setSelectedChannel(channel.id);
                                            if (isMobile) setShowSidebar(false);
                                        }}
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
                )}

                {/* Messages Area */}
                <Card className="chat-messages-area" style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    padding: 0,
                    overflow: 'hidden',
                    width: isMobile && showSidebar ? '0' : isMobile ? '100%' : 'auto',
                    opacity: isMobile && showSidebar ? 0 : 1,
                    pointerEvents: isMobile && showSidebar ? 'none' : 'auto'
                }}>
                    {/* Channel Header */}
                    {selectedChannelInfo && (
                        <div style={{
                            padding: isMobile ? '0.75rem' : '1rem',
                            borderBottom: '1px solid #e5e7eb',
                            background: '#f0f2f5',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem'
                        }}>
                            {/* Avatar/Icon */}
                            <div style={{
                                width: '40px',
                                height: '40px',
                                borderRadius: '50%',
                                background: selectedChannelInfo.type === 'dm' ? '#00a884' : '#3b82f6',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.25rem',
                                flexShrink: 0
                            }}>
                                {selectedChannelInfo.type === 'dm' ? '👤' : '💬'}
                            </div>
                            
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <h2 style={{ 
                                    margin: 0,
                                    fontSize: isMobile ? '1rem' : '1.1rem',
                                    color: '#111b21',
                                    fontWeight: '600',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                }}>
                                    {selectedChannelInfo.name}
                                </h2>
                                {selectedChannelInfo.description && (
                                    <p style={{ 
                                        margin: '0.125rem 0 0 0',
                                        fontSize: isMobile ? '0.75rem' : '0.8125rem',
                                        color: '#667781',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap'
                                    }}>{selectedChannelInfo.description}</p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Messages List */}
                    <div className="messages-list" style={{
                        flex: 1,
                        padding: isMobile ? '0.75rem' : '1rem',
                        overflow: 'auto',
                        background: '#e5ddd5',
                        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23d9d9d9' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
                    }}>
                        {messages.length === 0 ? (
                            <div className="messages-empty" style={{
                                background: 'white',
                                padding: '2rem',
                                borderRadius: '12px',
                                margin: '2rem auto',
                                maxWidth: '300px',
                                textAlign: 'center',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                            }}>
                                <p style={{ margin: '0.5rem 0', color: '#64748b', fontSize: '0.875rem' }}>Nenhuma mensagem ainda.</p>
                                <p style={{ margin: '0.5rem 0', color: '#94a3b8', fontSize: '0.8rem' }}>Comece uma conversa!</p>
                            </div>
                        ) : (
                            messages.map((msg, index) => {
                                const currentUser = getCurrentUser();
                                const isMyMessage = msg.sender === currentUser?.practitioner_id;
                                const prevMsg = index > 0 ? messages[index - 1] : null;
                                const showSender = !prevMsg || prevMsg.sender !== msg.sender;
                                
                                return (
                                    <div 
                                        key={msg.id} 
                                        style={{
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: isMyMessage ? 'flex-end' : 'flex-start',
                                            marginBottom: '0.5rem'
                                        }}
                                    >
                                        {/* Sender name (only for others' messages and when sender changes) */}
                                        {!isMyMessage && showSender && (
                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: '#667781',
                                                marginLeft: '0.75rem',
                                                marginBottom: '0.25rem',
                                                fontWeight: '500'
                                            }}>
                                                {msg.senderName}
                                            </div>
                                        )}
                                        
                                        {/* Message bubble */}
                                        <div style={{
                                            maxWidth: isMobile ? '85%' : '70%',
                                            background: isMyMessage ? '#d9fdd3' : 'white',
                                            padding: '0.5rem 0.75rem',
                                            borderRadius: '8px',
                                            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                                            position: 'relative'
                                        }}>
                                            {msg.content && (
                                                <p style={{
                                                    margin: 0,
                                                    color: '#111b21',
                                                    fontSize: '0.9375rem',
                                                    lineHeight: '1.4',
                                                    wordWrap: 'break-word',
                                                    whiteSpace: 'pre-wrap'
                                                }}>
                                                    {msg.content}
                                                </p>
                                            )}
                                            
                                            {msg.attachment && (
                                                <div 
                                                    onClick={() => handleAttachmentClick(msg)}
                                                    style={{ 
                                                        cursor: 'pointer',
                                                        marginTop: msg.content ? '0.5rem' : 0
                                                    }}
                                                >
                                                    {msg.attachment.type.startsWith('image/') ? (
                                                        msg.attachment.data ? (
                                                            <img 
                                                                src={msg.attachment.data} 
                                                                alt={msg.attachment.name}
                                                                title="Clique para ampliar"
                                                                style={{
                                                                    maxWidth: '100%',
                                                                    maxHeight: isMobile ? '200px' : '300px',
                                                                    borderRadius: '6px',
                                                                    display: 'block'
                                                                }}
                                                            />
                                                        ) : (
                                                            <div style={{
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                gap: '0.5rem',
                                                                padding: '0.5rem',
                                                                background: isMyMessage ? '#c8f0c0' : '#f0f2f5',
                                                                borderRadius: '6px'
                                                            }}>
                                                                <span style={{ fontSize: '1.5rem' }}>🖼️</span>
                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                    <div style={{ 
                                                                        fontSize: '0.875rem', 
                                                                        color: '#111b21',
                                                                        overflow: 'hidden',
                                                                        textOverflow: 'ellipsis',
                                                                        whiteSpace: 'nowrap'
                                                                    }}>
                                                                        {msg.attachment.name}
                                                                    </div>
                                                                    <div style={{ fontSize: '0.75rem', color: '#667781' }}>
                                                                        {formatFileSize(msg.attachment.size)}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )
                                                    ) : (
                                                        <div style={{
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '0.5rem',
                                                            padding: '0.5rem',
                                                            background: isMyMessage ? '#c8f0c0' : '#f0f2f5',
                                                            borderRadius: '6px'
                                                        }}>
                                                            <span style={{ fontSize: '1.5rem' }}>📎</span>
                                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                                <div style={{ 
                                                                    fontSize: '0.875rem', 
                                                                    color: '#111b21',
                                                                    overflow: 'hidden',
                                                                    textOverflow: 'ellipsis',
                                                                    whiteSpace: 'nowrap'
                                                                }}>
                                                                    {msg.attachment.name}
                                                                </div>
                                                                <div style={{ fontSize: '0.75rem', color: '#667781' }}>
                                                                    {formatFileSize(msg.attachment.size)}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                            
                                            {/* Timestamp */}
                                            <div style={{
                                                fontSize: '0.6875rem',
                                                color: '#667781',
                                                marginTop: '0.25rem',
                                                textAlign: 'right',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'flex-end',
                                                gap: '0.25rem'
                                            }}>
                                                {new Date(msg.timestamp).toLocaleTimeString('pt-BR', {
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                                {isMyMessage && <span style={{ color: '#53bdeb' }}>✓✓</span>}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input */}
                    <div style={{
                        padding: isMobile ? '0.5rem' : '0.75rem',
                        borderTop: '1px solid #e5e7eb',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                        background: '#f0f2f5'
                    }}>
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
                            <div style={{
                                display: 'flex',
                                flexDirection: isMobile ? 'column' : 'row',
                                alignItems: isMobile ? 'flex-start' : 'center',
                                gap: isMobile ? '0.25rem' : '0.5rem',
                                padding: '0.5rem 0.75rem',
                                background: 'white',
                                border: '1px solid #d1d7db',
                                borderRadius: '8px'
                            }}>
                                {attachment.type.startsWith('image/') ? (
                                    <img
                                        src={attachment.data}
                                        alt={attachment.name}
                                        style={{
                                            width: isMobile ? '100%' : '60px',
                                            height: isMobile ? 'auto' : '60px',
                                            maxHeight: isMobile ? '120px' : '60px',
                                            objectFit: 'cover',
                                            borderRadius: '4px'
                                        }}
                                    />
                                ) : (
                                    <span style={{ fontSize: '1.5rem' }}>📎</span>
                                )}
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{ 
                                        fontSize: '0.875rem',
                                        color: '#111b21',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap'
                                    }}>
                                        {attachment.name}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: '#667781' }}>
                                        {formatFileSize(attachment.size)}
                                    </div>
                                </div>
                                <button
                                    onClick={removeAttachment}
                                    type="button"
                                    style={{
                                        background: 'none',
                                        border: 'none',
                                        color: '#ef4444',
                                        cursor: 'pointer',
                                        padding: '0.25rem',
                                        fontSize: '1.25rem',
                                        lineHeight: 1,
                                        borderRadius: '50%',
                                        width: '28px',
                                        height: '28px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        transition: 'background 0.2s'
                                    }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = '#fee'}
                                    onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
                                >
                                    ✕
                                </button>
                            </div>
                        )}

                        <div style={{
                            display: 'flex',
                            gap: '0.5rem',
                            alignItems: 'center'
                        }}>
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                type="button"
                                title="Anexar arquivo"
                                style={{
                                    background: 'white',
                                    border: 'none',
                                    borderRadius: '50%',
                                    padding: '0.625rem',
                                    cursor: 'pointer',
                                    fontSize: '1.25rem',
                                    transition: 'all 0.2s',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: '40px',
                                    height: '40px',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = '#f0f2f5'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                            >
                                📎
                            </button>
                            <div style={{
                                flex: 1,
                                display: 'flex',
                                background: 'white',
                                borderRadius: '24px',
                                padding: '0.5rem 1rem',
                                alignItems: 'center',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                            }}>
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                                    placeholder="Digite uma mensagem..."
                                    style={{
                                        flex: 1,
                                        border: 'none',
                                        outline: 'none',
                                        fontSize: isMobile ? '16px' : '0.9375rem',
                                        background: 'transparent',
                                        color: '#111b21'
                                    }}
                                />
                            </div>
                            <button
                                onClick={sendMessage}
                                disabled={!newMessage.trim() && !attachment}
                                style={{
                                    background: (!newMessage.trim() && !attachment) ? '#d1d7db' : '#00a884',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '50%',
                                    cursor: (!newMessage.trim() && !attachment) ? 'not-allowed' : 'pointer',
                                    transition: 'background 0.2s',
                                    width: '40px',
                                    height: '40px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '1.25rem',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                                }}
                                onMouseEnter={(e) => {
                                    if (newMessage.trim() || attachment) {
                                        e.currentTarget.style.background = '#06cf9c';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (newMessage.trim() || attachment) {
                                        e.currentTarget.style.background = '#00a884';
                                    }
                                }}
                            >
                                ➤
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
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.85)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 10000
                    }}
                >
                    <div 
                        className="image-modal-content" 
                        onClick={(e) => e.stopPropagation()}
                        style={{
                            position: 'relative',
                            maxWidth: isMobile ? '95vw' : '90vw',
                            maxHeight: isMobile ? '95vh' : '90vh',
                            background: 'white',
                            borderRadius: '12px',
                            padding: isMobile ? '0.5rem' : '1rem',
                            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
                        }}
                    >
                        <button 
                            className="image-modal-close"
                            onClick={() => setImageModal(null)}
                            style={{
                                position: 'absolute',
                                top: isMobile ? '-10px' : '-15px',
                                right: isMobile ? '-10px' : '-15px',
                                width: isMobile ? '32px' : '40px',
                                height: isMobile ? '32px' : '40px',
                                background: '#ef4444',
                                color: 'white',
                                border: '3px solid white',
                                borderRadius: '50%',
                                fontSize: isMobile ? '1.25rem' : '1.5rem',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 'bold',
                                lineHeight: 1
                            }}
                        >
                            ×
                        </button>
                        <img 
                            src={imageModal.src} 
                            alt={imageModal.name}
                            style={{
                                maxWidth: '100%',
                                maxHeight: isMobile ? 'calc(95vh - 60px)' : 'calc(90vh - 80px)',
                                display: 'block',
                                borderRadius: '8px'
                            }}
                        />
                        <p style={{
                            margin: isMobile ? '0.5rem 0 0 0' : '0.75rem 0 0 0',
                            textAlign: 'center',
                            color: '#374151',
                            fontSize: isMobile ? '0.8rem' : '0.875rem',
                            fontWeight: '500'
                        }}>{imageModal.name}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatWorkspace;

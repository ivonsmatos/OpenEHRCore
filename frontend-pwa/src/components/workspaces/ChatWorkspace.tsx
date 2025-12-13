/**
 * Chat Workspace - Internal FHIR-based Communication
 * 
 * Uses FHIR Communication resources for clinical messaging.
 * Mattermost integration was removed from the project.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Card from '../base/Card';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Channel {
    id: string;
    name: string;
    type: 'group' | 'dm';
    description?: string;
}

interface Message {
    id: string;
    sender: string;
    content: string;
    timestamp: string;
}

const ChatWorkspace: React.FC = () => {
    const [channels, setChannels] = useState<Channel[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const fetchChannels = useCallback(async () => {
        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/chat/channels/`, { headers });

            // Format channels from response
            const channelList: Channel[] = [
                { id: 'general', name: '#geral', type: 'group', description: 'Canal geral da equipe' },
                { id: 'urgencia', name: '#urgência', type: 'group', description: 'Casos urgentes' },
                { id: 'laboratorio', name: '#laboratório', type: 'group', description: 'Resultados de exames' },
            ];

            // Add practitioners as DM channels
            if (response.data?.practitioners) {
                response.data.practitioners.forEach((p: any) => {
                    channelList.push({
                        id: `dm-${p.id}`,
                        name: p.name || `Dr. ${p.id}`,
                        type: 'dm'
                    });
                });
            }

            setChannels(channelList);
            if (channelList.length > 0 && !selectedChannel) {
                setSelectedChannel(channelList[0].id);
            }
        } catch (error) {
            console.error('Error fetching channels:', error);
            // Set default channels
            setChannels([
                { id: 'general', name: '#geral', type: 'group', description: 'Canal geral da equipe' },
                { id: 'urgencia', name: '#urgência', type: 'group', description: 'Casos urgentes' },
            ]);
        } finally {
            setLoading(false);
        }
    }, [selectedChannel]);

    const fetchMessages = useCallback(async () => {
        if (!selectedChannel) return;

        try {
            const headers = getAuthHeaders();
            const response = await axios.get(`${API_URL}/chat/messages/?channel_id=${selectedChannel}`, { headers });

            if (response.data?.messages) {
                setMessages(response.data.messages.map((m: any) => ({
                    id: m.id,
                    sender: m.sender || 'Sistema',
                    content: m.content || m.payload?.contentString || '',
                    timestamp: m.sent || new Date().toISOString()
                })));
            } else {
                setMessages([]);
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
            // Demo messages
            setMessages([
                { id: '1', sender: 'Sistema', content: 'Bem-vindo ao chat clínico!', timestamp: new Date().toISOString() },
                { id: '2', sender: 'Sistema', content: 'Use este canal para comunicação entre a equipe.', timestamp: new Date().toISOString() },
            ]);
        }
    }, [selectedChannel]);

    useEffect(() => {
        fetchChannels();
    }, [fetchChannels]);

    useEffect(() => {
        fetchMessages();
    }, [fetchMessages]);

    const sendMessage = async () => {
        if (!newMessage.trim() || !selectedChannel) return;

        try {
            const headers = getAuthHeaders();
            await axios.post(`${API_URL}/chat/send/`, {
                channel_id: selectedChannel,
                content: newMessage
            }, { headers });

            setNewMessage('');
            fetchMessages();
        } catch (error) {
            console.error('Error sending message:', error);
            // Add locally for demo
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                sender: 'Você',
                content: newMessage,
                timestamp: new Date().toISOString()
            }]);
            setNewMessage('');
        }
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <p>Carregando chat...</p>
            </div>
        );
    }

    return (
        <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div style={{ marginBottom: '1rem' }}>
                <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#1e3a5f' }}>
                    💬 Chat Clínico
                </h1>
                <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.875rem' }}>
                    Comunicação segura entre a equipe de saúde
                </p>
            </div>

            {/* Chat Layout */}
            <div style={{ display: 'flex', flex: 1, gap: '1rem', overflow: 'hidden' }}>
                {/* Channels Sidebar */}
                <Card style={{ width: '250px', padding: '1rem', overflow: 'auto' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.875rem', color: '#64748b', textTransform: 'uppercase' }}>
                        Canais
                    </h3>
                    {channels.filter(c => c.type === 'group').map(channel => (
                        <div
                            key={channel.id}
                            onClick={() => setSelectedChannel(channel.id)}
                            style={{
                                padding: '0.75rem',
                                marginBottom: '0.5rem',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                background: selectedChannel === channel.id ? '#dbeafe' : 'transparent',
                                color: selectedChannel === channel.id ? '#1e40af' : '#374151'
                            }}
                        >
                            <div style={{ fontWeight: '500' }}>{channel.name}</div>
                            {channel.description && (
                                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{channel.description}</div>
                            )}
                        </div>
                    ))}

                    <h3 style={{ margin: '1.5rem 0 1rem 0', fontSize: '0.875rem', color: '#64748b', textTransform: 'uppercase' }}>
                        Mensagens Diretas
                    </h3>
                    {channels.filter(c => c.type === 'dm').map(channel => (
                        <div
                            key={channel.id}
                            onClick={() => setSelectedChannel(channel.id)}
                            style={{
                                padding: '0.75rem',
                                marginBottom: '0.5rem',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                background: selectedChannel === channel.id ? '#dbeafe' : 'transparent',
                                color: selectedChannel === channel.id ? '#1e40af' : '#374151',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            <span style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: '#10b981'
                            }} />
                            {channel.name}
                        </div>
                    ))}
                </Card>

                {/* Messages Area */}
                <Card style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                    {/* Messages List */}
                    <div style={{ flex: 1, padding: '1rem', overflow: 'auto' }}>
                        {messages.length === 0 ? (
                            <div style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
                                <p>Nenhuma mensagem ainda.</p>
                                <p>Comece uma conversa!</p>
                            </div>
                        ) : (
                            messages.map(msg => (
                                <div key={msg.id} style={{ marginBottom: '1rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                                        <span style={{ fontWeight: '600', color: '#1e3a5f' }}>{msg.sender}</span>
                                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                                            {new Date(msg.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                    <p style={{ margin: '0.25rem 0 0 0', color: '#374151' }}>{msg.content}</p>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Message Input */}
                    <div style={{
                        padding: '1rem',
                        borderTop: '1px solid #e5e7eb',
                        display: 'flex',
                        gap: '0.75rem'
                    }}>
                        <input
                            type="text"
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Digite uma mensagem..."
                            style={{
                                flex: 1,
                                padding: '0.75rem 1rem',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                fontSize: '0.875rem'
                            }}
                        />
                        <button
                            onClick={sendMessage}
                            style={{
                                padding: '0.75rem 1.5rem',
                                background: '#3b82f6',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '500'
                            }}
                        >
                            Enviar
                        </button>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default ChatWorkspace;

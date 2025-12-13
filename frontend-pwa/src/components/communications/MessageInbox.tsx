/**
 * MessageInbox - Inbox de Comunicações entre Profissionais
 * 
 * Gerencia mensagens e comunicações FHIR:
 * - Inbox (recebidas)
 * - Enviadas
 * - Pedidos de parecer
 * - Notificações
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import {
    MessageSquare,
    Inbox,
    Send,
    Star,
    Trash2,
    Reply,
    Forward,
    Plus,
    Search,
    User,
    Clock,
    Paperclip,
    CheckCircle,
    AlertCircle,
    Filter,
    X
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface Message {
    id: string;
    subject: string;
    sender: string;
    senderId: string;
    recipient: string;
    recipientId: string;
    content: string;
    timestamp: string;
    read: boolean;
    starred: boolean;
    priority: 'routine' | 'urgent' | 'stat';
    category: 'message' | 'opinion_request' | 'notification' | 'alert';
    patientRef?: string;
    patientName?: string;
    attachments?: number;
}

type TabType = 'inbox' | 'sent' | 'opinions' | 'starred';

const MessageInbox: React.FC = () => {
    const { token, user } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabType>('inbox');
    const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
    const [showCompose, setShowCompose] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    // Compose form
    const [composeData, setComposeData] = useState({
        recipient: '',
        subject: '',
        content: '',
        priority: 'routine' as 'routine' | 'urgent' | 'stat',
        category: 'message' as 'message' | 'opinion_request',
        patientRef: ''
    });

    useEffect(() => {
        fetchMessages();
    }, [activeTab]);

    const fetchMessages = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/communications/${activeTab}/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setMessages(response.data.messages || []);
        } catch (err) {
            // Mock data for demo
            setMessages([
                {
                    id: '1',
                    subject: 'Parecer sobre paciente João Silva',
                    sender: 'Dra. Maria Santos',
                    senderId: 'pract-1',
                    recipient: user?.name || 'Você',
                    recipientId: 'pract-2',
                    content: 'Prezado colega, gostaria de solicitar sua opinião sobre o caso do paciente João Silva, 65 anos, com quadro de dor torácica atípica. Os exames laboratoriais mostram elevação de troponina...',
                    timestamp: new Date(Date.now() - 3600000).toISOString(),
                    read: false,
                    starred: true,
                    priority: 'urgent',
                    category: 'opinion_request',
                    patientRef: 'Patient/12345',
                    patientName: 'João Silva',
                    attachments: 2
                },
                {
                    id: '2',
                    subject: 'Resultado de exame - Maria Oliveira',
                    sender: 'Laboratório Central',
                    senderId: 'lab-1',
                    recipient: user?.name || 'Você',
                    recipientId: 'pract-2',
                    content: 'O resultado do hemograma da paciente Maria Oliveira está disponível. Valores dentro da normalidade.',
                    timestamp: new Date(Date.now() - 86400000).toISOString(),
                    read: true,
                    starred: false,
                    priority: 'routine',
                    category: 'notification',
                    patientRef: 'Patient/67890',
                    patientName: 'Maria Oliveira'
                },
                {
                    id: '3',
                    subject: 'Agendamento de reunião clínica',
                    sender: 'Dr. Carlos Pereira',
                    senderId: 'pract-3',
                    recipient: user?.name || 'Você',
                    recipientId: 'pract-2',
                    content: 'Convite para reunião clínica amanhã às 14h para discussão de casos complexos.',
                    timestamp: new Date(Date.now() - 172800000).toISOString(),
                    read: true,
                    starred: false,
                    priority: 'routine',
                    category: 'message'
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await axios.post(
                `${API_URL}/communications/send/`,
                composeData,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setShowCompose(false);
            setComposeData({
                recipient: '',
                subject: '',
                content: '',
                priority: 'routine',
                category: 'message',
                patientRef: ''
            });
            if (activeTab === 'sent') fetchMessages();
            alert('Mensagem enviada com sucesso!');
        } catch (err) {
            alert('Erro ao enviar mensagem');
        }
    };

    const markAsRead = async (id: string) => {
        setMessages(prev => prev.map(m => m.id === id ? { ...m, read: true } : m));
    };

    const toggleStar = async (id: string) => {
        setMessages(prev => prev.map(m => m.id === id ? { ...m, starred: !m.starred } : m));
    };

    const deleteMessage = async (id: string) => {
        if (window.confirm('Excluir esta mensagem?')) {
            setMessages(prev => prev.filter(m => m.id !== id));
            if (selectedMessage?.id === id) setSelectedMessage(null);
        }
    };

    const filteredMessages = messages.filter(m => {
        if (activeTab === 'starred' && !m.starred) return false;
        if (activeTab === 'opinions' && m.category !== 'opinion_request') return false;
        if (searchTerm &&
            !m.subject.toLowerCase().includes(searchTerm.toLowerCase()) &&
            !m.sender.toLowerCase().includes(searchTerm.toLowerCase())) return false;
        return true;
    });

    const unreadCount = messages.filter(m => !m.read).length;
    const urgentCount = messages.filter(m => m.priority === 'urgent' || m.priority === 'stat').length;

    const tabs = [
        { id: 'inbox' as const, label: 'Inbox', icon: Inbox, count: unreadCount },
        { id: 'sent' as const, label: 'Enviadas', icon: Send },
        { id: 'opinions' as const, label: 'Pareceres', icon: MessageSquare },
        { id: 'starred' as const, label: 'Favoritas', icon: Star },
    ];

    const priorityColors = {
        routine: { bg: '#f3f4f6', text: '#6b7280' },
        urgent: { bg: '#fef3c7', text: '#d97706' },
        stat: { bg: '#fee2e2', text: '#dc2626' }
    };

    return (
        <div className="message-inbox flex gap-4 h-[600px]">
            {/* Sidebar */}
            <div className="w-64 flex flex-col gap-4">
                <Button onClick={() => setShowCompose(true)} className="w-full">
                    <Plus size={16} className="mr-1" />
                    Nova Mensagem
                </Button>

                <Card className="p-0 overflow-hidden">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => { setActiveTab(tab.id); setSelectedMessage(null); }}
                            className={`w-full flex items-center justify-between px-4 py-3 text-left transition-colors ${activeTab === tab.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                                }`}
                        >
                            <span className="flex items-center gap-2">
                                <tab.icon size={18} />
                                {tab.label}
                            </span>
                            {tab.count !== undefined && tab.count > 0 && (
                                <span className="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">
                                    {tab.count}
                                </span>
                            )}
                        </button>
                    ))}
                </Card>

                {urgentCount > 0 && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-700 flex items-center gap-2">
                            <AlertCircle size={16} />
                            {urgentCount} mensagem(ns) urgente(s)
                        </p>
                    </div>
                )}
            </div>

            {/* Message List & Detail */}
            <div className="flex-1 flex gap-4">
                {/* List */}
                <Card className="w-2/5 flex flex-col overflow-hidden">
                    {/* Search */}
                    <div className="p-3 border-b">
                        <div className="relative">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Buscar mensagens..."
                                className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm"
                            />
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto">
                        {loading ? (
                            <p className="text-center text-gray-500 py-8">Carregando...</p>
                        ) : filteredMessages.length === 0 ? (
                            <p className="text-center text-gray-500 py-8 italic">Nenhuma mensagem</p>
                        ) : (
                            filteredMessages.map(msg => (
                                <div
                                    key={msg.id}
                                    onClick={() => { setSelectedMessage(msg); markAsRead(msg.id); }}
                                    className={`p-3 border-b cursor-pointer transition-colors ${selectedMessage?.id === msg.id ? 'bg-blue-50' :
                                            !msg.read ? 'bg-gray-50' : 'hover:bg-gray-50'
                                        }`}
                                >
                                    <div className="flex items-start gap-2">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); toggleStar(msg.id); }}
                                            className={msg.starred ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'}
                                        >
                                            <Star size={16} fill={msg.starred ? 'currentColor' : 'none'} />
                                        </button>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className={`font-medium truncate ${!msg.read ? 'text-gray-900' : 'text-gray-600'}`}>
                                                    {msg.sender}
                                                </span>
                                                {msg.priority !== 'routine' && (
                                                    <span
                                                        className="text-xs px-1.5 py-0.5 rounded"
                                                        style={{
                                                            backgroundColor: priorityColors[msg.priority].bg,
                                                            color: priorityColors[msg.priority].text
                                                        }}
                                                    >
                                                        {msg.priority === 'urgent' ? 'Urgente' : 'STAT'}
                                                    </span>
                                                )}
                                            </div>
                                            <p className={`text-sm truncate ${!msg.read ? 'font-medium' : ''}`}>
                                                {msg.subject}
                                            </p>
                                            <p className="text-xs text-gray-400">
                                                {new Date(msg.timestamp).toLocaleString('pt-BR', {
                                                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                                                })}
                                            </p>
                                        </div>
                                        {msg.attachments && msg.attachments > 0 && (
                                            <Paperclip size={14} className="text-gray-400" />
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Card>

                {/* Detail */}
                <Card className="flex-1 flex flex-col overflow-hidden">
                    {selectedMessage ? (
                        <>
                            {/* Header */}
                            <div className="p-4 border-b">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="text-lg font-semibold">{selectedMessage.subject}</h3>
                                        <p className="text-sm text-gray-500 flex items-center gap-2">
                                            <User size={14} /> {selectedMessage.sender}
                                            <span className="text-gray-300">|</span>
                                            <Clock size={14} /> {new Date(selectedMessage.timestamp).toLocaleString('pt-BR')}
                                        </p>
                                        {selectedMessage.patientName && (
                                            <p className="text-sm text-blue-600 mt-1">
                                                Paciente: {selectedMessage.patientName}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => toggleStar(selectedMessage.id)}
                                            className={selectedMessage.starred ? 'text-yellow-500' : 'text-gray-400'}
                                        >
                                            <Star size={20} fill={selectedMessage.starred ? 'currentColor' : 'none'} />
                                        </button>
                                        <button
                                            onClick={() => deleteMessage(selectedMessage.id)}
                                            className="text-gray-400 hover:text-red-500"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="flex-1 p-4 overflow-y-auto">
                                <p className="whitespace-pre-wrap text-gray-700">{selectedMessage.content}</p>
                            </div>

                            {/* Actions */}
                            <div className="p-4 border-t flex gap-2">
                                <Button variant="secondary">
                                    <Reply size={16} className="mr-1" />
                                    Responder
                                </Button>
                                <Button variant="secondary">
                                    <Forward size={16} className="mr-1" />
                                    Encaminhar
                                </Button>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-400">
                            <div className="text-center">
                                <MessageSquare size={48} className="mx-auto mb-2 opacity-50" />
                                <p>Selecione uma mensagem para visualizar</p>
                            </div>
                        </div>
                    )}
                </Card>
            </div>

            {/* Compose Modal */}
            {showCompose && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-lg p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold">Nova Mensagem</h3>
                            <button onClick={() => setShowCompose(false)} className="text-gray-400 hover:text-gray-600">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSend} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Destinatário</label>
                                <input
                                    type="text"
                                    value={composeData.recipient}
                                    onChange={(e) => setComposeData({ ...composeData, recipient: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    placeholder="Nome ou ID do profissional"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Assunto</label>
                                <input
                                    type="text"
                                    value={composeData.subject}
                                    onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    placeholder="Assunto da mensagem"
                                    required
                                />
                            </div>

                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
                                    <select
                                        value={composeData.priority}
                                        onChange={(e) => setComposeData({ ...composeData, priority: e.target.value as any })}
                                        className="w-full p-2 border border-gray-300 rounded-lg"
                                        aria-label="Prioridade"
                                    >
                                        <option value="routine">Rotina</option>
                                        <option value="urgent">Urgente</option>
                                        <option value="stat">STAT</option>
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                                    <select
                                        value={composeData.category}
                                        onChange={(e) => setComposeData({ ...composeData, category: e.target.value as any })}
                                        className="w-full p-2 border border-gray-300 rounded-lg"
                                        aria-label="Tipo de mensagem"
                                    >
                                        <option value="message">Mensagem</option>
                                        <option value="opinion_request">Pedido de Parecer</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Mensagem</label>
                                <textarea
                                    value={composeData.content}
                                    onChange={(e) => setComposeData({ ...composeData, content: e.target.value })}
                                    className="w-full p-2 border border-gray-300 rounded-lg"
                                    rows={5}
                                    placeholder="Digite sua mensagem..."
                                    required
                                />
                            </div>

                            <div className="flex justify-end gap-2 pt-2">
                                <Button variant="secondary" type="button" onClick={() => setShowCompose(false)}>
                                    Cancelar
                                </Button>
                                <Button type="submit">
                                    <Send size={16} className="mr-1" />
                                    Enviar
                                </Button>
                            </div>
                        </form>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default MessageInbox;

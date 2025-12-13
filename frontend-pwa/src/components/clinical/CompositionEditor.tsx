/**
 * CompositionEditor - Editor de Documentos Clínicos FHIR
 * 
 * Permite criar e editar Compositions (documentos estruturados):
 * - Sumário de Alta
 * - Notas de Evolução
 * - Notas Operatórias
 * - Notas de Admissão
 * - Atestados
 * - Prescrições
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import Card from '../base/Card';
import Button from '../base/Button';
import {
    FileText,
    Save,
    Send,
    Clock,
    CheckCircle,
    AlertTriangle,
    Plus,
    Trash2,
    Edit3,
    FileSignature,
    User,
    Calendar,
    Stethoscope
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface CompositionEditorProps {
    patientId: string;
    patientName: string;
    encounterId?: string;
    onSave?: (composition: any) => void;
    initialType?: CompositionType;
}

type CompositionType =
    | 'discharge-summary'      // Sumário de Alta
    | 'progress-note'          // Nota de Evolução
    | 'operative-note'         // Nota Operatória
    | 'admission-note'         // Nota de Admissão
    | 'medical-certificate'    // Atestado Médico
    | 'consultation-note';     // Nota de Consulta

interface Section {
    id: string;
    title: string;
    code: string;
    content: string;
    required?: boolean;
}

const COMPOSITION_TYPES: Record<CompositionType, { label: string; icon: string; sections: Omit<Section, 'id' | 'content'>[] }> = {
    'discharge-summary': {
        label: 'Sumário de Alta',
        icon: '📋',
        sections: [
            { title: 'Motivo da Internação', code: '46241-6', required: true },
            { title: 'Diagnóstico Principal', code: '29308-4', required: true },
            { title: 'Diagnósticos Secundários', code: '11450-4' },
            { title: 'Procedimentos Realizados', code: '47519-4' },
            { title: 'Medicamentos na Alta', code: '10160-0', required: true },
            { title: 'Orientações ao Paciente', code: '69730-0', required: true },
            { title: 'Acompanhamento', code: '18776-5' },
        ]
    },
    'progress-note': {
        label: 'Nota de Evolução',
        icon: '📝',
        sections: [
            { title: 'Subjetivo (Queixas)', code: '10154-3', required: true },
            { title: 'Objetivo (Exame Físico)', code: '10210-3', required: true },
            { title: 'Avaliação', code: '51848-0', required: true },
            { title: 'Plano', code: '18776-5', required: true },
        ]
    },
    'operative-note': {
        label: 'Nota Operatória',
        icon: '🏥',
        sections: [
            { title: 'Diagnóstico Pré-operatório', code: '10219-4', required: true },
            { title: 'Diagnóstico Pós-operatório', code: '10218-6', required: true },
            { title: 'Procedimento', code: '29554-3', required: true },
            { title: 'Descrição da Cirurgia', code: '8724-7', required: true },
            { title: 'Achados', code: '59776-5' },
            { title: 'Complicações', code: '55109-3' },
            { title: 'Espécimes', code: '22634-0' },
        ]
    },
    'admission-note': {
        label: 'Nota de Admissão',
        icon: '🚪',
        sections: [
            { title: 'Queixa Principal', code: '10154-3', required: true },
            { title: 'História da Doença Atual', code: '10164-2', required: true },
            { title: 'Antecedentes Pessoais', code: '11348-0' },
            { title: 'Antecedentes Familiares', code: '10157-6' },
            { title: 'Exame Físico', code: '10210-3', required: true },
            { title: 'Hipóteses Diagnósticas', code: '51848-0', required: true },
            { title: 'Plano Terapêutico', code: '18776-5', required: true },
        ]
    },
    'medical-certificate': {
        label: 'Atestado Médico',
        icon: '📄',
        sections: [
            { title: 'Período de Afastamento', code: '48765-2', required: true },
            { title: 'CID-10', code: '29308-4', required: true },
            { title: 'Observações', code: '48767-8' },
        ]
    },
    'consultation-note': {
        label: 'Nota de Consulta',
        icon: '👨‍⚕️',
        sections: [
            { title: 'Motivo da Consulta', code: '10154-3', required: true },
            { title: 'Anamnese', code: '10164-2' },
            { title: 'Exame Físico', code: '10210-3' },
            { title: 'Impressão Diagnóstica', code: '51848-0', required: true },
            { title: 'Conduta', code: '18776-5', required: true },
        ]
    },
};

const CompositionEditor: React.FC<CompositionEditorProps> = ({
    patientId,
    patientName,
    encounterId,
    onSave,
    initialType = 'consultation-note'
}) => {
    const { token, user } = useAuth();
    const [compositionType, setCompositionType] = useState<CompositionType>(initialType);
    const [sections, setSections] = useState<Section[]>([]);
    const [title, setTitle] = useState('');
    const [status, setStatus] = useState<'preliminary' | 'final'>('preliminary');
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Inicializar seções quando tipo muda
    useEffect(() => {
        const typeConfig = COMPOSITION_TYPES[compositionType];
        const initialSections: Section[] = typeConfig.sections.map((s, index) => ({
            id: `section-${index}`,
            title: s.title,
            code: s.code,
            content: '',
            required: s.required
        }));
        setSections(initialSections);
        setTitle(`${typeConfig.label} - ${patientName}`);
    }, [compositionType, patientName]);

    const updateSection = (id: string, content: string) => {
        setSections(prev => prev.map(s => s.id === id ? { ...s, content } : s));
        setSaved(false);
    };

    const handleSave = async (finalStatus: 'preliminary' | 'final' = 'preliminary') => {
        // Validar seções obrigatórias
        const missingRequired = sections.filter(s => s.required && !s.content.trim());
        if (missingRequired.length > 0) {
            setError(`Preencha os campos obrigatórios: ${missingRequired.map(s => s.title).join(', ')}`);
            return;
        }

        setSaving(true);
        setError(null);

        try {
            const compositionData = {
                patient_id: patientId,
                encounter_id: encounterId,
                type: compositionType,
                title: title,
                status: finalStatus,
                sections: sections.map(s => ({
                    title: s.title,
                    code: s.code,
                    text: s.content
                })),
                date: new Date().toISOString()
            };

            const response = await axios.post(
                `${API_URL}/compositions/`,
                compositionData,
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setSaved(true);
            setStatus(finalStatus);
            onSave?.(response.data);

            if (finalStatus === 'final') {
                alert('Documento finalizado com sucesso!');
            }
        } catch (err: any) {
            setError(err.response?.data?.message || 'Erro ao salvar documento');
        } finally {
            setSaving(false);
        }
    };

    const typeConfig = COMPOSITION_TYPES[compositionType];

    return (
        <div className="composition-editor space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start flex-wrap gap-4">
                <div>
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <FileText className="text-blue-600" />
                        Editor de Documentos Clínicos
                    </h2>
                    <p className="text-gray-500 flex items-center gap-2 mt-1">
                        <User size={14} /> {patientName}
                        <span className="text-gray-300">|</span>
                        <Calendar size={14} /> {new Date().toLocaleDateString('pt-BR')}
                    </p>
                </div>

                <div className="flex gap-2">
                    <Button
                        variant="secondary"
                        onClick={() => handleSave('preliminary')}
                        disabled={saving}
                    >
                        <Save size={16} className="mr-1" />
                        {saving ? 'Salvando...' : 'Salvar Rascunho'}
                    </Button>
                    <Button
                        onClick={() => handleSave('final')}
                        disabled={saving}
                    >
                        <Send size={16} className="mr-1" />
                        Finalizar
                    </Button>
                </div>
            </div>

            {/* Status e erros */}
            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
                    <AlertTriangle size={18} />
                    {error}
                </div>
            )}

            {saved && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
                    <CheckCircle size={18} />
                    Documento salvo como {status === 'final' ? 'final' : 'rascunho'}
                </div>
            )}

            {/* Tipo de documento */}
            <Card className="p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Documento
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                    {Object.entries(COMPOSITION_TYPES).map(([type, config]) => (
                        <button
                            key={type}
                            onClick={() => setCompositionType(type as CompositionType)}
                            className={`p-3 rounded-lg border-2 transition-all text-left ${compositionType === type
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                }`}
                        >
                            <span className="text-2xl block mb-1">{config.icon}</span>
                            <span className="text-sm font-medium">{config.label}</span>
                        </button>
                    ))}
                </div>
            </Card>

            {/* Título */}
            <Card className="p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Título do Documento
                </label>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Título do documento..."
                />
            </Card>

            {/* Seções */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                    <Edit3 size={18} />
                    Seções do Documento
                </h3>

                {sections.map((section) => (
                    <Card key={section.id} className="p-4">
                        <div className="flex justify-between items-center mb-2">
                            <label className="block font-medium text-gray-700">
                                {section.title}
                                {section.required && <span className="text-red-500 ml-1">*</span>}
                            </label>
                            <span className="text-xs text-gray-400">LOINC: {section.code}</span>
                        </div>
                        <textarea
                            value={section.content}
                            onChange={(e) => updateSection(section.id, e.target.value)}
                            className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[120px] ${section.required && !section.content.trim()
                                    ? 'border-amber-300 bg-amber-50'
                                    : 'border-gray-300'
                                }`}
                            placeholder={`Descreva: ${section.title.toLowerCase()}...`}
                        />
                    </Card>
                ))}
            </div>

            {/* Footer info */}
            <div className="text-sm text-gray-500 flex items-center gap-4 pt-4 border-t">
                <span className="flex items-center gap-1">
                    <Stethoscope size={14} />
                    Profissional: {user?.name || 'Não identificado'}
                </span>
                <span className="flex items-center gap-1">
                    <Clock size={14} />
                    Status: {status === 'final' ? 'Finalizado' : 'Rascunho'}
                </span>
                <span className="flex items-center gap-1">
                    <FileSignature size={14} />
                    FHIR Composition R4
                </span>
            </div>
        </div>
    );
};

export default CompositionEditor;

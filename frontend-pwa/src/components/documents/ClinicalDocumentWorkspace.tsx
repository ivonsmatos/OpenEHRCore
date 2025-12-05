
import React, { useState } from 'react';
import { FileText, Plus, FileSearch, Printer } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Button from '../base/Button';
import Card from '../base/Card';

// Componente Placeholder temporário enquanto criamos o form real
const AnamnesisForm = ({ onCancel }: { onCancel: () => void }) => (
    <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">Nova Anamnese</h3>
        <p className="text-sm text-gray-600 mb-4">Formulário em construção...</p>
        <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
    </div>
);

const ClinicalDocumentWorkspace: React.FC = () => {
    // const { user } = useAuth(); // Unused for now
    const [viewMode, setViewMode] = useState<'list' | 'create'>('list');

    // Mock data for initial display
    const documents = [
        { id: '1', title: 'Evolução Diária', date: '2023-10-25', author: 'Dr. Ivon Matos', type: 'Evolução' },
        { id: '2', title: 'Anamnese Inicial', date: '2023-10-24', author: 'Dr. Ivon Matos', type: 'Anamnese' },
    ];

    return (
        <div className="space-y-6">
            <header className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                        <FileText className="text-indigo-600" />
                        Documentos Clínicos
                    </h1>
                    <p className="text-slate-600">Gestão de prontuário, evoluções e atestados.</p>
                </div>
                {viewMode === 'list' && (
                    <Button onClick={() => setViewMode('create')}>
                        <Plus size={20} className="mr-2" />
                        Novo Documento
                    </Button>
                )}
            </header>

            {viewMode === 'list' ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {documents.map((doc) => (
                        <Card key={doc.id} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-indigo-500">
                            <div className="p-4 flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <FileText size={16} className="text-gray-400" />
                                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{doc.type}</span>
                                    </div>
                                    <h3 className="font-semibold text-lg text-slate-800">{doc.title}</h3>
                                    <p className="text-sm text-slate-500 mt-1">Autor: {doc.author}</p>
                                    <p className="text-xs text-slate-400 mt-1">{doc.date}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full" title="Visualizar">
                                        <FileSearch size={18} />
                                    </button>
                                    <button className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full" title="Imprimir PDF">
                                        <Printer size={18} />
                                    </button>
                                </div>
                            </div>
                        </Card>
                    ))}

                    {documents.length === 0 && (
                        <div className="col-span-full py-12 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                            <FileText size={48} className="mx-auto mb-4 opacity-20" />
                            <p>Nenhum documento encontrado.</p>
                            <Button variant="secondary" className="mt-4" onClick={() => setViewMode('create')}>
                                Criar Primeiro Documento
                            </Button>
                        </div>
                    )}
                </div>
            ) : (
                <Card>
                    <div className="p-6">
                        <AnamnesisForm onCancel={() => setViewMode('list')} />
                    </div>
                </Card>
            )}
        </div>
    );
};

export default ClinicalDocumentWorkspace;

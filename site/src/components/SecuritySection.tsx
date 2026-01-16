
import { Shield, Lock, FileCheck, Server } from 'lucide-react';

export const SecuritySection = () => {
    return (
        <section id="security" className="py-24 bg-slate-50 border-t border-slate-100">
            <div className="container mx-auto px-6 grid md:grid-cols-2 gap-16 items-center">
                <div>
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-primary-700 text-sm font-semibold border border-blue-200 mb-6">
                        <Shield className="w-4 h-4" /> Segurança Garantida
                    </div>
                    <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6">Proteção de dados em primeiro lugar.</h2>
                    <p className="text-slate-600 text-lg mb-8 leading-relaxed">
                        A conformidade com a LGPD e HIPAA não é opcional. Nossa arquitetura foi validada para garantir a privacidade e segurança do paciente.
                    </p>

                    <div className="space-y-6">
                        <div className="flex gap-4">
                            <div className="bg-white p-3 rounded-lg h-fit shadow-sm border border-slate-100">
                                <Lock className="w-6 h-6 text-primary-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-800 mb-2">Criptografia AES-256</h3>
                                <p className="text-slate-600">Dados criptografados em repouso e em trânsito, garantindo confidencialidade total.</p>
                            </div>
                        </div>

                        <div className="flex gap-4">
                            <div className="bg-white p-3 rounded-lg h-fit shadow-sm border border-slate-100">
                                <FileCheck className="w-6 h-6 text-accent-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-800 mb-2">Auditoria Completa</h3>
                                <p className="text-slate-600">Rastreabilidade total de quem acessou o quê, quando e onde. Logs imutáveis.</p>
                            </div>
                        </div>

                        <div className="flex gap-4">
                            <div className="bg-white p-3 rounded-lg h-fit shadow-sm border border-slate-100">
                                <Server className="w-6 h-6 text-indigo-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-800 mb-2">Redundância Geográfica</h3>
                                <p className="text-slate-600">Arquitetura distribuída para alta disponibilidade e recuperação de desastres.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="relative">
                    {/* Light theme security visual */}
                    <div className="relative bg-white border border-slate-200 rounded-2xl p-8 shadow-2xl">
                        <div className="flex items-center justify-between mb-8 border-b border-slate-100 pb-4">
                            <span className="text-sm font-mono text-slate-500">PAINEL DE SEGURANÇA</span>
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded font-bold border border-green-200">VERIFICADO</span>
                        </div>
                        <div className="space-y-4 font-mono text-sm">
                            <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                                <span className="text-slate-600 flex gap-2 items-center"><Lock className="w-4 h-4" /> Banco de Dados</span>
                                <span className="text-green-600 font-bold text-xs uppercase bg-green-50 px-2 py-1 rounded">Encriptado</span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                                <span className="text-slate-600 flex gap-2 items-center"><Shield className="w-4 h-4" /> Transmissão TLS</span>
                                <span className="text-green-600 font-bold text-xs uppercase bg-green-50 px-2 py-1 rounded">Seguro 1.3</span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                                <span className="text-slate-600 flex gap-2 items-center"><FileCheck className="w-4 h-4" /> Consentimento LGPD</span>
                                <span className="text-blue-600 font-bold text-xs uppercase bg-blue-50 px-2 py-1 rounded">Ativo</span>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-slate-100 text-center">
                            <p className="text-xs text-slate-400 mb-2">Última auditoria de segurança</p>
                            <p className="text-sm font-bold text-slate-700">Há 2 horas • Sem incidentes</p>
                        </div>
                    </div>

                    {/* Decorative background blur */}
                    <div className="absolute -z-10 inset-0 translate-x-4 translate-y-4 bg-primary-100 rounded-2xl blur-lg opacity-50"></div>
                </div>
            </div>
        </section>
    );
};

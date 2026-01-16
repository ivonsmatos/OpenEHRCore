
import { Mic, Clock, CheckCircle2, Stethoscope, ArrowRight } from 'lucide-react';

export const MedAsrHighlight = () => {
    return (
        <section className="py-24 bg-gradient-to-br from-blue-50/50 to-white overflow-hidden">
            <div className="container mx-auto px-6">
                <div className="flex flex-col lg:flex-row items-center gap-16">

                    {/* Visual Side */}
                    <div className="lg:w-1/2 relative">
                        <div className="relative z-10 bg-white p-8 rounded-2xl shadow-xl border border-blue-100">
                            <div className="flex items-center gap-4 mb-6 border-b border-slate-100 pb-4">
                                <div className="p-3 bg-blue-100 rounded-full text-primary-600">
                                    <Mic className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-slate-800">Transcrição em Tempo Real</h3>
                                    <p className="text-xs text-slate-500 uppercase tracking-wider">Live Demo</p>
                                </div>
                            </div>

                            <div className="space-y-4 font-mono text-sm text-slate-600">
                                <p className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                    <span className="text-blue-500 font-bold mr-2">Médico:</span>
                                    "Paciente relata <span className="text-slate-900 font-bold bg-yellow-100 px-1 rounded">cefaleia tensional</span> há 3 dias. Prescrevo <span className="text-slate-900 font-bold bg-green-100 px-1 rounded">Dipirona 1g</span> VO..."
                                </p>
                                <div className="flex items-center gap-2 text-primary-600 text-xs font-semibold">
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                    Detectando termos médicos...
                                </div>
                            </div>
                        </div>

                        {/* Background Decor */}
                        <div className="absolute top-10 -right-10 w-full h-full bg-blue-600/5 rounded-2xl -z-10 rotate-3"></div>
                        <div className="absolute -bottom-10 -left-10 w-full h-full bg-accent-600/5 rounded-2xl -z-10 -rotate-2"></div>
                    </div>

                    {/* Content Side */}
                    <div className="lg:w-1/2">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100/50 text-primary-700 text-sm font-semibold mb-6">
                            <Stethoscope className="w-4 h-4" /> Caso de Uso Real
                        </div>

                        <h2 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6 leading-tight">
                            Anamnese livre de <br />
                            <span className="text-primary-600">telas e teclados</span>.
                        </h2>

                        <p className="text-lg text-slate-600 mb-8 leading-relaxed">
                            Com o poder do <strong>Google MedASR</strong>, o Synchealth entende o contexto clínico. Não é apenas um "ditado", é uma inteligência que estrutura o prontuário enquanto você conversa com o paciente.
                        </p>

                        <div className="space-y-6">
                            {/* Benefit 1 */}
                            <div className="flex gap-4">
                                <div className="mt-1">
                                    <div className="p-2 bg-green-100 rounded-lg text-green-700">
                                        <Clock className="w-5 h-5" />
                                    </div>
                                </div>
                                <div>
                                    <h4 className="text-xl font-bold text-slate-800">Economia de Tempo</h4>
                                    <p className="text-slate-600 mt-1">
                                        Médicos economizam em média <strong>5 minutos por consulta</strong>. Em um dia com 20 atendimentos, isso significa 1h40m livres.
                                    </p>
                                </div>
                            </div>

                            {/* Benefit 2 */}
                            <div className="flex gap-4">
                                <div className="mt-1">
                                    <div className="p-2 bg-indigo-100 rounded-lg text-indigo-700">
                                        <CheckCircle2 className="w-5 h-5" />
                                    </div>
                                </div>
                                <div>
                                    <h4 className="text-xl font-bold text-slate-800">Vocabulário Especializado</h4>
                                    <p className="text-slate-600 mt-1">
                                        Treinado em milhões de termos médicos. Diferencia "Hipertenso" de "Hipotenso" e reconhece nomes comerciais de fármacos com precisão SOTA (State-of-the-Art).
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </section>
    );
};

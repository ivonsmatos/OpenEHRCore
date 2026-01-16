
import { ArrowRight, Activity, Heart, Users, Mic } from 'lucide-react';
import { motion } from 'framer-motion';

export const Hero = () => {
    return (
        <section className="relative min-h-[90vh] flex items-center bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden pt-20">
            <div className="container mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center">

                {/* Left Content */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8 }}
                    className="z-10"
                >
                    {/* Badge MedASR */}
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white shadow-sm border border-blue-100 text-primary-700 font-semibold mb-6 ring-2 ring-blue-50">
                        <Mic className="w-4 h-4 text-primary-600" />
                        <span>Powered by <span className="font-bold">Google MedASR</span></span>
                    </div>

                    <h1 className="text-5xl md:text-6xl font-bold text-slate-800 mb-6 leading-tight">
                        Transformando a <br />
                        <span className="text-primary-600">Saúde Digital</span> no Brasil
                    </h1>

                    <p className="text-lg text-slate-600 mb-8 leading-relaxed max-w-xl">
                        A primeira plataforma com <strong>Reconhecimento de Fala Médico</strong> de alta precisão. Transcreva consultas em tempo real com a tecnologia líder mundial da Google.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4">
                        <button className="bg-primary-600 hover:bg-primary-700 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all shadow-lg shadow-primary-500/20 hover:-translate-y-1 flex items-center justify-center gap-2">
                            Começar Agora <ArrowRight className="w-5 h-5" />
                        </button>
                        <button className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-8 py-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2">
                            Ver Vídeo Demo
                        </button>
                    </div>

                    <div className="mt-12 flex items-center gap-6 text-slate-500 font-medium text-sm">
                        <div className="flex items-center gap-2">
                            <Heart className="w-5 h-5 text-red-500" /> Cuidado Humanizado
                        </div>
                        <div className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-blue-500" /> +10k Profissionais
                        </div>
                    </div>
                </motion.div>

                {/* Right Image */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="relative hidden lg:block"
                >
                    <div className="relative rounded-[2rem] overflow-hidden shadow-2xl border-4 border-white">
                        <img
                            src="https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=2070"
                            alt="Médica sorrindo atendimento humanizado"
                            className="w-full h-full object-cover"
                        />
                        {/* Floating Badge */}
                        <div className="absolute bottom-8 left-8 bg-white/95 backdrop-blur-sm p-4 rounded-2xl shadow-lg border border-slate-100 flex items-center gap-4">
                            <div className="bg-green-100 p-3 rounded-full">
                                <Activity className="w-6 h-6 text-green-600" />
                            </div>
                            <div>
                                <p className="text-slate-500 text-xs font-bold uppercase">MedASR Ativo</p>
                                <p className="text-slate-800 font-bold">Transcrição: 99.8%</p>
                            </div>
                        </div>
                    </div>

                    {/* Decorative blobs */}
                    <div className="absolute -top-12 -right-12 w-64 h-64 bg-primary-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 z-[-1] animate-pulse"></div>
                    <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-accent-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70 z-[-1] animate-pulse"></div>
                </motion.div>
            </div>
        </section>
    );
};


import { Database, Lock, CloudOff, Smartphone, FileText, Mic } from 'lucide-react';

const features = [
    {
        icon: <Mic className="w-6 h-6 text-primary-600" />,
        title: "Transcrição com Google MedASR",
        description: "Tecnologia de ponta (SOTA) para reconhecimento de fala médica. Transcreva consultas e termos complexos com precisão superior, eliminando a digitação manual."
    },
    {
        icon: <Database className="w-6 h-6 text-accent-600" />,
        title: "FHIR R4 Nativo",
        description: "Interoperabilidade real com mais de 120 endpoints API seguindo o padrão mundial HL7 FHIR."
    },
    {
        icon: <FileText className="w-6 h-6 text-primary-600" />,
        title: "Integrações Brasil",
        description: "Pronto para o mercado nacional: Pagamentos PIX, TISS (ANS), RNDS (Ministério da Saúde) e Telemedicina."
    },
    {
        icon: <CloudOff className="w-6 h-6 text-accent-600" />,
        title: "PWA Offline-First",
        description: "Continue trabalhando mesmo sem internet. O sistema sincroniza automaticamente quando a conexão voltar."
    },
    {
        icon: <Smartphone className="w-6 h-6 text-primary-600" />,
        title: "Mobile-First UX",
        description: "Experiência perfeita em qualquer dispositivo, com chat integrado estilo WhatsApp e responsividade total."
    },
    {
        icon: <Lock className="w-6 h-6 text-accent-600" />,
        title: "Segurança Avançada",
        description: "Conformidade LGPD, autenticação Keycloak SSO e auditoria completa de ações."
    }
];

export const Features = () => {
    return (
        <section id="features" className="py-24 bg-white">
            <div className="container mx-auto px-6">
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <div className="inline-block text-accent-600 font-semibold mb-2 tracking-wide uppercase text-sm">Por que HealthStack?</div>
                    <h2 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6">
                        Tecnologia pensada para <br /><span className="text-primary-600">cuidar de pessoas</span>.
                    </h2>
                    <p className="text-lg text-slate-600">
                        Unimos o poder da interoperabilidade global com as necessidades específicas do sistema de saúde brasileiro.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, index) => (
                        <div key={index} className="bg-slate-50 p-8 rounded-2xl border border-slate-100 hover:shadow-xl transition-all hover:bg-white group cursor-default">
                            <div className="mb-6 p-3 bg-white rounded-xl shadow-sm inline-block group-hover:scale-110 transition-transform">
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-3">{feature.title}</h3>
                            <p className="text-slate-600 leading-relaxed text-sm">
                                {feature.description}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

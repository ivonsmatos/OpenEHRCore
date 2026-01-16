

export const Footer = () => {
    return (
        <footer className="bg-slate-950 text-slate-400 py-12 border-t border-slate-900">
            <div className="container mx-auto px-6 grid md:grid-cols-4 gap-8">
                <div className="col-span-1 md:col-span-2">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-6 h-6 bg-gradient-to-br from-primary-600 to-accent-500 rounded"></div>
                        <span className="text-xl font-bold text-white">Grephub</span>
                    </div>
                    <p className="max-w-xs text-sm">
                        Transformando a saúde com tecnologia inteligente, segura e humana.
                    </p>
                </div>

                <div>
                    <h4 className="font-bold text-white mb-4">Produto</h4>
                    <ul className="space-y-2 text-sm">
                        <li><a href="#features" className="hover:text-primary-400 transition-colors">Funcionalidades</a></li>
                        <li><a href="#security" className="hover:text-primary-400 transition-colors">Segurança</a></li>
                        <li><a href="#" className="hover:text-primary-400 transition-colors">Planos</a></li>
                    </ul>
                </div>

                <div>
                    <h4 className="font-bold text-white mb-4">Empresa</h4>
                    <ul className="space-y-2 text-sm">
                        <li><a href="#" className="hover:text-primary-400 transition-colors">Sobre</a></li>
                        <li><a href="#" className="hover:text-primary-400 transition-colors">Blog</a></li>
                        <li><a href="#" className="hover:text-primary-400 transition-colors">Contato</a></li>
                    </ul>
                </div>
            </div>
            <div className="container mx-auto px-6 mt-12 pt-8 border-t border-slate-900 text-center text-xs">
                © 2026 Grephub / OpenEHRCore. Todos os direitos reservados.
            </div>
        </footer>
    );
};


import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Navbar = () => {
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 10);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <nav className={`fixed w-full z-50 transition-all duration-300 ${isScrolled ? 'bg-white/90 backdrop-blur-md shadow-sm py-4' : 'bg-transparent py-6'}`}>
            <div className="container mx-auto px-6 flex justify-between items-center">
                <a href="#" className="flex items-center gap-2 group">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-accent-500 rounded-lg group-hover:scale-105 transition-transform"></div>
                    <span className="text-xl font-bold tracking-tight text-slate-800">Synchealth</span>
                </a>

                {/* Desktop Menu */}
                <div className="hidden md:flex items-center gap-8">
                    <a href="#features" className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors">Soluções</a>
                    <a href="#security" className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors">Segurança</a>
                    <a href="#about" className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors">Sobre</a>
                    <button className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2.5 rounded-full font-medium transition-all shadow-lg shadow-primary-500/30 hover:shadow-primary-500/40 hover:-translate-y-0.5">
                        Agendar Demo
                    </button>
                </div>

                {/* Mobile Toggle */}
                <button className="md:hidden text-slate-800" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </button>
            </div>

            {/* Mobile Menu */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="md:hidden bg-white border-t border-slate-100 overflow-hidden"
                    >
                        <div className="flex flex-col p-6 space-y-4">
                            <a href="#features" onClick={() => setIsMobileMenuOpen(false)} className="text-slate-600 font-medium hover:text-primary-600 block py-2">Soluções</a>
                            <a href="#security" onClick={() => setIsMobileMenuOpen(false)} className="text-slate-600 font-medium hover:text-primary-600 block py-2">Segurança</a>
                            <a href="#about" onClick={() => setIsMobileMenuOpen(false)} className="text-slate-600 font-medium hover:text-primary-600 block py-2">Sobre</a>
                            <button className="bg-primary-600 text-white px-5 py-3 rounded-lg font-medium w-full shadow-lg shadow-primary-500/20">
                                Agendar Demo
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
};

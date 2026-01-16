
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { SecuritySection } from './components/SecuritySection';
import { Footer } from './components/Footer';

function App() {
  return (
    <div className="font-sans antialiased text-slate-800 bg-white">
      <Navbar />
      <main>
        <Hero />
        <Features />
        <SecuritySection />
      </main>
      <Footer />
    </div>
  );
}

export default App;

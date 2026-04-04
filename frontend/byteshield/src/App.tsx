/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronRight } from 'lucide-react';
import Navbar from './components/Navbar';
import { Hero, Features, RecentScans, TrustLayer } from './components/Features';
import Scanner from './components/Scanner';
import Results from './components/Results';
import { HowItWorks, Footer } from './components/Footer';

export default function App() {
  const [scanResults, setScanResults] = useState<any>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const handleScanComplete = (results: any) => {
    setScanResults(results);
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Global Background Grid */}
      <div className="fixed inset-0 bg-grid -z-50" />
      
      <Navbar />
      
      <main className="flex-grow">
        <AnimatePresence mode="wait">
          {!scanResults ? (
            <motion.div
              key="scanner-page"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <Hero />
              <div className="px-4 sm:px-6 lg:px-8 -mt-32 mb-24 relative z-10">
                <Scanner onScanComplete={handleScanComplete} />
              </div>
              <TrustLayer />
              <HowItWorks />
              <Features />
              <RecentScans />
            </motion.div>
          ) : (
            <motion.div
              key="results-page"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="pt-32"
            >
              <div className="max-w-6xl mx-auto px-4 mb-8">
                <button 
                  onClick={() => setScanResults(null)}
                  className="flex items-center gap-2 text-foreground/40 hover:text-brand-500 transition-colors font-bold uppercase tracking-widest text-xs group"
                >
                  <ChevronRight className="w-4 h-4 rotate-180 group-hover:-translate-x-1 transition-transform" />
                  Back to Scanner
                </button>
              </div>
              <Results data={scanResults} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}

"use client";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Upload, CheckCircle2, Globe, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { cn } from '../lib/utils';
import { scanContent, ScanType } from '../lib/api';

type ScanTab = ScanType;

export default function Scanner({ onScanComplete }: { onScanComplete: (results: any) => void }) {
  const [activeTab, setActiveTab] = useState<ScanTab>('url');
  const [inputValue, setInputValue] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const steps = [
    'Validating Input',
    'Extracting Metadata',
    'Analyzing Signals',
    'Verifying Public Evidence',
    'Generating Safety Advice'
  ];

  const handleScan = async () => {
    if (!inputValue && activeTab !== 'file') return;
    if (activeTab === 'file' && !selectedFile) return;

    setIsScanning(true);
    setProgress(0);
    setCurrentStep(0);
    setError(null);

    try {
      // Progress simulation
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            return prev;
          }
          const next = prev + 3;
          setCurrentStep(Math.floor((next / 100) * steps.length));
          return next;
        });
      }, 100);

      const result = await scanContent({
        type: activeTab,
        url: activeTab === 'url' ? inputValue : undefined,
        text: activeTab === 'text' ? inputValue : undefined,
        file: activeTab === 'file' && selectedFile ? selectedFile : undefined,
      });

      clearInterval(interval);
      setProgress(100);
      setCurrentStep(steps.length - 1);

      setTimeout(() => {
        setIsScanning(false);
        onScanComplete(result);
      }, 500);
    } catch (err) {
      setIsScanning(false);
      setError(err instanceof Error ? err.message : 'An error occurred during scanning');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setInputValue(e.target.files[0].name);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="glass rounded-[2.5rem] overflow-hidden shadow-2xl border-white/10 glow-blue p-2">
        <div className="bg-background/40 rounded-[2rem] p-8 md:p-12">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">
              {error}
            </div>
          )}

          {/* Tabs */}
          <div className="flex items-center justify-center gap-4 mb-12">
            {(['url', 'text', 'file'] as ScanTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "flex items-center gap-3 px-6 py-3 rounded-2xl transition-all font-semibold text-sm",
                  activeTab === tab
                    ? "bg-brand-500/10 text-brand-500 border border-brand-500/20"
                    : "text-foreground/40 hover:text-foreground/60"
                )}
              >
                {tab === 'url' && <Globe className="w-4 h-4" />}
                {tab === 'text' && <MessageSquare className="w-4 h-4" />}
                {tab === 'file' && <Upload className="w-4 h-4" />}
                <span className="capitalize">{tab === 'url' ? 'Scan URL' : tab === 'text' ? 'Scan Text' : 'Scan Photo/File'}</span>
              </button>
            ))}
          </div>

          {/* Input Area */}
          <AnimatePresence mode="wait">
            {!isScanning ? (
              <motion.div
                key="input"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-8"
              >
                <div className="relative">
                  {activeTab === 'file' ? (
                    <div className="w-full bg-foreground/[0.03] border border-border/50 rounded-3xl p-8 h-48 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-lg resize-none placeholder:text-foreground/20">
                      <label className="flex flex-col items-center justify-center h-full cursor-pointer">
                        <Upload className="w-12 h-12 mb-4 text-foreground/40" />
                        <span className="text-foreground/60 mb-2">
                          {selectedFile ? selectedFile.name : "Click or drag to upload"}
                        </span>
                        <span className="text-sm text-foreground/40">
                          Supported: Images (PNG, JPG), PDF, Audio (MP3, WAV)
                        </span>
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*,.pdf,audio/*"
                          onChange={handleFileChange}
                        />
                      </label>
                    </div>
                  ) : (
                    <textarea
                      placeholder={
                        activeTab === 'url' ? "Paste suspicious job link or URL here..." :
                        "Paste suspicious text, message, or job description here..."
                      }
                      className="w-full bg-foreground/[0.03] border border-border/50 rounded-3xl p-8 h-48 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-lg resize-none placeholder:text-foreground/20"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                    />
                  )}
                </div>

                <div className="flex flex-col md:flex-row items-center justify-center gap-4">
                  <button
                    onClick={handleScan}
                    disabled={!inputValue && !selectedFile}
                    className="w-full md:w-auto bg-gradient-to-r from-brand-400 to-brand-600 hover:from-brand-500 hover:to-brand-700 text-white px-12 py-5 rounded-2xl font-bold transition-all shadow-xl shadow-brand-500/20 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Scan Now
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button className="w-full md:w-auto bg-foreground/[0.03] border border-border/50 hover:bg-foreground/[0.05] text-foreground font-bold px-12 py-5 rounded-2xl transition-all">
                    See How It Works
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="scanning"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-12 text-center"
              >
                <div className="relative w-32 h-32 mx-auto mb-8">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      className="text-foreground/5"
                    />
                    <motion.circle
                      cx="64"
                      cy="64"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray="377"
                      strokeDashoffset={377 - (377 * progress) / 100}
                      className="text-brand-500"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold font-display">{progress}%</span>
                  </div>
                </div>

                <div className="space-y-4 max-w-xs mx-auto">
                  <h3 className="text-xl font-bold">Analyzing Content...</h3>
                  <div className="flex flex-col gap-2">
                    {steps.map((step, idx) => (
                      <div key={step} className="flex items-center gap-3 text-sm">
                        <div className={cn(
                          "w-5 h-5 rounded-full flex items-center justify-center transition-colors",
                          idx < currentStep ? "bg-safe text-white" :
                          idx === currentStep ? "bg-brand-500 text-white animate-pulse" :
                          "bg-foreground/10 text-foreground/30"
                        )}>
                          {idx < currentStep ? <CheckCircle2 className="w-3 h-3" /> : <span className="text-[10px]">{idx + 1}</span>}
                        </div>
                        <span className={cn(
                          "transition-colors",
                          idx <= currentStep ? "text-foreground" : "text-foreground/30"
                        )}>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
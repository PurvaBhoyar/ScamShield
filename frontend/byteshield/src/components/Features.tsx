"use client";

import { motion } from 'motion/react';
import { ShieldCheck, ShieldAlert, ShieldX, Clock, Search, Globe, MessageSquare, FileText, ChevronRight, Shield, CheckCircle2 } from 'lucide-react';
import { cn } from '../lib/utils';

export function Hero() {
  return (
    <div className="relative pt-48 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden min-h-[80vh] flex flex-col items-center justify-center">
      {/* Background Elements */}
      <div className="absolute top-0 left-0 right-0 bottom-0 bg-grid -z-20" />
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-brand-500/20 blur-[120px] -z-10 rounded-full animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/10 blur-[120px] -z-10 rounded-full animate-pulse" />
      
      <div className="max-w-7xl mx-auto text-center space-y-8 relative z-10">
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-6xl md:text-8xl lg:text-9xl font-bold leading-[0.9] tracking-tight max-w-6xl mx-auto"
        >
          Detect Scam Risks <br />
          <span className="text-gradient">Before They Cost You</span>
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className="text-lg md:text-2xl text-foreground/60 max-w-3xl mx-auto leading-relaxed font-medium"
        >
          Scan suspicious URLs, text/messages, and photos/files in <br className="hidden md:block" />
          seconds using advanced AI detection
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-center gap-8 pt-8"
        >
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground/40">
            <CheckCircle2 className="w-4 h-4 text-safe" />
            AI-Powered Detection
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground/40">
            <ShieldCheck className="w-4 h-4 text-brand-500" />
            98.7% Accuracy
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground/40">
            <Clock className="w-4 h-4 text-brand-500" />
            Instant Results
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export function Features() {
  const features = [
    { title: 'URL Analysis', desc: 'Deep domain metadata inspection and registration history verification.', icon: Globe },
    { title: 'Message OCR', desc: 'Extract and analyze text from screenshots of WhatsApp, Telegram, or emails.', icon: MessageSquare },
    { title: 'Document Verification', desc: 'Verify offer letters and PDFs against official company templates.', icon: FileText },
    { title: 'Public Evidence', desc: 'AI agents check official careers pages and recruiter identities in real-time.', icon: Search }
  ];

  return (
    <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="text-center mb-16 space-y-4">
        <h2 className="text-4xl font-bold">Unified Scanning System</h2>
        <p className="text-foreground/60 max-w-xl mx-auto">One platform to handle all your security verification needs across multiple input types.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {features.map((feature, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: idx * 0.1 }}
            className="glass p-8 rounded-3xl border-white/10 hover:border-brand-500/30 transition-all group glow-blue"
          >
            <div className="bg-brand-500/10 w-12 h-12 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <feature.icon className="w-6 h-6 text-brand-500" />
            </div>
            <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
            <p className="text-foreground/60 text-sm leading-relaxed">{feature.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export function TrustLayer() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="glass rounded-[3rem] overflow-hidden border-white/10 glow-blue">
        <div className="grid grid-cols-1 lg:grid-cols-2">
          <div className="p-12 md:p-20 space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 text-brand-500 text-xs font-bold uppercase tracking-widest">
              Security Infrastructure
            </div>
            <h2 className="text-4xl md:text-5xl font-bold leading-tight">
              The Digital Trust Layer <br />
              <span className="text-brand-500">for Modern Careers</span>
            </h2>
            <p className="text-foreground/60 text-lg leading-relaxed">
              ByteShield isn't just a scanner. It's a comprehensive verification infrastructure that sits between you and potential threats. We use multi-agent AI to cross-reference every signal.
            </p>
            
            <div className="space-y-4">
              {[
                { title: 'Explainable AI', desc: 'No black boxes. Every risk score comes with clear, human-readable evidence.' },
                { title: 'Safe Autonomy', desc: 'Our agents follow strict policy boundaries when verifying public data.' },
                { title: 'Real-time Intelligence', desc: 'Global scam patterns are updated every minute across our network.' }
              ].map((item, idx) => (
                <div key={idx} className="flex gap-4">
                  <div className="mt-1 bg-brand-500/20 p-1 rounded-full shrink-0">
                    <ShieldCheck className="w-4 h-4 text-brand-500" />
                  </div>
                  <div>
                    <h4 className="font-bold">{item.title}</h4>
                    <p className="text-sm text-foreground/50">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-brand-500/5 p-12 flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#0e8ce415_0%,transparent_70%)]" />
            <div className="relative glass p-8 rounded-3xl border-white/20 shadow-2xl w-full max-w-md space-y-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground/40 uppercase tracking-widest">Verification Policy Log</span>
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-danger" />
                  <div className="w-2 h-2 rounded-full bg-caution" />
                  <div className="w-2 h-2 rounded-full bg-safe" />
                </div>
              </div>
              
              <div className="space-y-3 font-mono text-[10px]">
                <div className="p-2 rounded bg-foreground/5 border border-border/50 flex justify-between">
                  <span className="text-foreground/40">10:24:01</span>
                  <span className="text-foreground/80">INIT_SCAN_SEQUENCE</span>
                  <span className="text-safe">[OK]</span>
                </div>
                <div className="p-2 rounded bg-foreground/5 border border-border/50 flex justify-between">
                  <span className="text-foreground/40">10:24:03</span>
                  <span className="text-foreground/80">EXTRACT_DOMAIN_METADATA</span>
                  <span className="text-safe">[OK]</span>
                </div>
                <div className="p-2 rounded bg-foreground/5 border border-border/50 flex justify-between">
                  <span className="text-foreground/40">10:24:05</span>
                  <span className="text-foreground/80">VERIFY_WHOIS_DATA</span>
                  <span className="text-danger">[FLAGGED]</span>
                </div>
                <div className="p-2 rounded bg-foreground/5 border border-border/50 flex justify-between">
                  <span className="text-foreground/40">10:24:08</span>
                  <span className="text-foreground/80">CHECK_CAREERS_PORTAL</span>
                  <span className="text-caution">[NO_MATCH]</span>
                </div>
                <div className="p-2 rounded bg-foreground/5 border border-border/50 flex justify-between">
                  <span className="text-foreground/40">10:24:12</span>
                  <span className="text-foreground/80">GENERATE_RISK_REPORT</span>
                  <span className="text-safe">[READY]</span>
                </div>
              </div>
              
              <div className="pt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-bold">ByteShield Agent</span>
                    <span className="text-[8px] text-foreground/40">Active Verification</span>
                  </div>
                </div>
                <div className="px-3 py-1 rounded-lg bg-safe/10 text-safe text-[10px] font-bold animate-pulse">
                  SECURE_LAYER_ACTIVE
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
export function RecentScans() {
  const scans = [
    { type: 'URL', score: 84, label: 'Danger', time: '2 mins ago', target: 'bit.ly/job-offer-2024' },
    { type: 'Text', score: 12, label: 'Safe', time: '1 hour ago', target: 'LinkedIn Recruiter Message' },
    { type: 'File', score: 45, label: 'Caution', time: '3 hours ago', target: 'Offer_Letter_Final.pdf' },
    { type: 'URL', score: 92, label: 'Danger', time: '5 hours ago', target: 'amazon-career-portal.xyz' }
  ];

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="glass rounded-[2rem] p-8 md:p-12 border-white/10 glow-blue">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-6">
          <div className="space-y-2">
            <h2 className="text-3xl font-bold">Recent Intelligence</h2>
            <p className="text-foreground/60">Real-time global scam detection activity.</p>
          </div>
          <div className="flex gap-2">
            {['All', 'URL', 'Text', 'File'].map(filter => (
              <button key={filter} className="px-4 py-2 rounded-xl bg-foreground/[0.03] border border-border/50 text-sm font-semibold hover:bg-foreground/[0.05] transition-colors">
                {filter}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs font-bold text-foreground/30 uppercase tracking-widest border-b border-border/50">
                <th className="pb-6 px-4">Scan Type</th>
                <th className="pb-6 px-4">Target</th>
                <th className="pb-6 px-4">Risk Score</th>
                <th className="pb-6 px-4">Label</th>
                <th className="pb-6 px-4">Timestamp</th>
                <th className="pb-6 px-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {scans.map((scan, idx) => (
                <tr key={idx} className="group hover:bg-foreground/[0.01] transition-colors">
                  <td className="py-6 px-4">
                    <div className="flex items-center gap-3">
                      <div className="bg-foreground/[0.05] p-2 rounded-lg">
                        {scan.type === 'URL' && <Globe className="w-4 h-4" />}
                        {scan.type === 'Text' && <MessageSquare className="w-4 h-4" />}
                        {scan.type === 'File' && <FileText className="w-4 h-4" />}
                      </div>
                      <span className="font-bold">{scan.type}</span>
                    </div>
                  </td>
                  <td className="py-6 px-4 font-medium text-foreground/70">{scan.target}</td>
                  <td className="py-6 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-foreground/10 rounded-full overflow-hidden">
                        <div 
                          className={cn(
                            "h-full rounded-full",
                            scan.label === 'Danger' ? "bg-danger" : scan.label === 'Caution' ? "bg-caution" : "bg-safe"
                          )}
                          style={{ width: `${scan.score}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold">{scan.score}</span>
                    </div>
                  </td>
                  <td className="py-6 px-4">
                    <span className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
                      scan.label === 'Danger' ? "bg-danger/10 text-danger" : scan.label === 'Caution' ? "bg-caution/10 text-caution" : "bg-safe/10 text-safe"
                    )}>
                      {scan.label}
                    </span>
                  </td>
                  <td className="py-6 px-4 text-sm text-foreground/40 font-medium">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3 h-3" />
                      {scan.time}
                    </div>
                  </td>
                  <td className="py-6 px-4 text-right">
                    <button className="p-2 rounded-lg hover:bg-foreground/5 transition-colors">
                      <ChevronRight className="w-5 h-5 text-foreground/20 group-hover:text-brand-500 transition-colors" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

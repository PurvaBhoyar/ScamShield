"use client";
import { Shield, Github, Twitter, Linkedin, Mail, ArrowRight } from 'lucide-react';

export function HowItWorks() {
  const steps = [
    { title: 'Input', desc: 'Paste a link, message, or upload a document for analysis.', icon: '01' },
    { title: 'Analyze', desc: 'Our AI extracts metadata and identifies suspicious patterns.', icon: '02' },
    { title: 'Verify', desc: 'Agents cross-reference public data and official sources.', icon: '03' },
    { title: 'Protect', desc: 'Receive a detailed risk report and safety recommendations.', icon: '04' }
  ];

  return (
    <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="text-center mb-20 space-y-4">
        <h2 className="text-4xl font-bold">How ByteShield Protects You</h2>
        <p className="text-foreground/60 max-w-xl mx-auto">A multi-layered approach to digital trust and scam prevention.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 relative">
        {/* Connection Line */}
        <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent -z-10" />
        
        {steps.map((step, idx) => (
          <div key={idx} className="text-center space-y-6 group">
            <div className="relative">
              <div className="w-20 h-20 rounded-3xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform duration-500 shadow-lg shadow-brand-500/5">
                <span className="text-2xl font-bold font-display text-brand-500">{step.icon}</span>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-6 translate-x-1/2">
                  <ArrowRight className="w-5 h-5 text-border" />
                </div>
              )}
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold">{step.title}</h3>
              <p className="text-foreground/60 text-sm leading-relaxed">{step.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 border-t border-border/50 bg-foreground/[0.01]">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          <div className="space-y-6">
            <div className="flex items-center gap-2">
              <div className="bg-brand-500 p-1.5 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-display font-bold tracking-tight">
                Byte<span className="text-brand-500">Shield</span>
              </span>
            </div>
            <p className="text-foreground/60 text-sm leading-relaxed">
              Building the digital trust layer for the modern internet. AI-powered scam detection for everyone.
            </p>
            <div className="flex items-center gap-4">
              {[Twitter, Github, Linkedin, Mail].map((Icon, idx) => (
                <a key={idx} href="#" className="p-2 rounded-lg bg-foreground/[0.05] hover:bg-brand-500/10 hover:text-brand-500 transition-all">
                  <Icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-bold mb-6">Product</h4>
            <ul className="space-y-4 text-sm text-foreground/60">
              <li><a href="#" className="hover:text-brand-500 transition-colors">Scanner</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Intelligence API</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Enterprise Portal</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Browser Extension</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-6">Resources</h4>
            <ul className="space-y-4 text-sm text-foreground/60">
              <li><a href="#" className="hover:text-brand-500 transition-colors">Scam Database</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Safety Guides</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">API Documentation</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Community Forum</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-6">Company</h4>
            <ul className="space-y-4 text-sm text-foreground/60">
              <li><a href="#" className="hover:text-brand-500 transition-colors">About ByteCode</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-brand-500 transition-colors">Terms of Service</a></li>
            </ul>
          </div>
        </div>
        
        <div className="pt-8 border-t border-border/50 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-foreground/40 font-medium">
          <p>© 2026 ByteShield by Team ByteCode. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-brand-500 transition-colors">Status</a>
            <a href="#" className="hover:text-brand-500 transition-colors">Security</a>
            <a href="#" className="hover:text-brand-500 transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

"use client";
import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <button
      onClick={() => setIsDark(!isDark)}
      className="p-3 rounded-2xl bg-foreground/[0.03] border border-border/50 hover:bg-foreground/[0.05] transition-all group"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-brand-400 group-hover:rotate-45 transition-transform" />
      ) : (
        <Moon className="w-5 h-5 text-brand-600 group-hover:-rotate-12 transition-transform" />
      )}
    </button>
  );
}

'use client';

import React from 'react';

/**
 * SlushPilot Landing Page
 * Using standard HTML anchors to ensure compatibility with the preview environment
 * while maintaining the manuscript-inspired aesthetic.
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#f4f1ea] flex flex-col items-center justify-center p-6 font-serif text-[#2c2c2c] overflow-hidden relative">
      {/* Decorative background elements evoking aged parchment */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#dcd6bc] opacity-10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#dcd6bc] opacity-10 rounded-full blur-3xl"></div>

      <div className="max-w-3xl w-full text-center relative z-10">
        <header className="mb-12">
          <div className="inline-block mb-6">
             <div className="w-16 h-1 bg-[#1a1a1a] mx-auto mb-2"></div>
             <div className="w-8 h-1 bg-[#1a1a1a] mx-auto"></div>
          </div>
          <h1 className="text-7xl font-bold mb-4 tracking-tighter text-[#1a1a1a]">SlushPilot</h1>
          <p className="text-xl italic text-[#5c5c5c] max-w-lg mx-auto leading-relaxed">
            "Automating the journey through the publishing maze, from manuscript to masterpiece."
          </p>
        </header>

        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <a
              href="/login"
              className="px-10 py-4 bg-[#1a1a1a] text-white font-bold uppercase tracking-[0.2em] text-sm hover:bg-[#333] transition-all shadow-2xl active:translate-y-1 w-full sm:w-auto text-center"
            >
              Enter the Library
            </a>
            <a
              href="/login"
              className="px-10 py-4 border-2 border-[#1a1a1a] text-[#1a1a1a] font-bold uppercase tracking-[0.2em] text-sm hover:bg-[#1a1a1a] hover:text-white transition-all w-full sm:w-auto text-center"
            >
              Join the Guild
            </a>
          </div>

          <div className="pt-12">
             <div className="flex justify-center items-center space-x-8 text-[10px] font-bold uppercase tracking-[0.3em] text-[#999]">
                <span>Strategize</span>
                <span className="w-1 h-1 bg-[#dcd6bc] rounded-full"></span>
                <span>Compose</span>
                <span className="w-1 h-1 bg-[#dcd6bc] rounded-full"></span>
                <span>Publish</span>
             </div>
          </div>
        </div>

        <section className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-12 text-left border-t border-[#dcd6bc] pt-12">
          <div>
            <h3 className="font-bold text-[#1a1a1a] mb-2 uppercase tracking-wider text-xs">The Strategist</h3>
            <p className="text-sm text-[#666] leading-relaxed italic">Scanning the industry archives to find the perfect home for your prose.</p>
          </div>
          <div>
            <h3 className="font-bold text-[#1a1a1a] mb-2 uppercase tracking-wider text-xs">The Composer</h3>
            <p className="text-sm text-[#666] leading-relaxed italic">Forging personalized scrolls that capture your voice and command attention.</p>
          </div>
          <div>
            <h3 className="font-bold text-[#1a1a1a] mb-2 uppercase tracking-wider text-xs">The Supervisor</h3>
            <p className="text-sm text-[#666] leading-relaxed italic">Managing the complex web of submissions so you can focus on the next chapter.</p>
          </div>
        </section>
      </div>

      <footer className="absolute bottom-8 text-[#999] text-[10px] uppercase tracking-[0.4em]">
        SlushPilot — Batch 3 Group 4 — © 2026
      </footer>
    </div>
  );
}
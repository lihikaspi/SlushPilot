'use client';

import React, { useState } from 'react';
// Using the client utility to interact with Supabase
import { createClient } from '../utils/supabase/client';
import { useRouter } from 'next/navigation';

export default function EntryPage() {
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  const router = useRouter();
  const supabase = createClient();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      if (isSignUp) {
        // Sign up logic: Direct insertion into the profiles table
        const { error } = await supabase
          .from('profiles')
          .insert([
            {
              username: username,
              full_name: fullName
            }
          ]);

        if (error) {
          if (error.code === '23505') throw new Error('Username already exists.');
          throw error;
        }

        // AUTO-LOGIN AFTER SIGN UP
        localStorage.setItem('slushpilot_user', username);
        router.push('/dashboard');
      } else {
        // Login logic: Verify username existence in profiles table
        const { data, error } = await supabase
          .from('profiles')
          .select('username')
          .eq('username', username)
          .single();

        if (error || !data) {
          throw new Error('Username not found. Please sign up first.');
        }

        localStorage.setItem('slushpilot_user', username);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Authentication failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f1ea] flex flex-col items-center justify-center p-4 font-serif text-[#2c2c2c] relative overflow-hidden">

      {/* Background Decorative Elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute bottom-10 left-10 opacity-10 rotate-[-12deg]">
          <svg width="200" height="240" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
        </div>

        <div className="absolute top-10 right-10 opacity-10 rotate-[15deg]">
          <svg width="150" height="150" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </div>

        <svg className="absolute inset-0 w-full h-full opacity-10" viewBox="0 0 1000 1000" preserveAspectRatio="none">
           <path
             d="M150,850 Q400,600 500,500 T850,150"
             fill="none"
             stroke="#1a1a1a"
             strokeWidth="2"
             strokeDasharray="8,8"
           />
        </svg>
      </div>

      <div className="max-w-md w-full text-center mb-8 relative z-10">
        <h1 className="text-5xl font-bold mb-2 tracking-tight text-[#1a1a1a]">SlushPilot</h1>
        <p className="italic text-[#5c5c5c] text-lg">Automating the journey through the publishing maze.</p>
        <div className="mt-4 border-b-2 border-[#dcd6bc] w-24 mx-auto"></div>
      </div>

      <div className="max-w-md w-full bg-white border border-[#dcd6bc] shadow-xl p-8 rounded-sm relative z-10">
        <div className="absolute inset-0 opacity-5 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/p6.png')]"></div>

        <h2 className="text-2xl font-semibold mb-6 text-center border-b border-[#eee] pb-4">
          {isSignUp ? 'Create Author Account' : 'Writer Login'}
        </h2>

        {message && (
          <div className={`p-3 mb-6 text-sm rounded border ${
            message.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-green-50 border-green-200 text-green-700'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-1 uppercase tracking-wider text-[#666]">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              // Switched to font-sans for better readability in text boxes
              className="w-full px-4 py-3 rounded-none border border-[#ccc] outline-none bg-[#fafafa] focus:border-[#1a1a1a] font-sans"
              placeholder="Your unique scribe handle"
              required
            />
          </div>

          {isSignUp && (
            <div>
              <label className="block text-sm font-medium mb-1 uppercase tracking-wider text-[#666]">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                // Switched to font-sans for better readability in text boxes
                className="w-full px-4 py-3 rounded-none border border-[#ccc] outline-none bg-[#fafafa] focus:border-[#1a1a1a] font-sans"
                placeholder="Your author name"
                required
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#1a1a1a] text-white hover:bg-[#333] transition-colors font-semibold tracking-widest uppercase text-sm disabled:opacity-50 cursor-pointer"
          >
            {/* Updated button text */}
            {loading ? 'Processing...' : isSignUp ? 'Begin' : 'Enter'}
          </button>
        </form>

        <div className="mt-8 text-center text-sm border-t border-[#eee] pt-6">
          <p className="text-[#666]">
            {isSignUp ? "Already have an account?" : "Ready to pitch your masterpiece?"}
            <button
              onClick={() => {
                setIsSignUp(!isSignUp);
                setMessage(null);
              }}
              className="ml-2 font-bold text-[#1a1a1a] underline hover:text-[#555] cursor-pointer"
            >
              {isSignUp ? 'Sign In' : 'Sign Up for Free'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
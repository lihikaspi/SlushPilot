'use client';

import React, { useState } from 'react';
// Using relative path to fix resolution error
import { createClient } from '../../utils/supabase/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });
        if (error) throw error;
        setMessage({ type: 'success', text: 'Check your email for the confirmation link!' });
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        router.push('/dashboard');
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Authentication failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f1ea] flex flex-col items-center justify-center p-4 font-serif text-[#2c2c2c]">
      <div className="max-w-md w-full text-center mb-8">
        <h1 className="text-5xl font-bold mb-2 tracking-tight text-[#1a1a1a]">SlushPilot</h1>
        <p className="italic text-[#5c5c5c] text-lg">Automating the journey through the publishing maze.</p>
        <div className="mt-4 border-b-2 border-[#dcd6bc] w-24 mx-auto"></div>
      </div>

      <div className="max-w-md w-full bg-white border border-[#dcd6bc] shadow-xl p-8 rounded-sm relative">
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
            <label className="block text-sm font-medium mb-1 uppercase tracking-wider text-[#666]">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-none border border-[#ccc] outline-none bg-[#fafafa]"
              placeholder="author@manuscript.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 uppercase tracking-wider text-[#666]">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-none border border-[#ccc] outline-none bg-[#fafafa]"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#1a1a1a] text-white hover:bg-[#333] transition-colors font-semibold tracking-widest uppercase text-sm disabled:opacity-50"
          >
            {loading ? 'Processing...' : isSignUp ? 'Begin Journey' : 'Enter Library'}
          </button>
        </form>

        <div className="mt-8 text-center text-sm border-t border-[#eee] pt-6">
          <p className="text-[#666]">
            {isSignUp ? "Already have an account?" : "Ready to pitch your masterpiece?"}
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="ml-2 font-bold text-[#1a1a1a] underline hover:text-[#555]"
            >
              {isSignUp ? 'Sign In' : 'Sign Up for Free'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
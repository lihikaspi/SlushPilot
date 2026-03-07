"use client";

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { User, MessageSquare, History, ScrollText, Play, Loader2, PlusCircle, Save } from 'lucide-react';
import axios from 'axios';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const USER_ID = 1;
const API_BASE = "http://localhost:8000";

export default function SlushPilot() {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Data States
  const [userInfo, setUserInfo] = useState({ name: '', email: '', phone: '', city: '', bio: '' });
  const [traceSteps, setTraceSteps] = useState<any[]>([]);
  const [letters, setLetters] = useState<any[]>([]);
  const [selectedLetter, setSelectedLetter] = useState<any>(null);

  useEffect(() => {
    loadUserData();
    loadHistory();
  }, []);

  const loadUserData = async () => {
    const { data } = await supabase.from('users').select('*').eq('id', USER_ID).single();
    if (data) setUserInfo(data);
  };

  const loadHistory = async () => {
    const { data: steps } = await supabase.from('steps').select('*').eq('user', USER_ID).order('created_at', { ascending: false });
    if (steps) setTraceSteps(steps.flatMap(s => s.content || []));

    const { data: lets } = await supabase.from('letters').select('*').eq('user', USER_ID);
    setLetters(lets || []);
  };

  const handleNewChat = async () => {
    setMessages([]); // Clear local chat
    setInput('');
    // The server handles the new iteration ID during the next 'execute' call
    setActiveTab('chat');
  };

  const handleSaveProfile = async () => {
    const { error } = await supabase.from('users').update(userInfo).eq('id', USER_ID);
    if (!error) alert("Manuscript profile updated.");
  };

  const handleRunAgent = async () => {
    if (!input.trim() || loading) return;

    const userPrompt = input;
    setMessages(prev => [...prev, { role: 'user', content: userPrompt }]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/api/execute`, { prompt: userPrompt });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
      loadHistory();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-parchment text-ink">
      {/* Sidebar */}
      <aside className="w-64 border-r border-binding-gold flex flex-col p-6 bg-parchment">
        <div className="mb-10">
          <h1 className="text-2xl font-bold tracking-tighter uppercase border-b-2 border-ink pb-2">Slush Pilot</h1>
        </div>

        <nav className="space-y-4 flex-1">
          <NavBtn icon={<MessageSquare size={18}/>} label="Chat" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
          <NavBtn icon={<User size={18}/>} label="Personal Info" active={activeTab === 'info'} onClick={() => setActiveTab('info')} />
          <NavBtn icon={<History size={18}/>} label="Steps Trace" active={activeTab === 'trace'} onClick={() => setActiveTab('trace')} />
          <NavBtn icon={<ScrollText size={18}/>} label="Letters" active={activeTab === 'letters'} onClick={() => setActiveTab('letters')} />
        </nav>

        {/* New Chat Button */}
        <button
          onClick={handleNewChat}
          className="mt-auto flex items-center justify-center gap-2 p-3 border border-ink hover:bg-ink hover:text-parchment transition-all uppercase text-xs font-bold tracking-widest cursor-pointer"
        >
          <PlusCircle size={16} /> New Chat
        </button>
      </aside>

      <main className="flex-1 overflow-hidden flex flex-col relative">
        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col p-8 max-w-3xl mx-auto w-full relative">
            {messages.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center p-12 pointer-events-none">
                <p className="text-3xl text-binding-gold text-center italic opacity-60">
                  Welcome to Slush Pilot! Tell me about your book and I'll help you get it published.
                </p>
              </div>
            )}

            <div className="flex-1 overflow-y-auto space-y-6 pr-4 z-10">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded shadow-sm border ${m.role === 'user' ? 'bg-binding-gold border-ink' : 'bg-white border-binding-gold'}`}>
                    <p className="leading-relaxed">{m.content}</p>
                  </div>
                </div>
              ))}
              {loading && <Loader2 className="animate-spin text-manuscript-gray mx-auto" />}
            </div>

            <div className="mt-6 flex gap-3 bg-white p-2 border border-binding-gold shadow-inner z-10">
              <input
                className="flex-1 bg-transparent outline-none px-2 py-2 font-sans"
                placeholder="Describe your book..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button onClick={handleRunAgent} className="bg-ink text-parchment px-4 py-2 hover:bg-manuscript-gray flex items-center gap-2 uppercase text-xs font-bold tracking-widest cursor-pointer">
                <Play size={14} /> Run Agent
              </button>
            </div>
          </div>
        )}

        {/* INFO TAB */}
        {activeTab === 'info' && (
          <div className="p-12 max-w-xl">
            <h2 className="text-3xl font-bold mb-8 underline decoration-binding-gold underline-offset-8">Author Profile</h2>
            <div className="space-y-4 font-sans">
              {['name', 'email', 'phone', 'city'].map(field => (
                <div key={field}>
                  <label className="block text-[10px] uppercase tracking-widest text-manuscript-gray font-bold">{field}</label>
                  <input
                    className="w-full bg-white border border-binding-gold p-2 mt-1 focus:border-ink outline-none transition-colors"
                    value={(userInfo as any)[field] || ''}
                    onChange={(e) => setUserInfo({...userInfo, [field]: e.target.value})}
                  />
                </div>
              ))}
              <div>
                <label className="block text-[10px] uppercase tracking-widest text-manuscript-gray font-bold">Bio</label>
                <textarea
                  rows={4}
                  className="w-full bg-white border border-binding-gold p-2 mt-1 focus:border-ink outline-none transition-colors font-serif italic"
                  value={userInfo.bio || ''}
                  onChange={(e) => setUserInfo({...userInfo, bio: e.target.value})}
                />
              </div>
              <button
                onClick={handleSaveProfile}
                className="bg-ink text-parchment px-6 py-2 mt-4 hover:bg-manuscript-gray transition-colors flex items-center gap-2 uppercase text-xs font-bold tracking-widest cursor-pointer"
              >
                <Save size={16} /> Save Changes
              </button>
            </div>
          </div>
        )}

        {/* ... [Trace and Letters tabs remain the same as previous code] ... */}
      </main>
    </div>
  );
}

function NavBtn({ icon, label, active, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-4 px-4 py-3 border border-transparent transition-all cursor-pointer ${active ? 'bg-binding-gold border-ink translate-x-2' : 'hover:border-binding-gold'}`}
    >
      {icon}
      <span className="uppercase text-xs font-bold tracking-widest">{label}</span>
    </button>
  );
}
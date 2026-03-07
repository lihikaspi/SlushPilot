"use client";

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { User, MessageSquare, History, ScrollText, Play, Loader2, PlusCircle, Save } from 'lucide-react';

// Supabase Configuration
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const USER_ID = 1;
const ITERATION_ID = 1;

export default function SlushPilot() {
  const [activeTab, setActiveTab] = useState('chat');
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [selectedLetter, setSelectedLetter] = useState<any>(null);

  // States aligned with DB schemas
  const [userInfo, setUserInfo] = useState({
    name: '', email: '', phone: '', city: '', country: '', bio: ''
  });
  const [dbSteps, setDbSteps] = useState<any[]>([]);
  const [letters, setLetters] = useState<any[]>([]);

  // Fetch data exclusively from DB for User 1, Iteration 1
  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch from public.users
      const { data: user } = await supabase
        .from('users')
        .select('*')
        .eq('id', USER_ID)
        .single();
      if (user) setUserInfo(user);

      // 2. Fetch from public.steps for current iteration
      const { data: steps } = await supabase
        .from('steps')
        .select('*')
        .eq('user', USER_ID)
        .eq('iteration', ITERATION_ID)
        .order('message', { ascending: true });
      if (steps) setDbSteps(steps);

      // 3. Fetch from public.letters for current iteration
      const { data: lets } = await supabase
        .from('letters')
        .select('*')
        .eq('user', USER_ID)
        .eq('iteration', ITERATION_ID);
      if (lets) setLetters(lets);
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveProfile = async () => {
    setLoading(true);
    const { error } = await supabase
      .from('users')
      .upsert({ id: USER_ID, ...userInfo });
    setLoading(false);
    if (!error) alert("Author profile updated successfully.");
  };

  const handleRunAgent = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    // Placeholder for calling server.py API
    // After agent runs, we refresh data to show the new steps/letters in the DB
    await fetchData();
    setInput('');
    setLoading(false);
  };

  // Helper to strip outermost {} or [] from JSON for raw display
  const formatJsonRaw = (val: any) => {
    if (!val) return "No trace data available.";
    const str = JSON.stringify(val, null, 2);
    // Regex removes the first '{' or '[' and the last '}' or ']'
    return str.replace(/^[\{\[]|[\}\]]$/g, '').trim();
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
      </aside>

      <main className="flex-1 overflow-hidden flex flex-col relative">
        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col p-8 max-w-3xl mx-auto w-full relative">
            <div className="flex-1 overflow-y-auto space-y-6 pr-4 z-10">
              {dbSteps.map((row, i) => (
                <div key={i} className="space-y-4">
                  <div className="flex justify-end">
                    <div className="max-w-[80%] p-4 rounded shadow-sm border bg-binding-gold border-ink">
                      <p>{row.input}</p>
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-[80%] p-4 rounded shadow-sm border bg-white border-binding-gold">
                      <p>{row.response}</p>
                    </div>
                  </div>
                </div>
              ))}
              {loading && <Loader2 className="animate-spin text-manuscript-gray mx-auto" />}
            </div>
            <div className="mt-6 flex gap-3 bg-white p-2 border border-binding-gold shadow-inner z-10">
              <input
                className="flex-1 bg-transparent outline-none px-2 py-2 font-sans"
                placeholder="Talk to the agent..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRunAgent()}
              />
              <button onClick={handleRunAgent} className="bg-ink text-parchment px-4 py-2 hover:bg-manuscript-gray uppercase text-xs font-bold tracking-widest cursor-pointer">
                Run Agent
              </button>
            </div>
          </div>
        )}

        {/* INFO TAB */}
        {activeTab === 'info' && (
          <div className="p-12 max-w-xl h-full overflow-y-auto">
            <h2 className="text-3xl font-bold mb-8 underline decoration-binding-gold underline-offset-8">Author Profile</h2>
            <div className="space-y-4 font-sans">
              {['name', 'email', 'phone', 'city', 'country'].map(field => (
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
              <button onClick={handleSaveProfile} className="bg-ink text-parchment px-6 py-2 mt-4 hover:bg-manuscript-gray transition-colors flex items-center gap-2 uppercase text-xs font-bold tracking-widest cursor-pointer">
                <Save size={16} /> Save Changes
              </button>
            </div>
          </div>
        )}

        {/* STEPS TRACE TAB - Mirrors Chat layout, shows 'steps' jsonb, no input box */}
        {activeTab === 'trace' && (
          <div className="flex-1 flex flex-col p-8 max-w-3xl mx-auto w-full relative">
            <h2 className="text-3xl font-bold mb-8 underline decoration-binding-gold underline-offset-8">Iteration {ITERATION_ID} Trace</h2>
            <div className="flex-1 overflow-y-auto space-y-6 pr-4 z-10">
              {dbSteps.map((row, i) => (
                <div key={i} className="space-y-4">
                  <div className="flex justify-end">
                    <div className="max-w-[80%] p-4 rounded shadow-sm border bg-binding-gold border-ink">
                      <p className="text-[10px] font-bold uppercase opacity-50 mb-1">Input</p>
                      <p>{row.input}</p>
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-[80%] p-4 rounded shadow-sm border bg-white border-binding-gold w-full">
                      <p className="text-[10px] font-bold uppercase text-manuscript-gray mb-3 border-b border-binding-gold pb-1">Execution Steps (Msg #{row.message})</p>
                      <div className="bg-parchment/30 p-4 rounded">
                        <pre className="text-xs font-mono whitespace-pre-wrap text-ink leading-relaxed">
                          {formatJsonRaw(row.steps)}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {loading && <Loader2 className="animate-spin text-manuscript-gray mx-auto" />}
            </div>
          </div>
        )}

        {/* LETTERS TAB */}
        {activeTab === 'letters' && (
          <div className="p-12 h-full overflow-hidden flex flex-col">
            <h2 className="text-3xl font-bold mb-8 underline decoration-binding-gold underline-offset-8">Iteration {ITERATION_ID} Letters</h2>
            <div className="flex gap-8 flex-1 overflow-hidden">
              <div className="w-1/3 space-y-4 overflow-y-auto">
                {letters.map((letter) => (
                  <div
                    key={letter.id}
                    className={`p-4 border cursor-pointer transition-all ${selectedLetter?.id === letter.id ? 'bg-binding-gold border-ink' : 'bg-white border-binding-gold'}`}
                    onClick={() => setSelectedLetter(letter)}
                  >
                    <h3 className="font-bold text-sm uppercase tracking-wider">{letter.publisher}</h3>
                    <p className="text-[10px] text-manuscript-gray mt-1">{new Date(letter.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
              <div className="flex-1 bg-white border border-binding-gold p-8 shadow-lg font-serif italic overflow-y-auto">
                {selectedLetter ? (
                  <div className="whitespace-pre-wrap leading-relaxed text-ink">
                    <p className="font-bold mb-4 uppercase underline tracking-widest">Draft for: {selectedLetter.publisher}</p>
                    {selectedLetter.content}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-manuscript-gray opacity-50">
                    Select a publisher to view the letter.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function NavBtn({ icon, label, active, onClick }: any) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-4 px-4 py-3 border border-transparent transition-all cursor-pointer ${active ? 'bg-binding-gold border-ink translate-x-2' : 'hover:border-binding-gold'}`}>
      {icon}
      <span className="uppercase text-xs font-bold tracking-widest">{label}</span>
    </button>
  );
}
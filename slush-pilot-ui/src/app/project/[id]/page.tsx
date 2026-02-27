'use client';

import React, { useEffect, useState, use, useRef } from 'react';
import { createClient } from '@/src/utils/supabase/client';

const PROJECT_STATUS: Record<string, { label: string; colorClass: string }> = {
  new: { label: "New Project", colorClass: "bg-gray-400" },
  publisher_search: { label: "Publisher Search", colorClass: "bg-sky-600" },
  drafting: { label: "Drafting Letters", colorClass: "bg-emerald-600" }
};

interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  chat_message_id: number;
  created_at: string;
}

interface QueryLetter {
  id: string;
  publisher: string;
  content: string | null;
  updated_at: string;
}

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const supabase = createClient();

  const [activeTab, setActiveTab] = useState<'chat' | 'letters'>('chat');
  const [project, setProject] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [queryLetters, setQueryLetters] = useState<QueryLetter[]>([]);
  const [selectedLetter, setSelectedLetter] = useState<QueryLetter | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');

  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  const initializationInProgress = useRef(false);

  useEffect(() => {
    const scrollToBottom = () => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    };
    scrollToBottom();
    const timeoutId = setTimeout(scrollToBottom, 50);
    return () => clearTimeout(timeoutId);
  }, [messages, activeTab]);

  const getBookStyles = (id: string) => {
    const bookColors = [
      { bg: 'bg-red-600/5', spine: 'bg-red-600/30', text: 'text-red-900', border: 'border-red-600/20' },
      { bg: 'bg-green-600/5', spine: 'bg-green-600/30', text: 'text-green-900', border: 'border-green-600/20' },
      { bg: 'bg-blue-600/5', spine: 'bg-blue-600/30', text: 'text-blue-900', border: 'border-blue-600/20' },
      { bg: 'bg-pink-600/5', spine: 'bg-pink-600/30', text: 'text-pink-900', border: 'border-pink-600/20' },
      { bg: 'bg-purple-600/5', spine: 'bg-purple-600/30', text: 'text-purple-900', border: 'border-purple-600/20' },
      { bg: 'bg-teal-600/5', spine: 'bg-teal-600/30', text: 'text-teal-900', border: 'border-teal-600/20' },
    ];
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = id.charCodeAt(i) + ((hash << 5) - hash);
    return bookColors[Math.abs(hash) % bookColors.length];
  };

  const fetchData = async () => {
    const { data: projectData } = await supabase.from('projects').select('*').eq('id', id).single();
    if (!projectData) return;
    setRenameValue(projectData.title);

    const { data: messageData } = await supabase
      .from('messages')
      .select('*')
      .eq('project_id', id)
      .order('chat_message_id', { ascending: true });

    let finalMessages = messageData || [];

    if (messageData && messageData.length === 0 && !initializationInProgress.current) {
      initializationInProgress.current = true;
      const welcomeText = "Hello! I'm your Slush Pilot and I'm here to help getting your book published. Tell me the name of your book and a short description of the plot so we can get started.";
      const { data: welcomeMsg } = await supabase
        .from('messages')
        .insert({
          project_id: id,
          user_id: projectData.user_id,
          role: 'model',
          content: welcomeText,
          chat_message_id: 0
        })
        .select()
        .single();

      if (welcomeMsg) {
        finalMessages = [welcomeMsg];
        await supabase.from('projects').update({ updated_at: new Date().toISOString() }).eq('id', id);
      }
    }

    const { data: lettersData } = await supabase.from('query_letters')
      .select('id, publisher, content, updated_at')
      .eq('project_id', id)
      .order('updated_at', { ascending: false });

    const finalLetters = lettersData || [];

    let nextStatus = projectData.current_stage;
    if (finalLetters.length > 0) {
      nextStatus = 'drafting';
    } else if (finalMessages.length > 1) {
      nextStatus = 'publisher_search';
    } else {
      nextStatus = 'new';
    }

    if (nextStatus !== projectData.current_stage) {
      const now = new Date().toISOString();
      await supabase.from('projects').update({ current_stage: nextStatus, updated_at: now }).eq('id', id);
      setProject({ ...projectData, current_stage: nextStatus, updated_at: now });
    } else {
      setProject(projectData);
    }

    setMessages(finalMessages);
    setQueryLetters(finalLetters);
    if (finalLetters.length > 0 && !selectedLetter) setSelectedLetter(finalLetters[0]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !project) return;
    const now = new Date().toISOString();
    const nextId = messages.length > 0 ? Math.max(...messages.map(m => m.chat_message_id)) + 1 : 0;

    const { data, error } = await supabase
      .from('messages')
      .insert({
        project_id: id,
        user_id: project.user_id,
        role: 'user',
        content: inputValue.trim(),
        chat_message_id: nextId
      })
      .select()
      .single();

    if (data && !error) {
      const updatedMessages = [...messages, data];
      setMessages(updatedMessages);
      setInputValue('');

      let nextStatus = project.current_stage;
      if (queryLetters.length === 0 && updatedMessages.length > 1) {
        nextStatus = 'publisher_search';
      }

      await supabase.from('projects').update({ current_stage: nextStatus, updated_at: now }).eq('id', id);
      setProject({ ...project, current_stage: nextStatus, updated_at: now });
    }
  };

  const showNotification = (type: 'success' | 'error', text: string) => {
    setNotification({ type, text });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleSaveLetter = async () => {
    if (!selectedLetter || !editorRef.current) return;
    const content = editorRef.current.innerText;
    const now = new Date().toISOString();

    const { error } = await supabase.from('query_letters').update({ content: content, updated_at: now }).eq('id', selectedLetter.id);

    if (error) {
      showNotification('error', 'failed to save');
    } else {
      await supabase.from('projects').update({ updated_at: now }).eq('id', id);
      showNotification('success', 'letter saved');
      fetchData();
    }
  };

  const handleRenameProject = async () => {
    if (!renameValue.trim() || !project) return;
    const now = new Date().toISOString();
    const { error } = await supabase.from('projects').update({ title: renameValue.trim(), updated_at: now }).eq('id', id);
    if (!error) {
      setProject({ ...project, title: renameValue.trim(), updated_at: now });
      setIsRenameModalOpen(false);
      showNotification('success', 'manuscript renamed');
    } else {
      showNotification('error', 'failed to rename');
    }
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Reviewing manuscript files...</div>;

  const { bg, spine, text, border } = getBookStyles(id);
  const statusInfo = PROJECT_STATUS[project?.current_stage] || { label: project?.current_stage, colorClass: "bg-slate-300" };

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-[#f4f1ea] overflow-hidden relative">
      <aside className="w-60 bg-[#f4f1ea] border-r border-[#dcd6bc] flex flex-col shrink-0 overflow-hidden">
        <div className="p-5 border-b border-[#dcd6bc] flex flex-col items-center">
          <div className={`relative flex w-28 h-40 mb-3 ${bg} ${border} border rounded-r shadow-md overflow-hidden group`}>
            <div className={`w-2.5 h-full ${spine} border-r border-black/5`}></div>
            <div className="flex-1 p-2 flex flex-col justify-center">
              <h3 className={`text-sm font-bold leading-tight ${text} line-clamp-4 font-serif italic text-center`}>
                {project?.title || 'Untitled'}
              </h3>
            </div>
          </div>
          <button
            onClick={() => setIsRenameModalOpen(true)}
            className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#999] hover:text-[#1a1a1a] transition-colors mb-4 flex items-center gap-1 cursor-pointer"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Rename Manuscript
          </button>
          <span className={`${statusInfo.colorClass} opacity-80 text-white text-[9px] font-sans font-bold uppercase tracking-widest px-3 py-1 rounded-sm shadow-sm inline-block text-center w-fit`}>
            {statusInfo.label}
          </span>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <button onClick={() => setActiveTab('chat')} className={`w-full text-left px-4 py-3 text-[10px] font-sans font-bold uppercase tracking-widest transition-all rounded-sm flex items-center gap-3 cursor-pointer ${activeTab === 'chat' ? 'bg-[#1a1a1a] text-white shadow-md' : 'text-[#666] hover:bg-black/5'}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2M20 14h2M15 13v2M9 13v2" /></svg>
            Slush Pilot
          </button>
          <button onClick={() => setActiveTab('letters')} className={`w-full text-left px-4 py-3 text-[10px] font-sans font-bold uppercase tracking-widest transition-all rounded-sm flex items-center gap-3 cursor-pointer ${activeTab === 'letters' ? 'bg-[#1a1a1a] text-white shadow-md' : 'text-[#666] hover:bg-black/5'}`}>
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            Query Letters
          </button>
        </nav>
      </aside>

      <main className={`flex-1 flex flex-col overflow-hidden ${activeTab === 'chat' ? 'bg-[#fafaf9]' : 'bg-[#fdfcf9]'}`}>
        {activeTab === 'chat' ? (
          <div className="h-full flex flex-col max-w-5xl mx-auto w-full p-8 overflow-hidden">
             <div ref={scrollRef} className="flex-1 overflow-y-auto mb-6 scrollbar-thin pr-4 pb-12">
                {messages.map((msg, index) => {
                  const isSameRole = index > 0 && messages[index - 1].role === msg.role;
                  return (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} ${isSameRole ? 'mt-2' : 'mt-6'}`}>
                      <div className={`max-w-[75%] p-5 rounded-2xl shadow-sm font-sans text-sm leading-relaxed ${msg.role === 'user' ? `${bg} ${text} ${border} border rounded-tr-none` : 'bg-[#f4f1ea] border border-[#dcd6bc] text-[#444] rounded-tl-none'}`}>
                        {msg.content}
                      </div>
                    </div>
                  );
                })}
            </div>
            <div className="bg-white border border-[#dcd6bc] p-4 flex items-center space-x-4 shadow-lg shrink-0">
              <textarea className="flex-1 bg-transparent outline-none resize-none font-sans text-sm py-2 h-12" placeholder="Ask SlushPilot" rows={1} value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && inputValue.trim()) { e.preventDefault(); handleSendMessage(); } }} />
              <button onClick={handleSendMessage} disabled={!inputValue.trim()} className={`text-black p-3 hover:bg-black/5 shrink-0 flex items-center justify-center transition-all ${!inputValue.trim() ? 'opacity-20 cursor-default' : 'cursor-pointer'}`}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 12 2 21 5 12 2 3 22 12" /><line x1="5" y1="12" x2="22" y2="12" /></svg>
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex divide-x divide-[#dcd6bc] overflow-hidden">
            <div className="w-72 bg-[#fdfcf9] flex flex-col overflow-hidden border-r border-[#dcd6bc]">
              <div className="flex-1 overflow-y-auto">
                {queryLetters.map((letter) => (
                  <div key={letter.id} onClick={() => setSelectedLetter(letter)} className={`p-4 cursor-pointer transition-all border-b border-[#dcd6bc] ${selectedLetter?.id === letter.id ? 'bg-white shadow-sm' : 'hover:bg-black/5'}`}>
                    <p className="font-bold text-sm text-[#1a1a1a]">{letter.publisher}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex-1 bg-white flex flex-col overflow-hidden relative">
              <div className="p-4 border-b border-[#dcd6bc] flex justify-between items-center bg-[#fafafa] shrink-0">
                <span className="text-[10px] font-sans font-bold uppercase tracking-widest text-[#999]">Publisher: {selectedLetter?.publisher || 'None Selected'}</span>
                <div className="flex items-center gap-3"><button onClick={handleSaveLetter} className="bg-[#1a1a1a] text-white px-5 py-2 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#333] transition-all cursor-pointer shadow-sm">Save Letter</button></div>
              </div>
              <div className="flex-1 p-12 overflow-y-auto w-full">
                <div className="max-w-3xl mx-auto h-full">
                  {selectedLetter ? (
                    <div
                      ref={editorRef}
                      contentEditable
                      className="outline-none min-h-full whitespace-pre-wrap text-lg font-serif leading-loose text-[#333] relative before:content-[attr(data-placeholder)] before:text-gray-400/50 before:absolute before:pointer-events-none"
                      data-placeholder={!selectedLetter.content ? "Start writing your query letter here..." : ""}
                      suppressContentEditableWarning={true}
                    >
                      {selectedLetter.content || ""}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-center"><p className="font-serif italic text-lg text-[#666]">No letter selected.</p></div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {isRenameModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] z-50 flex items-center justify-center p-4">
          <div className="bg-[#fdfcf9] border border-[#dcd6bc] w-full max-w-md shadow-2xl p-8 rounded-sm animate-in fade-in zoom-in duration-200">
            <h2 className="text-xs font-sans font-bold uppercase tracking-widest text-[#999] mb-6">Rename Manuscript</h2>
            <input type="text" value={renameValue} onChange={(e) => setRenameValue(e.target.value)} className="w-full bg-white border border-[#dcd6bc] p-3 font-serif text-sm outline-none focus:border-[#1a1a1a] mb-8" placeholder="New Title..." autoFocus />
            <div className="flex space-x-4">
              <button onClick={handleRenameProject} className="flex-1 bg-[#1a1a1a] text-white py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#333] cursor-pointer">Update Title</button>
              <button onClick={() => setIsRenameModalOpen(false)} className="flex-1 border border-[#dcd6bc] text-[#666] py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#f9f8f4] cursor-pointer">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {notification && (
        <div className="fixed bottom-8 right-8 z-[100] animate-in slide-in-from-right-full fade-in duration-300">
          <div className={`px-6 py-4 shadow-xl border flex items-center gap-3 rounded-sm backdrop-blur-sm ${
            notification.type === 'success' 
              ? 'bg-emerald-50/90 border-emerald-200 text-emerald-800' 
              : 'bg-rose-50/90 border-rose-200 text-rose-800'
          }`}>
            <div className={`w-5 h-5 flex items-center justify-center rounded-full ${notification.type === 'success' ? 'bg-emerald-200' : 'bg-rose-200'}`}>
              {notification.type === 'success' ? (
                <svg className="w-3 h-3 text-emerald-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-3 h-3 text-rose-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
              )}
            </div>
            <p className="font-sans font-bold text-[10px] uppercase tracking-widest opacity-80">{notification.text}</p>
          </div>
        </div>
      )}
    </div>
  );
}
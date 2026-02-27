'use client';

import React, { useEffect, useState, use, useRef } from 'react';
import { createClient } from '@/src/utils/supabase/client';

const PROJECT_STATUS: Record<string, { label: string; colorClass: string }> = {
  new: { label: "New Project", colorClass: "bg-gray-400" },
  missing_info: { label: "Missing Information", colorClass: "bg-gray-400" },
  publisher_search: { label: "Publisher Search", colorClass: "bg-amber-500" },
  drafting: { label: "Drafting Letters", colorClass: "bg-blue-500" },
  sent: { label: "Letters Sent", colorClass: "bg-emerald-600" },
  respond: { label: "Response Received", colorClass: "bg-rose-600" }
};

const LETTER_STATUS: Record<string, { label: string; colorClass: string }> = {
  new: { label: "Unwritten", colorClass: "bg-gray-400" },
  draft: { label: "Drafted", colorClass: "bg-blue-500" },
  sent: { label: "Sent", colorClass: "bg-emerald-500" },
  respond: { label: "Responded", colorClass: "bg-rose-600" },
  rejected: { label: "Rejected", colorClass: "bg-black" }
};

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface QueryLetter {
  id: string;
  publisher: string;
  current_letter: string | null;
  content: string[] | null;
  responses: string[] | null;
  status: string;
  updated_at: string;
}

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const supabase = createClient();

  const [activeTab, setActiveTab] = useState<'chat' | 'letters'>('chat');
  const [viewMode, setViewMode] = useState<'editor' | 'history'>('editor');
  const [project, setProject] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [queryLetters, setQueryLetters] = useState<QueryLetter[]>([]);
  const [selectedLetter, setSelectedLetter] = useState<QueryLetter | null>(null);

  const [isStatusMenuOpen, setIsStatusMenuOpen] = useState(false);
  const [showResponseInput, setShowResponseInput] = useState(false);
  const [newStatus, setNewStatus] = useState<string>('');
  const [publisherResponse, setPublisherResponse] = useState('');
  const [loading, setLoading] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);

  const getBookStyles = (id: string) => {
    const bookColors = [
      { bg: 'bg-red-600/10', spine: 'bg-red-600/30', text: 'text-red-900', border: 'border-red-600/20' },
      { bg: 'bg-green-600/10', spine: 'bg-green-600/30', text: 'text-green-900', border: 'border-green-600/20' },
      { bg: 'bg-blue-600/10', spine: 'bg-blue-600/30', text: 'text-blue-900', border: 'border-blue-600/20' },
      { bg: 'bg-pink-600/10', spine: 'bg-pink-600/30', text: 'text-pink-900', border: 'border-pink-600/20' },
      { bg: 'bg-purple-600/10', spine: 'bg-purple-600/30', text: 'text-purple-900', border: 'border-purple-600/20' },
      { bg: 'bg-teal-600/10', spine: 'bg-teal-600/30', text: 'text-teal-900', border: 'border-teal-600/20' },
    ];
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = id.charCodeAt(i) + ((hash << 5) - hash);
    return bookColors[Math.abs(hash) % bookColors.length];
  };

  const fetchData = async () => {
    const { data: projectData } = await supabase.from('projects').select('*').eq('id', id).single();
    setProject(projectData);
    const { data: messageData } = await supabase.from('messages').select('*').eq('project_id', id).order('created_at', { ascending: true });
    setMessages(messageData || []);
    const { data: lettersData } = await supabase.from('query_letters').select('*').eq('project_id', id).order('updated_at', { ascending: false });
    setQueryLetters(lettersData || []);
    if (lettersData && !selectedLetter) setSelectedLetter(lettersData[0]);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleSaveManuscript = async () => {
    if (!selectedLetter || !editorRef.current) return;
    const content = editorRef.current.innerText;
    const now = new Date().toISOString();

    await supabase.from('query_letters').update({
      current_letter: content,
      updated_at: now
    }).eq('id', selectedLetter.id);

    await supabase.from('projects').update({ updated_at: now }).eq('id', id);
    fetchData();
  };

  const handleStatusChange = async () => {
    if (!selectedLetter) return;
    const now = new Date().toISOString();

    const updatedContent = [...(selectedLetter.content || []), selectedLetter.current_letter || ''].filter(Boolean);
    const updatedResponses = [...(selectedLetter.responses || []), publisherResponse].filter(Boolean);

    await supabase.from('query_letters').update({
      status: newStatus,
      content: updatedContent,
      responses: updatedResponses,
      current_letter: null,
      updated_at: now
    }).eq('id', selectedLetter.id);

    await supabase.from('projects').update({ updated_at: now }).eq('id', id);

    setIsStatusMenuOpen(false);
    setShowResponseInput(false);
    setPublisherResponse('');
    fetchData();
  };

  const customFormatDate = (dateString: string) => {
    const date = new Date(dateString);
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Reviewing manuscript files...</div>;

  const { bg, spine, text, border } = getBookStyles(id);
  const statusInfo = PROJECT_STATUS[project?.current_stage] || { label: project?.current_stage, colorClass: "bg-slate-300" };

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-[#f4f1ea] overflow-hidden">
      {/* SIDEBAR */}
      <aside className="w-60 bg-[#f4f1ea] border-r border-[#dcd6bc] flex flex-col shrink-0 overflow-hidden">
        <div className="p-5 border-b border-[#dcd6bc] flex flex-col items-center">
          <div className={`relative flex w-28 h-40 mb-4 ${bg} ${border} border rounded-r shadow-md overflow-hidden`}>
            <div className={`w-2.5 h-full ${spine} border-r border-black/5`}></div>
            <div className="flex-1 p-2 flex flex-col justify-center">
              <h3 className={`text-sm font-bold leading-tight ${text} line-clamp-4 font-serif italic text-center`}>
                {project?.title || 'Untitled'}
              </h3>
            </div>
          </div>
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
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5v10a2 2 0 002 2z" /></svg>
            Query Letters
          </button>
        </nav>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden bg-[#fdfcf9]">
        {activeTab === 'chat' ? (
          <div className="h-full flex flex-col max-w-5xl mx-auto w-full p-8 overflow-hidden">
             <div ref={scrollRef} className="flex-1 overflow-y-auto mb-6 space-y-6 scrollbar-thin pr-4">
              {messages.length === 0 ? (
                <div className="flex justify-start">
                  <div className="max-w-[80%] p-6 rounded-2xl rounded-tl-none bg-white border border-[#eee] shadow-sm font-sans text-sm text-[#444] leading-relaxed">
                    Hello! I'm your Slush Pilot and I'm here to help getting your book published. Tell me the name of your book and a short description of the plot so we can get started.
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[75%] p-5 rounded-2xl shadow-sm font-sans text-sm leading-relaxed ${msg.role === 'user' ? 'bg-[#d9d4c0] text-[#1a1a1a] border border-[#dcd6bc] rounded-tr-none' : 'bg-white border border-[#eee] text-[#444] rounded-tl-none'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="bg-white border border-[#dcd6bc] p-4 flex items-center space-x-4 shadow-lg shrink-0">
              <textarea className="flex-1 bg-transparent outline-none resize-none font-sans text-sm py-2 h-12" placeholder="Ask SlushPilot" rows={1} />
              <button className="bg-[#1a1a1a] text-white px-8 py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#333] cursor-pointer shrink-0">Send</button>
            </div>
          </div>
        ) : (
          <div className="h-full flex divide-x divide-[#dcd6bc] overflow-hidden">
            <div className="w-72 bg-[#fdfcf9] flex flex-col overflow-hidden border-r border-[#dcd6bc]">
              <div className="flex-1 overflow-y-auto">
                {queryLetters.map((letter) => {
                  const letterInfo = LETTER_STATUS[letter.status] || { label: letter.status, colorClass: "bg-gray-400" };
                  return (
                    <div key={letter.id} onClick={() => { setSelectedLetter(letter); setViewMode('editor'); }} className={`p-4 cursor-pointer transition-all border-b border-[#dcd6bc] ${selectedLetter?.id === letter.id ? 'bg-white shadow-sm' : 'hover:bg-black/5'}`}>
                      <p className="font-bold text-sm text-[#1a1a1a] mb-2">{letter.publisher}</p>
                      <div className="flex justify-between items-center">
                        <span className={`${letterInfo.colorClass} opacity-80 text-white text-[8px] font-sans font-bold uppercase tracking-widest px-2 py-0.5 rounded-sm shadow-xs`}>{letterInfo.label}</span>
                        <span className="text-[11px] font-sans text-[#666]">{customFormatDate(letter.updated_at)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex-1 bg-white flex flex-col overflow-hidden relative">
              <div className="p-4 border-b border-[#dcd6bc] flex justify-between items-center bg-[#fafafa] shrink-0">
                <span className="text-[10px] font-sans font-bold uppercase tracking-widest text-[#999]">
                  Publisher: {selectedLetter?.publisher || 'None Selected'}
                </span>
                <div className="flex items-center gap-3">
                  <button onClick={() => setViewMode(viewMode === 'editor' ? 'history' : 'editor')} className="text-[10px] font-sans font-bold uppercase tracking-widest text-[#1a1a1a] border border-[#dcd6bc] px-3 py-1.5 hover:bg-black/5 cursor-pointer">
                    {viewMode === 'editor' ? 'View History' : 'Back to Editor'}
                  </button>

                  {viewMode === 'editor' && (
                    <>
                      <div className="relative">
                        <button onClick={() => setIsStatusMenuOpen(!isStatusMenuOpen)} className="text-[10px] font-sans font-bold uppercase tracking-widest text-[#1a1a1a] border border-[#dcd6bc] px-3 py-1.5 hover:bg-black/5 cursor-pointer flex items-center gap-1">
                          Update Status <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7" strokeWidth="2"/></svg>
                        </button>
                        {isStatusMenuOpen && (
                          <div className="absolute top-full right-0 mt-1 w-40 bg-white border border-[#dcd6bc] shadow-xl z-50">
                            {Object.entries(LETTER_STATUS).map(([key, info]) => (
                              <button key={key} onClick={() => { setNewStatus(key); setShowResponseInput(key === 'respond' || key === 'rejected'); if (key !== 'respond' && key !== 'rejected') handleStatusChange(); }} className="w-full text-left px-4 py-2 text-[10px] font-sans font-bold uppercase hover:bg-black/5">{info.label}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <button onClick={handleSaveManuscript} className="text-[10px] font-sans font-bold uppercase tracking-widest text-blue-600 border border-blue-600/20 px-3 py-1.5 hover:bg-blue-50 cursor-pointer">
                        Save Manuscript
                      </button>
                    </>
                  )}
                </div>
              </div>

              {showResponseInput && (
                <div className="p-6 bg-[#fff5f5] border-b border-red-100 flex flex-col gap-3">
                  <p className="text-[10px] font-sans font-bold uppercase tracking-widest text-red-600">Enter Publisher Feedback</p>
                  <textarea value={publisherResponse} onChange={(e) => setPublisherResponse(e.target.value)} className="w-full p-4 border border-[#dcd6bc] font-serif text-sm outline-none" rows={3} placeholder="Paste the editor's response here..." />
                  <div className="flex justify-end gap-2">
                    <button onClick={() => setShowResponseInput(false)} className="text-[10px] font-sans font-bold uppercase text-[#999]">Cancel</button>
                    <button onClick={handleStatusChange} className="bg-red-600 text-white px-4 py-2 text-[10px] font-sans font-bold uppercase">Confirm Transition</button>
                  </div>
                </div>
              )}

              <div className="flex-1 p-12 overflow-y-auto w-full">
                <div className="max-w-3xl mx-auto h-full">
                  {viewMode === 'editor' ? (
                    selectedLetter?.current_letter ? (
                      <div ref={editorRef} contentEditable className="outline-none min-h-full whitespace-pre-wrap text-lg font-serif leading-loose text-[#333]" suppressContentEditableWarning={true}>
                        {selectedLetter.current_letter}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-64 text-center">
                        <p className="font-serif italic text-lg text-[#666]">
                          {selectedLetter?.status === 'sent' ? (selectedLetter.content?.[selectedLetter.content.length-1]) :
                           (selectedLetter?.status === 'respond' || selectedLetter?.status === 'rejected') ? (selectedLetter.responses?.[selectedLetter.responses.length-1]) :
                           "No active draft. Ask the agent to create a draft!"}
                        </p>
                      </div>
                    )
                  ) : (
                    <div className="space-y-8">
                      {selectedLetter?.content?.map((c, i) => (
                        <div key={i} className="space-y-6">
                          <div className="flex justify-end">
                            <div className="max-w-[85%] p-6 bg-[#ebe6d5] border border-[#dcd6bc] font-serif text-sm leading-loose">
                              <p className="text-[10px] font-sans font-bold uppercase text-[#999] mb-4 border-b border-[#dcd6bc]/50 pb-2">Our Pitch — {customFormatDate(selectedLetter.updated_at)}</p>
                              {c}
                            </div>
                          </div>
                          {selectedLetter.responses?.[i] && (
                            <div className="flex justify-start">
                              <div className="max-w-[85%] p-6 bg-white border border-[#eee] font-serif text-sm leading-loose shadow-sm">
                                <p className="text-[10px] font-sans font-bold uppercase text-rose-400 mb-4 border-b border-rose-50 pb-2">Publisher Feedback</p>
                                {selectedLetter.responses[i]}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
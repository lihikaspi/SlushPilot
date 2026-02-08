'use client';

import React, { useEffect, useState, use } from 'react';
import { createClient } from '@/src/utils/supabase/client';

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const supabase = createClient();
  const [activeTab, setActiveTab] = useState<'chat' | 'letters'>('chat');
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function getProject() {
      const { data } = await supabase.from('projects').select('*').eq('id', id).single();
      setProject(data);
      setLoading(false);
    }
    getProject();
  }, [id, supabase]);

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Retrieving manuscript files...</div>;

  return (
    <div className="h-screen flex flex-col bg-[#f4f1ea]">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-[#dcd6bc] flex items-center justify-between px-8 py-4 shrink-0">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-bold tracking-tight text-[#1a1a1a]">{project?.title || 'Untitled'}</h2>
          <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-[#f0f0f0] text-[#666]">
            {project?.current_stage}
          </span>
        </div>

        <div className="flex bg-[#f0f0f0] p-1 rounded-sm">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-6 py-1 text-[10px] font-bold uppercase tracking-widest transition-all ${
              activeTab === 'chat' ? 'bg-white shadow-sm text-[#1a1a1a]' : 'text-[#999]'
            }`}
          >
            Advisor Chat
          </button>
          <button
            onClick={() => setActiveTab('letters')}
            className={`px-6 py-1 text-[10px] font-bold uppercase tracking-widest transition-all ${
              activeTab === 'letters' ? 'bg-white shadow-sm text-[#1a1a1a]' : 'text-[#999]'
            }`}
          >
            Query Letters
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? (
          <div className="h-full flex flex-col max-w-4xl mx-auto p-6">
            <div className="flex-1 overflow-y-auto mb-4 space-y-6 scrollbar-thin">
              <div className="bg-[#fdfcf9] border border-[#eee] p-6 text-sm italic font-serif text-[#666]">
                Greetings, Author. How shall we proceed with your manuscript today?
              </div>
            </div>
            <div className="bg-white border border-[#dcd6bc] p-4 flex items-end space-x-4 shadow-sm">
              <textarea
                className="flex-1 bg-transparent outline-none resize-none font-serif text-sm py-2"
                placeholder="Instruct the Supervisor..."
                rows={1}
              />
              <button className="bg-[#1a1a1a] text-white px-6 py-2 text-[10px] font-bold uppercase tracking-widest hover:bg-[#333]">
                Dispatch
              </button>
            </div>
          </div>
        ) : (
          <div className="h-full flex divide-x divide-[#dcd6bc]">
            {/* Sidebar: Publisher List */}
            <div className="w-80 bg-[#f9f8f4] overflow-y-auto">
              <div className="p-4 border-b border-[#dcd6bc]">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#999]">Identified Publishers</h3>
              </div>
              <div className="p-4 space-y-4">
                <div className="p-4 bg-white border border-[#eee] shadow-sm cursor-pointer hover:border-[#1a1a1a]">
                  <p className="font-bold text-sm">Penguin Random House</p>
                  <p className="text-[10px] text-[#999] uppercase mt-1">Status: Drafting</p>
                </div>
              </div>
            </div>

            {/* Editor: Letter Preview */}
            <div className="flex-1 bg-white flex flex-col overflow-hidden">
              <div className="p-4 border-b border-[#eee] flex justify-between items-center bg-[#fafafa]">
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#999]">Manuscript Draft</span>
                <button className="text-[10px] font-bold uppercase tracking-widest text-blue-600 underline">Save Manuscript</button>
              </div>
              <div className="flex-1 p-12 overflow-y-auto font-serif leading-loose text-[#333] max-w-3xl mx-auto w-full">
                <div
                  contentEditable
                  className="outline-none focus:ring-0 min-h-full whitespace-pre-wrap"
                  suppressContentEditableWarning={true}
                >
                  Dear Editor,{"\n\n"}
                  I am pleased to present my manuscript for your consideration...
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
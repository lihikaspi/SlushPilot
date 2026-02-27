'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createClient } from '../../utils/supabase/client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const PROJECT_STATUS: Record<string, { label: string; colorClass: string }> = {
  new: { label: "New Project", colorClass: "bg-gray-400" },
  publisher_search: { label: "Publisher Search", colorClass: "bg-sky-600" },
  drafting: { label: "Drafting Letters", colorClass: "bg-emerald-600" }
};

interface Project {
  id: string;
  title: string;
  current_stage: string;
  updated_at: string;
  visible: boolean;
  query_letters: { id: string }[];
}

export default function DashboardPage() {
  const supabase = createClient();
  const router = useRouter();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);

  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [modalType, setModalType] = useState<'rename' | 'delete' | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [renameValue, setRenameValue] = useState('');

  const menuRef = useRef<HTMLDivElement>(null);

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

  const fetchDashboardData = async () => {
    const storedUsername = localStorage.getItem('slushpilot_user');
    if (!storedUsername) return router.push('/');

    const { data: profile } = await supabase.from('profiles').select('id').eq('username', storedUsername).single();
    if (profile) {
      setUserId(profile.id);
      const { data } = await supabase.from('projects')
        .select('*, query_letters(id)')
        .eq('user_id', profile.id)
        .eq('visible', true)
        .order('updated_at', { ascending: false });
      if (data) setProjects(data as unknown as Project[]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDashboardData();
    const handleClickOutside = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setActiveMenu(null); };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const openRenameModal = (project: Project) => { setSelectedProject(project); setRenameValue(project.title); setModalType('rename'); setActiveMenu(null); };
  const openDeleteModal = (project: Project) => { setSelectedProject(project); setModalType('delete'); setActiveMenu(null); };
  const closeModal = () => { setModalType(null); setSelectedProject(null); setRenameValue(''); };

  const confirmRename = async () => {
    if (!selectedProject || !renameValue.trim()) return;
    await supabase.from('projects').update({ title: renameValue.trim(), updated_at: new Date().toISOString() }).eq('id', selectedProject.id);
    fetchDashboardData();
    closeModal();
  };

  const confirmDelete = async () => {
    if (!selectedProject) return;
    await supabase.from('projects').update({ visible: false, updated_at: new Date().toISOString() }).eq('id', selectedProject.id);
    fetchDashboardData();
    closeModal();
  };

  const createNewProject = async () => {
    if (!userId) return;
    const { data } = await supabase.from('projects').insert({ title: 'Untitled Manuscript', current_stage: 'new', user_id: userId, visible: true }).select().single();
    if (data) router.push(`/project/${data.id}`);
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Reviewing your library...</div>;

  return (
    <div className="p-8 max-w-[1600px] mx-auto h-[calc(100vh-4rem)]">
      <header className="flex justify-between items-end mb-12">
        <div>
          <h1 className="text-4xl font-bold text-[#1a1a1a] mb-2 tracking-tight">Your Slush Pile</h1>
          <p className="text-[#5c5c5c] italic text-lg font-serif">"Every great work begins with a single pitch."</p>
        </div>
        <button onClick={createNewProject} className="bg-[#1a1a1a] text-white px-6 py-3 font-sans font-bold uppercase tracking-widest text-xs hover:bg-[#333] transition-all cursor-pointer shadow-sm">
          New Book
        </button>
      </header>

      <div className="flex flex-wrap gap-x-16 gap-y-20">
        {projects.map((project) => {
          const statusInfo = PROJECT_STATUS[project.current_stage] || { label: project.current_stage, colorClass: "bg-slate-300" };
          const letterCount = (project.query_letters || []).length;
          const { bg, spine, text, border } = getBookStyles(project.id);

          return (
            <div key={project.id} className="flex flex-col group relative w-40">
              <div className="relative mb-5">
                <div className="absolute top-2 right-2 z-20">
                  <button
                    onClick={(e) => { e.stopPropagation(); setActiveMenu(activeMenu === project.id ? null : project.id); }}
                    className="p-1 bg-white/50 backdrop-blur-sm hover:bg-white/80 rounded-full transition-colors cursor-pointer text-black/40 hover:text-black/80 font-sans"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg>
                  </button>

                  {activeMenu === project.id && (
                    <div ref={menuRef} className="absolute left-full top-0 ml-1 w-32 bg-white border border-[#dcd6bc] shadow-xl z-30 py-1">
                      <button onClick={() => openRenameModal(project)} className="w-full text-left px-4 py-2 text-[10px] font-sans font-bold uppercase tracking-wider hover:bg-[#f9f8f4] text-[#1a1a1a] cursor-pointer">Rename</button>
                      <button onClick={() => openDeleteModal(project)} className="w-full text-left px-4 py-2 text-[10px] font-sans font-bold uppercase tracking-wider hover:bg-red-50 text-red-600 cursor-pointer">Delete</button>
                    </div>
                  )}
                </div>

                <Link href={`/project/${project.id}`} className="relative flex w-40 h-56 transition-transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-md hover:shadow-xl">
                  <div className={`relative flex w-full h-full ${bg} ${border} border rounded-r-lg overflow-hidden`}>
                    <div className={`w-4 h-full ${spine} border-r border-black/5`}></div>
                    <div className="flex-1 p-3 flex flex-col justify-center">
                      <h3 className={`text-base font-bold leading-tight ${text} line-clamp-5 font-serif italic text-center px-1`}>
                        {project.title}
                      </h3>
                    </div>
                  </div>
                </Link>
              </div>

              <div className="space-y-2 px-1 flex flex-col items-center text-center">
                <div>
                  <span className={`${statusInfo.colorClass} text-white text-[10px] font-sans font-bold uppercase tracking-widest px-2.5 py-1 rounded-sm shadow-sm inline-block w-fit`}>
                    {statusInfo.label}
                  </span>
                </div>
                <div className="flex items-center justify-center w-full">
                  <span className="text-xs font-sans font-bold text-[#444] tracking-tight">
                    {letterCount} {letterCount === 1 ? 'Letter' : 'Letters'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {modalType && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px] z-50 flex items-center justify-center p-4">
          <div className="bg-[#fdfcf9] border border-[#dcd6bc] w-full max-w-md shadow-2xl p-8 rounded-sm animate-in fade-in zoom-in duration-200">
            {modalType === 'rename' ? (
              <>
                <h2 className="text-xs font-sans font-bold uppercase tracking-widest text-[#999] mb-6">Rename Manuscript</h2>
                <input type="text" value={renameValue} onChange={(e) => setRenameValue(e.target.value)} className="w-full bg-white border border-[#dcd6bc] p-3 font-serif text-sm outline-none focus:border-[#1a1a1a] mb-8" placeholder="New Title..." autoFocus />
                <div className="flex space-x-4">
                  <button onClick={confirmRename} className="flex-1 bg-[#1a1a1a] text-white py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#333] cursor-pointer">Update Title</button>
                  <button onClick={closeModal} className="flex-1 border border-[#dcd6bc] text-[#666] py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#f9f8f4] cursor-pointer">Cancel</button>
                </div>
              </>
            ) : (
              <>
                <h2 className="text-xs font-sans font-bold uppercase tracking-widest text-red-600 mb-6">Confirm Deletion</h2>
                <p className="font-serif italic text-[#1a1a1a] mb-8">This action cannot be undone. Are you sure you want to delete this project?</p>
                <div className="flex space-x-4">
                  <button onClick={confirmDelete} className="flex-1 bg-red-600 text-white py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-red-700 cursor-pointer">Yes, Delete</button>
                  <button onClick={closeModal} className="flex-1 border border-[#dcd6bc] text-[#666] py-3 text-[10px] font-sans font-bold uppercase tracking-widest hover:bg-[#f9f8f4] cursor-pointer">Cancel</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
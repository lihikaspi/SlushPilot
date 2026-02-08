'use client';

import React, { useEffect, useState } from 'react';
// Using relative path to resolve internal utility issue
import { createClient } from '../../utils/supabase/client';
import Link from 'next/link';

interface Project {
  id: string;
  title: string;
  current_stage: string;
  updated_at: string;
}

export default function DashboardPage() {
  const supabase = createClient();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false });

      if (data) setProjects(data);
      if (error) console.error("Error fetching manuscripts:", error);
      setLoading(false);
    }

    fetchProjects();
  }, [supabase]);

  const createNewProject = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { data, error } = await supabase
      .from('projects')
      .insert({
        title: 'Untitled Manuscript',
        current_stage: 'publisher search',
        user_id: user.id
      })
      .select()
      .single();

    if (error) {
      console.error("Error creating new scroll:", error);
      return;
    }

    if (data) {
      window.location.href = `/project/${data.id}`;
    }
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Reviewing your library...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <header className="flex justify-between items-end mb-12">
        <div>
          <h1 className="text-4xl font-bold text-[#1a1a1a] mb-2 tracking-tight">Your Slush Pile</h1>
          <p className="text-[#5c5c5c] italic text-lg font-serif">"Every great work begins with a single pitch."</p>
        </div>
        <button
          onClick={createNewProject}
          className="bg-[#1a1a1a] text-white px-6 py-3 font-bold uppercase tracking-widest text-xs hover:bg-[#333] transition-all shadow-lg active:translate-y-1"
        >
          New Manuscript
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {projects.length === 0 ? (
          <div className="col-span-full py-20 border-2 border-dashed border-[#dcd6bc] text-center bg-white/50">
            <p className="text-[#999] font-serif italic text-lg mb-4">Your library is currently empty.</p>
            <button
              onClick={createNewProject}
              className="text-[#1a1a1a] font-bold underline hover:text-[#555] uppercase tracking-widest text-xs"
            >
              Start your first project
            </button>
          </div>
        ) : (
          projects.map((project) => (
            <Link
              key={project.id}
              href={`/project/${project.id}`}
              className="group block bg-white border border-[#dcd6bc] p-6 shadow-sm hover:shadow-xl transition-all relative overflow-hidden active:scale-[0.98]"
            >
              {/* Corner bookmark effect */}
              <div className="absolute top-0 right-0 w-12 h-12 bg-[#f4f1ea] rotate-45 translate-x-6 -translate-y-6 border-b border-[#dcd6bc]"></div>

              <div className="relative z-10 h-full flex flex-col justify-between">
                <div>
                  <h3 className="text-xl font-bold text-[#1a1a1a] mb-2 group-hover:text-blue-900 transition-colors line-clamp-2 leading-tight">
                    {project.title}
                  </h3>
                  <div className="flex items-center space-x-2 mt-4">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[#888]">
                      {project.current_stage}
                    </span>
                  </div>
                </div>

                <div className="mt-8 pt-4 border-t border-[#f0f0f0] flex justify-between items-center text-[10px] text-[#aaa]">
                  <span className="italic font-serif">
                    Revised: {new Date(project.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                  <span className="font-bold group-hover:translate-x-1 transition-transform">READ →</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      <footer className="mt-20 border-t border-[#dcd6bc] pt-8 text-center">
        <div className="inline-block px-4 bg-[#f4f1ea] -mt-11">
          <div className="w-2 h-2 rounded-full bg-[#dcd6bc] inline-block mx-1"></div>
          <div className="w-2 h-2 rounded-full bg-[#1a1a1a] inline-block mx-1"></div>
          <div className="w-2 h-2 rounded-full bg-[#dcd6bc] inline-block mx-1"></div>
        </div>
      </footer>
    </div>
  );
}
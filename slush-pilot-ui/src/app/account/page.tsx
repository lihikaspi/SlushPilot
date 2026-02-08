'use client';

import React, { useEffect, useState } from 'react';
import { createClient } from '../../utils/supabase/client';

export default function AccountPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    full_name: '',
    city: '',
    country: '',
    bio: '',
    phone: ''
  });

  useEffect(() => {
    async function loadProfile() {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', user.id)
          .single();

        if (data) {
          setProfile({
            full_name: data.full_name || '',
            city: data.city || '',
            country: data.country || '',
            bio: data.bio || '',
            phone: data.phone || ''
          });
        }
      }
      setLoading(false);
    }
    loadProfile();
  }, [supabase]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase
      .from('profiles')
      .upsert({ id: user.id, ...profile, updated_at: new Date().toISOString() });

    if (error) alert('Error saving biography.');
    else alert('Biography updated.');
    setSaving(false);
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Unrolling parchment...</div>;

  return (
    <div className="p-12 max-w-4xl mx-auto">
      <header className="mb-12 border-b-2 border-[#dcd6bc] pb-6">
        <h1 className="text-4xl font-bold text-[#1a1a1a] mb-2 tracking-tight">Author Biography</h1>
        <p className="text-[#5c5c5c] italic font-serif text-lg">Personal details used by the Composer to ink your letters.</p>
      </header>

      <form onSubmit={handleUpdate} className="bg-white border border-[#dcd6bc] shadow-sm p-10 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Legal Name / Nom de Plume</label>
              <input
                type="text"
                value={profile.full_name}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">City</label>
              <input
                type="text"
                value={profile.city}
                onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
              />
            </div>
          </div>
          <div className="space-y-6">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Contact Number</label>
              <input
                type="text"
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Country</label>
              <input
                type="text"
                value={profile.country}
                onChange={(e) => setProfile({ ...profile, country: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
              />
            </div>
          </div>
        </div>

        <div>
          <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Author Background</label>
          <textarea
            value={profile.bio}
            rows={6}
            onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
            className="w-full p-4 border border-[#eee] focus:border-[#1a1a1a] outline-none bg-[#fafafa] font-serif italic text-sm leading-relaxed"
            placeholder="Describe your writing history, accolades, or specific tone..."
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-10 py-3 bg-[#1a1a1a] text-white font-bold uppercase tracking-widest text-xs hover:bg-[#333] shadow-lg disabled:opacity-50"
          >
            {saving ? 'Updating...' : 'Update Record'}
          </button>
        </div>
      </form>
    </div>
  );
}
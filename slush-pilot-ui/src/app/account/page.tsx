'use client';

import React, { useEffect, useState } from 'react';
import { createClient } from '../../utils/supabase/client';

export default function AccountPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  // State for the notification message
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [profile, setProfile] = useState({
    username: '',
    full_name: '',
    phone: '',
    email: '',
    city: '',
    country: '',
    bio: ''
  });

  useEffect(() => {
    async function loadProfile() {
      const storedUsername = localStorage.getItem('slushpilot_user');

      if (storedUsername) {
        const { data, error } = await supabase
          .from('profiles')
          .select('*')
          .eq('username', storedUsername)
          .single();

        if (data && !error) {
          setProfile({
            username: data.username || '',
            full_name: data.full_name || '',
            phone: data.phone || '',
            email: data.email || '',
            city: data.city || '',
            country: data.country || '',
            bio: data.bio || ''
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
    setNotification(null); // Clear existing notifications

    const { error } = await supabase
      .from('profiles')
      .update({
        full_name: profile.full_name,
        phone: profile.phone,
        email: profile.email,
        city: profile.city,
        country: profile.country,
        bio: profile.bio
      })
      .eq('username', profile.username);

    if (error) {
      setNotification({ type: 'error', text: 'failed to update the biography' });
    } else {
      setNotification({ type: 'success', text: 'biography updated successfully' });
    }

    setSaving(false);

    // Automatically hide notification after 4 seconds
    setTimeout(() => {
      setNotification(null);
    }, 4000);
  };

  if (loading) return <div className="p-12 font-serif italic text-[#999]">Unrolling parchment...</div>;

  return (
    <div className="p-12 max-w-6xl mx-auto relative">
      <header className="mb-12 border-b-2 border-[#dcd6bc] pb-6 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-[#1a1a1a] mb-2 tracking-tight">Author Biography</h1>
          <p className="text-[#5c5c5c] italic font-serif text-lg">Personal details used by the Composer to ink your letters.</p>
        </div>

        <button
          onClick={(e) => handleUpdate(e as any)}
          disabled={saving}
          className="px-10 py-3 bg-[#1a1a1a] text-white font-sans font-bold uppercase tracking-widest text-xs hover:bg-[#333] shadow-lg disabled:opacity-50 cursor-pointer h-fit transition-all"
        >
          {saving ? 'Inking parchment...' : 'Update Biography'}
        </button>
      </header>

      <form onSubmit={handleUpdate} className="bg-white border border-[#dcd6bc] shadow-sm p-10 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">

          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Legal Name / Nom de Plume *</label>
              <input
                type="text"
                value={profile.full_name}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Username (Scribe Handle)</label>
              <input
                type="text"
                value={profile.username}
                disabled
                tabIndex={-1}
                className="w-full px-4 py-2 border-b border-[#eee] outline-none bg-[#f9f9f9] font-serif text-[#999] cursor-default pointer-events-none"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Phone Number</label>
              <input
                type="text"
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
                placeholder="+1 (555) 000-0000"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Email Address</label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
                placeholder="author@inkwell.com"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">City</label>
              <input
                type="text"
                value={profile.city}
                onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
                placeholder="London"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Country</label>
              <input
                type="text"
                value={profile.country}
                onChange={(e) => setProfile({ ...profile, country: e.target.value })}
                className="w-full px-4 py-2 border-b border-[#eee] focus:border-[#1a1a1a] outline-none bg-transparent font-serif"
                placeholder="United Kingdom"
              />
            </div>
          </div>

          <div className="lg:col-span-1 flex flex-col">
            <label className="block text-[10px] font-bold uppercase tracking-[0.2em] text-[#999] mb-2">Author Background</label>
            <textarea
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              className="flex-1 w-full p-4 border border-[#eee] focus:border-[#1a1a1a] outline-none bg-[#fafafa] font-serif italic text-sm leading-relaxed min-h-[300px]"
              placeholder="Describe your writing history, accolades, or specific tone..."
            />
          </div>
        </div>
      </form>

      {/* Toast Notification Container */}
      {notification && (
        <div className="fixed bottom-8 right-8 z-[100] animate-in slide-in-from-right-full fade-in duration-300">
          <div className={`px-6 py-4 shadow-2xl border flex items-center gap-3 rounded-sm ${
            notification.type === 'success' 
              ? 'bg-emerald-600 border-emerald-500 text-white' 
              : 'bg-rose-600 border-rose-500 text-white'
          }`}>
            {/* Status Icon */}
            <div className="w-5 h-5 flex items-center justify-center bg-white/20 rounded-full">
              {notification.type === 'success' ? (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>

            <p className="font-sans font-bold text-xs uppercase tracking-widest">
              {notification.text}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
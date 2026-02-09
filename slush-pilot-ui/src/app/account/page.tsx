'use client';

import React, { useEffect, useState } from 'react';
// Using the client utility to interact with Supabase
import { createClient } from '../../utils/supabase/client';

export default function AccountPage() {
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // State matching the public.profiles table fields
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
      // Retrieve the session username from local storage
      const storedUsername = localStorage.getItem('slushpilot_user');

      if (storedUsername) {
        // Fetch the user's profile data from the profiles table
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

    // Update the record in the profiles table based on the username
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
      alert('Error saving biography: ' + error.message);
    } else {
      alert('Biography updated successfully.');
    }
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">

          {/* Row 1: Full Name and Username */}
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
              className="w-full px-4 py-2 border-b border-[#eee] outline-none bg-[#f9f9f9] font-serif text-[#999] cursor-not-allowed"
            />
          </div>

          {/* Row 2: Phone and Email */}
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

          {/* Row 3: City and Country */}
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

        {/* Bio Section */}
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
            className="px-10 py-3 bg-[#1a1a1a] text-white font-bold uppercase tracking-widest text-xs hover:bg-[#333] shadow-lg disabled:opacity-50 cursor-pointer"
          >
            {saving ? 'Inking parchment...' : 'Update Biography'}
          </button>
        </div>
      </form>
    </div>
  );
}
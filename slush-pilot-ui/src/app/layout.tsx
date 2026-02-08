'use client';

import "./globals.css";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
// Using the client utility to interact with Supabase
import { createClient } from "../utils/supabase/client";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/";

  const [profile, setProfile] = useState<{ fullName: string; username: string } | null>(null);
  const supabase = createClient();

  useEffect(() => {
    const fetchUserData = async () => {
      const storedUsername = localStorage.getItem('slushpilot_user');

      if (storedUsername) {
        // Fetch profile details from the database
        const { data, error } = await supabase
          .from('profiles')
          .select('full_name, username')
          .eq('username', storedUsername)
          .single();

        if (data && !error) {
          setProfile({
            fullName: data.full_name,
            username: data.username
          });
        }
      } else if (!isLoginPage) {
        router.push("/");
      }
    };

    fetchUserData();
  }, [pathname, isLoginPage, router, supabase]);

  const handleLogout = () => {
    localStorage.removeItem('slushpilot_user');
    window.location.href = "/";
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  /**
   * Seeded Color Logic: Uses the unique username for better distribution
   * to ensure all colors are used.
   */
  const getBookStyles = (username: string) => {
    const bookColors = [
      { bg: 'bg-red-600/10', spine: 'bg-red-600/30', text: 'text-red-900' },
      { bg: 'bg-green-600/10', spine: 'bg-green-600/30', text: 'text-green-900' },
      { bg: 'bg-blue-600/10', spine: 'bg-blue-600/30', text: 'text-blue-900' },
      { bg: 'bg-pink-600/10', spine: 'bg-pink-600/30', text: 'text-pink-900' },
      { bg: 'bg-purple-600/10', spine: 'bg-purple-600/30', text: 'text-purple-900' },
      { bg: 'bg-indigo-600/10', spine: 'bg-indigo-600/30', text: 'text-indigo-900' },
      { bg: 'bg-teal-600/10', spine: 'bg-teal-600/30', text: 'text-teal-900' },
    ];

    // Hash function for strings to ensure even distribution
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % bookColors.length;
    return bookColors[index];
  };

  const initials = profile ? getInitials(profile.fullName) : "?";
  // Pass the unique username as the seed for better color randomization
  const { bg: bookBg, spine: spineBg, text: textColor } = getBookStyles(profile?.username || "default");

  return (
    <html lang="en">
      <head>
        <title>SlushPilot</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased bg-[#f4f1ea] text-[#2c2c2c] font-['Inter',sans-serif]">
        <div className="flex min-h-screen">
          {!isLoginPage && (
            <aside className="w-64 bg-white border-r border-[#dcd6bc] flex flex-col fixed h-full shadow-sm z-20">

              {/* Profile Header centered with the book icon */}
              <div className="p-6 flex items-center gap-4">
                <div className={`relative flex min-w-[42px] h-[54px] ${bookBg} rounded-r-md shadow-sm border border-black/5 overflow-hidden`}>
                  <div className={`w-[10px] ${spineBg} border-r border-black/5`}></div>
                  {/* Spaced Initials */}
                  <div className={`flex-1 flex items-center justify-center text-[11px] font-bold tracking-tighter ${textColor}`}>
                    {initials.split('').join(' ')}
                  </div>
                </div>

                <div className="min-w-0">
                  {/* Larger Name Display */}
                  <h2 className="text-base font-bold text-[#1a1a1a] truncate leading-tight">
                    {profile?.fullName || "Loading..."}
                  </h2>
                </div>
              </div>

              <div className="mx-6 border-b border-[#eee] mb-4"></div>

              <nav className="flex-1 p-4 space-y-1">
                <Link
                  href="/account"
                  className={`flex items-center p-3 text-xs font-bold uppercase tracking-widest transition-colors rounded-sm cursor-pointer ${
                    pathname === '/account' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-[#f9f8f4] text-[#666]'
                  }`}
                >
                  Biography
                </Link>
                <Link
                  href="/dashboard"
                  className={`flex items-center p-3 text-xs font-bold uppercase tracking-widest transition-colors rounded-sm cursor-pointer ${
                    pathname === '/dashboard' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-[#f9f8f4] text-[#666]'
                  }`}
                >
                  Library
                </Link>
              </nav>

              <div className="mt-auto">
                {/* Relocated Logout Button above branding */}
                <div className="px-6 py-4">
                  <button
                    onClick={handleLogout}
                    className="w-full py-2 text-[10px] font-bold uppercase tracking-widest text-red-700 hover:bg-red-50 transition-colors border border-red-100 rounded-sm cursor-pointer"
                  >
                    Logout
                  </button>
                </div>

                <div className="p-8 border-t border-[#eee]">
                  <h1 className="text-xl font-bold tracking-tighter text-[#1a1a1a] font-serif">SlushPilot</h1>
                  <p className="text-[9px] uppercase tracking-[0.2em] text-[#bbb] mt-1">Scribe Portal</p>
                </div>
              </div>
            </aside>
          )}

          <main className={`flex-1 ${!isLoginPage ? 'ml-64' : ''} min-h-screen relative font-serif`}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
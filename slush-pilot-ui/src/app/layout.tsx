'use client';

import "./globals.css";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
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

  const getProfileStyles = (username: string) => {
    const colors = [
      { bg: 'bg-red-600/10', text: 'text-red-900' },
      { bg: 'bg-green-600/10', text: 'text-green-900' },
      { bg: 'bg-blue-600/10', text: 'text-blue-900' },
      { bg: 'bg-pink-600/10', text: 'text-pink-900' },
      { bg: 'bg-purple-600/10', text: 'text-purple-900' },
      { bg: 'bg-indigo-600/10', text: 'text-indigo-900' },
      { bg: 'bg-teal-600/10', text: 'text-teal-900' },
    ];

    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colors.length;
    return colors[index];
  };

  const initials = profile ? getInitials(profile.fullName) : "?";
  const { bg: profileBg, text: textColor } = getProfileStyles(profile?.username || "default");

  return (
    <html lang="en">
      <head>
        <title>SlushPilot</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased bg-[#f4f1ea] text-[#2c2c2c] font-['Inter',sans-serif]">
        <div className="flex flex-col min-h-screen">
          {!isLoginPage && (
            <header className="sticky top-0 z-50 w-full h-16 bg-[#ebe6d5] border-b border-[#dcd6bc] grid grid-cols-3 items-center px-8 shadow-sm">

              {/* Left Side: Profile and Logout */}
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 ${profileBg} border border-black/5 flex items-center justify-center rounded-sm shadow-sm`}>
                    <span className={`text-xs font-serif font-bold tracking-widest ${textColor}`}>
                      {initials}
                    </span>
                  </div>
                  <h2 className="text-sm font-bold text-[#1a1a1a] truncate max-w-[120px]">
                    {profile?.fullName || "Loading..."}
                  </h2>
                </div>

                <button
                  onClick={handleLogout}
                  className="px-3 py-1.5 text-[10px] font-sans font-bold uppercase tracking-widest text-red-700 bg-red-500/15 hover:bg-red-700 hover:text-white hover:border-red-700 transition-all border border-red-200 rounded-sm cursor-pointer"
                >
                  Sign Out
                </button>
              </div>

              {/* Center: Navigation Section */}
              <nav className="flex items-center justify-center gap-2">
                <Link
                  href="/account"
                  className={`flex items-center gap-2 px-4 py-2 text-[11px] font-sans font-bold uppercase tracking-widest transition-colors rounded-sm ${
                    pathname === '/account' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-black/5 text-[#666]'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Biography
                </Link>
                <Link
                  href="/dashboard"
                  className={`flex items-center gap-2 px-4 py-2 text-[11px] font-sans font-bold uppercase tracking-widest transition-colors rounded-sm ${
                    pathname === '/dashboard' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-black/5 text-[#666]'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Library
                </Link>
              </nav>

              {/* Right Side: Branding Section */}
              <div className="text-right">
                <h1 className="text-xl font-bold tracking-tighter text-[#1a1a1a] font-serif">SlushPilot</h1>
                <p className="text-[8px] uppercase tracking-[0.2em] text-[#bbb] -mt-1">Scribe Portal</p>
              </div>
            </header>
          )}

          <main className="flex-1 h-screen relative font-serif">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
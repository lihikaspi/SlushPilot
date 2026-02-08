'use client';

import "./globals.css";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "../utils/supabase/client";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const supabase = createClient();

  useEffect(() => {
    const checkUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUserEmail(user?.email || null);
    };
    checkUser();
  }, [supabase, pathname]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = "/login";
  };

  return (
    <html lang="en">
      <head>
        <title>SlushPilot</title>
      </head>
      <body className="antialiased bg-[#f4f1ea] text-[#2c2c2c] font-serif">
        <div className="flex min-h-screen">
          {!isLoginPage && (
            <aside className="w-64 bg-white border-r border-[#dcd6bc] flex flex-col fixed h-full shadow-sm z-20">
              <div className="p-8 border-b border-[#eee]">
                <h1 className="text-2xl font-bold tracking-tighter text-[#1a1a1a]">SlushPilot</h1>
                <p className="text-[10px] uppercase tracking-[0.2em] text-[#999] mt-1">Scribe Portal</p>
              </div>

              <nav className="flex-1 p-4 space-y-1 mt-4">
                <Link
                  href="/dashboard"
                  className={`flex items-center p-3 text-xs font-bold uppercase tracking-widest transition-colors ${
                    pathname === '/dashboard' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-[#f9f8f4] text-[#666]'
                  }`}
                >
                  Library
                </Link>
                <Link
                  href="/account"
                  className={`flex items-center p-3 text-xs font-bold uppercase tracking-widest transition-colors ${
                    pathname === '/account' ? 'bg-[#1a1a1a] text-white' : 'hover:bg-[#f9f8f4] text-[#666]'
                  }`}
                >
                  Biography
                </Link>
              </nav>

              <div className="p-6 border-t border-[#eee]">
                {userEmail && (
                  <div className="mb-4">
                    <p className="text-[10px] text-[#999] uppercase truncate">{userEmail}</p>
                  </div>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full text-left py-2 text-[10px] font-bold uppercase tracking-widest text-red-700 hover:underline"
                >
                  Logout
                </button>
              </div>
            </aside>
          )}

          <main className={`flex-1 ${!isLoginPage ? 'ml-64' : ''} min-h-screen relative`}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
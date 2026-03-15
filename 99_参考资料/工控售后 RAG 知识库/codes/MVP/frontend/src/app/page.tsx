'use client';

import React, { useState, useEffect } from 'react';
import { MoreHorizontal, Activity } from 'lucide-react';
import { Sidebar } from '@/components/Sidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { Dashboard } from '@/components/Dashboard';
import { UserManagement } from '@/components/UserManagement';
import { BadCases } from '@/components/BadCases';
import { SystemMonitor } from '@/components/SystemMonitor';
import { History } from '@/components/History';
import { Login } from '@/components/Login';

export default function Home() {
  const [user, setUser] = useState<any>(null); // Logged in user object
  const [activeTab, setActiveTab] = useState('chat'); // Default to chat
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Handle Login
  const handleLogin = (userData: any) => {
    setUser(userData);
    // If admin, default to dashboard? Or stay at chat? Let's default to dashboard for admin usually, but chat is fine.
    // Actually, if 'user', force chat.
    if (userData.role === 'user') {
      setActiveTab('chat');
    } else {
      setActiveTab('dashboard');
    }
  };

  // If not logged in, show Login only
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  const currentRole = user.role || 'user';

  return (
    <div className="flex h-screen bg-[#f5f7fa] text-slate-800 font-sans overflow-hidden selection:bg-blue-100">

      {/* Sidebar */}
      <Sidebar
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isMobileMenuOpen={isMobileMenuOpen}
        onLogout={() => setUser(null)}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full relative w-full transition-all duration-300">

        {/* Mobile Header Trigger (Hidden on Desktop) */}
        <div className="md:hidden h-14 bg-white border-b border-slate-200 flex items-center px-4 justify-between">
          <div className="font-bold text-slate-700">工业智能助手</div>
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 text-slate-500">
            <MoreHorizontal />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative">
          {activeTab === 'chat' && <ChatInterface role={currentRole} user={user} />}
          {activeTab === 'history' && <History user={user} />}
          {activeTab === 'dashboard' && currentRole === 'admin' && <Dashboard />}
          {activeTab === 'users' && currentRole === 'admin' && <UserManagement />}
          {activeTab === 'badcases' && currentRole === 'admin' && <BadCases />}
          {activeTab === 'performance' && currentRole === 'admin' && <SystemMonitor />}

          {/* Fallback for other tabs */}
          {(activeTab !== 'chat' && activeTab !== 'history' && activeTab !== 'dashboard' && activeTab !== 'users' && activeTab !== 'badcases' && activeTab !== 'performance') && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <Activity size={48} className="mb-4 opacity-20" />
              <p>该模块 ({activeTab}) 正在开发中...</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

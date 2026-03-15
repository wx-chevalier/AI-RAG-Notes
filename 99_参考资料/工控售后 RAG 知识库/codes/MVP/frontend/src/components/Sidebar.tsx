import React from 'react';
import { MessageSquare, LayoutDashboard, Users, AlertTriangle, Activity, Clock } from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
    user: any;
    activeTab: string;
    setActiveTab: (tab: string) => void;
    isMobileMenuOpen: boolean;
    onLogout: () => void;
}

export function Sidebar({ user, activeTab, setActiveTab, isMobileMenuOpen, onLogout }: SidebarProps) {
    interface MenuItem {
        id: string;
        label: string;
        type: 'header' | 'item';
        icon: React.ReactNode | null;
        badge?: string;
    }

    // Removed historyItems fetch logic as requested

    const baseItems: MenuItem[] = [
        { id: 'section-1', label: '工作区', type: 'header', icon: null },
        { id: 'chat', label: '智能问答', icon: <MessageSquare size={18} />, type: 'item' },
        { id: 'history', label: '历史记录', icon: <Clock size={18} />, type: 'item' },
    ];



    const adminItems: MenuItem[] = [
        { id: 'section-2', label: '管理后台', type: 'header', icon: null },
        { id: 'dashboard', label: '数据概览', icon: <LayoutDashboard size={18} />, type: 'item' },
        { id: 'users', label: '用户管理', icon: <Users size={18} />, type: 'item' },
        { id: 'badcases', label: 'Bad Cases', icon: <AlertTriangle size={18} />, type: 'item' },
        { id: 'performance', label: '系统监控', icon: <Activity size={18} />, type: 'item' },
    ];

    const menuItems = user.role === 'admin' ? [...baseItems, ...adminItems] : baseItems;

    return (
        <aside className={clsx(
            "bg-white border-r border-slate-200 flex flex-col h-full z-20 transition-all duration-300",
            isMobileMenuOpen ? 'absolute w-64 shadow-2xl' : 'hidden md:flex md:w-64'
        )}>
            {/* Logo */}
            <div className="p-6 border-b border-slate-100 flex items-center gap-3">
                <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm shadow-blue-200">
                    亚
                </div>
                <div>
                    <h1 className="font-bold text-sm text-slate-800 tracking-tight">智能售后助手</h1>
                    <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Enterprise AI</p>
                </div>
            </div>

            {/* Menu */}
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1 scrollbar-hide">
                {menuItems.map((item, idx) => {
                    if (item.type === 'header') {
                        return <div key={idx} className={`text-xs font-bold text-slate-400 px-3 mb-2 uppercase tracking-wider ${idx > 0 ? 'mt-6' : 'mt-2'}`}>{item.label}</div>;
                    }
                    return (
                        <div
                            key={item.id}
                            onClick={() => item.id && setActiveTab(item.id)}
                            className={clsx(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all text-sm font-medium group",
                                activeTab === item.id
                                    ? 'bg-blue-50 text-blue-600 shadow-sm ring-1 ring-blue-100'
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                            )}
                        >
                            <span className={clsx("transition-colors", activeTab === item.id ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600')}>{item.icon}</span>
                            <span className="flex-1">{item.label}</span>
                            {(item as any).badge && (
                                <span className="bg-rose-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold shadow-sm shadow-rose-200">{(item as any).badge}</span>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* User & Role Switcher */}
            <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-3 mb-3 shadow-sm">
                    <div className={clsx("w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold uppercase", user.role === 'admin' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600')}>
                        {user.display_name?.[0] || user.email?.[0] || 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold text-slate-700 truncate">{user.display_name || 'User'}</div>
                        <div className="text-xs text-slate-400 truncate font-mono">{user.email}</div>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={onLogout}
                        className="flex-1 text-xs font-medium text-slate-500 hover:text-red-600 flex items-center justify-center gap-2 py-2.5 border border-dashed border-slate-300 rounded-lg hover:bg-red-50 hover:border-red-200 transition-all"
                    >
                        <span>退出登录</span>
                    </button>
                    <span className="px-2 py-2.5 text-[10px] font-mono text-slate-400 bg-slate-100 rounded-lg border border-slate-200" title="当前角色">
                        {user.role === 'admin' ? 'ADM' : 'USR'}
                    </span>
                </div>
            </div>
        </aside>
    );
}

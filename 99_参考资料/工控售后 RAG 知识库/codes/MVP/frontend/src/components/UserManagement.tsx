import React, { useEffect, useState } from 'react';
import { Search, MoreHorizontal, User, Shield, Briefcase } from 'lucide-react';
import clsx from 'clsx';

interface UserProfile {
    id: string;
    display_name: string;
    email: string;
    role: 'admin' | 'user';
    department: string;
    status: string;
    stats: {
        total_queries: number;
        total_feedback_given: number;
    };
    created_at: string;
}

export function UserManagement() {
    const [users, setUsers] = useState<UserProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetch('http://localhost:8000/admin/users')
            .then(res => res.json())
            .then(data => {
                setUsers(data);
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, []);

    const filteredUsers = users.filter(u =>
        u.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.department?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex-1 overflow-y-auto bg-[#f5f7fa] p-8 h-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white sticky top-0 z-10">
                    <h3 className="font-bold text-slate-700 text-lg">用户列表</h3>
                    <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus-within:ring-2 focus-within:ring-blue-100 transition-all w-64">
                        <Search size={16} className="text-slate-400" />
                        <input
                            type="text"
                            placeholder="搜索用户或部门..."
                            className="bg-transparent border-none outline-none text-sm w-full"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-50 border-b border-slate-100">
                            <tr>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">用户</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">部门</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">角色</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">提问数</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">反馈数</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">反馈率</th>
                                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">状态</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr><td colSpan={8} className="p-8 text-center text-slate-400">加载中...</td></tr>
                            ) : filteredUsers.length === 0 ? (
                                <tr><td colSpan={8} className="p-8 text-center text-slate-400">未找到用户</td></tr>
                            ) : (
                                filteredUsers.map((u) => {
                                    const rate = u.stats?.total_queries > 0
                                        ? ((u.stats.total_feedback_given / u.stats.total_queries) * 100).toFixed(1)
                                        : '0.0';

                                    return (
                                        <tr key={u.id} className="hover:bg-slate-50 transition-colors group">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-100 to-blue-100 flex items-center justify-center text-indigo-600 font-bold text-xs uppercase">
                                                        {u.display_name?.[0] || u.email[0]}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-slate-800">{u.display_name}</div>
                                                        <div className="text-xs text-slate-400">{u.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6 text-sm text-slate-600">
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-100 text-slate-600 text-xs font-medium">
                                                    <Briefcase size={12} /> {u.department || 'Unknown'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className={clsx(
                                                    "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold",
                                                    u.role === 'admin' ? "bg-purple-100 text-purple-600" : "bg-blue-50 text-blue-600"
                                                )}>
                                                    {u.role === 'admin' ? <Shield size={10} /> : <User size={10} />}
                                                    {u.role === 'admin' ? '管理员' : '用户'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6 text-sm font-medium text-slate-700">{u.stats?.total_queries || 0}</td>
                                            <td className="py-4 px-6 text-sm font-medium text-slate-700">{u.stats?.total_feedback_given || 0}</td>
                                            <td className="py-4 px-6 text-sm text-slate-500">{rate}%</td>
                                            <td className="py-4 px-6">
                                                <span className={clsx(
                                                    "w-2 h-2 rounded-full inline-block mr-2",
                                                    u.status === 'active' ? "bg-green-500" : "bg-slate-300"
                                                )}></span>
                                                <span className="text-sm text-slate-600 capitalize">{u.status}</span>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

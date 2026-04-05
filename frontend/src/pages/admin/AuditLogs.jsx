import React, { useState, useEffect } from 'react';
import { admin } from '../../services/api';
import { Search, Filter, Download, Clock, User, Activity } from 'lucide-react';

const AuditLogs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const loadLogs = async () => {
        setLoading(true);
        try {
            const params = { page, limit: 20 };
            if (filter) params.action_type = filter;
            const res = await admin.auditLogs(params);
            if (res.data.success) {
                setLogs(res.data.data);
                setTotalPages(Math.ceil(res.data.total / 20) || 1);
            }
        } catch (err) {
            console.error("Failed to load audit logs", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadLogs(); }, [filter, page]);

    const filteredLogs = logs.filter(log =>
        log.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.action?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getActionBadge = (action) => {
        const colors = {
            LOGIN: 'bg-blue-100 text-blue-700',
            LOGOUT: 'bg-slate-100 text-slate-700',
            CREATE: 'bg-green-100 text-green-700',
            UPDATE: 'bg-yellow-100 text-yellow-700',
            DELETE: 'bg-red-100 text-red-700',
            APPROVE: 'bg-purple-100 text-purple-700',
            REJECT: 'bg-orange-100 text-orange-700',
        };
        return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[action] || 'bg-slate-100 text-slate-700'}`}>{action}</span>;
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Audit Logs</h2>
                    <p className="text-slate-500">Track all system activities and actions</p>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200">
                <div className="p-4 border-b border-slate-100 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <select
                        className="px-3 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 text-sm"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                    >
                        <option value="">All Actions</option>
                        <option value="LOGIN">Login</option>
                        <option value="LOGOUT">Logout</option>
                        <option value="CREATE">Create</option>
                        <option value="UPDATE">Update</option>
                        <option value="DELETE">Delete</option>
                        <option value="APPROVE">Approve</option>
                        <option value="REJECT">Reject</option>
                    </select>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-50 text-slate-600 font-medium text-sm">
                            <tr>
                                <th className="px-6 py-4">Timestamp</th>
                                <th className="px-6 py-4">User</th>
                                <th className="px-6 py-4">Action</th>
                                <th className="px-6 py-4">Details</th>
                                <th className="px-6 py-4">IP Address</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr><td colSpan="5" className="text-center py-8 text-slate-400">Loading...</td></tr>
                            ) : filteredLogs.length === 0 ? (
                                <tr><td colSpan="5" className="text-center py-8 text-slate-400">No logs found</td></tr>
                            ) : (
                                filteredLogs.map((log, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50 transition">
                                        <td className="px-6 py-4 text-sm text-slate-500">
                                            <div className="flex items-center gap-2">
                                                <Clock size={14} />
                                                {new Date(log.created_at).toLocaleString()}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <User size={14} className="text-slate-400" />
                                                {log.username || 'System'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">{getActionBadge(log.action_type)}</td>
                                        <td className="px-6 py-4 text-sm text-slate-600 max-w-xs truncate">{log.details || '-'}</td>
                                        <td className="px-6 py-4 text-sm text-slate-400">{log.ip_address || '-'}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="p-4 border-t border-slate-100 flex justify-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 rounded border border-slate-200 text-sm disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="px-3 py-1 text-sm text-slate-500">Page {page} of {totalPages}</span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-3 py-1 rounded border border-slate-200 text-sm disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuditLogs;
import React from 'react';
import { Bell, X, AlertTriangle, Package } from 'lucide-react';
import { useWebSocketAlerts } from '../../context/WebSocketContext';

const AlertsDropdown = () => {
    const { alerts, clearAlert, clearAllAlerts } = useWebSocketAlerts();
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
            >
                <Bell size={20} />
                {alerts.length > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                )}
            </button>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 z-20 overflow-hidden">
                        <div className="p-3 border-b border-slate-100 flex items-center justify-between">
                            <span className="font-semibold text-slate-800">Real-time Alerts</span>
                            {alerts.length > 0 && (
                                <button
                                    onClick={clearAllAlerts}
                                    className="text-xs text-slate-500 hover:text-slate-700"
                                >
                                    Clear all
                                </button>
                            )}
                        </div>
                        <div className="max-h-80 overflow-y-auto">
                            {alerts.length === 0 ? (
                                <div className="p-4 text-center text-slate-400 text-sm">
                                    No new alerts
                                </div>
                            ) : (
                                alerts.map((alert, index) => (
                                    <div
                                        key={index}
                                        className="p-3 border-b border-slate-50 hover:bg-slate-50 transition relative"
                                    >
                                        <button
                                            onClick={() => clearAlert(index)}
                                            className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
                                        >
                                            <X size={14} />
                                        </button>
                                        <div className="flex items-start gap-2 pr-6">
                                            {alert.type === 'low_stock_alert' ? (
                                                <AlertTriangle size={16} className="text-amber-500 mt-0.5 shrink-0" />
                                            ) : (
                                                <Package size={16} className="text-blue-500 mt-0.5 shrink-0" />
                                            )}
                                            <div>
                                                <p className="text-sm font-medium text-slate-800">{alert.message || 'Low stock alert'}</p>
                                                {alert.item_name && (
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        Item: {alert.item_name}
                                                    </p>
                                                )}
                                                {alert.location_name && (
                                                    <p className="text-xs text-slate-400">
                                                        Location: {alert.location_name}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default AlertsDropdown;
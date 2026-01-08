import { useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

const Toast = ({ message, type = 'info', onClose, duration = 5000 }) => {
    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(() => {
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [duration, onClose]);

    const icons = {
        success: CheckCircle,
        error: AlertCircle,
        warning: AlertTriangle,
        info: Info
    };

    const colors = {
        success: 'bg-green-900/90 border-green-500 text-green-100',
        error: 'bg-red-900/90 border-red-500 text-red-100',
        warning: 'bg-yellow-900/90 border-yellow-500 text-yellow-100',
        info: 'bg-blue-900/90 border-blue-500 text-blue-100'
    };

    const Icon = icons[type] || icons.info;

    return (
        <div className={`flex items-center gap-3 p-4 rounded-lg border shadow-lg min-w-[300px] max-w-[500px] ${colors[type]}`}>
            <Icon className="w-5 h-5 flex-shrink-0" />
            <p className="flex-1 text-sm font-medium">{message}</p>
            <button
                onClick={onClose}
                className="flex-shrink-0 hover:opacity-70 transition-opacity"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

export default Toast;

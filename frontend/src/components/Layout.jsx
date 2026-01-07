import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Map, BarChart2, LogOut, Layers, Users } from 'lucide-react';

export default function Layout() {
    const { user, logout } = useAuth();
    const location = useLocation();

    const navItems = [
        { name: 'Map View', path: '/', icon: Map },
        { name: 'Analysis', path: '/analysis', icon: BarChart2 },
        { name: 'Regions', path: '/regions', icon: Layers },
        { name: 'Teams', path: '/teams', icon: Users },
    ];

    return (
        <div className="flex h-screen bg-gray-900 text-gray-100">
            {/* Sidebar */}
            <aside className="w-64 border-r border-gray-800 bg-gray-900 flex flex-col">
                <div className="p-6">
                    <h1 className="text-xl font-bold text-blue-400">BlackSea Monitor</h1>
                    <p className="text-xs text-gray-500 mt-1">v1.0.0</p>
                </div>

                <nav className="flex-1 space-y-1 px-3">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${isActive
                                    ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`}
                            >
                                <Icon size={20} />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                <div className="border-t border-gray-800 p-4">
                    <div className="flex items-center gap-3 mb-4 px-2">
                        <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center font-bold">
                            {user?.username?.charAt(0).toUpperCase()}
                        </div>
                        <div className="overflow-hidden">
                            <p className="truncate text-sm font-medium text-white">{user?.username || 'User'}</p>
                            <p className="truncate text-xs text-gray-500">{user?.role || 'Viewer'}</p>
                        </div>
                    </div>

                    <button
                        onClick={logout}
                        className="flex w-full items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 transition-colors"
                    >
                        <LogOut size={18} />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden relative">
                <Outlet />
            </main>
        </div>
    );
}

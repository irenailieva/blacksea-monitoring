import { Outlet, Link, useLocation } from 'react-router-dom';
import useAuth from '../store/useAuth';
import { useNotifications } from '@/store/useNotifications';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Archive, LayoutDashboard, Map, Menu, Bell, Users, LucideIcon } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface NavigationItem {
    name: string;
    href: string;
    icon: LucideIcon;
    role?: string;
}

export default function Layout() {
    const { user, logout } = useAuth();
    const { notifications, unreadCount, markAsRead } = useNotifications();
    const location = useLocation();

    const navigation: NavigationItem[] = [
        { name: 'Map', href: '/', icon: Map },
        { name: 'Analysis', href: '/analysis', icon: LayoutDashboard },
        { name: 'Data', href: '/data', icon: Archive },
        { name: 'Admin', href: '/admin', icon: Users, role: 'admin' },
    ];

    const filteredNav = navigation.filter(item => !item.role || (user && user.role === item.role) || !user);

    return (
        <div className="flex min-h-screen w-full flex-col">
            <header className="sticky top-0 z-[99999] flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6 shadow-sm">
                <div id="header-portal-root" className="absolute top-0 left-0 w-0 h-0" />
                <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
                    <Link
                        to="/"
                        className="flex items-center gap-2 text-lg font-semibold md:text-base"
                    >
                        <img src="/logo.svg" alt="Black Sea Monitor" className="h-8 w-auto" />
                        <span className="sr-only">Black Sea Monitor</span>
                    </Link>
                    {filteredNav.map((item) => (
                        <Link
                            key={item.name}
                            to={item.href}
                            className={`transition-colors hover:text-foreground ${location.pathname === item.href ? 'text-foreground' : 'text-muted-foreground'
                                }`}
                        >
                            {item.name}
                        </Link>
                    ))}
                </nav>
                <Sheet>
                    <SheetTrigger asChild>
                        <Button
                            variant="outline"
                            size="icon"
                            className="shrink-0 md:hidden"
                        >
                            <Menu className="h-5 w-5" />
                            <span className="sr-only">Toggle navigation menu</span>
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left">
                        <nav className="grid gap-6 text-lg font-medium">
                            <Link
                                to="/"
                                className="flex items-center gap-2 text-lg font-semibold"
                            >
                                <img src="/logo.svg" alt="Black Sea Monitor" className="h-8 w-auto" />
                                <span className="sr-only">Black Sea Monitor</span>
                            </Link>
                            {filteredNav.map((item) => (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className="hover:text-foreground"
                                >
                                    {item.name}
                                </Link>
                            ))}
                        </nav>
                    </SheetContent>
                </Sheet>
                <div className="flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
                    <div className="ml-auto flex-1 sm:flex-initial">
                        <span className="text-sm text-gray-500 mr-4">Team: Demo Team</span>
                    </div>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="relative">
                                <Bell className="h-5 w-5" />
                                {unreadCount > 0 && (
                                    <span className="absolute top-2 right-2 flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
                                    </span>
                                )}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-80">
                            <DropdownMenuLabel>Notifications ({unreadCount})</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <div className="max-h-80 overflow-y-auto">
                                {notifications.length === 0 ? (
                                    <div className="p-4 text-center text-xs text-muted-foreground">No notifications</div>
                                ) : (
                                    <div className="p-2 flex flex-col gap-1">
                                        {notifications.map((n) => (
                                            <div
                                                key={n.id}
                                                className={`p-2 rounded-md hover:bg-muted cursor-pointer transition-colors ${n.read ? 'opacity-60' : ''}`}
                                                onClick={() => markAsRead(n.id)}
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className={`text-[11px] font-bold ${n.type === 'alert' ? 'text-red-500' : 'text-primary'}`}>
                                                        {n.title}
                                                    </span>
                                                    <span className="text-[9px] text-muted-foreground">
                                                        {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                                <p className="text-[10px] text-muted-foreground leading-tight">
                                                    {n.message}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </DropdownMenuContent>
                    </DropdownMenu>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="secondary" size="icon" className="rounded-full">
                                <Avatar>
                                    <AvatarImage src="" />
                                    <AvatarFallback>{user?.email?.charAt(0).toUpperCase() || 'U'}</AvatarFallback>
                                </Avatar>
                                <span className="sr-only">Toggle user menu</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuLabel>My Account</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem asChild>
                                <Link to="/settings" className="w-full cursor-pointer">Settings</Link>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </header>
            <main className="relative z-0 flex min-h-[calc(100vh_-_theme(spacing.16))] flex-1 flex-col gap-4 bg-muted/40 p-4 md:gap-8 md:p-10">
                <Outlet />
            </main>
        </div>
    );
}

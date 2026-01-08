import { Outlet, Link, useLocation } from 'react-router-dom';
import useAuth from '../store/useAuth';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Archive, LayoutDashboard, Map, Menu, User, Bell, Users, LucideIcon } from 'lucide-react';
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
            <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
                <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
                    <Link
                        to="/"
                        className="flex items-center gap-2 text-lg font-semibold md:text-base"
                    >
                        <Map className="h-6 w-6" />
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
                                <Map className="h-6 w-6" />
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
                    <Button variant="ghost" size="icon" className="relative">
                        <Bell className="h-5 w-5" />
                        <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-600"></span>
                    </Button>
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
                            <DropdownMenuItem>Settings</DropdownMenuItem>
                            <DropdownMenuItem>Support</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </header>
            <main className="flex min-h-[calc(100vh_-_theme(spacing.16))] flex-1 flex-col gap-4 bg-muted/40 p-4 md:gap-8 md:p-10">
                <Outlet />
            </main>
        </div>
    );
}

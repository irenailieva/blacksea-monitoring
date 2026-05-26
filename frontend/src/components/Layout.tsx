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

// Интерфейс, описващ навигационен елемент (линк в менюто)
interface NavigationItem {
    name: string; // Визуално име на линка
    href: string; // Път (URL) за навигация
    icon: LucideIcon; // Иконка за визуално обогатяване
    roles?: string[]; // (Опционално) Списък от роли, които имат достъп до този линк
}

// Главен компонент за оформление (Layout), който обвива всички страници след успешен вход
export default function Layout() {
    // Извличане на данни за потребителя и функция за изход от Zustand store
    const { user, logout } = useAuth();
    // Извличане на известията и функция за маркиране им като прочетени
    const { notifications, unreadCount, markAsRead } = useNotifications();
    // Текущо местоположение в приложението (URL)
    const location = useLocation();

    // Дефиниране на основната навигация на приложението
    const navigation: NavigationItem[] = [
        { name: 'Map', href: '/', icon: Map },
        { name: 'Analysis', href: '/analysis', icon: LayoutDashboard },
        { name: 'Data', href: '/data', icon: Archive, roles: ['researcher', 'admin'] }, // Достъпно само за изследователи и админи
        { name: 'Admin', href: '/admin', icon: Users, roles: ['admin'] },               // Само за администратори
        { name: 'Regions', href: '/regions', icon: Map, roles: ['admin'] },             // Само за администратори
    ];

    // Филтриране на навигационното меню въз основа на ролята на текущия потребител
    const filteredNav = navigation.filter(item =>
        !item.roles || (user && item.roles.includes(user.role)) || !user
    );

    return (
        // Основен контейнер на приложението
        <div className="flex min-h-screen w-full flex-col">
            {/* Горен навигационен панел (Header) */}
            <header className="sticky top-0 z-[99999] flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6 shadow-sm">
                <div id="header-portal-root" className="absolute top-0 left-0 w-0 h-0" />
                
                {/* Навигация за десктоп устройства */}
                <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
                    {filteredNav.map((item) => (
                        <Link
                            key={item.name}
                            to={item.href}
                            // Добавяне на стил за активен линк (highlighting)
                            className={`transition-colors hover:text-foreground ${location.pathname === item.href ? 'text-foreground' : 'text-muted-foreground'
                                }`}
                        >
                            {item.name}
                        </Link>
                    ))}
                </nav>
                
                {/* Мобилно меню тип 'Sheet' (издърпващо се отстрани) */}
                <Sheet>
                    <SheetTrigger asChild>
                        {/* Бутон за показване на мобилното меню */}
                        <Button
                            variant="outline"
                            size="icon"
                            className="shrink-0 md:hidden"
                        >
                            <Menu className="h-5 w-5" />
                            <span className="sr-only">Превключване на навигационното меню</span>
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left">
                        {/* Линкове в мобилното меню */}
                        <nav className="grid gap-6 text-lg font-medium">
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
                
                {/* Дясна част на хедъра: потребителско меню и известия */}
                <div className="flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
                    <div className="ml-auto flex-1 sm:flex-initial">
                        {/* Информационен текст за текущия екип */}
                        <span className="text-sm text-gray-500 mr-4">Екип: Demo Team</span>
                    </div>
                    
                    {/* Падaщо меню за известия */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="relative">
                                <Bell className="h-5 w-5" />
                                {/* Индикатор (червена точка) при наличие на непрочетени известия */}
                                {unreadCount > 0 && (
                                    <span className="absolute top-2 right-2 flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
                                    </span>
                                )}
                            </Button>
                        </DropdownMenuTrigger>
                        {/* Съдържание на известията */}
                        <DropdownMenuContent align="end" className="w-80">
                            <DropdownMenuLabel>Известия ({unreadCount})</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <div className="max-h-80 overflow-y-auto">
                                {notifications.length === 0 ? (
                                    <div className="p-4 text-center text-xs text-muted-foreground">Няма нови известия</div>
                                ) : (
                                    <div className="p-2 flex flex-col gap-1">
                                        {/* Рендиране на всяко едно известие */}
                                        {notifications.map((n) => (
                                            <div
                                                key={n.id}
                                                // Промяна на прозрачността, ако известието вече е прочетено
                                                className={`p-2 rounded-md hover:bg-muted cursor-pointer transition-colors ${n.read ? 'opacity-60' : ''}`}
                                                onClick={() => markAsRead(n.id)} // При клик известието се маркира като прочетено
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
                    
                    {/* Падaщо меню за потребителския профил */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="secondary" size="icon" className="rounded-full">
                                <Avatar>
                                    <AvatarImage src="" />
                                    {/* Ако потребителят няма аватар, показваме първата буква от името му */}
                                    <AvatarFallback>{user?.username?.charAt(0).toUpperCase() || 'U'}</AvatarFallback>
                                </Avatar>
                                <span className="sr-only">Превключване на потребителското меню</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Моят профил</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem asChild>
                                <Link to="/settings" className="w-full cursor-pointer">Настройки</Link>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {/* Бутон за изход */}
                            <DropdownMenuItem onClick={logout}>Изход</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </header>
            
            {/* Основно съдържание, което се визуализира спрямо текущия маршрут чрез компонента Outlet */}
            <main className="relative z-0 flex h-[calc(100vh-4rem)] flex-col pt-4 px-4 pb-0 md:pt-8 md:px-10 md:pb-0 bg-slate-100/80 overflow-hidden shadow-inner border-t border-slate-200/60">
                <Outlet />
            </main>
        </div>
    );
}

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { UserPlus, MoreHorizontal, Mail, Shield, Loader2 } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import api from '@/api/axios';
import { User } from '@/api/types';

// Компонент за страница "Управление на екипа" (Team Management)
// Позволява на администраторите да преглеждат и управляват членовете на проекта и техните роли.
export default function TeamManagement() {
    // Състояния за съхранение на потребителите и флаг за зареждане
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    // Извикване на данните при зареждане на компонента
    useEffect(() => {
        const fetchUsers = async () => {
            try {
                // В реално приложение този ендпойнт може да е /teams/:id/members
                // Тук се прави GET заявка към /users за извличане на всички потребители (ако има права)
                const response = await api.get<User[]>('/users');
                setUsers(response.data);
            } catch (error) {
                console.error('Неуспешно извличане на потребителите:', error);
            } finally {
                setLoading(false); // Скриване на индикатора за зареждане
            }
        };
        fetchUsers();
    }, []);

    // Показване на индикатор за зареждане, докато се извличат данните
    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto pr-2">
            <div className="container mx-auto py-6 space-y-6">
                {/* Горен панел: Заглавие и бутон за добавяне */}
                <div className="flex items-center justify-between p-1">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Team Management</h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            Manage project members, roles, and access permissions.
                        </p>
                    </div>
                    <Button>
                        <UserPlus className="mr-2 h-4 w-4" />
                        Invite member
                    </Button>
                </div>

                {/* Основна карта с таблица */}
                <Card>
                    <CardHeader>
                        <CardTitle>Organization Members</CardTitle>
                        <CardDescription>
                            A list of all users in your organization and their project roles.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {/* Таблица за визуализиране на членовете */}
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>User</TableHead>
                                    <TableHead>Role</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {users.map((user) => (
                                    <TableRow key={user.id}>
                                        <TableCell>
                                            <div className="flex flex-col">
                                                {/* Показване на частта преди '@' като име */}
                                                <span className="font-medium">{user.email.split('@')[0]}</span>
                                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                    <Mail className="h-3 w-3" />
                                                    {user.email}
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Shield className="h-4 w-4 text-muted-foreground" />
                                                <span className="capitalize text-sm">{user.role}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {/* Статичен етикет "Активен" (в реално приложение се взима от бекенда) */}
                                            <Badge variant="default">
                                                active
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {/* Падащо меню с действия за конкретния потребител */}
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                    <DropdownMenuItem>Edit role</DropdownMenuItem>
                                                    <DropdownMenuItem>View activity</DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem className="text-destructive">
                                                        Remove from team
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

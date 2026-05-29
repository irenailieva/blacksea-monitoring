import { useEffect, useState, useCallback } from 'react';
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    UserPlus,
    MoreHorizontal,
    Mail,
    Shield,
    Loader2,
    Plus,
    Trash2,
    Users,
    Pencil,
} from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import api from '@/api/axios';
import { User } from '@/api/types';

// Интерфейс за данните на екип, получени от API-то
interface TeamData {
    id: number;
    name: string;
    created_at: string;
    updated_at: string;
}

// Интерфейс за членство в екип, включващ информация за потребителя
interface TeamMembership {
    user_id: number;
    team_id: number;
    role: string;
    user?: User & { created_at?: string; updated_at?: string };
    created_at: string;
    updated_at: string;
}

// Компонент за страница "Управление на екипа" (Team Management)
// Позволява на администраторите да създават/изтриват екипи, да добавят/премахват членове
// и да променят ролите на потребителите в екипите.
export default function TeamManagement() {
    // Състояния за екипи и членове
    const [teams, setTeams] = useState<TeamData[]>([]);
    const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
    const [members, setMembers] = useState<TeamMembership[]>([]);
    const [allUsers, setAllUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [membersLoading, setMembersLoading] = useState(false);

    // Състояния за диалозите
    const [createTeamOpen, setCreateTeamOpen] = useState(false);
    const [addMemberOpen, setAddMemberOpen] = useState(false);
    const [editRoleOpen, setEditRoleOpen] = useState(false);
    const [deleteTeamOpen, setDeleteTeamOpen] = useState(false);
    const [removeMemberOpen, setRemoveMemberOpen] = useState(false);

    // Състояния за формите
    const [newTeamName, setNewTeamName] = useState('');
    const [selectedUserId, setSelectedUserId] = useState<string>('');
    const [selectedMemberRole, setSelectedMemberRole] = useState<string>('member');
    const [editingMember, setEditingMember] = useState<TeamMembership | null>(null);
    const [editRole, setEditRole] = useState<string>('member');
    const [removingMember, setRemovingMember] = useState<TeamMembership | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Извличане на списъка с екипи от бекенда
    const fetchTeams = useCallback(async () => {
        try {
            const response = await api.get<TeamData[]>('/teams');
            setTeams(response.data);
            // Ако все още няма избран екип, избираме първия от списъка
            if (response.data.length > 0 && !selectedTeamId) {
                setSelectedTeamId(response.data[0].id);
            }
        } catch (error) {
            console.error('Неуспешно извличане на екипите:', error);
        }
    }, [selectedTeamId]);

    // Извличане на членовете на избрания екип
    const fetchMembers = useCallback(async (teamId: number) => {
        setMembersLoading(true);
        try {
            const response = await api.get<TeamMembership[]>(`/teams/${teamId}/members`);
            setMembers(response.data);
        } catch (error) {
            console.error('Неуспешно извличане на членовете:', error);
            setMembers([]);
        } finally {
            setMembersLoading(false);
        }
    }, []);

    // Извличане на всички потребители (за добавяне към екип)
    const fetchAllUsers = useCallback(async () => {
        try {
            const response = await api.get<User[]>('/users');
            setAllUsers(response.data);
        } catch (error) {
            console.error('Неуспешно извличане на потребителите:', error);
        }
    }, []);

    // Първоначално зареждане на данните
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            await Promise.all([fetchTeams(), fetchAllUsers()]);
            setLoading(false);
        };
        init();
    }, [fetchTeams, fetchAllUsers]);

    // При промяна на избрания екип — зареждаме членовете
    useEffect(() => {
        if (selectedTeamId) {
            fetchMembers(selectedTeamId);
        }
    }, [selectedTeamId, fetchMembers]);

    // Обработчик: Създаване на нов екип
    const handleCreateTeam = async () => {
        if (!newTeamName.trim()) return;
        setSubmitting(true);
        try {
            const response = await api.post<TeamData>('/teams', { name: newTeamName.trim() });
            setTeams(prev => [...prev, response.data]);
            setSelectedTeamId(response.data.id);
            setNewTeamName('');
            setCreateTeamOpen(false);
        } catch (error: any) {
            console.error('Грешка при създаване на екип:', error);
            alert(error?.response?.data?.detail || 'Failed to create team');
        } finally {
            setSubmitting(false);
        }
    };

    // Обработчик: Изтриване на екип
    const handleDeleteTeam = async () => {
        if (!selectedTeamId) return;
        setSubmitting(true);
        try {
            await api.delete(`/teams/${selectedTeamId}`);
            const remaining = teams.filter(t => t.id !== selectedTeamId);
            setTeams(remaining);
            setSelectedTeamId(remaining.length > 0 ? remaining[0].id : null);
            setMembers([]);
            setDeleteTeamOpen(false);
        } catch (error: any) {
            console.error('Грешка при изтриване на екип:', error);
            alert(error?.response?.data?.detail || 'Failed to delete team');
        } finally {
            setSubmitting(false);
        }
    };

    // Обработчик: Добавяне на член към екип
    const handleAddMember = async () => {
        if (!selectedTeamId || !selectedUserId) return;
        setSubmitting(true);
        try {
            await api.post(`/teams/${selectedTeamId}/members`, {
                user_id: parseInt(selectedUserId),
                team_id: selectedTeamId,
                role: selectedMemberRole,
            });
            await fetchMembers(selectedTeamId);
            setSelectedUserId('');
            setSelectedMemberRole('member');
            setAddMemberOpen(false);
        } catch (error: any) {
            console.error('Грешка при добавяне на член:', error);
            alert(error?.response?.data?.detail || 'Failed to add member');
        } finally {
            setSubmitting(false);
        }
    };

    // Обработчик: Промяна на ролята на член
    const handleEditRole = async () => {
        if (!selectedTeamId || !editingMember) return;
        setSubmitting(true);
        try {
            await api.put(`/teams/${selectedTeamId}/members/${editingMember.user_id}`, {
                role: editRole,
            });
            await fetchMembers(selectedTeamId);
            setEditingMember(null);
            setEditRoleOpen(false);
        } catch (error: any) {
            console.error('Грешка при промяна на ролята:', error);
            alert(error?.response?.data?.detail || 'Failed to update role');
        } finally {
            setSubmitting(false);
        }
    };

    // Обработчик: Премахване на член от екип
    const handleRemoveMember = async () => {
        if (!selectedTeamId || !removingMember) return;
        setSubmitting(true);
        try {
            await api.delete(`/teams/${selectedTeamId}/members/${removingMember.user_id}`);
            await fetchMembers(selectedTeamId);
            setRemovingMember(null);
            setRemoveMemberOpen(false);
        } catch (error: any) {
            console.error('Грешка при премахване на член:', error);
            alert(error?.response?.data?.detail || 'Failed to remove member');
        } finally {
            setSubmitting(false);
        }
    };

    // Помощна функция: Определяне на цвят на бадж за ролята
    const getRoleBadgeVariant = (role: string) => {
        switch (role) {
            case 'admin': return 'destructive' as const;
            case 'moderator': return 'default' as const;
            default: return 'secondary' as const;
        }
    };

    // Филтриране на потребителите, които все още не са членове на избрания екип
    const availableUsers = allUsers.filter(
        u => !members.some(m => m.user_id === u.id)
    );

    const selectedTeam = teams.find(t => t.id === selectedTeamId);

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
                {/* Горен панел: Заглавие и бутони */}
                <div className="flex items-center justify-between p-1">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Team Management</h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            Manage project teams, members, roles, and access permissions.
                        </p>
                    </div>
                    <Button onClick={() => setCreateTeamOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Team
                    </Button>
                </div>

                {/* Списък с екипи (tabs-like) */}
                {teams.length === 0 ? (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                            <Users className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No teams yet</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Create your first team to start collaborating with your colleagues.
                            </p>
                            <Button onClick={() => setCreateTeamOpen(true)}>
                                <Plus className="mr-2 h-4 w-4" />
                                Create Team
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        {/* Хоризонтален списък от екипи като бутони */}
                        <div className="flex items-center gap-2 flex-wrap">
                            {teams.map((team) => (
                                <Button
                                    key={team.id}
                                    variant={selectedTeamId === team.id ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setSelectedTeamId(team.id)}
                                    className="transition-all"
                                >
                                    <Users className="mr-2 h-4 w-4" />
                                    {team.name}
                                </Button>
                            ))}
                        </div>

                        {/* Информация за избрания екип + членове */}
                        {selectedTeam && (
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                                    <div>
                                        <CardTitle className="flex items-center gap-2">
                                            <Users className="h-5 w-5" />
                                            {selectedTeam.name}
                                        </CardTitle>
                                        <CardDescription>
                                            {members.length} member{members.length !== 1 ? 's' : ''} · Created {new Date(selectedTeam.created_at).toLocaleDateString()}
                                        </CardDescription>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            size="sm"
                                            onClick={() => {
                                                setSelectedUserId('');
                                                setSelectedMemberRole('member');
                                                setAddMemberOpen(true);
                                            }}
                                        >
                                            <UserPlus className="mr-2 h-4 w-4" />
                                            Add Member
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant="destructive"
                                            onClick={() => setDeleteTeamOpen(true)}
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete Team
                                        </Button>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {membersLoading ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="h-6 w-6 animate-spin text-primary" />
                                        </div>
                                    ) : members.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-8 text-center">
                                            <UserPlus className="h-8 w-8 text-muted-foreground mb-3" />
                                            <p className="text-sm text-muted-foreground">
                                                No members in this team yet. Add members to get started.
                                            </p>
                                        </div>
                                    ) : (
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>User</TableHead>
                                                    <TableHead>Team Role</TableHead>
                                                    <TableHead>Status</TableHead>
                                                    <TableHead className="text-right">Actions</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {members.map((membership) => (
                                                    <TableRow key={membership.user_id}>
                                                        <TableCell>
                                                            <div className="flex flex-col">
                                                                {/* Показване на потребителското име или частта преди '@' */}
                                                                <span className="font-medium">
                                                                    {membership.user?.username || membership.user?.email?.split('@')[0] || `User #${membership.user_id}`}
                                                                </span>
                                                                {membership.user?.email && (
                                                                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                                        <Mail className="h-3 w-3" />
                                                                        {membership.user.email}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <div className="flex items-center gap-2">
                                                                <Shield className="h-4 w-4 text-muted-foreground" />
                                                                <Badge variant={getRoleBadgeVariant(membership.role)}>
                                                                    {membership.role}
                                                                </Badge>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Badge variant="default">
                                                                active
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            {/* Падащо меню с действия за конкретния член */}
                                                            <DropdownMenu>
                                                                <DropdownMenuTrigger asChild>
                                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                                        <MoreHorizontal className="h-4 w-4" />
                                                                    </Button>
                                                                </DropdownMenuTrigger>
                                                                <DropdownMenuContent align="end">
                                                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                                    <DropdownMenuItem
                                                                        onClick={() => {
                                                                            setEditingMember(membership);
                                                                            setEditRole(membership.role);
                                                                            setEditRoleOpen(true);
                                                                        }}
                                                                    >
                                                                        <Pencil className="mr-2 h-4 w-4" />
                                                                        Edit role
                                                                    </DropdownMenuItem>
                                                                    <DropdownMenuSeparator />
                                                                    <DropdownMenuItem
                                                                        className="text-destructive"
                                                                        onClick={() => {
                                                                            setRemovingMember(membership);
                                                                            setRemoveMemberOpen(true);
                                                                        }}
                                                                    >
                                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                                        Remove from team
                                                                    </DropdownMenuItem>
                                                                </DropdownMenuContent>
                                                            </DropdownMenu>
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    )}
                                </CardContent>
                            </Card>
                        )}
                    </>
                )}
            </div>

            {/* ========== ДИАЛОГ: Създаване на нов екип ========== */}
            <Dialog open={createTeamOpen} onOpenChange={setCreateTeamOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Create New Team</DialogTitle>
                        <DialogDescription>
                            Enter a name for the new team. You will be added as the team admin automatically.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="team-name">Team Name</Label>
                            <Input
                                id="team-name"
                                placeholder="e.g., Varna Bay Research"
                                value={newTeamName}
                                onChange={(e) => setNewTeamName(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleCreateTeam()}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateTeamOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleCreateTeam} disabled={submitting || !newTeamName.trim()}>
                            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Team
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ========== ДИАЛОГ: Добавяне на член ========== */}
            <Dialog open={addMemberOpen} onOpenChange={setAddMemberOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Add Team Member</DialogTitle>
                        <DialogDescription>
                            Select a user and assign them a role in "{selectedTeam?.name}".
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label>User</Label>
                            {availableUsers.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                    All users are already members of this team.
                                </p>
                            ) : (
                                <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a user..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {availableUsers.map((user) => (
                                            <SelectItem key={user.id} value={String(user.id)}>
                                                {user.username || user.email} ({user.role})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        </div>
                        <div className="grid gap-2">
                            <Label>Role</Label>
                            <Select value={selectedMemberRole} onValueChange={setSelectedMemberRole}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="member">Member</SelectItem>
                                    <SelectItem value="moderator">Moderator</SelectItem>
                                    <SelectItem value="admin">Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setAddMemberOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleAddMember}
                            disabled={submitting || !selectedUserId || availableUsers.length === 0}
                        >
                            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Add Member
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ========== ДИАЛОГ: Промяна на ролята ========== */}
            <Dialog open={editRoleOpen} onOpenChange={setEditRoleOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Edit Member Role</DialogTitle>
                        <DialogDescription>
                            Change the role of{' '}
                            <strong>
                                {editingMember?.user?.username || editingMember?.user?.email || `User #${editingMember?.user_id}`}
                            </strong>{' '}
                            in "{selectedTeam?.name}".
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label>New Role</Label>
                            <Select value={editRole} onValueChange={setEditRole}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="member">Member</SelectItem>
                                    <SelectItem value="moderator">Moderator</SelectItem>
                                    <SelectItem value="admin">Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setEditRoleOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleEditRole} disabled={submitting}>
                            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Changes
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ========== ДИАЛОГ: Потвърждение за изтриване на екип ========== */}
            <Dialog open={deleteTeamOpen} onOpenChange={setDeleteTeamOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Team</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete <strong>"{selectedTeam?.name}"</strong>?
                            This action cannot be undone. All memberships will be permanently removed.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteTeamOpen(false)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={handleDeleteTeam} disabled={submitting}>
                            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Delete Team
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ========== ДИАЛОГ: Потвърждение за премахване на член ========== */}
            <Dialog open={removeMemberOpen} onOpenChange={setRemoveMemberOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Remove Member</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to remove{' '}
                            <strong>
                                {removingMember?.user?.username || removingMember?.user?.email || `User #${removingMember?.user_id}`}
                            </strong>{' '}
                            from "{selectedTeam?.name}"? They will lose access to all team resources.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setRemoveMemberOpen(false)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={handleRemoveMember} disabled={submitting}>
                            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Remove Member
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

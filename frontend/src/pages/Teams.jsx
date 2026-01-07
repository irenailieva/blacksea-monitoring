import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Users, Plus, Trash2, UserPlus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Teams() {
    const { user } = useAuth();
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTeam, setSelectedTeam] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newTeamName, setNewTeamName] = useState('');
    const [newMemberId, setNewMemberId] = useState('');
    const [members, setMembers] = useState([]);
    const [memberLoading, setMemberLoading] = useState(false);

    useEffect(() => {
        fetchTeams();
    }, []);

    useEffect(() => {
        if (selectedTeam) {
            fetchMembers(selectedTeam.id);
        } else {
            setMembers([]);
        }
    }, [selectedTeam]);

    const fetchTeams = async () => {
        try {
            const res = await api.get('/teams/');
            setTeams(res.data);
        } catch (error) {
            console.error("Failed to fetch teams:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchMembers = async (teamId) => {
        setMemberLoading(true);
        try {
            const res = await api.get(`/teams/${teamId}/members`);
            setMembers(res.data);
        } catch (error) {
            console.error("Failed to fetch members:", error);
        } finally {
            setMemberLoading(false);
        }
    };

    const handleCreateTeam = async (e) => {
        e.preventDefault();
        try {
            await api.post('/teams/', { name: newTeamName });
            setNewTeamName('');
            setShowCreateModal(false);
            fetchTeams();
        } catch (error) {
            alert("Failed to create team: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleAddMember = async (e) => {
        e.preventDefault();
        if (!selectedTeam) return;
        try {
            await api.post(`/teams/${selectedTeam.id}/members`, {
                user_id: parseInt(newMemberId),
                team_id: selectedTeam.id,
                role: 'member'
            });
            setNewMemberId('');
            fetchMembers(selectedTeam.id);
        } catch (error) {
            alert("Failed to add member: " + (error.response?.data?.detail || error.message));
        }
    };

    return (
        <div className="h-full flex flex-col p-6 bg-gray-950 text-white overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Users className="text-blue-400" />
                        Teams
                    </h1>
                    <p className="text-gray-400 text-sm">Manage teams and memberships</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium shadow-lg shadow-blue-900/20"
                >
                    <Plus size={16} />
                    Create Team
                </button>
            </div>

            <div className="flex gap-6 h-full overflow-hidden">
                {/* Teams List */}
                <div className="w-1/3 bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-gray-800 bg-gray-900/80">
                        <h2 className="font-semibold text-gray-300">All Teams</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-2">
                        {loading ? (
                            <p className="text-center text-gray-500 py-4">Loading teams...</p>
                        ) : teams.length === 0 ? (
                            <p className="text-center text-gray-500 py-4">No teams found.</p>
                        ) : (
                            teams.map(team => (
                                <div
                                    key={team.id}
                                    onClick={() => setSelectedTeam(team)}
                                    className={`p-3 rounded-lg cursor-pointer transition-colors border ${selectedTeam?.id === team.id
                                        ? 'bg-blue-600/20 border-blue-600/50 text-blue-100'
                                        : 'bg-gray-800/50 border-gray-800 hover:bg-gray-800 hover:border-gray-700 text-gray-300'
                                        }`}
                                >
                                    <div className="font-medium">{team.name}</div>
                                    <div className="text-xs text-gray-500 mt-1">ID: {team.id}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Team Details / Members */}
                <div className="flex-1 bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden flex flex-col">
                    {selectedTeam ? (
                        <>
                            <div className="p-4 border-b border-gray-800 bg-gray-900/80 flex justify-between items-center">
                                <div>
                                    <h2 className="font-semibold text-white text-lg">{selectedTeam.name}</h2>
                                    <p className="text-xs text-gray-500">Managing members</p>
                                </div>
                            </div>

                            <div className="p-4 border-b border-gray-800 bg-gray-800/20">
                                <form onSubmit={handleAddMember} className="flex gap-2">
                                    <input
                                        type="number"
                                        placeholder="User ID to add"
                                        value={newMemberId}
                                        onChange={e => setNewMemberId(e.target.value)}
                                        className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                                        required
                                    />
                                    <button
                                        type="submit"
                                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                                    >
                                        <UserPlus size={16} />
                                        Add Member
                                    </button>
                                </form>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4">
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Members</h3>
                                {memberLoading ? (
                                    <p className="text-gray-500 text-sm">Loading members...</p>
                                ) : members.length === 0 ? (
                                    <p className="text-gray-500 text-sm">No members in this team.</p>
                                ) : (
                                    <div className="space-y-2">
                                        {members.map(member => (
                                            <div key={member.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-800">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-300">
                                                        U{member.user_id}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-gray-200">User ID: {member.user_id}</div>
                                                        <div className="text-xs text-gray-500 capitalize">{member.role}</div>
                                                        <div className="text-xs text-gray-600 font-mono">
                                                            {member.user ? member.user.username : 'Loading...'}
                                                            {/* API should return user object if expanded, otherwise just ID */}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                            <Users size={48} className="mb-4 opacity-20" />
                            <p>Select a team to view details</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Create Team Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-white">Create New Team</h2>
                            <button onClick={() => setShowCreateModal(false)} className="text-gray-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleCreateTeam}>
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-400 mb-2">Team Name</label>
                                <input
                                    type="text"
                                    value={newTeamName}
                                    onChange={e => setNewTeamName(e.target.value)}
                                    className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                                    placeholder="Enter team name"
                                    required
                                />
                            </div>
                            <div className="flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                                >
                                    Create Team
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

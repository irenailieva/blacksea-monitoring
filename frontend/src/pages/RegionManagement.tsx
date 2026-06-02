import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Plus, MoreHorizontal, Loader2, MapPin, Trash2, Pencil } from 'lucide-react';
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
    DialogHeader,
    DialogTitle,
    DialogFooter
} from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import api from '@/api/axios';
import { Region } from '@/api/types';

// Region Management page — allows admin users to Create, Read, Edit and Delete
// geographic monitoring zones (Areas of Interest).
export default function RegionManagement() {
    // ─── List state ──────────────────────────────────────────────────────────
    const [regions, setRegions] = useState<Region[]>([]);
    const [loading, setLoading] = useState(true);

    // ─── Create dialog state ─────────────────────────────────────────────────
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newGeoJSON, setNewGeoJSON] = useState('');
    const [adding, setAdding] = useState(false);
    const [addError, setAddError] = useState('');

    // ─── Edit dialog state ───────────────────────────────────────────────────
    const [editRegion, setEditRegion] = useState<Region | null>(null);
    const [editName, setEditName] = useState('');
    const [editDesc, setEditDesc] = useState('');
    const [editGeoJSON, setEditGeoJSON] = useState('');
    const [editing, setEditing] = useState(false);
    const [editError, setEditError] = useState('');

    // ─── Delete confirmation state ───────────────────────────────────────────
    const [deleteTarget, setDeleteTarget] = useState<Region | null>(null);
    const [deleting, setDeleting] = useState(false);

    // ─── Fetch ───────────────────────────────────────────────────────────────
    const fetchRegions = async () => {
        setLoading(true);
        try {
            const response = await api.get<Region[]>('/regions');
            setRegions(response.data);
        } catch (error) {
            console.error('Failed to fetch regions:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRegions();
    }, []);

    // ─── Helpers ─────────────────────────────────────────────────────────────
    const parseGeometry = (raw: string) => {
        try {
            const geom = JSON.parse(raw);
            if (geom.type !== 'Polygon' && geom.type !== 'MultiPolygon') {
                throw new Error('Geometry must be a GeoJSON Polygon or MultiPolygon');
            }
            return geom;
        } catch (e: any) {
            throw new Error(e.message ?? 'Invalid JSON in the geometry field');
        }
    };

    // ─── Create ──────────────────────────────────────────────────────────────
    const handleAddRegion = async () => {
        setAdding(true);
        setAddError('');
        try {
            const geometry = parseGeometry(newGeoJSON);
            await api.post('/regions', {
                name: newName,
                description: newDesc || undefined,
                area_km2: 100, // calculated server-side via PostGIS in production
                geometry,
            });
            setIsAddOpen(false);
            setNewName('');
            setNewDesc('');
            setNewGeoJSON('');
            await fetchRegions();
        } catch (error: any) {
            console.error('Failed to add region:', error);
            setAddError(error.message || error.response?.data?.detail || 'An error occurred while adding the region');
        } finally {
            setAdding(false);
        }
    };

    const openAdd = () => {
        setNewName('');
        setNewDesc('');
        setNewGeoJSON('');
        setAddError('');
        setIsAddOpen(true);
    };

    // ─── Edit ────────────────────────────────────────────────────────────────
    const openEdit = (region: Region) => {
        setEditRegion(region);
        setEditName(region.name);
        setEditDesc(region.description ?? '');
        // Pre-fill geometry as pretty-printed JSON if region was loaded with geometry
        setEditGeoJSON(region.geometry ? JSON.stringify(region.geometry, null, 2) : '');
        setEditError('');
    };

    const handleEditRegion = async () => {
        if (!editRegion) return;
        setEditing(true);
        setEditError('');
        try {
            const payload: Record<string, unknown> = {};
            if (editName && editName !== editRegion.name) payload.name = editName;
            if (editDesc !== (editRegion.description ?? '')) payload.description = editDesc || null;
            if (editGeoJSON.trim()) {
                payload.geometry = parseGeometry(editGeoJSON);
            }
            await api.put(`/regions/${editRegion.id}`, payload);
            setEditRegion(null);
            await fetchRegions();
        } catch (error: any) {
            console.error('Failed to update region:', error);
            setEditError(error.message || error.response?.data?.detail || 'An error occurred while updating the region');
        } finally {
            setEditing(false);
        }
    };

    // ─── Delete ──────────────────────────────────────────────────────────────
    const confirmDelete = (region: Region) => {
        setDeleteTarget(region);
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;
        setDeleting(true);
        try {
            await api.delete(`/regions/${deleteTarget.id}`);
            setDeleteTarget(null);
            await fetchRegions();
        } catch (error: any) {
            console.error('Failed to delete region:', error);
            alert(error.response?.data?.detail ?? 'Failed to delete region');
        } finally {
            setDeleting(false);
        }
    };

    // ─── Loading skeleton ────────────────────────────────────────────────────
    if (loading && regions.length === 0) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    const isPermanent = (r: Region) =>
        !r.name.startsWith('AOI_') && !r.name.startsWith('aoi_');

    // ─── Render ──────────────────────────────────────────────────────────────
    return (
        <div className="h-full overflow-y-auto pr-2">
            <div className="container mx-auto py-6 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between p-1">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Region Management</h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            Manage permanent geographic zones for Sentinel-2 monitoring.
                        </p>
                    </div>
                    <Button id="add-region-btn" onClick={openAdd}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Region
                    </Button>
                </div>

                {/* Regions table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Configured Regions</CardTitle>
                        <CardDescription>
                            These regions are actively mapped and tracked by the ETL pipeline.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Region</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Description</TableHead>
                                    <TableHead>Added</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {regions.map((region) => (
                                    <TableRow key={region.id}>
                                        <TableCell>
                                            <div className="flex flex-col">
                                                <span className="font-medium flex items-center gap-2">
                                                    <MapPin className="h-4 w-4 text-primary" />
                                                    {region.name}
                                                </span>
                                                <span className="text-xs text-muted-foreground mt-0.5">ID: {region.id}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {isPermanent(region) ? (
                                                <Badge variant="default" className="bg-green-600">Permanent</Badge>
                                            ) : (
                                                <Badge variant="secondary">Temporary AOI</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground text-sm max-w-[200px] truncate">
                                            {region.description || <span className="italic opacity-50">—</span>}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground text-sm">
                                            {region.created_at
                                                ? new Date(region.created_at).toLocaleDateString()
                                                : '—'}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button
                                                        id={`region-actions-${region.id}`}
                                                        variant="ghost"
                                                        className="h-8 w-8 p-0"
                                                    >
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                    <DropdownMenuItem
                                                        id={`edit-region-${region.id}`}
                                                        onClick={() => openEdit(region)}
                                                    >
                                                        <Pencil className="mr-2 h-4 w-4" />
                                                        Edit
                                                    </DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem
                                                        id={`delete-region-${region.id}`}
                                                        className="text-destructive"
                                                        onClick={() => confirmDelete(region)}
                                                    >
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        Delete
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {regions.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                                            No regions found. Add one to get started.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>

            {/* ── Create Dialog ────────────────────────────────────────────── */}
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogContent id="add-region-dialog" className="sm:max-w-[520px]">
                    <DialogHeader>
                        <DialogTitle>Add New Region</DialogTitle>
                        <DialogDescription>
                            Define a new permanent area of interest. It will be automatically added to the analysis dashboard.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="add-name">Region name *</Label>
                            <Input
                                id="add-name"
                                placeholder="e.g. Sunny Beach Coastline"
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="add-desc">Description</Label>
                            <Input
                                id="add-desc"
                                placeholder="Optional description"
                                value={newDesc}
                                onChange={e => setNewDesc(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="add-geojson">GeoJSON Geometry (Polygon) *</Label>
                            <Textarea
                                id="add-geojson"
                                placeholder='{"type": "Polygon", "coordinates": [[[...]]]}' 
                                className="h-32 font-mono text-xs"
                                value={newGeoJSON}
                                onChange={e => setNewGeoJSON(e.target.value)}
                            />
                        </div>
                        {addError && (
                            <div className="text-sm text-destructive font-medium bg-destructive/10 p-2 rounded-md">
                                {addError}
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button
                            id="add-region-cancel"
                            variant="outline"
                            onClick={() => setIsAddOpen(false)}
                            disabled={adding}
                        >
                            Cancel
                        </Button>
                        <Button
                            id="add-region-save"
                            onClick={handleAddRegion}
                            disabled={adding || !newName.trim() || !newGeoJSON.trim()}
                        >
                            {adding && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Region
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ── Edit Dialog ──────────────────────────────────────────────── */}
            <Dialog open={!!editRegion} onOpenChange={(open) => { if (!open) setEditRegion(null); }}>
                <DialogContent id="edit-region-dialog" className="sm:max-w-[520px]">
                    <DialogHeader>
                        <DialogTitle>Edit Region</DialogTitle>
                        <DialogDescription>
                            Update the name, description, or geometry of <strong>{editRegion?.name}</strong>.
                            Leave the geometry field empty to keep the existing boundary.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="edit-name">Region name *</Label>
                            <Input
                                id="edit-name"
                                value={editName}
                                onChange={e => setEditName(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="edit-desc">Description</Label>
                            <Input
                                id="edit-desc"
                                placeholder="Optional description"
                                value={editDesc}
                                onChange={e => setEditDesc(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="edit-geojson">
                                GeoJSON Geometry (Polygon)
                                <span className="ml-1 text-muted-foreground text-xs">(leave empty to keep current)</span>
                            </Label>
                            <Textarea
                                id="edit-geojson"
                                placeholder='{"type": "Polygon", "coordinates": [[[...]]]}' 
                                className="h-32 font-mono text-xs"
                                value={editGeoJSON}
                                onChange={e => setEditGeoJSON(e.target.value)}
                            />
                        </div>
                        {editError && (
                            <div className="text-sm text-destructive font-medium bg-destructive/10 p-2 rounded-md">
                                {editError}
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button
                            id="edit-region-cancel"
                            variant="outline"
                            onClick={() => setEditRegion(null)}
                            disabled={editing}
                        >
                            Cancel
                        </Button>
                        <Button
                            id="edit-region-save"
                            onClick={handleEditRegion}
                            disabled={editing || !editName.trim()}
                        >
                            {editing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Changes
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ── Delete Confirmation Dialog ───────────────────────────────── */}
            <AlertDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}>
                <AlertDialogContent id="delete-region-dialog">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete region "{deleteTarget?.name}"?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. Deleting this region will also remove all associated
                            scenes, index values, and classification results from the database.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel id="delete-region-cancel" disabled={deleting}>
                            Cancel
                        </AlertDialogCancel>
                        <AlertDialogAction
                            id="delete-region-confirm"
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={handleDelete}
                            disabled={deleting}
                        >
                            {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

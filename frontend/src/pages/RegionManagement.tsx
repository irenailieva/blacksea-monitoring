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
import { Plus, MoreHorizontal, Loader2, MapPin, Trash2 } from 'lucide-react';
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
    DialogTrigger,
    DialogFooter
} from "@/components/ui/dialog";
import api from '@/api/axios';
import { Region } from '@/api/types';

export default function RegionManagement() {
    const [regions, setRegions] = useState<Region[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddOpen, setIsAddOpen] = useState(false);
    
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newGeoJSON, setNewGeoJSON] = useState('');
    const [adding, setAdding] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    const fetchRegions = async () => {
        setLoading(true);
        try {
            const response = await api.get<Region[]>('/regions');
            // Filter out AOI_ if we want, or keep them to show what's temp
            // Let's show all, but we can badge the temp ones
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

    const handleAddRegion = async () => {
        setAdding(true);
        setErrorMsg('');
        try {
            let geometry;
            try {
                geometry = JSON.parse(newGeoJSON);
            } catch (e) {
                throw new Error("Invalid JSON in Geometry");
            }
            
            if (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon") {
                throw new Error("Geometry must be a GeoJSON Polygon or MultiPolygon");
            }

            const payload = {
                name: newName,
                description: newDesc,
                area_km2: 100, // Dummy area, a real system would calculate it
                geometry: geometry
            };

            await api.post('/regions', payload);
            setIsAddOpen(false);
            fetchRegions();
            setNewName('');
            setNewDesc('');
            setNewGeoJSON('');
        } catch (error: any) {
            console.error('Failed to add region:', error);
            setErrorMsg(error.message || error.response?.data?.detail || "Failed to add region");
        } finally {
            setAdding(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this region?")) return;
        try {
            await api.delete(`/regions/${id}`);
            fetchRegions();
        } catch (error) {
            console.error('Failed to delete region:', error);
            alert("Failed to delete region");
        }
    };

    if (loading && regions.length === 0) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto pr-2">
            <div className="container mx-auto py-6 space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Region Management</h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            Manage permanent geographical regions for Sentinel-2 monitoring.
                        </p>
                    </div>
                    
                    <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="mr-2 h-4 w-4" />
                                Add Region
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[500px]">
                            <DialogHeader>
                                <DialogTitle>Add New Region</DialogTitle>
                                <DialogDescription>
                                    Define a new permanent area of interest. It will immediately be added to the Analysis dashboards.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Region Name</Label>
                                    <Input 
                                        id="name" 
                                        placeholder="e.g. Sunny Beach Coastline" 
                                        value={newName} 
                                        onChange={e => setNewName(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="desc">Description</Label>
                                    <Input 
                                        id="desc" 
                                        placeholder="Optional description" 
                                        value={newDesc} 
                                        onChange={e => setNewDesc(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="geojson">GeoJSON Geometry (Polygon)</Label>
                                    <Textarea 
                                        id="geojson" 
                                        placeholder='{"type": "Polygon", "coordinates": [[[...]]]}' 
                                        className="h-32 font-mono text-xs"
                                        value={newGeoJSON}
                                        onChange={e => setNewGeoJSON(e.target.value)}
                                    />
                                </div>
                                {errorMsg && (
                                    <div className="text-sm text-destructive font-medium bg-destructive/10 p-2 rounded-md">
                                        {errorMsg}
                                    </div>
                                )}
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsAddOpen(false)} disabled={adding}>Cancel</Button>
                                <Button onClick={handleAddRegion} disabled={adding || !newName || !newGeoJSON}>
                                    {adding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Save Region
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

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
                                    <TableHead>Date Added</TableHead>
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
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {region.name.startsWith("AOI_") || region.name.startsWith("aoi_") ? (
                                                <Badge variant="secondary">Temporary AOI</Badge>
                                            ) : (
                                                <Badge variant="default" className="bg-green-600">Permanent</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground text-sm">
                                            {/* In a real app we'd have created_at, but Region might not return it in the schema, just mocking it or showing id */}
                                            ID: {region.id}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                    <DropdownMenuItem>View on Map</DropdownMenuItem>
                                                    <DropdownMenuItem>Edit Geometry</DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem className="text-destructive" onClick={() => handleDelete(region.id)}>
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        Delete Region
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {regions.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                                            No regions found. Add one to get started.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

import { useState } from 'react';
import { VegetationChart } from '@/components/Analysis/VegetationChart';
import { ShapExplanation } from '@/components/Analysis/ShapExplanation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

export default function Analysis() {
    const [selectedRegion, setSelectedRegion] = useState('varna-bay');

    return (
        <div className="flex flex-col space-y-4 h-full  overflow-y-auto pr-2">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Analysis Dashboard</h2>
                <div className="flex items-center space-x-2">
                    <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select Region" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="varna-bay">Varna Bay</SelectItem>
                            <SelectItem value="burgas-bay">Burgas Bay</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button size="icon" variant="outline">
                        <Download className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Vegetation Area</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">12,345 m²</div>
                        <p className="text-xs text-muted-foreground">+2.5% from last month</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg. Confidence Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">94.8%</div>
                        <p className="text-xs text-muted-foreground">+0.2% from last month</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Anomalies</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3</div>
                        <p className="text-xs text-muted-foreground">-1 from last week</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
                <VegetationChart />
                <ShapExplanation />
            </div>

            <div className="grid gap-4 md:grid-cols-1">
                <Card>
                    <CardHeader>
                        <CardTitle>Detailed Report</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border p-4 text-sm text-center text-muted-foreground bg-muted/20">
                            Table of specific classification results per scene will go here.
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

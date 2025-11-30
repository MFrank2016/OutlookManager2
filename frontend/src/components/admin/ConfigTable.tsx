"use client";

import { useConfigs, useUpdateConfig } from "@/hooks/useAdmin";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Save } from "lucide-react";

export function ConfigTable() {
  const { data, isLoading } = useConfigs();
  
  if (isLoading) return <div>Loading config...</div>;

  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Key</TableHead>
            <TableHead>Value</TableHead>
            <TableHead>Description</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.configs.map((config) => (
            <ConfigRow key={config.key} config={config} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ConfigRow({ config }: { config: any }) {
    const [value, setValue] = useState(config.value);
    const updateConfig = useUpdateConfig();
    const isDirty = value !== config.value;

    const handleSave = () => {
        updateConfig.mutate({ key: config.key, value });
    };

    return (
        <TableRow>
            <TableCell className="font-medium">{config.key}</TableCell>
            <TableCell>
                <Input 
                    value={value} 
                    onChange={(e) => setValue(e.target.value)} 
                    className="max-w-md"
                />
            </TableCell>
            <TableCell className="text-gray-500">{config.description}</TableCell>
            <TableCell className="text-right">
                {isDirty && (
                    <Button size="sm" onClick={handleSave} disabled={updateConfig.isPending}>
                        <Save className="h-4 w-4 mr-1" /> Save
                    </Button>
                )}
            </TableCell>
        </TableRow>
    )
}


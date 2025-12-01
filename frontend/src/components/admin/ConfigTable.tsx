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
  
  if (isLoading) return <div>加载配置中...</div>;

  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>配置项</TableHead>
            <TableHead>值</TableHead>
            <TableHead>描述</TableHead>
            <TableHead className="text-right">操作</TableHead>
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
                        <Save className="h-4 w-4 mr-1" /> 保存
                    </Button>
                )}
            </TableCell>
        </TableRow>
    )
}


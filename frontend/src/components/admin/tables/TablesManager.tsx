"use client";

import { useState } from "react";
import { useTables, useTableData, useDeleteTableRecord } from "@/hooks/useAdmin";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trash2, Database, ArrowLeft, Edit, Plus, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { TableRecordDialog } from "./TableRecordDialog";

export function TablesManager() {
  const { data: tablesData, isLoading: tablesLoading } = useTables();
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  if (tablesLoading) return <div>加载数据表中...</div>;

  if (selectedTable) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setSelectedTable(null)}>
            <ArrowLeft className="mr-2 h-4 w-4" /> 返回
          </Button>
          <h2 className="text-xl font-bold">{selectedTable}</h2>
        </div>
        <TableDataView tableName={selectedTable} />
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {tablesData?.tables.map((table) => (
        <Card key={table.name} className="hover:bg-slate-50 transition-colors cursor-pointer border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium capitalize">
              {table.name}
            </CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{table.record_count}</div>
            <p className="text-xs text-muted-foreground">条记录</p>
            <Button 
                className="w-full mt-4" 
                size="sm" 
                onClick={() => setSelectedTable(table.name)}
            >
                查看数据
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TableDataView({ tableName }: { tableName: string }) {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const { data, isLoading } = useTableData(tableName, { page, page_size: 20, search });
    const deleteRecord = useDeleteTableRecord();

    if (isLoading) return <div>加载数据中...</div>;
    if (!data) return <div>未找到数据</div>;

    // Get columns from first record if available
    const columns = data.records.length > 0 ? Object.keys(data.records[0]) : [];

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <Input 
                        placeholder="搜索..." 
                        className="pl-9" 
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                </div>
                {/* Add Record Button - needs to know columns which we might infer or fetch schema */}
                {columns.length > 0 && (
                    <TableRecordDialog tableName={tableName} columns={columns} />
                )}
                <div className="text-sm text-muted-foreground">
                    总计: {data.total_records} 条
                </div>
            </div>

            <div className="rounded-md border bg-white overflow-x-auto">
                <Table>
                    <TableHeader>
                        <TableRow>
                            {columns.map(col => (
                                <TableHead key={col} className="whitespace-nowrap">{col}</TableHead>
                            ))}
                            <TableHead className="text-right">操作</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.records.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={columns.length + 1} className="text-center p-4">
                                    未找到记录
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.records.map((record, idx) => (
                                <TableRow key={record.id || idx}>
                                    {columns.map(col => (
                                        <TableCell key={col} className="max-w-[200px] truncate" title={String(record[col])}>
                                            {String(record[col])}
                                        </TableCell>
                                    ))}
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-2">
                                            <TableRecordDialog 
                                                tableName={tableName} 
                                                columns={columns} 
                                                record={record}
                                                trigger={
                                                    <Button variant="ghost" size="icon">
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                }
                                            />
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => {
                                                    if (confirm("确定要删除这条记录吗？")) {
                                                        deleteRecord.mutate({ tableName, recordId: record.id });
                                                    }
                                                }}
                                                disabled={!record.id}
                                            >
                                                <Trash2 className="h-4 w-4 text-red-500" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            {data.total_pages > 1 && (
                <div className="flex items-center justify-end space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                        上一页
                    </Button>
                    <span className="text-sm">
                        第 {page} 页，共 {data.total_pages} 页
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                        disabled={page === data.total_pages}
                    >
                        下一页
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    )
}

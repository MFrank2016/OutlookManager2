"use client";

import { useState, useMemo } from "react";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Trash2, 
  Database, 
  ArrowLeft, 
  Edit, 
  Plus, 
  ChevronLeft, 
  ChevronRight, 
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Loader2,
  Code,
  X
} from "lucide-react";
import { TableRecordDialog } from "./TableRecordDialog";
import { SqlQueryPanel } from "./SqlQueryPanel";

type SortState = {
  column: string | null;
  order: "asc" | "desc";
};

export function TablesManager() {
  const { data: tablesData, isLoading: tablesLoading } = useTables();
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  if (tablesLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg">加载数据表中...</span>
      </div>
    );
  }

  if (selectedTable) {
    return (
      <div className="space-y-4 animate-in fade-in duration-300">
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            onClick={() => setSelectedTable(null)}
            className="transition-all duration-200 hover:bg-blue-50"
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> 返回
          </Button>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            📊 {selectedTable}
          </h2>
        </div>
        <TableDataView tableName={selectedTable} />
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-in fade-in duration-300">
      {tablesData?.tables.map((table, idx) => (
        <Card 
          key={table.name} 
          className="hover:shadow-lg transition-all duration-300 cursor-pointer border-l-4 border-l-blue-500 hover:border-l-indigo-600 hover:scale-[1.02] animate-in fade-in"
          style={{ animationDelay: `${idx * 50}ms` }}
          onClick={() => setSelectedTable(table.name)}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg font-semibold capitalize flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-500" />
              {table.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 mb-1">{table.record_count}</div>
            <p className="text-sm text-muted-foreground mb-4">条记录</p>
            <Button 
                className="w-full transition-all duration-200 hover:bg-blue-600" 
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedTable(table.name);
                }}
            >
              <Database className="mr-2 h-4 w-4" />
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
    const [sortState, setSortState] = useState<SortState>({ column: "id", order: "asc" });
    const [selectedFields, setSelectedFields] = useState<string[]>([]);
    const [fieldSearch, setFieldSearch] = useState<Record<string, string>>({});
    const [showSqlPanel, setShowSqlPanel] = useState(false);
    
    // 构建查询参数
    const queryParams = useMemo(() => {
      const params: any = {
        page,
        page_size: 20,
      };
      
      if (search) {
        params.search = search;
      }
      
      if (sortState.column) {
        params.sort_by = sortState.column;
        params.sort_order = sortState.order;
      }
      
      if (Object.keys(fieldSearch).length > 0) {
        params.field_search = fieldSearch;
      }
      
      return params;
    }, [page, search, sortState, fieldSearch]);
    
    const { data, isLoading } = useTableData(tableName, queryParams);
    const deleteRecord = useDeleteTableRecord();

    // Get columns from first record if available
    const columns = data?.records && data.records.length > 0 ? Object.keys(data.records[0]) : [];

    const handleSort = (column: string) => {
      setSortState(prev => {
        if (prev.column === column) {
          // 切换排序方向：asc -> desc -> null (回到默认)
          if (prev.order === "asc") {
            return { column, order: "desc" };
          } else {
            // 回到默认排序（按主键）
            return { column: "id", order: "asc" };
          }
        } else {
          return { column, order: "asc" };
        }
      });
      setPage(1);
    };

    const getSortIcon = (column: string) => {
      if (sortState.column !== column) {
        return <ArrowUpDown className="h-4 w-4 text-gray-400" />;
      }
      return sortState.order === "asc" 
        ? <ArrowUp className="h-4 w-4 text-blue-600" />
        : <ArrowDown className="h-4 w-4 text-blue-600" />;
    };

    const addFieldFilter = () => {
      if (columns.length > 0) {
        const firstColumn = columns[0];
        setSelectedFields([...selectedFields, firstColumn]);
        setFieldSearch({ ...fieldSearch, [firstColumn]: "" });
      }
    };

    const removeFieldFilter = (field: string) => {
      const newFields = selectedFields.filter(f => f !== field);
      const newSearch = { ...fieldSearch };
      delete newSearch[field];
      setSelectedFields(newFields);
      setFieldSearch(newSearch);
      setPage(1);
    };

    const updateFieldSearch = (field: string, value: string) => {
      setFieldSearch({ ...fieldSearch, [field]: value });
      setPage(1);
    };

    if (isLoading) {
      return (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <span className="ml-2 text-lg">加载数据中...</span>
        </div>
      );
    }
    
    if (!data) return <div className="text-center p-8 text-muted-foreground">未找到数据</div>;

    return (
        <div className="space-y-4">
            {/* 搜索和操作栏 */}
            <div className="flex flex-wrap items-center gap-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <Input 
                        placeholder="🔍 全字段搜索..." 
                        className="pl-9 transition-all duration-200 focus:ring-2 focus:ring-blue-500" 
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                </div>
                
                {/* 字段筛选 */}
                <div className="flex flex-wrap items-center gap-2">
                  {selectedFields.map(field => (
                    <div key={field} className="flex items-center gap-2 bg-white px-3 py-1 rounded-md border">
                      <Select
                        value={field}
                        onValueChange={(newField) => {
                          const newFields = selectedFields.map(f => f === field ? newField : f);
                          const newSearch = { ...fieldSearch };
                          const oldValue = newSearch[field];
                          delete newSearch[field];
                          newSearch[newField] = oldValue || "";
                          setSelectedFields(newFields);
                          setFieldSearch(newSearch);
                        }}
                      >
                        <SelectTrigger className="w-[120px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {columns.map(col => (
                            <SelectItem key={col} value={col}>{col}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder="搜索值"
                        className="w-[150px] h-8"
                        value={fieldSearch[field] || ""}
                        onChange={(e) => updateFieldSearch(field, e.target.value)}
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => removeFieldFilter(field)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addFieldFilter}
                    className="h-8"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    添加字段筛选
                  </Button>
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center gap-2">
                    {columns.length > 0 && (
                        <TableRecordDialog tableName={tableName} columns={columns} />
                    )}
                    <Button
                      variant={showSqlPanel ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowSqlPanel(!showSqlPanel)}
                      className="h-8"
                    >
                      <Code className="h-4 w-4 mr-1" />
                      {showSqlPanel ? "隐藏" : "显示"} SQL查询
                    </Button>
                </div>
                
                <div className="text-sm font-semibold text-blue-700">
                    📊 总计: {data.total_records} 条
                </div>
            </div>

            {/* SQL查询面板 */}
            {showSqlPanel && (
              <div className="animate-in fade-in duration-300">
                <SqlQueryPanel tableName={tableName} />
              </div>
            )}

            {/* 数据表格 */}
            <div className="rounded-lg border bg-white overflow-x-auto shadow-sm">
                <Table>
                    <TableHeader>
                        <TableRow className="bg-gradient-to-r from-blue-50 to-indigo-50 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50">
                            {columns.map(col => (
                                <TableHead 
                                    key={col} 
                                    className="whitespace-nowrap font-bold text-gray-700 cursor-pointer hover:bg-blue-100 transition-colors duration-200 h-12"
                                    onClick={() => handleSort(col)}
                                >
                                    <div className="flex items-center gap-2">
                                        {col}
                                        {getSortIcon(col)}
                                    </div>
                                </TableHead>
                            ))}
                            <TableHead className="text-right font-bold text-gray-700 h-12">操作</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.records.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={columns.length + 1} className="text-center p-8 text-muted-foreground">
                                    <div className="text-lg">📭 未找到记录</div>
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.records.map((record, idx) => (
                                <TableRow 
                                    key={record.id || idx}
                                    className={`transition-all duration-200 hover:bg-blue-50 hover:shadow-md ${
                                        idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                                    }`}
                                >
                                    {columns.map(col => (
                                        <TableCell 
                                            key={col} 
                                            className="max-w-[200px] truncate" 
                                            title={String(record[col] ?? "")}
                                        >
                                            {String(record[col] ?? "")}
                                        </TableCell>
                                    ))}
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-2">
                                            <TableRecordDialog 
                                                tableName={tableName} 
                                                columns={columns} 
                                                record={record}
                                                trigger={
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-blue-100 transition-colors duration-200"
                                                    >
                                                        <Edit className="h-4 w-4 text-blue-600" />
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
                                                className="hover:bg-red-100 transition-colors duration-200"
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

            {/* 分页 */}
            {data.total_pages > 1 && (
                <div className="flex items-center justify-end space-x-2 p-4 bg-gray-50 rounded-lg">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="transition-all duration-200 hover:bg-blue-50"
                    >
                        <ChevronLeft className="h-4 w-4" />
                        上一页
                    </Button>
                    <span className="text-sm font-medium px-4">
                        第 {page} 页，共 {data.total_pages} 页
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                        disabled={page === data.total_pages}
                        className="transition-all duration-200 hover:bg-blue-50"
                    >
                        下一页
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    )
}

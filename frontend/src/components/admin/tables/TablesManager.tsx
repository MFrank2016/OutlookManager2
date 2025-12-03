"use client";

import { useState, useMemo, memo, useEffect } from "react";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { Check } from "lucide-react";

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
    // 临时搜索状态（不触发查询）
    const [tempSearch, setTempSearch] = useState("");
    // 实际查询用的搜索（触发查询）
    const [appliedSearch, setAppliedSearch] = useState("");
    
    const [sortState, setSortState] = useState<SortState>({ column: "id", order: "asc" });
    const [selectedFields, setSelectedFields] = useState<string[]>([]);
    // 临时字段筛选状态（不触发查询）
    const [tempFieldSearch, setTempFieldSearch] = useState<Record<string, string>>({});
    // 实际查询用的字段筛选（触发查询）
    const [appliedFieldSearch, setAppliedFieldSearch] = useState<Record<string, string>>({});
    const [showSqlPanel, setShowSqlPanel] = useState(false);
    // 保存列信息，避免在加载时丢失
    const [stableColumns, setStableColumns] = useState<string[]>([]);
    
    // 构建实际查询参数（只有这些变化时才触发查询）
    const queryParams = useMemo(() => {
      const params: any = {
        page,
        page_size: 20,
      };
      
      if (appliedSearch) {
        params.search = appliedSearch;
      }
      
      if (sortState.column) {
        params.sort_by = sortState.column;
        params.sort_order = sortState.order;
      }
      
      if (Object.keys(appliedFieldSearch).length > 0) {
        // 过滤掉空值
        const filtered = Object.fromEntries(
          Object.entries(appliedFieldSearch).filter(([_, v]) => v && v.trim())
        );
        if (Object.keys(filtered).length > 0) {
          params.field_search = filtered;
        }
      }
      
      return params;
    }, [page, appliedSearch, sortState, appliedFieldSearch]);
    
    const { data, isLoading } = useTableData(tableName, queryParams);
    const deleteRecord = useDeleteTableRecord();

    // Get columns from first record if available, and update stable columns
    const currentColumns = data?.records && data.records.length > 0 ? Object.keys(data.records[0]) : [];
    const currentColumnsKey = currentColumns.length > 0 ? currentColumns.join(',') : '';
    
    // 更新稳定的列信息（只在有新列时更新，避免在加载时清空）
    useEffect(() => {
      if (currentColumns.length > 0) {
        setStableColumns(currentColumns);
      }
    }, [currentColumnsKey]);
    
    // 使用稳定的列信息，如果当前没有数据则使用之前的列信息
    const columns = currentColumns.length > 0 ? currentColumns : stableColumns;

    const handleSort = (column: string, e?: React.MouseEvent) => {
      // 阻止默认行为和事件冒泡，防止页面刷新
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      
      // 排序立即生效，更新状态会触发查询
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
    
    // 应用筛选条件（点击查询按钮时调用）
    const applyFilters = () => {
      setAppliedSearch(tempSearch);
      setAppliedFieldSearch(tempFieldSearch);
      setPage(1);
    };
    
    // 清除筛选条件
    const clearFilters = () => {
      setTempSearch("");
      setAppliedSearch("");
      setTempFieldSearch({});
      setAppliedFieldSearch({});
      setSelectedFields([]);
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
        setTempFieldSearch({ ...tempFieldSearch, [firstColumn]: "" });
      }
    };

    const removeFieldFilter = (field: string) => {
      const newFields = selectedFields.filter(f => f !== field);
      const newSearch = { ...tempFieldSearch };
      delete newSearch[field];
      setSelectedFields(newFields);
      setTempFieldSearch(newSearch);
      // 同时从已应用的筛选中移除
      const newApplied = { ...appliedFieldSearch };
      delete newApplied[field];
      setAppliedFieldSearch(newApplied);
      setPage(1);
    };

    const updateFieldSearch = (field: string, value: string) => {
      // 只更新临时状态，不触发查询
      setTempFieldSearch({ ...tempFieldSearch, [field]: value });
    };

    return (
        <div className="space-y-4">
            {/* 搜索和操作栏 */}
            <div className="flex flex-wrap items-center gap-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <Input 
                        placeholder="🔍 全字段搜索..." 
                        className="pl-9 transition-all duration-200 focus:ring-2 focus:ring-blue-500" 
                        value={tempSearch}
                        onChange={(e) => setTempSearch(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            applyFilters();
                          }
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
                          const newSearch = { ...tempFieldSearch };
                          const oldValue = newSearch[field];
                          delete newSearch[field];
                          newSearch[newField] = oldValue || "";
                          setSelectedFields(newFields);
                          setTempFieldSearch(newSearch);
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
                        value={tempFieldSearch[field] || ""}
                        onChange={(e) => updateFieldSearch(field, e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            applyFilters();
                          }
                        }}
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

                {/* 查询和清除按钮 */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={applyFilters}
                    className="h-8 bg-blue-600 hover:bg-blue-700"
                  >
                    <Search className="h-4 w-4 mr-1" />
                    查询
                  </Button>
                  {(tempSearch || Object.keys(tempFieldSearch).length > 0 || appliedSearch || Object.keys(appliedFieldSearch).length > 0) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={clearFilters}
                      className="h-8"
                    >
                      <X className="h-4 w-4 mr-1" />
                      清除
                    </Button>
                  )}
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
                    📊 总计: {data?.total_records ?? 0} 条
                </div>
            </div>

            {/* SQL查询面板 */}
            {showSqlPanel && (
              <div className="animate-in fade-in duration-300">
                <SqlQueryPanel tableName={tableName} />
              </div>
            )}

            {/* 数据表格 - 使用React.memo优化，避免不必要的重新渲染 */}
            {isLoading ? (
              <div className="rounded-md border bg-white">
                {columns.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {columns.map((col) => (
                          <TableHead
                            key={col}
                            className="cursor-pointer select-none hover:bg-gray-100 transition-colors"
                            onClick={(e) => handleSort(col, e)}
                          >
                            <div className="flex items-center gap-2">
                              <span className="capitalize">{col}</span>
                              {getSortIcon(col)}
                            </div>
                          </TableHead>
                        ))}
                        <TableHead className="text-right w-[120px]">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center py-8">
                          <div className="flex items-center justify-center gap-2">
                            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                            <span className="text-gray-500">加载数据中...</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                )}
                {columns.length === 0 && (
                  <div className="flex items-center justify-center p-8">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                    <span className="ml-2 text-lg">加载数据中...</span>
                  </div>
                )}
              </div>
            ) : !data ? (
              <div className="rounded-md border bg-white">
                {columns.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {columns.map((col) => (
                          <TableHead
                            key={col}
                            className="cursor-pointer select-none hover:bg-gray-100 transition-colors"
                            onClick={(e) => handleSort(col, e)}
                          >
                            <div className="flex items-center gap-2">
                              <span className="capitalize">{col}</span>
                              {getSortIcon(col)}
                            </div>
                          </TableHead>
                        ))}
                        <TableHead className="text-right w-[120px]">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell colSpan={columns.length + 1} className="text-center text-gray-500 py-8">
                          未找到数据
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                )}
                {columns.length === 0 && (
                  <div className="text-center p-8 text-muted-foreground">未找到数据</div>
                )}
              </div>
            ) : (
              <TableContent 
                columns={columns}
                records={data.records}
                sortState={sortState}
                tableName={tableName}
                onSort={handleSort}
                getSortIcon={getSortIcon}
                deleteRecord={deleteRecord}
              />
            )}

            {/* 分页 */}
            {data && data.total_pages > 1 && (
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

// TableContent 组件 - 用于渲染表格内容
const TableContent = memo(function TableContent({
  columns,
  records,
  sortState,
  tableName,
  onSort,
  getSortIcon,
  deleteRecord,
}: {
  columns: string[];
  records: any[];
  sortState: SortState;
  tableName: string;
  onSort: (column: string, e?: React.MouseEvent) => void;
  getSortIcon: (column: string) => React.ReactNode;
  deleteRecord: ReturnType<typeof useDeleteTableRecord>;
}) {
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const handleDelete = (record: any) => {
    if (confirm(`确定要删除这条记录吗？\nID: ${record.id}`)) {
      deleteRecord.mutate({ tableName, recordId: record.id });
    }
  };

  const handleCopy = async (value: any, cellKey: string) => {
    try {
      let textToCopy: string;
      
      if (value === null || value === undefined) {
        textToCopy = "";
      } else if (typeof value === "object") {
        textToCopy = JSON.stringify(value, null, 2);
      } else {
        textToCopy = String(value);
      }
      
      await navigator.clipboard.writeText(textToCopy);
      setCopiedCell(cellKey);
      toast.success("已复制到剪贴板");
      setTimeout(() => setCopiedCell(null), 2000);
    } catch (error) {
      toast.error("复制失败");
      console.error("复制失败:", error);
    }
  };

  const formatCellValue = (value: any): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "boolean") return value ? "是" : "否";
    if (typeof value === "object") return JSON.stringify(value);
    const str = String(value);
    // 截断过长的文本
    return str.length > 50 ? str.substring(0, 50) + "..." : str;
  };

  return (
    <div className="rounded-md border bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <Table className="w-full">
          <colgroup>
            {columns.map((col) => (
              <col key={col} style={{ width: '200px', minWidth: '100px', maxWidth: '200px' }} />
            ))}
            <col style={{ width: '120px', minWidth: '120px' }} />
          </colgroup>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead
                  key={col}
                  className="cursor-pointer select-none hover:bg-gray-100 transition-colors"
                  onClick={(e) => onSort(col, e)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="capitalize truncate">{col}</span>
                    {getSortIcon(col)}
                  </div>
                </TableHead>
              ))}
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {records.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} className="text-center text-gray-500 py-8">
                  暂无数据
                </TableCell>
              </TableRow>
            ) : (
              records.map((record, idx) => (
                <TableRow key={record.id || idx} className="hover:bg-gray-50">
                  {columns.map((col) => {
                    const cellValue = formatCellValue(record[col]);
                    const originalValue = record[col];
                    const isLongText = typeof originalValue === 'string' && originalValue.length > 50;
                    const displayValue = isLongText 
                      ? originalValue.substring(0, 50) + '...' 
                      : cellValue;
                    const fullValue = typeof originalValue === 'string' ? originalValue : cellValue;
                    const cellKey = `${record.id || idx}-${col}`;
                    const isCopied = copiedCell === cellKey;
                    
                    return (
                      <TableCell 
                        key={col} 
                        className="overflow-hidden cursor-pointer select-none hover:bg-blue-50 transition-colors"
                        onDoubleClick={() => handleCopy(originalValue, cellKey)}
                        title="双击复制"
                      >
                        <div className="flex items-center gap-2">
                          {isLongText ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="truncate cursor-help flex-1">
                                  {displayValue}
                                </div>
                              </TooltipTrigger>
                              <TooltipContent className="max-w-md break-words">
                                <p>{fullValue}</p>
                              </TooltipContent>
                            </Tooltip>
                          ) : (
                            <div className="truncate flex-1">{displayValue}</div>
                          )}
                          {isCopied && <Check className="h-4 w-4 text-green-600 flex-shrink-0" />}
                        </div>
                      </TableCell>
                    );
                  })}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <TableRecordDialog
                        tableName={tableName}
                        columns={columns}
                        record={record}
                        trigger={
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Edit className="h-4 w-4 text-blue-600" />
                          </Button>
                        }
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 hover:bg-red-50 hover:text-red-600"
                        onClick={() => handleDelete(record)}
                        disabled={deleteRecord.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
});
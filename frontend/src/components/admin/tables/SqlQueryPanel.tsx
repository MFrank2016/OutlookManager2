"use client";

import { useState } from "react";
import { 
  useExecuteSql, 
  useSqlHistory, 
  useSqlFavorites, 
  useCreateSqlFavorite, 
  useDeleteSqlFavorite 
} from "@/hooks/useAdmin";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Play,
  Trash2,
  Star,
  History,
  Download,
  Loader2,
  X,
  CheckCircle2,
  AlertCircle,
  Code
} from "lucide-react";
import { toast } from "sonner";

interface SqlQueryPanelProps {
  tableName?: string;
}

export function SqlQueryPanel({ tableName }: SqlQueryPanelProps) {
  const [sql, setSql] = useState("");
  const [showFavorites, setShowFavorites] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showFavoriteDialog, setShowFavoriteDialog] = useState(false);
  const [favoriteName, setFavoriteName] = useState("");
  const [favoriteDescription, setFavoriteDescription] = useState("");
  
  const executeSql = useExecuteSql();
  const { data: favoritesData } = useSqlFavorites();
  const { data: historyData } = useSqlHistory({ page: 1, page_size: 20 });
  const createFavorite = useCreateSqlFavorite();
  const deleteFavorite = useDeleteSqlFavorite();

  const handleExecute = () => {
    if (!sql.trim()) {
      toast.error("请输入SQL语句");
      return;
    }
    executeSql.mutate({ sql: sql.trim(), max_rows: 10000 });
  };

  const handleLoadFavorite = (favoriteSql: string) => {
    setSql(favoriteSql);
    setShowFavorites(false);
    toast.success("已加载收藏的SQL");
  };

  const handleLoadHistory = (historySql: string) => {
    setSql(historySql);
    setShowHistory(false);
    toast.success("已加载历史SQL");
  };

  const handleSaveFavorite = () => {
    if (!favoriteName.trim()) {
      toast.error("请输入收藏名称");
      return;
    }
    if (!sql.trim()) {
      toast.error("SQL语句不能为空");
      return;
    }
    createFavorite.mutate(
      {
        name: favoriteName,
        sql_query: sql.trim(),
        description: favoriteDescription || undefined,
      },
      {
        onSuccess: () => {
          setShowFavoriteDialog(false);
          setFavoriteName("");
          setFavoriteDescription("");
        },
      }
    );
  };

  const handleDeleteFavorite = (id: number) => {
    if (confirm("确定要删除这个收藏吗？")) {
      deleteFavorite.mutate(id);
    }
  };

  const handleExport = (format: "csv" | "json") => {
    if (!executeSql.data?.data || executeSql.data.data.length === 0) {
      toast.error("没有可导出的数据");
      return;
    }

    let content = "";
    let filename = "";
    let mimeType = "";

    if (format === "csv") {
      // CSV导出
      const headers = Object.keys(executeSql.data.data[0]);
      const rows = executeSql.data.data.map((row: any) =>
        headers.map((header) => {
          const value = row[header];
          // 处理包含逗号、引号或换行符的值
          if (typeof value === "string" && (value.includes(",") || value.includes('"') || value.includes("\n"))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? "";
        })
      );
      content = [headers.join(","), ...rows.map((row: any[]) => row.join(","))].join("\n");
      filename = `sql_query_${new Date().toISOString().split("T")[0]}.csv`;
      mimeType = "text/csv";
    } else {
      // JSON导出
      content = JSON.stringify(executeSql.data.data, null, 2);
      filename = `sql_query_${new Date().toISOString().split("T")[0]}.json`;
      mimeType = "application/json";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`已导出为 ${format.toUpperCase()}`);
  };

  return (
    <Card className="border-2 border-blue-200 shadow-lg">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardTitle className="flex items-center gap-2 text-xl">
          <Code className="h-5 w-5 text-blue-600" />
          SQL查询面板
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-6">
        {/* SQL编辑器 */}
        <div className="space-y-2">
          <Label className="text-sm font-semibold">SQL语句</Label>
          <Textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            placeholder={`-- 输入SQL查询语句\n-- 例如: SELECT * FROM ${tableName || "accounts"} LIMIT 10;`}
            className="font-mono text-sm min-h-[150px] resize-y"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                handleExecute();
              }
            }}
          />
        </div>

        {/* 操作按钮栏 */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={handleExecute}
            disabled={executeSql.isPending || !sql.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {executeSql.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                执行中...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                执行 (Ctrl+Enter)
              </>
            )}
          </Button>

          <Button
            variant="outline"
            onClick={() => setSql("")}
            disabled={!sql}
          >
            <X className="mr-2 h-4 w-4" />
            清除
          </Button>

          <Dialog open={showFavoriteDialog} onOpenChange={setShowFavoriteDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" disabled={!sql.trim()}>
                <Star className="mr-2 h-4 w-4" />
                收藏
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>收藏SQL查询</DialogTitle>
                <DialogDescription>
                  为这个SQL查询添加一个名称和描述，方便以后使用
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="favorite-name">名称 *</Label>
                  <Input
                    id="favorite-name"
                    value={favoriteName}
                    onChange={(e) => setFavoriteName(e.target.value)}
                    placeholder="例如: 查询所有账户"
                  />
                </div>
                <div>
                  <Label htmlFor="favorite-desc">描述</Label>
                  <Textarea
                    id="favorite-desc"
                    value={favoriteDescription}
                    onChange={(e) => setFavoriteDescription(e.target.value)}
                    placeholder="可选：添加描述信息"
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowFavoriteDialog(false)}>
                  取消
                </Button>
                <Button onClick={handleSaveFavorite} disabled={createFavorite.isPending}>
                  {createFavorite.isPending ? "保存中..." : "保存"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showFavorites} onOpenChange={setShowFavorites}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Star className="mr-2 h-4 w-4" />
                收藏列表
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>SQL收藏列表</DialogTitle>
                <DialogDescription>
                  点击收藏项加载SQL到编辑器
                </DialogDescription>
              </DialogHeader>
              <div className="max-h-[400px] overflow-y-auto">
                {favoritesData?.favorites.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    暂无收藏
                  </div>
                ) : (
                  <div className="space-y-2">
                    {favoritesData?.favorites.map((favorite) => (
                      <Card key={favorite.id} className="p-3 hover:bg-blue-50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-semibold">{favorite.name}</div>
                            {favorite.description && (
                              <div className="text-sm text-muted-foreground mt-1">
                                {favorite.description}
                              </div>
                            )}
                            <div className="text-xs text-muted-foreground mt-2 font-mono bg-gray-100 p-2 rounded">
                              {favorite.sql_query}
                            </div>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleLoadFavorite(favorite.sql_query)}
                            >
                              加载
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteFavorite(favorite.id)}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showHistory} onOpenChange={setShowHistory}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <History className="mr-2 h-4 w-4" />
                历史记录
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>SQL执行历史</DialogTitle>
                <DialogDescription>
                  点击历史记录加载SQL到编辑器
                </DialogDescription>
              </DialogHeader>
              <div className="max-h-[400px] overflow-y-auto">
                {historyData?.history.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    暂无历史记录
                  </div>
                ) : (
                  <div className="space-y-2">
                    {historyData?.history.map((item) => (
                      <Card
                        key={item.id}
                        className={`p-3 hover:bg-blue-50 transition-colors ${
                          item.status === "error" ? "border-red-200" : ""
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {item.status === "success" ? (
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-red-500" />
                              )}
                              <span className="text-xs text-muted-foreground">
                                {new Date(item.created_at).toLocaleString()}
                              </span>
                              {item.execution_time_ms && (
                                <span className="text-xs text-muted-foreground">
                                  ({item.execution_time_ms}ms)
                                </span>
                              )}
                              {item.result_count !== null && (
                                <span className="text-xs text-muted-foreground">
                                  {item.result_count} 行
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-muted-foreground mt-2 font-mono bg-gray-100 p-2 rounded">
                              {item.sql_query}
                            </div>
                            {item.error_message && (
                              <div className="text-sm text-red-600 mt-2">
                                {item.error_message}
                              </div>
                            )}
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleLoadHistory(item.sql_query)}
                            className="ml-4"
                          >
                            加载
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>

          {executeSql.data?.success && executeSql.data.data && (
            <div className="flex gap-2">
              <Select onValueChange={(value) => handleExport(value as "csv" | "json")}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="导出格式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">
                    <Download className="mr-2 h-4 w-4 inline" />
                    CSV
                  </SelectItem>
                  <SelectItem value="json">
                    <Download className="mr-2 h-4 w-4 inline" />
                    JSON
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* 执行结果 */}
        {executeSql.data && (
          <div className="space-y-2 animate-in fade-in duration-300">
            {executeSql.data.success ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-green-600 font-semibold">
                  <CheckCircle2 className="h-5 w-5" />
                  <span>
                    执行成功 - {executeSql.data.row_count ?? 0} 行，耗时{" "}
                    {executeSql.data.execution_time_ms}ms
                  </span>
                </div>
                {executeSql.data.data && executeSql.data.data.length > 0 ? (
                  <div className="rounded-lg border overflow-x-auto max-h-[500px] overflow-y-auto">
                    <Table>
                      <TableHeader className="sticky top-0 bg-white z-10">
                        <TableRow className="bg-gradient-to-r from-blue-50 to-indigo-50">
                          {Object.keys(executeSql.data.data[0] || {}).map((key) => (
                            <TableHead key={key} className="font-bold whitespace-nowrap">
                              {key}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {executeSql.data.data.map((row: any, idx: number) => {
                          const firstRow = executeSql.data.data?.[0];
                          if (!firstRow) return null;
                          return (
                            <TableRow
                              key={idx}
                              className={idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"}
                            >
                              {Object.keys(firstRow).map((key) => (
                                <TableCell key={key} className="max-w-[200px] truncate" title={String(row[key] ?? "")}>
                                  {String(row[key] ?? "")}
                                </TableCell>
                              ))}
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    查询成功，但没有返回数据
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-600 font-semibold p-4 bg-red-50 rounded-lg">
                <AlertCircle className="h-5 w-5" />
                <div>
                  <div>执行失败</div>
                  {executeSql.data.error_message && (
                    <div className="text-sm font-normal mt-1">
                      {executeSql.data.error_message}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}


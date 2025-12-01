"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { AlertTriangle, CheckCircle, Loader2, ArrowLeft, Trash2, FileText, Play } from "lucide-react";
import Link from "next/link";

interface BatchResult {
  email: string;
  status: "success" | "error";
  message: string;
}

export default function BatchAddPage() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [importMethod, setImportMethod] = useState<"imap" | "graph">("imap");
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [currentCount, setCurrentCount] = useState({ current: 0, total: 0 });

  const handleLoadSample = () => {
    const sample = `example1@outlook.com----password1----refresh_token_here_1----client_id_here_1
example2@outlook.com----password2----refresh_token_here_2----client_id_here_2
example3@outlook.com----password3----refresh_token_here_3----client_id_here_3`;
    setInput(sample);
    toast.info("示例数据已加载");
  };

  const handleClear = () => {
    setInput("");
    setTagsInput("");
    setResults([]);
    setProgress(0);
    setCurrentCount({ current: 0, total: 0 });
  };

  const handleValidate = () => {
    if (!input.trim()) {
      toast.warning("请先输入账户信息");
      return;
    }

    const lines = input.split("\n").filter((line) => line.trim());
    const invalidLines = lines
      .map((line, index) => {
        const parts = line.split("----");
        // Although password is in the format, we mainly need email, refresh_token, client_id
        // The old format was email----password----refresh----client
        // We check if we have at least 4 parts or if the user skipped password but kept separators?
        // Let's stick to the exact check from batch.js: parts.length === 4
        return parts.length === 4 && parts.every((p) => p.trim().length > 0) ? null : index + 1;
      })
      .filter(Boolean);

    if (invalidLines.length === 0) {
      toast.success(`格式有效！找到 ${lines.length} 个账户。`);
    } else {
      toast.error(`以下行格式无效: ${invalidLines.join(", ")}`);
    }
  };

  const handleBatchAdd = async () => {
    const lines = input.split("\n").filter((line) => line.trim());
    if (lines.length === 0) {
      toast.warning("没有有效的行可处理");
      return;
    }

    setIsProcessing(true);
    setResults([]);
    setProgress(0);
    setCurrentCount({ current: 0, total: lines.length });

    let successCount = 0;
    let failCount = 0;
    const newResults: BatchResult[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const parts = line.split("----").map((p) => p.trim());

      // Update progress
      setCurrentCount({ current: i + 1, total: lines.length });
      const currentProgress = Math.round(((i + 1) / lines.length) * 100);
      setProgress(currentProgress);

      if (parts.length !== 4) {
        failCount++;
        newResults.push({
          email: parts[0] || "Invalid Format",
          status: "error",
          message: "格式错误：应为 email----pwd----token----client_id",
        });
        setResults([...newResults]); // Update UI incrementally
        continue;
      }

      const [email, , refreshToken, clientId] = parts;

      // 解析标签：将逗号分隔的字符串转换为标签数组
      const tags = tagsInput
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);

      try {
        await api.post("/accounts", {
          email,
          refresh_token: refreshToken,
          client_id: clientId,
          tags: tags.length > 0 ? tags : undefined,
          api_method: importMethod,
        });
        successCount++;
        newResults.push({
          email,
          status: "success",
          message: "添加成功",
        });
      } catch (error: any) {
        failCount++;
        const msg = error.response?.data?.detail || error.message || "未知错误";
        newResults.push({
          email,
          status: "error",
          message: msg,
        });
      }
      setResults([...newResults]);
      
      // Small delay to prevent rate limiting
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    setIsProcessing(false);
    if (successCount > 0) {
      toast.success(`完成：成功 ${successCount} 个，失败 ${failCount} 个`);
    } else {
      toast.error("所有账户添加失败");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto px-4 sm:px-0">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight">批量添加账户</h1>
          <p className="text-sm sm:text-base text-muted-foreground">一次性添加多个邮箱账户。</p>
        </div>
        <Button variant="outline" asChild className="w-full sm:w-auto min-h-[44px]">
          <Link href="/dashboard">
            <ArrowLeft className="mr-2 h-4 w-4" /> 返回列表
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>批量输入</CardTitle>
          <CardDescription>
            每行格式: <code className="bg-slate-100 px-1 rounded">email----password----refresh_token----client_id</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 p-4 bg-slate-50 rounded-lg border">
            <span className="text-sm font-medium shrink-0">导入方式:</span>
            <Select
              value={importMethod}
              onValueChange={(value: "imap" | "graph") => setImportMethod(value)}
            >
              <SelectTrigger className="w-full sm:w-[180px] min-h-[44px]">
                <SelectValue placeholder="选择方式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="imap">IMAP (标准)</SelectItem>
                <SelectItem value="graph">Microsoft Graph API</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-xs text-muted-foreground flex-1">
              {importMethod === "imap"
                ? "使用标准 IMAP 协议。适用于大多数情况。"
                : "使用 Microsoft Graph API。对某些账户更快且更可靠。"}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">标签 (可选)</label>
            <Input
              placeholder="输入标签，多个标签用逗号分隔，例如：工作,重要,批量导入"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              disabled={isProcessing}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              为批量导入的所有账号统一添加标签，多个标签请用逗号分隔
            </p>
          </div>

          <div className="text-sm text-muted-foreground space-y-2">
            <div className="font-medium">推荐购买（非广告）:</div>
            <div className="flex flex-wrap gap-3">
              <a 
                href="https://uemail.vip/" 
                target="_blank" 
                rel="noreferrer" 
                className="text-blue-600 hover:underline hover:text-blue-800"
              >
                蓝森林-微软邮箱大全 (uemail.vip)
              </a>
              <a 
                href="https://annimail.com/" 
                target="_blank" 
                rel="noreferrer" 
                className="text-blue-600 hover:underline hover:text-blue-800"
              >
                安妮邮箱 (annimail.com)
              </a>
              <a 
                href="https://a.qqhhh.top/" 
                target="_blank" 
                rel="noreferrer" 
                className="text-blue-600 hover:underline hover:text-blue-800"
              >
                诚信邮箱批发 (a.qqhhh.top)
              </a>
              <a 
                href="https://weiyouxiang.top/" 
                target="_blank" 
                rel="noreferrer" 
                className="text-blue-600 hover:underline hover:text-blue-800"
              >
                微邮箱店铺 (weiyouxiang.top)
              </a>
            </div>
          </div>

          <Textarea
            placeholder="在此粘贴您的账户信息..."
            className="min-h-[200px] sm:min-h-[300px] font-mono text-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isProcessing}
          />

          <Alert className="bg-yellow-50 border-yellow-200">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertTitle className="text-yellow-800">重要提示</AlertTitle>
            <AlertDescription className="text-yellow-700 text-xs mt-2">
              <ul className="list-disc list-inside space-y-1">
                <li>确保格式正确（4 部分，用 ---- 分隔）</li>
                <li>先用少量账户测试</li>
                <li>处理过程中请勿关闭此页面</li>
              </ul>
            </AlertDescription>
          </Alert>

          <div className="flex flex-col sm:flex-row flex-wrap gap-2">
            <Button 
              onClick={handleBatchAdd} 
              disabled={isProcessing || !input.trim()}
              className="w-full sm:w-auto min-h-[44px]"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 处理中...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" /> 开始批量添加
                </>
              )}
            </Button>
            <Button 
              variant="secondary" 
              onClick={handleClear} 
              disabled={isProcessing}
              className="w-full sm:w-auto min-h-[44px]"
            >
              <Trash2 className="mr-2 h-4 w-4" /> 清空
            </Button>
            <Button 
              variant="secondary" 
              onClick={handleValidate} 
              disabled={isProcessing}
              className="w-full sm:w-auto min-h-[44px]"
            >
              <CheckCircle className="mr-2 h-4 w-4" /> 验证格式
            </Button>
            <Button 
              variant="secondary" 
              onClick={handleLoadSample} 
              disabled={isProcessing}
              className="w-full sm:w-auto min-h-[44px]"
            >
              <FileText className="mr-2 h-4 w-4" /> 加载示例
            </Button>
          </div>

          {isProcessing || results.length > 0 ? (
            <div className="space-y-4 mt-6 border-t pt-6">
              <div className="flex justify-between text-sm font-medium">
                <span>进度</span>
                <span>{currentCount.current} / {currentCount.total}</span>
              </div>
              <Progress value={progress} className="h-2" />
              
              <div className="space-y-2 max-h-[300px] overflow-y-auto border rounded-md p-4 bg-slate-50">
                {results.length === 0 && <p className="text-sm text-muted-foreground text-center">等待开始...</p>}
                {results.map((res, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    {res.status === "success" ? (
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                    )}
                    <div className="flex-1 break-all">
                      <span className="font-semibold">{res.email}</span>:{" "}
                      <span className={res.status === "success" ? "text-green-700" : "text-red-700"}>
                        {res.message}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}


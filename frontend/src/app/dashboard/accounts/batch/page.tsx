"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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
    toast.info("Example data loaded");
  };

  const handleClear = () => {
    setInput("");
    setResults([]);
    setProgress(0);
    setCurrentCount({ current: 0, total: 0 });
  };

  const handleValidate = () => {
    if (!input.trim()) {
      toast.warning("Please enter account information first");
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
      toast.success(`Format valid! ${lines.length} accounts found.`);
    } else {
      toast.error(`Invalid format in lines: ${invalidLines.join(", ")}`);
    }
  };

  const handleBatchAdd = async () => {
    const lines = input.split("\n").filter((line) => line.trim());
    if (lines.length === 0) {
      toast.warning("No valid lines to process");
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
          message: "Format error: Should be email----pwd----token----client_id",
        });
        setResults([...newResults]); // Update UI incrementally
        continue;
      }

      const [email, , refreshToken, clientId] = parts;

      try {
        await api.post("/accounts", {
          email,
          refresh_token: refreshToken,
          client_id: clientId,
          tags: ["batch-import"], // Optional: tag them
          api_method: importMethod,
        });
        successCount++;
        newResults.push({
          email,
          status: "success",
          message: "Added successfully",
        });
      } catch (error: any) {
        failCount++;
        const msg = error.response?.data?.detail || error.message || "Unknown error";
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
      toast.success(`Completed: ${successCount} success, ${failCount} failed`);
    } else {
      toast.error("All accounts failed to add");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Batch Add Accounts</h1>
          <p className="text-muted-foreground">Add multiple email accounts at once.</p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/dashboard">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to List
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Batch Input</CardTitle>
          <CardDescription>
            Format per line: <code className="bg-slate-100 px-1 rounded">email----password----refresh_token----client_id</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4 p-4 bg-slate-50 rounded-lg border">
            <span className="text-sm font-medium">Import Method:</span>
            <Select
              value={importMethod}
              onValueChange={(value: "imap" | "graph") => setImportMethod(value)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select method" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="imap">IMAP (Standard)</SelectItem>
                <SelectItem value="graph">Microsoft Graph API</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-xs text-muted-foreground">
              {importMethod === "imap"
                ? "Uses standard IMAP protocol. Good for most cases."
                : "Uses Microsoft Graph API. Faster and more reliable for some accounts."}
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            Recommended purchase:{" "}
            <a href="http://wmemail.com" target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
              wmemail.com
            </a>{" "}
            (Not an ad)
          </div>

          <Textarea
            placeholder="Paste your accounts here..."
            className="min-h-[300px] font-mono text-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isProcessing}
          />

          <Alert className="bg-yellow-50 border-yellow-200">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertTitle className="text-yellow-800">Important Notes</AlertTitle>
            <AlertDescription className="text-yellow-700 text-xs mt-2">
              <ul className="list-disc list-inside space-y-1">
                <li>Ensure format is correct (4 parts separated by ----)</li>
                <li>Test with a few accounts first</li>
                <li>Do not close this page while processing</li>
              </ul>
            </AlertDescription>
          </Alert>

          <div className="flex flex-wrap gap-2">
            <Button onClick={handleBatchAdd} disabled={isProcessing || !input.trim()}>
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" /> Start Batch Add
                </>
              )}
            </Button>
            <Button variant="secondary" onClick={handleClear} disabled={isProcessing}>
              <Trash2 className="mr-2 h-4 w-4" /> Clear
            </Button>
            <Button variant="secondary" onClick={handleValidate} disabled={isProcessing}>
              <CheckCircle className="mr-2 h-4 w-4" /> Validate Format
            </Button>
            <Button variant="secondary" onClick={handleLoadSample} disabled={isProcessing}>
              <FileText className="mr-2 h-4 w-4" /> Load Sample
            </Button>
          </div>

          {isProcessing || results.length > 0 ? (
            <div className="space-y-4 mt-6 border-t pt-6">
              <div className="flex justify-between text-sm font-medium">
                <span>Progress</span>
                <span>{currentCount.current} / {currentCount.total}</span>
              </div>
              <Progress value={progress} className="h-2" />
              
              <div className="space-y-2 max-h-[300px] overflow-y-auto border rounded-md p-4 bg-slate-50">
                {results.length === 0 && <p className="text-sm text-muted-foreground text-center">Waiting to start...</p>}
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


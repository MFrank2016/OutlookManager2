"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAccounts } from "@/hooks/useAccounts";
import { useEmails, useEmailDetail } from "@/hooks/useEmails";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import { SendEmailDialog } from "@/components/emails/SendEmailDialog";
import { 
    Search, 
    Filter, 
    ArrowUpDown, 
    ChevronLeft, 
    ChevronRight,
    Inbox,
    Trash2,
    Mail,
    Key
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function EmailsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialAccount = searchParams.get("account");

  const [selectedAccount, setSelectedAccount] = useState<string | null>(initialAccount);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  
  // Filters
  const [search, setSearch] = useState("");
  const [searchType, setSearchType] = useState<"subject" | "sender">("subject");
  const [folder, setFolder] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data: accountsData } = useAccounts({ page_size: 100 });
  const { data: emailsData, isLoading: isEmailsLoading } = useEmails({
    account: selectedAccount || "",
    search,
    searchType,
    folder,
    sortBy,
    sortOrder,
    page,
    page_size: pageSize
  });

  // Update URL when account changes
  useEffect(() => {
      if (selectedAccount) {
          const currentAccountParam = searchParams.get("account");
          if (currentAccountParam !== selectedAccount) {
              const params = new URLSearchParams(searchParams.toString());
              params.set("account", selectedAccount);
              router.replace(`?${params.toString()}`);
          }
      }
  }, [selectedAccount, router, searchParams]);

  // If no account selected and accounts loaded, select first
  useEffect(() => {
      if (!selectedAccount && accountsData?.accounts?.length && accountsData.accounts.length > 0) {
          const firstAccount = accountsData.accounts[0].email_id;
          if (firstAccount !== selectedAccount) {
             setSelectedAccount(firstAccount);
          }
      }
  }, [accountsData, selectedAccount]);

  // Reset page when filters change
  useEffect(() => {
      setPage(1);
  }, [search, folder, sortBy, sortOrder, selectedAccount]);

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col space-y-4">
      {/* Top Bar: Account Selection & Filters */}
      <div className="flex flex-col gap-4 bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex items-center gap-4">
            <div className="w-64">
                <Select value={selectedAccount || ""} onValueChange={setSelectedAccount}>
                    <SelectTrigger>
                        <SelectValue placeholder="Select Account" />
                    </SelectTrigger>
                    <SelectContent>
                        {accountsData?.accounts.map(acc => (
                            <SelectItem key={acc.email_id} value={acc.email_id}>
                                {acc.email_id}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
            <div className="flex-1 flex gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <Input 
                        placeholder={searchType === "subject" ? "Search subject..." : "Search sender..."}
                        className="pl-9" 
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <Select value={searchType} onValueChange={(v: any) => setSearchType(v)}>
                    <SelectTrigger className="w-[130px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="subject">Subject</SelectItem>
                        <SelectItem value="sender">Sender</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <SendEmailDialog account={selectedAccount} />
        </div>

        <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Folder:</span>
                <Select value={folder} onValueChange={setFolder}>
                    <SelectTrigger className="w-[140px] h-8">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Mail</SelectItem>
                        <SelectItem value="inbox">Inbox</SelectItem>
                        <SelectItem value="junk">Junk Email</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Sort:</span>
                <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-[140px] h-8">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="date">Date</SelectItem>
                        <SelectItem value="subject">Subject</SelectItem>
                        <SelectItem value="from_email">Sender</SelectItem>
                    </SelectContent>
                </Select>
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 px-2"
                    onClick={() => setSortOrder(prev => prev === "asc" ? "desc" : "asc")}
                >
                    <ArrowUpDown className={cn("h-4 w-4 mr-1", sortOrder === "asc" && "rotate-180")} />
                    {sortOrder === "asc" ? "Asc" : "Desc"}
                </Button>
            </div>

            {emailsData && (
                <div className="ml-auto flex items-center gap-2">
                    <span className="text-muted-foreground">
                        Page {page} of {emailsData.total_pages} ({emailsData.total_emails} total)
                    </span>
                    <div className="flex gap-1">
                        <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setPage(p => Math.min(emailsData.total_pages, p + 1))}
                            disabled={page >= emailsData.total_pages}
                        >
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            )}
        </div>
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Email List */}
        <Card className="w-[400px] flex flex-col border-none shadow-md">
            <div className="p-3 border-b bg-slate-50/50 font-medium text-sm text-slate-600 flex justify-between items-center">
                <span>Message List</span>
                {isEmailsLoading && <span className="text-xs animate-pulse">Refreshing...</span>}
            </div>
            <ScrollArea className="flex-1 bg-white">
                {isEmailsLoading && !emailsData ? (
                    <div className="p-8 text-center text-muted-foreground">Loading emails...</div>
                ) : (
                    <div className="divide-y">
                        {emailsData?.emails.map((email, idx) => (
                            <div 
                                key={email.message_id}
                                onClick={() => setSelectedEmailId(email.message_id)}
                                className={cn(
                                    "p-4 cursor-pointer hover:bg-slate-50 transition-all duration-200 group relative",
                                    selectedEmailId === email.message_id ? "bg-blue-50/60 border-l-4 border-blue-500" : "border-l-4 border-transparent",
                                    idx % 2 === 0 ? "bg-white" : "bg-slate-50/30" // Zebra striping
                                )}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <div className="font-semibold text-slate-900 truncate pr-2 flex-1">
                                        {email.from_email}
                                    </div>
                                    <span className="text-[10px] text-slate-400 whitespace-nowrap">
                                        {formatDistanceToNow(new Date(email.date), { addSuffix: true })}
                                    </span>
                                </div>
                                
                                <div className="text-sm font-medium text-slate-700 truncate mb-1">
                                    {email.verification_code ? (
                                        <span className="inline-flex items-center mr-2 text-amber-600">
                                            <Key className="w-3 h-3 mr-1" />
                                            {email.verification_code}
                                        </span>
                                    ) : null}
                                    {email.subject}
                                </div>
                                
                                <div className="flex items-center gap-2 mt-2">
                                    <Badge variant="secondary" className="text-[10px] px-1 py-0 h-5 font-normal">
                                        {email.folder}
                                    </Badge>
                                    {/* Add more badges/flags here if available */}
                                </div>
                            </div>
                        ))}
                        {emailsData?.emails.length === 0 && (
                            <div className="p-12 text-center flex flex-col items-center text-muted-foreground">
                                <Inbox className="h-12 w-12 mb-4 text-slate-200" />
                                <p>No emails found</p>
                            </div>
                        )}
                    </div>
                )}
            </ScrollArea>
        </Card>

        {/* Email Detail */}
        <Card className="flex-1 flex flex-col border-none shadow-md overflow-hidden">
            {selectedEmailId ? (
                <EmailDetailView account={selectedAccount!} messageId={selectedEmailId} />
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-300 bg-slate-50/30">
                    <Mail className="h-16 w-16 mb-4 opacity-20" />
                    <p className="text-lg font-medium text-slate-400">Select an email to read</p>
                </div>
            )}
        </Card>
      </div>
    </div>
  );
}

function EmailDetailView({ account, messageId }: { account: string, messageId: string }) {
    const { data: email, isLoading, error } = useEmailDetail(account, messageId);

    if (isLoading) return <div className="flex-1 flex items-center justify-center text-muted-foreground">Loading content...</div>;
    if (error) return <div className="flex-1 flex items-center justify-center text-red-500">Failed to load email</div>;
    if (!email) return <div className="flex-1 flex items-center justify-center text-muted-foreground">Email not found</div>;

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="p-6 border-b bg-slate-50/30">
                <div className="flex justify-between items-start gap-4 mb-4">
                    <h2 className="text-xl font-bold text-slate-900 leading-tight">{email.subject}</h2>
                    {email.verification_code && (
                        <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100 border-amber-200 shrink-0 text-base px-3 py-1">
                            Code: {email.verification_code}
                        </Badge>
                    )}
                </div>
                
                <div className="flex justify-between items-end">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <span className="font-medium text-slate-500 w-12">From:</span> 
                            <span className="font-semibold text-slate-900">{email.from_email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                            <span className="font-medium text-slate-500 w-12">To:</span> 
                            <span>{email.to_email}</span>
                        </div>
                    </div>
                    <div className="text-xs text-slate-400">
                        {new Date(email.date).toLocaleString(undefined, { 
                            dateStyle: 'full', 
                            timeStyle: 'long' 
                        })}
                    </div>
                </div>
            </div>
            
            <ScrollArea className="flex-1 p-8">
                <div 
                    className="prose prose-slate max-w-none dark:prose-invert email-content"
                    dangerouslySetInnerHTML={{ __html: email.body_html || email.body_plain || "" }} 
                />
            </ScrollArea>
        </div>
    );
}

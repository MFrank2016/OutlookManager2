"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, RefreshCw, Trash, Tag, Mail, CheckCircle, XCircle, Clock } from "lucide-react";
import { Account } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { TagsDialog } from "./TagsDialog";
import { useDeleteAccount, useRefreshToken } from "@/hooks/useAccounts";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface AccountsTableProps {
  accounts: Account[];
  isLoading: boolean;
}

export function AccountsTable({ accounts, isLoading }: AccountsTableProps) {
  const [tagDialogState, setTagDialogState] = useState<{ open: boolean; email: string | null; tags: string[] }>({
    open: false,
    email: null,
    tags: [],
  });
  
  const deleteAccount = useDeleteAccount();
  const refreshToken = useRefreshToken();

  const handleEditTags = (account: Account) => {
    setTagDialogState({ open: true, email: account.email_id, tags: account.tags || [] });
  };

  // Function to generate a deterministic color for tags
  const getTagColor = (tag: string) => {
    const colors = ["bg-blue-100 text-blue-800", "bg-green-100 text-green-800", "bg-purple-100 text-purple-800", "bg-pink-100 text-purple-800", "bg-yellow-100 text-yellow-800", "bg-indigo-100 text-indigo-800"];
    let hash = 0;
    for (let i = 0; i < tag.length; i++) {
        hash = tag.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  if (isLoading) {
    return <div className="p-4 text-center">Loading accounts...</div>;
  }

  if (accounts.length === 0) {
    return <div className="p-4 text-center text-gray-500">No accounts found.</div>;
  }

  return (
    <>
      <div className="rounded-md border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50 hover:bg-slate-50">
              <TableHead className="w-[50px]"></TableHead>
              <TableHead>Account</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Refresh Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account, index) => (
              <TableRow key={account.email_id} className={index % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
                <TableCell>
                    <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-blue-500 text-white text-xs">
                            {account.email_id.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </TableCell>
                <TableCell className="font-medium">
                  <div className="flex flex-col">
                    <span className="text-sm">{account.email_id}</span>
                    <span className="text-xs text-gray-400 font-mono">ID: {account.client_id.substring(0, 8)}...</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1.5">
                    {account.tags?.map(tag => (
                      <Badge key={tag} variant="secondary" className={cn("text-xs font-normal border-0", getTagColor(tag))}>
                        {tag}
                      </Badge>
                    ))}
                    {(!account.tags || account.tags.length === 0) && <span className="text-xs text-gray-400 italic">No tags</span>}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant="outline" 
                    className={cn(
                        "font-normal",
                        account.status === "active" ? "bg-green-50 text-green-700 border-green-200" : 
                        account.status === "invalid" ? "bg-red-50 text-red-700 border-red-200" :
                        "bg-yellow-50 text-yellow-700 border-yellow-200"
                    )}
                  >
                    {account.status === "active" ? "Active" : account.status === "invalid" ? "Invalid" : "Error"}
                  </Badge>
                </TableCell>
                <TableCell>
                   <div className="flex items-center gap-2">
                     {account.refresh_status === "success" && <CheckCircle className="h-4 w-4 text-green-500" />}
                     {account.refresh_status === "failed" && <XCircle className="h-4 w-4 text-red-500" />}
                     {account.refresh_status === "pending" && <Clock className="h-4 w-4 text-yellow-500" />}
                     <div className="flex flex-col">
                        <span className={cn(
                            "text-xs font-medium",
                            account.refresh_status === "success" ? "text-green-700" : 
                            account.refresh_status === "failed" ? "text-red-700" : "text-yellow-700"
                        )}>
                            {account.refresh_status === "success" ? "Success" : account.refresh_status === "failed" ? "Failed" : "Pending"}
                        </span>
                        {account.last_refresh_time && (
                        <span className="text-[10px] text-gray-400">
                            {formatDistanceToNow(new Date(account.last_refresh_time), { addSuffix: true })}
                        </span>
                        )}
                     </div>
                   </div>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem asChild>
                         <Link href={`/dashboard/emails?account=${account.email_id}`}>
                           <Mail className="mr-2 h-4 w-4" /> View Emails
                         </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => refreshToken.mutate(account.email_id)}>
                        <RefreshCw className="mr-2 h-4 w-4" /> Refresh Token
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleEditTags(account)}>
                        <Tag className="mr-2 h-4 w-4" /> Manage Tags
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600 focus:text-red-600 focus:bg-red-50" onClick={() => {
                          if (confirm("Are you sure you want to delete this account?")) {
                              deleteAccount.mutate(account.email_id);
                          }
                      }}>
                        <Trash className="mr-2 h-4 w-4" /> Delete Account
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <TagsDialog 
        open={tagDialogState.open} 
        onOpenChange={(open) => setTagDialogState(prev => ({ ...prev, open }))}
        accountEmail={tagDialogState.email}
        initialTags={tagDialogState.tags}
      />
    </>
  );
}

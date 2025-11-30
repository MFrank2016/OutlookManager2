"use client";

import { useState } from "react";
import { useUsers, useDeleteUser } from "@/hooks/useAdmin";
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
import { Input } from "@/components/ui/input";
import { Trash, Edit, Search, User as UserIcon, ShieldAlert, ShieldCheck, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { UserDialog } from "./UserDialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export function UsersTable() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  
  const { data, isLoading } = useUsers({ 
      page, 
      page_size: 20,
      search 
  });
  const deleteUser = useDeleteUser();

  if (isLoading) return <div className="p-8 text-center text-muted-foreground">Loading users...</div>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
                placeholder="Search users..." 
                className="pl-9" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                }}
            />
        </div>
        <UserDialog />
      </div>

      <div className="rounded-md border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50 hover:bg-slate-50">
              <TableHead className="w-[50px]"></TableHead>
              <TableHead>User</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Login</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.users.length === 0 && (
                <TableRow>
                    <TableCell colSpan={6} className="text-center p-8 text-muted-foreground">
                        No users found
                    </TableCell>
                </TableRow>
            )}
            {data?.users.map((user, index) => (
              <TableRow key={user.id} className={index % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
                <TableCell>
                    <Avatar className="h-8 w-8">
                        <AvatarFallback className={cn(
                            "text-xs text-white",
                            user.role === 'admin' ? "bg-purple-500" : "bg-slate-500"
                        )}>
                            {user.username.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </TableCell>
                <TableCell className="font-medium">
                    <div className="flex flex-col">
                        <span className="text-sm text-slate-900">{user.username}</span>
                        <span className="text-xs text-slate-500">{user.email || "No email"}</span>
                    </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(
                      "font-normal capitalize",
                      user.role === 'admin' 
                        ? "bg-purple-50 text-purple-700 border-purple-200" 
                        : "bg-slate-50 text-slate-700 border-slate-200"
                  )}>
                    {user.role === 'admin' && <ShieldAlert className="w-3 h-3 mr-1" />}
                    {user.role === 'user' && <ShieldCheck className="w-3 h-3 mr-1" />}
                    {user.role}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(
                      "font-normal",
                      user.is_active 
                        ? "bg-green-50 text-green-700 border-green-200" 
                        : "bg-red-50 text-red-700 border-red-200"
                  )}>
                    {user.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center text-xs text-slate-500">
                    <Clock className="w-3 h-3 mr-1" />
                    {user.last_login
                        ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                        : "Never"}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <UserDialog 
                        user={user} 
                        trigger={
                            <Button variant="ghost" size="icon" className="hover:bg-slate-100">
                                <Edit className="h-4 w-4 text-slate-600" />
                            </Button>
                        } 
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="hover:bg-red-50 hover:text-red-600"
                      onClick={() => {
                        if (confirm(`Delete user ${user.username}?`)) {
                          deleteUser.mutate(user.username);
                        }
                      }}
                      disabled={user.role === "admin"} 
                    >
                      <Trash className="h-4 w-4 text-slate-400" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between pt-2">
            <div className="text-sm text-muted-foreground">
                Total: {data.total_users} users
            </div>
            <div className="flex gap-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                >
                    Previous
                </Button>
                <span className="flex items-center px-2 text-sm font-medium">
                    Page {page} of {data.total_pages}
                </span>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                >
                    Next
                </Button>
            </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { memo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface ShareTokenSearchProps {
  accountSearch: string;
  tokenSearch: string;
  onAccountSearchChange: (value: string) => void;
  onTokenSearchChange: (value: string) => void;
  onSearch: () => void;
  isLoading?: boolean;
}

export const ShareTokenSearch = memo(function ShareTokenSearch({
  accountSearch,
  tokenSearch,
  onAccountSearchChange,
  onTokenSearchChange,
  onSearch,
  isLoading = false,
}: ShareTokenSearchProps) {
  return (
    <div className="flex flex-col gap-2 bg-white p-2 md:p-4 rounded-lg shadow-sm border">
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
          <Input 
            placeholder="搜索账户..."
            className="pl-9 h-9 text-sm" 
            value={accountSearch}
            onChange={(e) => onAccountSearchChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onSearch();
              }
            }}
          />
        </div>
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
          <Input 
            placeholder="搜索Token..."
            className="pl-9 h-9 text-sm" 
            value={tokenSearch}
            onChange={(e) => onTokenSearchChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onSearch();
              }
            }}
          />
        </div>
        <Button 
          onClick={onSearch}
          disabled={isLoading}
          className="h-9 px-4 w-full md:w-auto"
        >
          <Search className="mr-2 h-4 w-4" />
          查询
        </Button>
      </div>
    </div>
  );
});


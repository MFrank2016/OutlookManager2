"use client";

import { memo } from "react";
import { FilterToolbar } from "@/components/ui/filter-toolbar";
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
    <FilterToolbar
      leading={
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="搜索账户..."
            className="pl-9 h-9 text-sm" 
            value={accountSearch}
            onChange={(e) => onAccountSearchChange(e.target.value)}
            debounce={true}
            debounceMs={500}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onSearch();
              }
            }}
          />
        </div>
      }
      center={
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="搜索Token..."
            className="pl-9 h-9 text-sm" 
            value={tokenSearch}
            onChange={(e) => onTokenSearchChange(e.target.value)}
            debounce={true}
            debounceMs={500}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onSearch();
              }
            }}
          />
        </div>
      }
      trailing={
        <Button 
          onClick={onSearch}
          disabled={isLoading}
          throttle={true}
          throttleMs={300}
          className="h-9 px-4 w-full md:w-auto"
        >
          <Search className="mr-2 h-4 w-4" />
          查询
        </Button>
      }
    />
  );
});

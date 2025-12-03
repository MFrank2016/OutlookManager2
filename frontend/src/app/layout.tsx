import type { Metadata } from "next";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Outlook Manager",
  description: "Professional Outlook Email Management System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="font-sans">
        <QueryProvider>
          {children}
          <Toaster position="top-right" />
        </QueryProvider>
      </body>
    </html>
  );
}

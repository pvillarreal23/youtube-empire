import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { ToastProvider } from "@/components/Toast";

export const metadata: Metadata = {
  title: "YouTube Empire",
  description: "Multi-Agent Communication Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="h-screen overflow-hidden font-sans">
        <ToastProvider>
          <div className="flex h-full">
            <Sidebar />
            <main className="flex-1 overflow-hidden">{children}</main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}

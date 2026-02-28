"use client";

import { Sidebar } from "@/components/Sidebar";
import { Workspace } from "@/components/Workspace";

export default function Home() {
  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Workspace />
      </main>
    </div>
  );
}

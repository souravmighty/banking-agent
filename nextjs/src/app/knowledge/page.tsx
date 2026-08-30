"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function KnowledgeRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/staff/knowledge");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-500 text-xs">
      Redirecting to Enterprise Knowledge Base...
    </div>
  );
}

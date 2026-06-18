import { Suspense } from "react";
import { ChatProvider } from "@/components/chat/ChatProvider";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { DashboardLayout } from "@/components/DashboardLayout";

export default function HomePage(): React.JSX.Element {
  return (
    <DashboardLayout>
      <div className="flex flex-col h-full bg-white rounded-3xl overflow-hidden shadow-2xl shadow-slate-200/40 border border-slate-100/50">
        <Suspense fallback={<div className="p-8 text-center text-slate-400 font-medium">Loading ABC Bank Assistant...</div>}>
          <ChatProvider>
            <ChatContainer />
          </ChatProvider>
        </Suspense>
      </div>
    </DashboardLayout>
  );
}

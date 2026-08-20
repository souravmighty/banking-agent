import { StaffSidebarLayout } from "@/components/staff/StaffSidebarLayout";
import { StaffChatContainer } from "@/components/staff/copilot/StaffChatContainer";

export const metadata = {
  title: "Analytics Copilot | BankPilot Operations",
  description: "Enterprise portfolio, risk, and BigQuery analytics AI copilot for bank staff",
};

export default function StaffCopilotPage() {
  return (
    <StaffSidebarLayout>
      <StaffChatContainer />
    </StaffSidebarLayout>
  );
}

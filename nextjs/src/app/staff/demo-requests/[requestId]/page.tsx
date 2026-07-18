import { DemoRequestsDashboard } from "../DemoRequestsDashboard";

export default async function DeepLinkRequestPage({ params }: { params: Promise<{ requestId: string }> }) {
  const resolvedParams = await params;
  return <DemoRequestsDashboard requestId={resolvedParams.requestId} />;
}

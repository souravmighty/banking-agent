import DemoRequestsDashboard from "../page";

export default async function DeepLinkRequestPage({ params }: { params: Promise<{ requestId: string }> }) {
  const resolvedParams = await params;
  return <DemoRequestsDashboard params={resolvedParams} />;
}

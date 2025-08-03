import { redirect } from 'next/navigation';

// Make the component async
export default async function ScanRedirect({ params }: { params: Promise<{ id: string }> }) {
  // Await the params
  const { id } = await params;
  redirect(`/projects/${id}/scans/new`);
}
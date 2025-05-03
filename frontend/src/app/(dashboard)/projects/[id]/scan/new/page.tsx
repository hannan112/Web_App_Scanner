import { redirect } from 'next/navigation';

// Make the component async
export default async function ScanRedirect({ params }: { params: { id: string } }) {
  // Await the params
  const { id } = params;
  redirect(`/projects/${id}/scans/new`);
}
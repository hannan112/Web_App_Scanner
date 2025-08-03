import { Metadata } from 'next';
import PasswordResetConfirmForm from "@/components/auth/PasswordResetConfirmForm";
import { notFound } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Reset Password',
  description: 'Reset your account password'
};

interface PasswordResetConfirmPageProps {
  params: Promise<{
    token: string;
  }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function PasswordResetConfirmPage({ 
  params,
  searchParams 
}: PasswordResetConfirmPageProps) {
  const { token } = await params;
  const resolvedSearchParams = await searchParams;
  const uid = resolvedSearchParams?.uid;
  
  // Validate required parameters
  if (!token || !uid) {
    notFound();
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <PasswordResetConfirmForm 
        token={token} 
        uid={uid.toString()} 
      />
    </div>
  );
}
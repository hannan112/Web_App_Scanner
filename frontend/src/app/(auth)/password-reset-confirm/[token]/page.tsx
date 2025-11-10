import { Metadata } from 'next';
import PasswordResetConfirmForm from "@/components/auth/PasswordResetConfirmForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
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
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <PasswordResetConfirmForm
          token={token}
          uid={uid.toString()}
        />
      </div>
    </div>
  );
}
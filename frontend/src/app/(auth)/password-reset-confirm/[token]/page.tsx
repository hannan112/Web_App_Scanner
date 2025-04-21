/* eslint-disable @typescript-eslint/no-unused-vars */
import { Metadata } from 'next';
import PasswordResetConfirmForm from "@/components/auth/PasswordResetConfirmForm";
import { notFound } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Reset Password',
  description: 'Reset your account password'
};

interface PasswordResetConfirmPageProps {
  params: {
    token: string;
  };
  searchParams: { [key: string]: string | string[] | undefined };
}

export default function PasswordResetConfirmPage({ 
  params,
  searchParams 
}: PasswordResetConfirmPageProps) {
  const uid = searchParams?.uid;
  
  // Validate required parameters
  if (!params.token || !uid) {
    notFound();
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <PasswordResetConfirmForm 
        token={params.token} 
        uid={uid.toString()} 
      />
    </div>
  );
}
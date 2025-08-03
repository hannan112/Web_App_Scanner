import EmailVerification from "@/components/auth/EmailVerification";

interface VerifyEmailPageProps {
  params: Promise<{
    token: string;
  }>;
}

export default async function VerifyEmailPage({ params }: VerifyEmailPageProps) {
  const { token } = await params;
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <EmailVerification token={token} />
    </div>
  );
}
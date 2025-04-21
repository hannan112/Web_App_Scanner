import EmailVerification from "@/components/auth/EmailVerification";

interface VerifyEmailPageProps {
  params: {
    token: string;
  };
}

export default function VerifyEmailPage({ params }: VerifyEmailPageProps) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <EmailVerification token={params.token} />
    </div>
  );
}
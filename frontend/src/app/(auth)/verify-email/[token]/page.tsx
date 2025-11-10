import EmailVerification from "@/components/auth/EmailVerification";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

interface VerifyEmailPageProps {
  params: Promise<{
    token: string;
  }>;
}

export default async function VerifyEmailPage({ params }: VerifyEmailPageProps) {
  const { token } = await params;

  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <EmailVerification token={token} />
      </div>
    </div>
  );
}
import PasswordResetForm from "@/components/auth/PasswordResetForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

export default function PasswordResetPage() {
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <PasswordResetForm />
      </div>
    </div>
  );
}
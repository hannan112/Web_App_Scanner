import RegisterForm from "@/components/auth/RegisterForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

export default function RegisterPage() {
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10 w-full max-w-lg px-4">
        <RegisterForm />
      </div>
    </div>
  );
}
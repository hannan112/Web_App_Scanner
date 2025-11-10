import LoginForm from "@/components/auth/LoginForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

export default function LoginPage() {
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <LoginForm />
      </div>
    </div>
  );
}
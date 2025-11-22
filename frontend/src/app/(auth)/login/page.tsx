import { Suspense } from "react";
import LoginForm from "@/components/auth/LoginForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

export default function LoginPage() {
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <Suspense fallback={
          <div className="w-full max-w-lg p-8 mx-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-xl shadow-2xl">
            <div className="flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
          </div>
        }>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
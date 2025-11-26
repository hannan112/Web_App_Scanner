// import RegisterForm from "@/components/auth/RegisterForm";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";

export default function RegisterPage() {
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10 max-w-md w-full p-8 mx-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl text-center">
        <div className="mb-6">
          <div className="h-16 w-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-blue-500/30">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Beta Access Only</h2>
          <p className="text-gray-400 text-lg">
            Thank you for your interest! Unfortunately, this project is currently in its beta stage, so account creation is temporarily blocked.
          </p>
        </div>
      </div>
    </div>
  );

  /* Original Code
  return (
    <div className="relative flex items-center justify-center min-h-screen">
      <WorldMapAnimation />
      <div className="relative z-10">
        <RegisterForm />
      </div>
    </div>
  );
  */
}
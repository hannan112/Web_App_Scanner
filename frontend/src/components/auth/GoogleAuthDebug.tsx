"use client";

import { useEffect, useState } from "react";

export default function GoogleAuthDebug() {
  const [debugInfo, setDebugInfo] = useState({
    hasGoogleScript: false,
    hasGoogleObject: false,
    clientId: "",
    scriptLoaded: false,
    errors: [] as string[]
  });

  useEffect(() => {
    const checkGoogleAuth = () => {
      const info = {
        hasGoogleScript: !!document.querySelector('script[src*="accounts.google.com/gsi/client"]'),
        hasGoogleObject: !!window.google,
        clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "NOT_SET",
        scriptLoaded: false,
        errors: [] as string[]
      };

      // Check if Google object is available
      if (window.google) {
        info.scriptLoaded = true;
        info.hasGoogleObject = true;
      }

      // Check for common issues
      if (!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID) {
        info.errors.push("NEXT_PUBLIC_GOOGLE_CLIENT_ID environment variable not set");
      }

      if (!info.hasGoogleScript) {
        info.errors.push("Google Identity Services script not found in DOM");
      }

      if (!info.hasGoogleObject && info.hasGoogleScript) {
        info.errors.push("Google script loaded but window.google object not available");
      }

      setDebugInfo(info);
    };

    // Check immediately
    checkGoogleAuth();

    // Check again after a delay to see if script loads
    const timer = setTimeout(checkGoogleAuth, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (process.env.NODE_ENV === 'production') {
    return null; // Don't show debug info in production
  }

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-lg text-sm">
      <h3 className="font-semibold mb-2">Google Auth Debug Info:</h3>
      <div className="space-y-1">
        <div>Script in DOM: {debugInfo.hasGoogleScript ? "✅" : "❌"}</div>
        <div>Google Object: {debugInfo.hasGoogleObject ? "✅" : "❌"}</div>
        <div>Client ID: {debugInfo.clientId}</div>
        <div>Script Loaded: {debugInfo.scriptLoaded ? "✅" : "❌"}</div>
        {debugInfo.errors.length > 0 && (
          <div className="mt-2">
            <div className="font-semibold text-red-600">Errors:</div>
            {debugInfo.errors.map((error, index) => (
              <div key={index} className="text-red-600">• {error}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}



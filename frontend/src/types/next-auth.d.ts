// src/types/next-auth.d.ts
import { DefaultSession } from "next-auth";

declare module "next-auth" {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    user: {
      /** User ID from your database */
      id?: string;
      /** User name from your database */
      name?: string;
      /** Username from your database */
      username?: string;
      /** Access token for authenticated API requests */
      accessToken?: string;
      /** Refresh token for refreshing the access token */
      refreshToken?: string;
      /** Provider used for authentication (e.g. 'credentials', 'google') */
      provider?: string;
      /** User email */
      email?: string;
    } & DefaultSession["user"];
    accessToken?: string;
    refreshToken?: string;
    error?: string;
  }
}
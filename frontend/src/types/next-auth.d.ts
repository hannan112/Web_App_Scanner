/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
// src/types/next-auth.d.ts (create or update this file)

import NextAuth, { DefaultSession } from "next-auth"
import { JWT } from "next-auth/jwt"

declare module "next-auth" {
  /**
   * Extend the built-in session types
   */
  interface Session {
    accessToken?: string
    refreshToken?: string
    error?: string
    user: {
      id?: string
      provider?: string
    } & DefaultSession["user"]
  }

  /**
   * Extend the built-in user types
   */
  interface User {
    id: string
    accessToken?: string
    refreshToken?: string
    username?: string
  }
}

declare module "next-auth/jwt" {
  /** Extend the built-in JWT types */
  interface JWT {
    accessToken?: string
    refreshToken?: string
    provider?: string
    user?: any
    error?: string
  }
}
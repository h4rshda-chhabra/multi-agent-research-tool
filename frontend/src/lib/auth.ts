import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { loginApi } from "./api";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        try {
          const token = await loginApi(
            credentials.email as string,
            credentials.password as string
          );
          return {
            id: token.user_id,
            name: token.name,
            email: token.email,
            plan: token.plan,
            access_token: token.access_token,
          };
        } catch (err) {
          console.error("Auth error in authorize:", err);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.access_token = (user as { access_token: string }).access_token;
        token.plan = (user as { plan: string }).plan;
      }
      return token;
    },
    async session({ session, token }) {
      (session.user as { access_token?: string; plan?: string }).access_token =
        token.access_token as string;
      (session.user as { plan?: string }).plan = token.plan as string;
      return session;
    },
  },
  pages: {
    signIn: "/sign-in",
    error: "/sign-in",
  },
  session: { strategy: "jwt" },
  secret: process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET,
  trustHost: true,
});

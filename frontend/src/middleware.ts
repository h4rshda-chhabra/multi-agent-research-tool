export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/research/:path*",
    "/history/:path*",
    "/saved/:path*",
    "/settings/:path*",
  ],
};

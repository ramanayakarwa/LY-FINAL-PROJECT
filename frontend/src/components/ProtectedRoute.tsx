import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { auth } from "@/lib/auth";

type Props = {
  children: ReactNode;
};

export default function ProtectedRoute({
  children,
}: Props) {
  if (!auth.isLoggedIn()) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return <>{children}</>;
}
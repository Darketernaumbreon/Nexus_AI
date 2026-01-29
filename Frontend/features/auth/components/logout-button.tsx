"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { AuthAPI } from "@/lib/api";
import { LogOut } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

interface LogoutButtonProps {
  variant?: "default" | "ghost" | "outline";
  showLabel?: boolean;
}

export function LogoutButton({
  variant = "ghost",
  showLabel = true,
}: LogoutButtonProps) {
  const router = useRouter();
  const { logout } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogout = async () => {
    setIsLoading(true);
    try {
      await AuthAPI.logout();
      logout();
      router.push("/login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      onClick={handleLogout}
      disabled={isLoading}
      className="rounded-xl"
    >
      {isLoading ? (
        <Spinner className="h-4 w-4" />
      ) : (
        <LogOut className="h-4 w-4" />
      )}
      {showLabel && <span className="ml-2">Logout</span>}
    </Button>
  );
}

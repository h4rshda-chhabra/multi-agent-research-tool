"use client";

import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { User, Mail, Shield } from "lucide-react";

export default function SettingsPage() {
  const { data: session } = useSession();

  return (
    <div className="px-6 py-8 max-w-2xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your account</p>
      </motion.div>

      <div className="space-y-4">
        <div className="glass rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Profile</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <div>
                <p className="text-xs text-slate-500">Name</p>
                <p className="text-sm text-white">{session?.user?.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="w-4 h-4 text-slate-500" />
              <div>
                <p className="text-xs text-slate-500">Email</p>
                <p className="text-sm text-white">{session?.user?.email}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="glass rounded-xl p-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Plan</h2>
          <div className="flex items-center gap-3">
            <Shield className="w-4 h-4 text-brand-400" />
            <div>
              <p className="text-xs text-slate-500">Current Plan</p>
              <p className="text-sm text-white capitalize">
                {(session?.user as { plan?: string })?.plan ?? "Free"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

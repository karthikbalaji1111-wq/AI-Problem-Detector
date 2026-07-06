"use client";

import { FormEvent, Suspense, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, KeyRound, Network, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { storeSession } from "@/lib/auth";

function LoginContent() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("founder@nexus.local");
  const [name, setName] = useState("NEXUS Founder");
  const [password, setPassword] = useState("NexusPass123!");

  const auth = useMutation({
    mutationFn: () =>
      mode === "login" ? api.login(email, password) : api.register(email, name, password),
    onSuccess: (response) => {
      storeSession(response.access_token, response.user);
      router.push("/dashboard");
    }
  });

  const google = useMutation({
    mutationFn: () => api.googleStart(),
    onSuccess: (response) => {
      window.location.href = response.authorization_url;
    }
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    auth.mutate();
  }

  return (
    <main className="nexus-grid min-h-screen bg-background p-4 text-foreground md:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-6 lg:grid-cols-[1fr_420px]">
        <section className="flex flex-col justify-between rounded-lg border border-white/10 bg-white/5 p-6 shadow-panel">
          <div>
            <Badge tone="cyan">NEXUS</Badge>
            <motion.h1
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 max-w-3xl text-4xl font-semibold tracking-normal md:text-6xl"
            >
              The Autonomous AI Workforce.
            </motion.h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-muted">
              Create organizations, not chatbots. Watch agents plan, negotiate, delegate, verify,
              request approval, execute work, and learn.
            </p>
          </div>
          <div className="mt-10 grid gap-3 md:grid-cols-3">
            {[
              ["Organizations", Building2, "Generate complete autonomous teams from natural language."],
              ["Governance", ShieldCheck, "JWT auth, RBAC, audit logs, approvals, and encrypted connectors."],
              ["Agent Mesh", Network, "CEO, supervisors, specialists, critics, verifiers, and executors."]
            ].map(([label, Icon, detail]) => {
              const TypedIcon = Icon as typeof Building2;
              return (
                <div key={label as string} className="rounded-lg border border-white/10 bg-black/20 p-4">
                  <TypedIcon className="h-5 w-5 text-cyan" />
                  <div className="mt-3 text-sm font-medium">{label as string}</div>
                  <p className="mt-1 text-xs leading-5 text-muted">{detail as string}</p>
                </div>
              );
            })}
          </div>
        </section>
        <Card className="self-center">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-cyan" />
              Access Mission Control
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-3">
              {mode === "register" && (
                <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name" />
              )}
              <Input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                placeholder="Email"
              />
              <Input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                placeholder="Password"
              />
              <Button className="w-full" type="submit" variant="primary" disabled={auth.isPending}>
                {auth.isPending ? "Authenticating" : mode === "login" ? "Sign in" : "Create account"}
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                className="w-full"
                type="button"
                variant="secondary"
                disabled={google.isPending}
                onClick={() => google.mutate()}
              >
                Continue with Google
              </Button>
              {auth.error && <p className="text-xs text-coral">{auth.error.message}</p>}
            </form>
            <div className="mt-4 flex items-center justify-between text-xs text-muted">
              <span>{mode === "login" ? "Need an account?" : "Already onboarded?"}</span>
              <button
                className="text-cyan hover:underline"
                onClick={() => setMode(mode === "login" ? "register" : "login")}
              >
                {mode === "login" ? "Register" : "Sign in"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}


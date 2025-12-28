import { useState } from "react";
import { Layout } from "@/components/Layout";
import { CVResume } from "./CVResume";
import { JobsDashboard } from "./JobsDashboard";

export default function Index() {
  const [activeNav, setActiveNav] = useState<"cv" | "dashboard">("cv");

  return (
    <Layout activeNav={activeNav} onNavChange={setActiveNav}>
      {activeNav === "cv" ? <CVResume /> : <JobsDashboard />}
    </Layout>
  );
}

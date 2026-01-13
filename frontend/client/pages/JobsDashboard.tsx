import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Loader2 } from "lucide-react";

// API Base URL
const API_BASE = "http://localhost:8001";

// Types
interface MetricsData {
  total_jobs: number;
  total_companies: number;
  total_skills: number;
  total_locations: number;
}

interface SkillData {
  skill_name: string;
  job_count: number;
}

interface LocationData {
  city_name: string;
  job_count: number;
}

interface SourceData {
  source: string;
  job_count: number;
}

export function JobsDashboard() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [topSkills, setTopSkills] = useState<SkillData[]>([]);
  const [topLocations, setTopLocations] = useState<LocationData[]>([]);
  const [jobsBySource, setJobsBySource] = useState<SourceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch all endpoints in parallel
      const [metricsRes, skillsRes, locationsRes, sourcesRes] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/metrics`),
        fetch(`${API_BASE}/api/dashboard/top-skills?limit=20`),
        fetch(`${API_BASE}/api/dashboard/top-locations?limit=10`),
        fetch(`${API_BASE}/api/dashboard/jobs-by-source`),
      ]);

      if (!metricsRes.ok || !skillsRes.ok || !locationsRes.ok || !sourcesRes.ok) {
        throw new Error("Failed to fetch dashboard data");
      }

      const [metricsData, skillsData, locationsData, sourcesData] = await Promise.all([
        metricsRes.json(),
        skillsRes.json(),
        locationsRes.json(),
        sourcesRes.json(),
      ]);

      setMetrics(metricsData);
      setTopSkills(skillsData);
      setTopLocations(locationsData);
      setJobsBySource(sourcesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Transform skills data for pie chart (top 6 + others)
  const getPieChartData = () => {
    if (topSkills.length === 0) return [];

    const top6 = topSkills.slice(0, 6);
    const othersCount = topSkills.slice(6).reduce((sum, skill) => sum + skill.job_count, 0);

    const data = top6.map((skill, index) => ({
      name: skill.skill_name,
      value: skill.job_count,
      color: COLORS[index % COLORS.length],
    }));

    if (othersCount > 0) {
      data.push({
        name: "Others",
        value: othersCount,
        color: "#9ca3af",
      });
    }

    return data;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/30 p-8 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-lg text-muted-foreground">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/30 p-8 flex items-center justify-center">
        <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-semibold text-destructive mb-2">Error Loading Dashboard</h3>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const pieChartData = getPieChartData();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/30 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-3">
            IT Jobs Trending Dashboard
          </h1>
          <p className="text-lg text-muted-foreground">
            Real-time insights into the IT job market
          </p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Total Postings
            </p>
            <p className="text-3xl font-bold text-foreground">
              {metrics?.total_jobs.toLocaleString() || "0"}
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Companies
            </p>
            <p className="text-3xl font-bold text-foreground">
              {metrics?.total_companies.toLocaleString() || "0"}
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Skills Tracked
            </p>
            <p className="text-3xl font-bold text-foreground">
              {metrics?.total_skills.toLocaleString() || "0"}
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Locations
            </p>
            <p className="text-3xl font-bold text-foreground">
              {metrics?.total_locations.toLocaleString() || "0"}
            </p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Top Skills Chart */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Top Skills Demand
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topSkills.slice(0, 10)}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--border)"
                  opacity={0.5}
                />
                <XAxis
                  dataKey="skill_name"
                  stroke="var(--muted-foreground)"
                  style={{ fontSize: "12px" }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  stroke="var(--muted-foreground)"
                  style={{ fontSize: "12px" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--foreground)",
                  }}
                />
                <Bar
                  dataKey="job_count"
                  fill="hsl(var(--primary))"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Technology Distribution */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Technology Distribution
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} (${value})`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--foreground)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Top Locations */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Top Locations
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topLocations}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--border)"
                  opacity={0.5}
                />
                <XAxis
                  dataKey="city_name"
                  stroke="var(--muted-foreground)"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  stroke="var(--muted-foreground)"
                  style={{ fontSize: "12px" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--foreground)",
                  }}
                />
                <Bar
                  dataKey="job_count"
                  fill="hsl(var(--accent))"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Jobs by Source */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Jobs by Platform
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={jobsBySource.map((item, idx) => ({
                    ...item,
                    name: item.source,
                    value: item.job_count,
                    color: SOURCE_COLORS[idx % SOURCE_COLORS.length],
                  }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {jobsBySource.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SOURCE_COLORS[index % SOURCE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--foreground)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// Color constants
const COLORS = ["#61dafb", "#3776ab", "#ff9900", "#68a063", "#007396", "#326ce5"];
const SOURCE_COLORS = ["#8b5cf6", "#ec4899", "#f59e0b", "#10b981"];

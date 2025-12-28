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

// Sample data
const jobsByPosition = [
  { position: "Frontend", count: 2450 },
  { position: "Backend", count: 2150 },
  { position: "Full Stack", count: 1890 },
  { position: "Data Engineer", count: 1320 },
  { position: "DevOps", count: 980 },
  { position: "AI/ML", count: 1650 },
];

const hiringTrends = [
  { month: "Jan", jobs: 1200, applications: 4500 },
  { month: "Feb", jobs: 1450, applications: 5200 },
  { month: "Mar", jobs: 1820, applications: 6100 },
  { month: "Apr", jobs: 2100, applications: 7200 },
  { month: "May", jobs: 2450, applications: 8500 },
  { month: "Jun", jobs: 2800, applications: 9800 },
];

const techStack = [
  { name: "React", value: 32, color: "#61dafb" },
  { name: "Python", value: 28, color: "#3776ab" },
  { name: "AWS", value: 24, color: "#ff9900" },
  { name: "Node.js", value: 20, color: "#68a063" },
  { name: "Java", value: 18, color: "#007396" },
  { name: "Kubernetes", value: 15, color: "#326ce5" },
  { name: "Others", value: 23, color: "#9ca3af" },
];

export function JobsDashboard() {
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

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Jobs by Position */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Jobs by Position
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobsByPosition}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--border)"
                  opacity={0.5}
                />
                <XAxis
                  dataKey="position"
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
                  dataKey="count"
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
                  data={techStack}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} (${value}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {techStack.map((entry, index) => (
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
                  formatter={(value: number) => `${value}%`}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hiring Trends */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Hiring Trends (Last 6 Months)
          </h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={hiringTrends}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                opacity={0.5}
              />
              <XAxis
                dataKey="month"
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
              <Legend
                wrapperStyle={{
                  color: "var(--foreground)",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="jobs"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ fill: "hsl(var(--primary))", r: 4 }}
                activeDot={{ r: 6 }}
                name="Job Postings"
              />
              <Line
                type="monotone"
                dataKey="applications"
                stroke="hsl(var(--accent))"
                strokeWidth={2}
                dot={{ fill: "hsl(var(--accent))", r: 4 }}
                activeDot={{ r: 6 }}
                name="Applications"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Total Postings
            </p>
            <p className="text-3xl font-bold text-foreground">12.4K</p>
            <p className="text-xs text-muted-foreground mt-2">+15% from last month</p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Avg. Salary
            </p>
            <p className="text-3xl font-bold text-foreground">$125K</p>
            <p className="text-xs text-muted-foreground mt-2">Across all roles</p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Top Tech
            </p>
            <p className="text-3xl font-bold text-foreground">React</p>
            <p className="text-xs text-muted-foreground mt-2">32% of positions</p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Avg. Experience
            </p>
            <p className="text-3xl font-bold text-foreground">4.2y</p>
            <p className="text-xs text-muted-foreground mt-2">Years required</p>
          </div>
        </div>
      </div>
    </div>
  );
}

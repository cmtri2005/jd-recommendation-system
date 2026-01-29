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
  Label,
} from "recharts";
import { Loader2, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

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

interface CompanyData {
  company_name: string;
  company_industry: string | null;
  job_count: number;
}

interface JobTitleData {
  job_title: string;
  job_count: number;
}

interface LevelData {
  job_level: string;
  job_count: number;
}


interface IndustryData {
  industry: string;
  company_count: number;
  job_count: number;
}

interface WorkModelData {
  work_model: string;
  job_count: number;
}

export function JobsDashboard() {
  // State for data
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [topSkills, setTopSkills] = useState<SkillData[]>([]);
  const [topLocations, setTopLocations] = useState<LocationData[]>([]);
  const [topCompanies, setTopCompanies] = useState<CompanyData[]>([]);
  const [topJobTitles, setTopJobTitles] = useState<JobTitleData[]>([]);
  const [jobsBySource, setJobsBySource] = useState<SourceData[]>([]);
  const [jobsByLevel, setJobsByLevel] = useState<LevelData[]>([]);
  const [industryDist, setIndustryDist] = useState<IndustryData[]>([]);
  const [workModelDist, setWorkModelDist] = useState<WorkModelData[]>([]);

  // State for UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [showFilters, setShowFilters] = useState(false);

  // Filter state
  const [filterSources, setFilterSources] = useState<string[]>([]);
  const [filterLocations, setFilterLocations] = useState<string[]>([]);

  // Available filter options
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [availableLocations, setAvailableLocations] = useState<string[]>([]);

  // Fetch data on mount and when filters change
  useEffect(() => {
    fetchDashboardData();
  }, [filterSources, filterLocations]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build filter query params
      const params = new URLSearchParams();
      if (filterSources.length > 0) params.append("sources", filterSources.join(","));
      if (filterLocations.length > 0) params.append("locations", filterLocations.join(","));

      // Fetch all endpoints in parallel
      const [
        metricsRes,
        skillsRes,
        locationsRes,
        companiesRes,
        jobTitlesRes,
        sourcesRes,
        levelsRes,
        industryRes,
        workModelRes,
      ] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/metrics?${params}`),
        fetch(`${API_BASE}/api/dashboard/top-skills?limit=20&${params}`),
        fetch(`${API_BASE}/api/dashboard/top-locations?limit=10&${params}`),
        fetch(`${API_BASE}/api/dashboard/top-companies?limit=15&${params}`),
        fetch(`${API_BASE}/api/dashboard/top-job-titles?limit=20&${params}`),
        fetch(`${API_BASE}/api/dashboard/jobs-by-source?${params}`),
        fetch(`${API_BASE}/api/dashboard/jobs-by-level?${params}`),
        fetch(`${API_BASE}/api/dashboard/industry-distribution?limit=15&${params}`),
        fetch(`${API_BASE}/api/dashboard/work-model-distribution?${params}`),
      ]);

      if (!metricsRes.ok || !skillsRes.ok || !locationsRes.ok || !sourcesRes.ok) {
        throw new Error("Failed to fetch dashboard data");
      }

      const [
        metricsData,
        skillsData,
        locationsData,
        companiesData,
        jobTitlesData,
        sourcesData,
        levelsData,
        industryData,
        workModelData,
      ] = await Promise.all([
        metricsRes.json(),
        skillsRes.json(),
        locationsRes.json(),
        companiesRes.json(),
        jobTitlesRes.json(),
        sourcesRes.json(),
        levelsRes.json(),
        industryRes.json(),
        workModelRes.json(),
      ]);

      setMetrics(metricsData);
      setTopSkills(skillsData);

      // Normalize and merge locations (Robust Mapping)
      const locMap = new Map<string, number>();

      const normalizeCity = (name: string): string => {
        let n = name.toLowerCase().trim();
        // Remove suffixes
        n = n.replace(/\s*\(mới\)$/i, "").replace(/^tp\.?\s*/i, "");

        // Map common variations
        if (n.includes("hà nội") || n.includes("ha noi") || n.includes("hanoi")) return "Hà Nội";
        if (n.includes("hồ chí minh") || n.includes("ho chi minh") || n.includes("hcm") || n.includes("saigon")) return "Hồ Chí Minh";
        if (n.includes("đà nẵng") || n.includes("da nang")) return "Đà Nẵng";
        if (n.includes("bắc ninh") || n.includes("bac ninh")) return "Bắc Ninh";
        if (n.includes("hải phòng") || n.includes("hai phong")) return "Hải Phòng";
        if (n.includes("cần thơ") || n.includes("can tho")) return "Cần Thơ";

        // Return capitalized original if no match (simple title case)
        return n.charAt(0).toUpperCase() + n.slice(1);
      };

      locationsData.forEach((item: LocationData) => {
        // Handle "Hà Nội, Hồ Chí Minh" type strings -> Split? 
        // For simple visualization, we'll just normalize the whole string or split if comma present.
        // Let's split by comma and count each.
        const parts = item.city_name.split(/,|&|-/);
        parts.forEach(p => {
          const normName = normalizeCity(p);
          // Distribute count if split? No, usually a job in multiple locations means openings in both. 
          // We'll add the full job_count to each location.
          locMap.set(normName, (locMap.get(normName) || 0) + item.job_count);
        });
      });

      const mergedLocations = Array.from(locMap.entries())
        .map(([city_name, job_count]) => ({ city_name, job_count }))
        .sort((a, b) => b.job_count - a.job_count)
        .filter(l => l.city_name.length > 2); // Filter out noise

      setTopLocations(mergedLocations.slice(0, 10)); // Take top 10

      setTopCompanies(companiesData);
      setTopJobTitles(jobTitlesData);
      setJobsBySource(sourcesData);
      setJobsByLevel(levelsData);
      setIndustryDist(industryData);
      setWorkModelDist(workModelData);

      // Update available filter options (only on first load)
      if (availableSources.length === 0) {
        setAvailableSources(sourcesData.map((s: SourceData) => s.source));
      }
      if (availableLocations.length === 0) {
        setAvailableLocations(locationsData.map((l: LocationData) => l.city_name));
      }

      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData();
  };

  const handleResetFilters = () => {
    setFilterSources([]);
    setFilterLocations([]);
  };

  // Transform skills data for distribution (top 10 only)
  const getTechDistributionData = () => {
    if (topSkills.length === 0) return [];

    const top10 = topSkills.slice(0, 10);
    // User requested "Top 10" list, "Others" obscures the view so we remove it.

    const data = top10.map((skill, index) => ({
      name: skill.skill_name,
      value: skill.job_count,
      color: COLORS[index % COLORS.length],
    }));

    return data;
  };

  // Loading state
  if (loading && !metrics) {
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

  const techDistData = getTechDistributionData();

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-4xl font-bold text-foreground">
              IT Jobs Trending Dashboard
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
          <p className="text-lg text-muted-foreground">
            Real-time insights into the IT job market
          </p>
        </div>

        {/* Filter Panel */}
        <div className="bg-card border border-border rounded-lg p-4 mb-8">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center justify-between w-full text-left"
          >
            <h2 className="text-xl font-semibold text-foreground">Filters</h2>
            {showFilters ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>

          {showFilters && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Data Sources
                </label>
                <select
                  multiple
                  value={filterSources}
                  onChange={(e) => setFilterSources(Array.from(e.target.selectedOptions, option => option.value))}
                  className="w-full h-24 px-3 py-2 bg-background border border-border rounded-md text-foreground"
                >
                  {availableSources.map(source => (
                    <option key={source} value={source}>{source}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Locations
                </label>
                <select
                  multiple
                  value={filterLocations}
                  onChange={(e) => setFilterLocations(Array.from(e.target.selectedOptions, option => option.value))}
                  className="w-full h-24 px-3 py-2 bg-background border border-border rounded-md text-foreground"
                >
                  {availableLocations.map(location => (
                    <option key={location} value={location}>{location}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleResetFilters}
                  className="px-4 py-2 bg-muted text-foreground rounded-md hover:bg-muted/80"
                >
                  Reset Filters
                </button>
              </div>
            </div>
          )}
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

        {/* Charts Grid Row 1: Jobs by Source & Job Level */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Jobs by Platform
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobsBySource} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Number of Jobs" offset={-5} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
                </XAxis>
                <YAxis dataKey="source" type="category" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }} width={100} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="job_count" fill={SOURCE_COLORS[0]} radius={[0, 4, 4, 0]} name="Jobs" barSize={30} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Jobs by Level
            </h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={jobsByLevel} margin={{ bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="job_level"
                  stroke="#475569"
                  style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }}
                  angle={-30}
                  textAnchor="end"
                  height={60}
                />
                <YAxis stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Job Count" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fontWeight: 600, fill: '#475569' }} />
                </YAxis>
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="job_count" fill={COLORS[0]} radius={[4, 4, 0, 0]} name="Jobs" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Charts Grid Row 2: Top Skills & Technology Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Top Skills Demand
            </h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={topSkills.slice(0, 10)} margin={{ bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="skill_name"
                  stroke="#475569"
                  style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }}
                  angle={-30}
                  textAnchor="end"
                  height={60}
                />
                <YAxis stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Frequency" angle={-90} position="insideLeft" style={{ textAnchor: 'middle', fontWeight: 600, fill: '#475569' }} />
                </YAxis>
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="job_count" fill={COLORS[2]} radius={[4, 4, 0, 0]} name="Mentions" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Technology Distribution
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={techDistData} layout="vertical" margin={{ left: 10, right: 30, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Mentions" offset={-5} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
                </XAxis>
                <YAxis dataKey="name" type="category" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }} width={120} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="value" fill={COLORS[0]} radius={[0, 4, 4, 0]} name="Mentions" barSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Charts Grid Row 3: Top Locations & Work Model */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Top Locations
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topLocations} layout="vertical" margin={{ left: 10, right: 30, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Number of Jobs" offset={-5} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
                </XAxis>
                <YAxis dataKey="city_name" type="category" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }} width={120} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="job_count" fill={COLORS[1]} radius={[0, 4, 4, 0]} name="Jobs" barSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-foreground mb-6">
              Work Model Distribution
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={workModelDist.sort((a, b) => b.job_count - a.job_count)}
                layout="vertical"
                margin={{ left: 10, right: 30, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                  <Label value="Number of Jobs" offset={-5} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
                </XAxis>
                <YAxis dataKey="work_model" type="category" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif", fontWeight: 500 }} width={120} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
                <Bar dataKey="job_count" fill={WORK_MODEL_COLORS[0]} radius={[0, 4, 4, 0]} name="Jobs" barSize={25} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>


        {/* Top Companies - Full Width */}
        <div className="bg-card border border-border rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Top Companies
          </h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={topCompanies.slice(0, 15)} layout="vertical" margin={{ left: 10, right: 30, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                <Label value="Job Openings" offset={-10} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
              </XAxis>
              <YAxis
                type="category"
                dataKey="company_name"
                stroke="#475569"
                style={{ fontSize: "11px", fontFamily: "sans-serif", fontWeight: 500 }}
                width={180}
              />
              <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
              <Bar dataKey="job_count" fill={COLORS[3]} radius={[0, 4, 4, 0]} name="Jobs" barSize={15} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Job Titles - Full Width */}
        <div className="bg-card border border-border rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Top Job Titles
          </h2>
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={topJobTitles.slice(0, 20)} layout="vertical" margin={{ left: 10, right: 30, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                <Label value="Job Openings" offset={-10} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
              </XAxis>
              <YAxis
                type="category"
                dataKey="job_title"
                stroke="#475569"
                style={{ fontSize: "11px", fontFamily: "sans-serif", fontWeight: 500 }}
                width={220}
              />
              <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
              <Bar dataKey="job_count" fill={COLORS[4]} radius={[0, 4, 4, 0]} name="Jobs" barSize={15} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Industry Distribution - Full Width */}
        <div className="bg-card border border-border rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-6">
            Industry Distribution
          </h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={industryDist.slice(0, 15)} layout="vertical" margin={{ left: 10, right: 30, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#475569" style={{ fontSize: "12px", fontFamily: "sans-serif" }}>
                <Label value="Job Openings" offset={-10} position="insideBottom" style={{ fontWeight: 600, fill: '#475569' }} />
              </XAxis>
              <YAxis
                type="category"
                dataKey="industry"
                stroke="#475569"
                style={{ fontSize: "11px", fontFamily: "sans-serif", fontWeight: 500 }}
                width={180}
              />
              <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "4px", color: "#1e293b", boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)" }} />
              <Bar dataKey="job_count" fill={COLORS[5]} radius={[0, 4, 4, 0]} name="Jobs" barSize={15} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// Color constants
// Academic Color Palette
// Primary: Deep Navy/Blue, Secondary: Muted Grey/Blue, Accent: Gold/Orange (sparingly)
const COLORS = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600"];
const SOURCE_COLORS = ["#003f5c", "#58508d", "#bc5090", "#ff6361"];
const WORK_MODEL_COLORS = ["#003f5c", "#444e86", "#955196", "#dd5182"];

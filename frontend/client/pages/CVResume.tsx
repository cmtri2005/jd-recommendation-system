import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { FileText, Upload, Loader2, ClipboardList, ChevronDown, ChevronRight, TrendingUp, Target, Award } from "lucide-react";
import { evaluateResume, type EvaluationResponse } from "../../shared/api";
import { SkillGapWithResources } from "../components/LearningResources";

export function CVResume() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [useFileForJob, setUseFileForJob] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const handleResumeUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
      setError(null);
    }
  };

  const handleJobFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setJobFile(file);
    }
  };

  const handleAnalyze = async () => {
    if (!resumeFile) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await evaluateResume(
        resumeFile,
        useFileForJob && jobFile ? jobFile : undefined,
        !useFileForJob ? jobDescription : undefined
      );
      setEvaluation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const getCategoryExplanation = (categoryName: string) => {
    if (!evaluation) return null;

    const categoryKeywords: Record<string, string[]> = {
      'skill': ['skill', 'technical', 'hard skill', 'technology', 'programming'],
      'experience': ['experience', 'work', 'project', 'role', 'position'],
      'years': ['year', 'tenure', 'duration', 'time'],
      'education': ['education', 'degree', 'academic', 'university', 'school'],
      'soft': ['soft', 'communication', 'team', 'leadership', 'collaboration'],
      'extra': ['extra', 'certification', 'cert', 'project', 'award', 'achievement']
    };

    const keywords = categoryKeywords[categoryName] || [categoryName];

    const relevantStrengths = evaluation.strengths.filter(s =>
      keywords.some(kw => s.category.toLowerCase().includes(kw))
    );
    const relevantWeaknesses = evaluation.weaknesses.filter(w =>
      keywords.some(kw => w.category.toLowerCase().includes(kw))
    );

    if (relevantStrengths.length === 0 && relevantWeaknesses.length === 0) {
      return null;
    }

    return (
      <div className="mt-3 ml-1 p-4 bg-muted/40 rounded-md text-sm space-y-2.5 border border-muted">
        {relevantStrengths.map((s, i) => (
          <div key={`str-${i}`} className="flex items-start gap-2.5">
            <span className="text-green-600 font-semibold mt-0.5 text-base">✓</span>
            <span className="text-muted-foreground leading-relaxed">{s.details}</span>
          </div>
        ))}
        {relevantWeaknesses.map((w, i) => (
          <div key={`weak-${i}`} className="flex items-start gap-2.5">
            <span className="text-red-600 font-semibold mt-0.5 text-base">✗</span>
            <span className="text-muted-foreground leading-relaxed">{w.details}</span>
          </div>
        ))}
      </div>
    );
  };

  const ScoreCategory = ({
    name,
    score,
    maxScore,
    color,
    matchKey
  }: {
    name: string;
    score: number;
    maxScore: number;
    color: string;
    matchKey: string;
  }) => {
    const isExpanded = expandedCategories.has(matchKey);
    const explanation = getCategoryExplanation(matchKey);
    const hasExplanation = explanation !== null;
    const percentage = (score / maxScore) * 100;

    return (
      <div className="group">
        <div
          className={`${hasExplanation ? 'cursor-pointer hover:bg-muted/30' : ''} p-2 -mx-2 rounded-md transition-colors`}
          onClick={() => hasExplanation && toggleCategory(matchKey)}
        >
          <div className="flex justify-between items-center mb-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">{name}</span>
              {hasExplanation && (
                isExpanded
                  ? <ChevronDown className="w-4 h-4 text-muted-foreground transition-transform" />
                  : <ChevronRight className="w-4 h-4 text-muted-foreground transition-transform" />
              )}
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-base font-semibold text-foreground">{score}</span>
              <span className="text-sm text-muted-foreground">/ {maxScore}</span>
              <span className="text-xs text-muted-foreground ml-1">({percentage.toFixed(0)}%)</span>
            </div>
          </div>
          <div className="h-2.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full ${color} transition-all duration-500 ease-out`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
        {isExpanded && explanation}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="max-w-6xl mx-auto p-6 space-y-8">
        <div className="text-center space-y-3 py-8">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            AI Job Fit Analysis
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Get AI-powered insights on how well your resume matches the job requirements
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Resume Upload */}
          <Card className="border-2 hover:border-primary/50 transition-all">
            <CardHeader className="space-y-1">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <CardTitle className="text-xl">Your Resume</CardTitle>
              </div>
              <CardDescription>Upload your resume (PDF, DOC, or DOCX)</CardDescription>
            </CardHeader>
            <CardContent>
              <label
                className={`
                  block border-2 border-dashed rounded-xl p-8 
                  transition-all cursor-pointer
                  ${resumeFile
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'
                  }
                `}
              >
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleResumeUpload}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-3 text-center">
                  <Upload className={`w-10 h-10 ${resumeFile ? 'text-primary' : 'text-muted-foreground'}`} />
                  <div>
                    <p className="font-medium text-foreground">
                      {resumeFile ? resumeFile.name : 'Click to upload your resume'}
                    </p>
                    {resumeFile && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {(resumeFile.size / 1024).toFixed(1)} KB
                      </p>
                    )}
                  </div>
                </div>
              </label>
              {resumeFile && (
                <button
                  onClick={() => setResumeFile(null)}
                  className="w-full mt-3 text-sm text-muted-foreground hover:text-destructive transition-colors"
                >
                  Remove file
                </button>
              )}
            </CardContent>
          </Card>

          {/* Job Description */}
          <Card className="border-2 hover:border-primary/50 transition-all">
            <CardHeader className="space-y-1">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-primary" />
                <CardTitle className="text-xl">Job Description</CardTitle>
              </div>
              <CardDescription>Paste text or upload a file</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3 p-1 bg-muted rounded-lg">
                <button
                  onClick={() => setUseFileForJob(false)}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${!useFileForJob
                    ? 'bg-background shadow-sm text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  Paste Text
                </button>
                <button
                  onClick={() => setUseFileForJob(true)}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${useFileForJob
                    ? 'bg-background shadow-sm text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  Upload File
                </button>
              </div>

              {!useFileForJob ? (
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here..."
                  className="w-full min-h-[160px] p-4 rounded-lg border-2 border-input bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                />
              ) : (
                <label className="block border-2 border-dashed border-muted-foreground/25 rounded-xl p-8 hover:border-primary/50 hover:bg-muted/30 transition-all cursor-pointer">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleJobFileUpload}
                    className="hidden"
                  />
                  <div className="flex flex-col items-center gap-3 text-center">
                    <Upload className="w-10 h-10 text-muted-foreground" />
                    <p className="font-medium text-foreground">
                      {jobFile ? jobFile.name : 'Click to upload job description'}
                    </p>
                  </div>
                </label>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Analyze Button */}
        <div className="flex justify-center pt-4">
          <button
            onClick={handleAnalyze}
            disabled={!resumeFile || (!jobDescription && !jobFile) || isLoading}
            className="group relative px-10 py-4 bg-primary text-primary-foreground rounded-xl font-semibold text-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl hover:scale-105 disabled:hover:scale-100 flex items-center gap-3"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Analyze Match
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="border-2">
            <AlertTitle className="font-semibold">Analysis Failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Results */}
        {evaluation && (
          <div className="mt-12 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex items-center justify-between">
              <h2 className="text-3xl font-bold flex items-center gap-2">
                <Award className="w-8 h-8 text-primary" />
                Results
              </h2>
              <button
                onClick={() => {
                  setEvaluation(null);
                  setResumeFile(null);
                  setJobDescription("");
                  setJobFile(null);
                }}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors border px-4 py-2 rounded-lg hover:bg-muted"
              >
                New Analysis
              </button>
            </div>

            {/* Overall Score */}
            <Card className="border-2 shadow-lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">Match Score</CardTitle>
                    <CardDescription className="mt-1">Overall compatibility assessment</CardDescription>
                  </div>
                  <Badge
                    variant={evaluation.recommendation === 'suitable' ? 'default' : 'destructive'}
                    className="text-sm px-3 py-1"
                  >
                    {evaluation.recommendation === 'suitable' ? '✓ Suitable' : '✗ Not Suitable'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div className="text-7xl font-bold text-primary tabular-nums">
                    {evaluation.total_score}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="h-6 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-primary/80 transition-all duration-1000 ease-out"
                        style={{ width: `${evaluation.total_score}%` }}
                      />
                    </div>
                    <p className="text-sm font-medium text-muted-foreground">
                      {evaluation.total_score >= 75 ? "Strong Match - Excellent fit!" :
                        evaluation.total_score >= 60 ? "Good Match - Potential fit" :
                          evaluation.total_score >= 45 ? "Moderate Match - Worth reviewing" : "📈 Needs Improvement"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Summary */}
            <Card className="border-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>Analysis Summary</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <p className="text-base leading-relaxed text-foreground whitespace-pre-line">
                    {evaluation.summary}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recommendation */}
            {evaluation.recommendation_reason && (
              <Card className={`border-2 ${evaluation.recommendation === 'suitable' ? 'border-green-200 bg-green-50/50' : 'border-red-200 bg-red-50/50'}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span>{evaluation.recommendation === 'suitable' ? '✅' : '❌'}</span>
                    <span>Suitability Assessment</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-base leading-relaxed text-foreground">
                    {evaluation.recommendation_reason}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Score Breakdown */}
            <Card className="border-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Detailed Score Breakdown
                </CardTitle>
                <CardDescription>Click categories to see detailed explanations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <ScoreCategory
                  name="Hard Skills"
                  score={evaluation.score_breakdown.hard_skills_score}
                  maxScore={30}
                  color="bg-blue-500"
                  matchKey="skill"
                />
                <ScoreCategory
                  name="Work Experience"
                  score={evaluation.score_breakdown.work_experience_score}
                  maxScore={30}
                  color="bg-green-500"
                  matchKey="experience"
                />
                <ScoreCategory
                  name="Years of Experience"
                  score={evaluation.score_breakdown.years_of_experience_score}
                  maxScore={15}
                  color="bg-purple-500"
                  matchKey="years"
                />
                <ScoreCategory
                  name="Education"
                  score={evaluation.score_breakdown.education_score}
                  maxScore={10}
                  color="bg-yellow-500"
                  matchKey="education"
                />
                <ScoreCategory
                  name="Soft Skills"
                  score={evaluation.score_breakdown.soft_skills_score}
                  maxScore={5}
                  color="bg-pink-500"
                  matchKey="soft"
                />
                <ScoreCategory
                  name="Additional Qualifications"
                  score={evaluation.score_breakdown.extras_score}
                  maxScore={10}
                  color="bg-orange-500"
                  matchKey="extra"
                />
              </CardContent>
            </Card>

            {/* Strengths */}
            {evaluation.strengths.length > 0 && (
              <Card className="border-2 border-green-200">
                <CardHeader>
                  <CardTitle className="text-green-700">💪 Key Strengths</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {evaluation.strengths.map((strength, idx) => (
                    <div key={idx} className="flex gap-3 p-3 bg-green-50 rounded-lg border-l-4 border-green-500">
                      <div className="flex-1">
                        <h4 className="font-semibold text-green-900 mb-1">{strength.category}</h4>
                        <p className="text-sm text-green-800 leading-relaxed">{strength.details}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Weaknesses */}
            {evaluation.weaknesses.length > 0 && (
              <Card className="border-2 border-orange-200">
                <CardHeader>
                  <CardTitle className="text-orange-700">⚡ Areas for Improvement</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {evaluation.weaknesses.map((weakness, idx) => (
                    <div key={idx} className="flex gap-3 p-3 bg-orange-50 rounded-lg border-l-4 border-orange-500">
                      <div className="flex-1">
                        <h4 className="font-semibold text-orange-900 mb-1">{weakness.category}</h4>
                        <p className="text-sm text-orange-800 leading-relaxed">{weakness.details}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Recommended Jobs */}
            {evaluation.retrieved_jobs && evaluation.retrieved_jobs.length > 0 && (
              <Card className="border-2 border-indigo-200 shadow-md bg-gradient-to-br from-indigo-50/50 to-white">
                <CardHeader>
                  <CardTitle className="text-indigo-900 flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Similar Job Opportunities
                  </CardTitle>
                  <CardDescription>
                    Jobs from our database that match your profile
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  {evaluation.retrieved_jobs.map((jobStr, idx) => {
                    // Parse the new hybrid score format
                    const hybridMatch = jobStr.match(/Hybrid Score: ([\d.]+)%/);
                    const vectorMatch = jobStr.match(/Vector: ([\d.]+)%/);
                    const skillsMatch = jobStr.match(/Skills: ([\d.]+)%/);
                    const titleMatch = jobStr.match(/Title: (.*?)\n/);
                    const sourceMatch = jobStr.match(/Source: (.*?)\n/);
                    const matchedSkillsMatch = jobStr.match(/✓ Matched Skills: (.*?)\n/);
                    const missingSkillsMatch = jobStr.match(/✗ Missing Skills: (.*?)\n/);

                    const hybridScore = hybridMatch ? parseFloat(hybridMatch[1]) : 0;
                    const vectorScore = vectorMatch ? parseFloat(vectorMatch[1]) : 0;
                    const skillScore = skillsMatch ? parseFloat(skillsMatch[1]) : 0;
                    const title = titleMatch ? titleMatch[1] : "Unknown Position";
                    const source = sourceMatch ? sourceMatch[1] : "#";
                    const matchedSkills = matchedSkillsMatch ? matchedSkillsMatch[1] : "";
                    const missingSkills = missingSkillsMatch ? missingSkillsMatch[1] : "";

                    return (
                      <div key={idx} className="flex flex-col p-4 bg-white rounded-xl border-2 border-indigo-100 hover:border-indigo-300 hover:shadow-md transition-all group">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1 mr-2">
                            <h4 className="font-bold text-indigo-950 line-clamp-2 leading-tight min-h-[2.5rem]">
                              {title}
                            </h4>
                          </div>
                          <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200 shrink-0">
                            {hybridScore.toFixed(0)}% Match
                          </Badge>
                        </div>

                        {/* Score breakdown */}
                        <div className="mb-3 space-y-2 flex-1">
                          {/* Hybrid score bar */}
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full"
                              style={{ width: `${hybridScore}%` }}
                            />
                          </div>


                          {/* Score details - simplified */}
                          <div className="flex gap-3 text-xs">
                            <span className="text-muted-foreground" title="Semantic similarity">
                              Vector: {vectorScore.toFixed(0)}%
                            </span>
                          </div>

                          {/* Matched skills */}
                          {matchedSkills && (
                            <div className="flex items-start gap-1.5 text-xs">
                              <span className="text-green-700 leading-relaxed">
                                {matchedSkills}
                              </span>
                            </div>
                          )}

                          {/* Missing skills */}
                          {missingSkills && (
                            <div className="flex items-start gap-1.5 text-xs">
                              <span className="text-orange-700 leading-relaxed">
                                Missing: {missingSkills}
                              </span>
                            </div>
                          )}
                        </div>

                        <a
                          href={source}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-auto w-full py-2 px-4 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-100 transition-colors flex items-center justify-center gap-2 group-hover:bg-indigo-600 group-hover:text-white"
                        >
                          View Job Details
                          <ChevronRight className="w-4 h-4" />
                        </a>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}

            {/* Missing Skills */}
            {evaluation.missing_hard_skills.length > 0 && (
              <Card className="border-2 border-blue-200 shadow-md">
                <CardHeader>
                  <CardTitle className="text-blue-900">🎓 Recommended Learning Path</CardTitle>
                  <CardDescription>
                    Verified learning resources from online platforms and UIT courses
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {evaluation.missing_hard_skills.map((skill) => (
                    <SkillGapWithResources
                      key={skill.skill_name}
                      skillName={skill.skill_name}
                      importance={skill.importance}
                      learningResources={skill.learning_resources}
                    />
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

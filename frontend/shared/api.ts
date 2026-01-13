/**
 * Shared code between client and server
 * Useful to share types between client and server
 * and/or small pure JS functions that can be used on both client and server
 */

/**
 * Example response type for /api/demo
 */
export interface DemoResponse {
  message: string;
}

// ==================== JD Recommendation API Types ====================

export interface LearningResource {
  title: string;
  organization: string;
  url: string;
  rating: string;
  difficulty: string;
  type: string;
  verified: boolean;
}

export interface SkillGap {
  skill_name: string;
  importance: 'critical' | 'important' | 'nice-to-have';
  learning_resources: string[];
}

export interface ScoreBreakdown {
  hard_skills_score: number;
  soft_skills_score: number;
  work_experience_score: number;
  years_of_experience_score: number;
  education_score: number;
  extras_score: number;
}

export interface MatchItem {
  category: string;
  details: string;
}

export interface EvaluationResponse {
  total_score: number;
  score_breakdown: ScoreBreakdown;
  strengths: MatchItem[];
  weaknesses: MatchItem[];
  missing_hard_skills: SkillGap[];
  summary: string;
  recommendation: 'suitable' | 'not_suitable';
  recommendation_reason: string;
  retrieved_jobs: string[];
}

export interface KBStats {
  total_courses: number;
  collection_name: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

// ==================== API Client Functions ====================

const API_BASE_URL = typeof window !== 'undefined'
  ? (import.meta.env?.VITE_API_URL || 'http://localhost:8001')
  : 'http://localhost:8001';

export async function evaluateResume(
  resumeFile: File,
  jdFile?: File,
  jdText?: string
): Promise<EvaluationResponse> {
  console.log('DEBUG - evaluateResume called with:', {
    resumeFile,
    jdFile,
    jdText,
    resumeFileName: resumeFile?.name,
    resumeFileSize: resumeFile?.size
  });

  const formData = new FormData();
  formData.append('resume_file', resumeFile);

  if (jdFile) {
    formData.append('jd_file', jdFile);
    console.log('DEBUG - Added jd_file:', jdFile.name);
  } else if (jdText) {
    formData.append('jd_text', jdText);
    console.log('DEBUG - Added jd_text:', jdText.substring(0, 50) + '...');
  }

  console.log('DEBUG - FormData entries:');
  for (const [key, value] of formData.entries()) {
    console.log(`  ${key}:`, value);
  }

  console.log('DEBUG - Sending to:', `${API_BASE_URL}/api/evaluate`);

  const response = await fetch(`${API_BASE_URL}/api/evaluate`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type - browser will set it with boundary
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('API Error:', error);
    throw new Error(`Evaluation failed: ${error}`);
  }

  return response.json();
}

export async function getLearningResources(
  skill: string,
  maxResults: number = 3,
  minRating: number = 4.0
): Promise<LearningResource[]> {
  const params = new URLSearchParams({
    max_results: maxResults.toString(),
    min_rating: minRating.toString(),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/learning-resources/${encodeURIComponent(skill)}?${params}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch learning resources: ${response.statusText}`);
  }

  return response.json();
}

export async function getKBStats(): Promise<KBStats> {
  const response = await fetch(`${API_BASE_URL}/api/kb-stats`);

  if (!response.ok) {
    throw new Error(`Failed to fetch KB stats: ${response.statusText}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

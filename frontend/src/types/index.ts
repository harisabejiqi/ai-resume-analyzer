export interface WorkExperience {
  title: string | null;
  company: string | null;
  start: string | null;
  end: string | null;
  duration_months: number;
  bullets: string[];
}

export interface Analysis {
  name: string | null;
  email: string | null;
  phone: string | null;
  skills: {
    technical: string[];
    soft: string[];
  };
  education: string[];
  experience_years: number;
  work_experience: WorkExperience[];
  sections: string[];
  word_count: number;
}

export interface ScoreBreakdown {
  skills: number;
  education: number;
  experience: number;
  relevance?: number;
}

export interface Score {
  total_score: number;
  match_score: number;
  has_job_description: boolean;
  missing_keywords: string[];
  suggestions: string[];
  breakdown: ScoreBreakdown;
}

export interface SkillMatch {
  matched: string[];
  missing: string[];
  coverage: number | null;
}

export interface JobDescription {
  required_skills: {
    technical: string[];
    soft: string[];
  };
  experience_required: number | null;
  education_required: string[];
  qualifications: string[];
  skill_match: SkillMatch;
}

export interface GrammarIssue {
  type: string;
  message: string;
  text: string;
  suggestions: string[];
  context: string;
}

export interface Grammar {
  available: boolean;
  issue_count: number;
  issues: GrammarIssue[];
}

export interface AnalyzeResponse {
  analysis: Analysis;
  score: Score;
  job_description: JobDescription | null;
  grammar?: Grammar;
}

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

export type CvPart = "experience" | "skills" | "contact" | "language" | "education" | "length";

export interface CvStatistics {
  word_count: number;
  line_count: number;
  sections: string[];
  roles: number;
  bullet_count: number;
  avg_bullets_per_role: number;
  avg_words_per_bullet: number;
  quantified_bullets_pct: number;
  action_verb_bullets_pct: number;
  technical_skills: number;
  soft_skills: number;
  education_entries: number;
  experience_years: number;
}

export interface ReadabilityCheck {
  id: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface CvQuality {
  score: number;
  breakdown: Partial<Record<CvPart, { score: number; weight: number }>>;
  statistics: CvStatistics;
  summary: { sentences: string[]; method: "sbert_centroid" | "fallback" };
  checks: ReadabilityCheck[];
  suggestions: string[];
}

export interface Evidence {
  requirement: string;
  best_chunk: string;
  score: number;
}

export interface JobMatch {
  score: number | null;
  reliability: "normal" | "low" | "insufficient";
  reliability_note: string | null;
  requirement_count: number;
  evidence: Evidence[];
  skill_match: SkillMatch;
  missing_keywords: string[];
  requirements_check: {
    experience: { required: number | null; candidate: number; met: boolean | null };
    education: { required: string[]; resume_has_education: boolean };
  };
  suggestions: string[];
  disclaimer: string;
}

export interface AnalyzeResponse {
  analysis: Analysis;
  grammar: Grammar;
  cv_quality: CvQuality;
  job_description: JobDescription | null;
  job_match: JobMatch | null;
}

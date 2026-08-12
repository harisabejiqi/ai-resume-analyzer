import { useLocation, Navigate, Link } from "react-router-dom";
import type { AnalyzeResponse } from "../types";
import ScoreCard from "./ScoreCard";
import ScoreBreakdown from "./ScoreBreakdown";
import ContactInfo from "./ContactInfo";
import SkillsBadges from "./SkillsBadges";
import EducationList from "./EducationList";
import WorkExperienceList from "./WorkExperienceList";
import Suggestions from "./Suggestions";
import GrammarCheck from "./GrammarCheck";
import MissingKeywords from "./MissingKeywords";
import JobRequirements from "./JobRequirements";
import ScoreCharts from "./charts/ScoreCharts";

export default function ResultDashboard() {
  const location = useLocation();
  const data = location.state as AnalyzeResponse | null;

  if (!data) {
    return <Navigate to="/" replace />;
  }

  const { analysis, score } = data;
  const hasJobDescription = score.has_job_description;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-surface-900">
            Analysis result
          </h1>
          <p className="mt-1 text-sm text-surface-700">
            {analysis.word_count} words · {analysis.skills.technical.length}{" "}
            technical skills detected
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Analyze another
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <aside className="space-y-0 lg:col-span-1">
          <ScoreCard score={score} hasJobDescription={hasJobDescription} />
          <ScoreBreakdown breakdown={score.breakdown} />
        </aside>

        <div className="space-y-6 lg:col-span-2">
          <ScoreCharts score={score} />
          {data.job_description && (
            <JobRequirements
              jd={data.job_description}
              candidateYears={analysis.experience_years}
            />
          )}
          <Suggestions suggestions={score.suggestions} />
          <GrammarCheck grammar={data.grammar} />
          <ContactInfo analysis={analysis} />
          <SkillsBadges
            technical={analysis.skills.technical}
            soft={analysis.skills.soft}
          />
          <EducationList education={analysis.education} />
          <WorkExperienceList workExperience={analysis.work_experience} />
          <MissingKeywords keywords={score.missing_keywords} />
        </div>
      </div>
    </div>
  );
}

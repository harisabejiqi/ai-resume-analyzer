import type { AnalyzeResponse } from "../types";

export interface HistoryEntry {
  id: string;
  createdAt: number;
  fileName: string;
  cvScore?: number;
  jobMatchScore?: number | null;
  totalScore?: number;
  hasJobDescription: boolean;
  data: AnalyzeResponse;
}

export function isLegacy(entry: HistoryEntry): boolean {
  return !entry.data || !(entry.data as Partial<AnalyzeResponse>).cv_quality;
}

const STORAGE_KEY = "resume-analyses";
const MAX_ENTRIES = 50;

function newId() {
  try {
    return crypto.randomUUID();
  } catch {
    return `${Date.now().toString(36)}-${Math.floor(
      Math.random() * 1e9,
    ).toString(36)}`;
  }
}

export function getHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as HistoryEntry[];
  } catch {
    return [];
  }
}

function write(entries: HistoryEntry[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    return;
  }
}

export function addHistory(
  fileName: string,
  data: AnalyzeResponse,
): HistoryEntry {
  const entry: HistoryEntry = {
    id: newId(),
    createdAt: Date.now(),
    fileName,
    cvScore: data.cv_quality.score,
    jobMatchScore: data.job_match ? data.job_match.score : null,
    hasJobDescription: data.job_match !== null,
    data,
  };
  const next = [entry, ...getHistory()].slice(0, MAX_ENTRIES);
  write(next);
  return entry;
}

export function removeHistory(id: string): HistoryEntry[] {
  const next = getHistory().filter((e) => e.id !== id);
  write(next);
  return next;
}

export function clearHistory() {
  write([]);
}

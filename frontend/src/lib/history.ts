import type { AnalyzeResponse } from "../types";

export interface HistoryEntry {
  id: string;
  createdAt: number;
  fileName: string;
  totalScore: number;
  hasJobDescription: boolean;
  data: AnalyzeResponse;
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
    totalScore: data.score.total_score,
    hasJobDescription: data.score.has_job_description,
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

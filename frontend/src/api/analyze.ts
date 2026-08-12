import axios from "axios";
import type { AnalyzeResponse } from "../types";

export async function analyzeResume(
  file: File,
  jobDescription: string,
  onUploadProgress?: (percent: number) => void
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("resume", file);
  formData.append("job_description", jobDescription);

  const response = await axios.post<AnalyzeResponse>("/api/analyze", formData, {
    onUploadProgress: (event) => {
      if (!onUploadProgress) return;
      const total = event.total ?? file.size;
      if (!total) return;
      onUploadProgress(Math.min(100, Math.round((event.loaded / total) * 100)));
    },
  });
  return response.data;
}

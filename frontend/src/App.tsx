import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import UploadForm from "./components/UploadForm";
import ResultDashboard from "./components/ResultDashboard";
import HistoryDashboard from "./components/HistoryDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<UploadForm />} />
          <Route path="/results" element={<ResultDashboard />} />
          <Route path="/dashboard" element={<HistoryDashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

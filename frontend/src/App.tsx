import { Routes, Route } from "react-router-dom";
import Dashboard from "@/pages/Dashboard";
import TodayFocus from "@/pages/TodayFocus";
import MonthlyConsistency from "@/pages/MonthlyConsistency";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/today" element={<TodayFocus />} />
      <Route path="/monthly" element={<MonthlyConsistency />} />
    </Routes>
  );
}

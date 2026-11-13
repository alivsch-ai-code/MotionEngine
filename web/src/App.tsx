import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { PageSkeleton } from "./components/PageSkeleton";
import { AppShell } from "./layouts/AppShell";

// Every page is its own chunk: the landing page does not download the charting or formula code.
const Landing = lazy(() => import("./pages/Landing"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Simulate = lazy(() => import("./pages/Simulate"));
const TrajectoryEditor = lazy(() => import("./pages/TrajectoryEditor"));
const Inspector = lazy(() => import("./pages/Inspector"));
const Predict = lazy(() => import("./pages/Predict"));
const Chat = lazy(() => import("./pages/Chat"));
const Parking = lazy(() => import("./pages/Parking"));
const Workbench = lazy(() => import("./pages/Workbench"));
const Research = lazy(() => import("./pages/Research"));
const Architecture = lazy(() => import("./pages/Architecture"));
const Matlab = lazy(() => import("./pages/Matlab"));
const Knowledge = lazy(() => import("./pages/Knowledge"));
const Vehicles = lazy(() => import("./pages/Vehicles"));
const Models = lazy(() => import("./pages/Models"));
const Settings = lazy(() => import("./pages/Settings"));
const DesignSystem = lazy(() => import("./pages/DesignSystem"));
const NotFound = lazy(() => import("./pages/NotFound"));

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Suspense fallback={null}><Landing /></Suspense>} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="simulate" element={<Simulate />} />
          <Route path="trajectory" element={<TrajectoryEditor />} />
          <Route path="assistant" element={<Chat />} />
          <Route path="inspector" element={<Inspector />} />
          <Route path="parking" element={<Parking />} />
          <Route path="workbench" element={<Workbench />} />
          <Route path="research" element={<Research />} />
          <Route path="architecture" element={<Architecture />} />
          <Route path="matlab" element={<Matlab />} />
          <Route path="knowledge" element={<Knowledge />} />
          <Route path="predict" element={<Predict />} />
          <Route path="vehicles" element={<Vehicles />} />
          <Route path="models" element={<Models />} />
          <Route path="settings" element={<Settings />} />
          <Route path="design" element={<DesignSystem />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<Suspense fallback={<PageSkeleton />}><NotFound /></Suspense>} />
      </Routes>
    </BrowserRouter>
  );
}

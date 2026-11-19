import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import ProtectedRoute from "@/components/ProtectedRoute";

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import CropRecommendation from "@/pages/CropRecommendation";
import DiseaseDetection from "@/pages/DiseaseDetection";
import YieldPrediction from "@/pages/YieldPrediction";
import Logs from "@/pages/Logs";
import RoverControl from "@/pages/RoverControl";
import PlantInspection from "@/pages/PlantInspection";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const protect = (page: JSX.Element) => (
  <ProtectedRoute>{page}</ProtectedRoute>
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />

        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={protect(<Dashboard />)} />
            <Route path="/crop" element={protect(<CropRecommendation />)} />
            <Route path="/disease" element={protect(<DiseaseDetection />)} />
            <Route path="/yield" element={protect(<YieldPrediction />)} />
            <Route path="/inspection" element={protect(<PlantInspection />)} />
            <Route path="/rover" element={protect(<RoverControl />)} />
            <Route path="/logs" element={protect(<Logs />)} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
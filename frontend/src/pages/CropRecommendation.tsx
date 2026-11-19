import { useState } from "react";
import { motion } from "framer-motion";
import { Target, Zap, Activity } from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import {
  api,
  type CropRequest,
  type CropPredictionResponse,
  type YieldPredictionResponse,
} from "@/services/api";

const fields: {
  key: keyof CropRequest;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
}[] = [
  { key: "N", label: "Nitrogen (N)", unit: "kg/ha", min: 0, max: 140, step: 1 },
  { key: "P", label: "Phosphorus (P)", unit: "kg/ha", min: 0, max: 145, step: 1 },
  { key: "K", label: "Potassium (K)", unit: "kg/ha", min: 0, max: 205, step: 1 },
  { key: "temperature", label: "Temperature", unit: "°C", min: 0, max: 50, step: 0.1 },
  { key: "humidity", label: "Humidity", unit: "%", min: 0, max: 100, step: 0.1 },
  { key: "ph", label: "Soil pH", unit: "", min: 0, max: 14, step: 0.1 },
  { key: "rainfall", label: "Rainfall", unit: "mm", min: 0, max: 300, step: 1 },
];

const CropRecommendation = () => {
  const [soilData, setSoilData] = useState<CropRequest>({
    N: 44,
    P: 12,
    K: 18,
    temperature: 26.4,
    humidity: 72,
    ph: 6.8,
    rainfall: 120,
  });

  const [prediction, setPrediction] = useState<CropPredictionResponse | null>(null);
  const [yieldPred, setYieldPred] = useState<YieldPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const HIGH_VALUE_CROPS = [
    "grapes",
    "pomegranate",
    "mango",
    "cotton",
    "coffee",
    "coconut",
    "banana",
    "orange",
    "papaya",
  ];

  const handleChange = (key: keyof CropRequest, value: string) => {
    setSoilData((prev) => ({ ...prev, [key]: parseFloat(value) || 0 }));
  };

  const runPrediction = async () => {
    try {
      setLoading(true);

      const crop = await api.predictCrop(soilData);
      setPrediction(crop);

      const yld = await api.predictYield({
        State_Name: "Maharashtra",
        District_Name: "Pune",
        Crop_Year: 2019,
        Season: "Kharif",
        Crop: crop.recommended_crop,
        Area: 1,
      });
      setYieldPred(yld);
    } catch (error) {
      console.error(error);
      alert("Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const isHighValueCrop =
    prediction && HIGH_VALUE_CROPS.includes(prediction.recommended_crop.trim().toLowerCase());

  return (
    <AppLayout>
      <div className="grid grid-cols-12 gap-4">
        <motion.div
          className="col-span-12"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="ares-label">Module.Crop_Recommendation</h1>
          <p
            className="text-2xl font-bold tracking-tight text-foreground mt-1"
            style={{ letterSpacing: "-0.02em" }}
          >
            SOIL ANALYSIS & PREDICTION ENGINE
          </p>
        </motion.div>

        <motion.div
          className="col-span-12 xl:col-span-7 ares-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.05 }}
        >
          <h3 className="ares-heading mb-6 flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" />
            Soil Parameters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            {fields.map(({ key, label, unit, min, max, step }) => (
              <div key={key}>
                <label className="ares-label">
                  {label} {unit && `(${unit})`}
                </label>
                <input
                  type="number"
                  min={min}
                  max={max}
                  step={step}
                  value={soilData[key]}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="w-full mt-1 px-3 py-2.5 bg-background border border-border font-mono text-sm text-foreground rounded-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors tabular-nums"
                />
              </div>
            ))}
          </div>

          <button
            onClick={runPrediction}
            disabled={loading}
            className="ares-button-primary w-full mt-6 py-3.5 disabled:opacity-50"
          >
            {loading ? "COMPUTING..." : "RUN PREDICTION ENGINE"}
          </button>
        </motion.div>

        <motion.div
          className="col-span-12 xl:col-span-5 space-y-4"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          {prediction ? (
            <>
              <div className="ares-card">
                <h3 className="ares-heading mb-4 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  Recommended Crop
                </h3>

                <p className="text-3xl font-bold text-foreground tracking-tight">
                  {prediction.recommended_crop}
                </p>

                <div className="flex items-center gap-2 mt-2">
                  <div className="w-full bg-muted h-2 rounded-sm overflow-hidden">
                    <motion.div
                      className="h-full bg-primary"
                      initial={{ width: 0 }}
                      animate={{ width: `${prediction.confidence * 100}%` }}
                      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                  <span className="font-mono text-sm text-foreground tabular-nums">
                    {(prediction.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="mt-4 pt-4 border-t border-border space-y-2">
                  <p className="text-sm">
                    <strong>High Value Crop:</strong> {isHighValueCrop ? "Yes" : "No"}
                  </p>
                  <p className="text-sm">
                    <strong>Priority Monitoring:</strong> {isHighValueCrop ? "High" : "Normal"}
                  </p>
                </div>
              </div>

              <div className="ares-card">
                <h3 className="ares-heading mb-3">Alternatives</h3>
                <div className="space-y-2">
                  {prediction.alternatives.map((alt) => (
                    <div key={alt.crop} className="flex items-center justify-between">
                      <span className="font-mono text-sm text-foreground">{alt.crop}</span>
                      <div className="flex items-center gap-2 w-1/2">
                        <div className="w-full bg-muted h-1.5 rounded-sm overflow-hidden">
                          <div
                            className="h-full bg-accent"
                            style={{ width: `${alt.confidence * 100}%` }}
                          />
                        </div>
                        <span className="ares-label tabular-nums w-10 text-right">
                          {(alt.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {yieldPred && (
                <div className="ares-card">
                  <h3 className="ares-heading mb-3 flex items-center gap-2">
                    <Activity className="h-4 w-4 text-accent" />
                    Yield Forecast
                  </h3>
                  <p className="text-2xl font-bold font-mono text-foreground tabular-nums">
                    {yieldPred.predicted_production.toFixed(2)}
                  </p>
                  <p className="ares-label mt-2">Predicted Production</p>
                </div>
              )}
            </>
          ) : (
            <div className="ares-card flex flex-col items-center justify-center min-h-[400px] text-center">
              <Target className="h-10 w-10 text-muted-foreground mb-4" />
              <p className="ares-heading">Awaiting Parameters</p>
              <p className="ares-label mt-2">Configure soil data and run prediction</p>
            </div>
          )}
        </motion.div>
      </div>
    </AppLayout>
  );
};

export default CropRecommendation;
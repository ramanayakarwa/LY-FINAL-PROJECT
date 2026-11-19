
import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import {
  api,
  type DiseasePredictionResponse,
} from "@/services/api";

export default function DiseaseDetection() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const [result, setResult] =
    useState<DiseasePredictionResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selected = event.target.files?.[0] ?? null;

    setFile(selected);
    setResult(null);
    setError("");

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    if (selected) {
      setPreview(URL.createObjectURL(selected));
    } else {
      setPreview(null);
    }
  };

  const analyze = async () => {
    if (!file) {
      setError("Please select a leaf image.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await api.detectDisease(file);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Disease detection failed."
      );
    } finally {
      setLoading(false);
    }
  };

  const healthy =
    result?.health_status?.toLowerCase() === "healthy" ||
    result?.disease?.toLowerCase().includes("healthy");

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="ares-card">
          <h1 className="text-3xl font-bold">
            AI Plant Disease Detection
          </h1>

          <p className="text-muted-foreground mt-2">
            Upload a Tomato or Spinach leaf photograph
            to identify its predicted disease class
            using the trained CNN model.
          </p>

          <p className="text-sm text-amber-600 mt-2">
            This page analyses the image only.
            No dummy ESP32 sensor readings are used.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <section className="ares-card space-y-4">
            <h2 className="text-xl font-semibold">
              Leaf Image
            </h2>

            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              className="block w-full text-sm"
            />

            {preview ? (
              <img
                src={preview}
                alt="Selected leaf"
                className="w-full max-h-[360px] object-contain rounded-lg border"
              />
            ) : (
              <div className="h-64 border-2 border-dashed rounded-lg flex items-center justify-center text-muted-foreground">
                Select a plant leaf image
              </div>
            )}

            <button
              onClick={analyze}
              disabled={!file || loading}
              className="ares-button-primary disabled:opacity-50"
            >
              {loading
                ? "Analysing Leaf..."
                : "Detect Disease"}
            </button>

            {error && (
              <p
                role="alert"
                className="text-red-600 text-sm"
              >
                {error}
              </p>
            )}
          </section>

          <section className="ares-card space-y-4">
            <h2 className="text-xl font-semibold">
              AI Detection Result
            </h2>

            {!result ? (
              <p className="text-muted-foreground">
                Upload and analyse an image to see
                the CNN prediction.
              </p>
            ) : (
              <>
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">
                    Identified Plant
                  </p>

                  <p className="text-2xl font-bold">
                    {result.crop}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">
                    Predicted Disease
                  </p>

                  <p className="text-xl font-semibold">
                    {result.disease}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">
                    Model Confidence
                  </p>

                  <p className="text-2xl font-bold">
                    {(result.confidence * 100).toFixed(2)}%
                  </p>

                  <div className="h-2 rounded-full bg-muted mt-2 overflow-hidden">
                    <div
                      className="h-full bg-green-600"
                      style={{
                        width: `${
                          Math.max(
                            0,
                            Math.min(
                              100,
                              result.confidence * 100
                            )
                          )
                        }%`,
                      }}
                    />
                  </div>

                  <p className="text-xs text-muted-foreground mt-2">
                    Confidence is the model score,
                    not disease severity.
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium">
                    Plant Health Status
                  </p>

                  <p
                    className={
                      healthy
                        ? "text-green-600 font-semibold"
                        : "text-amber-600 font-semibold"
                    }
                  >
                    {result.health_status}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold">
                    Recommended Treatment / Guidance
                  </h3>

                  <p className="text-sm mt-1">
                    {result.treatment}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold">
                    Precautions
                  </h3>

                  {result.precautions.length ? (
                    <ul className="list-disc pl-5 mt-2 space-y-1 text-sm">
                      {result.precautions.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No specific precautions available.
                    </p>
                  )}
                </div>

                <div>
                  <h3 className="font-semibold">
                    Prevention
                  </h3>

                  {result.prevention.length ? (
                    <ul className="list-disc pl-5 mt-2 space-y-1 text-sm">
                      {result.prevention.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No specific prevention guidance available.
                    </p>
                  )}
                </div>

                <div className="border-t pt-4 text-sm text-amber-600">
                  Image classification does not locate
                  an individual affected leaf for robotic
                  gripping or removal. No physical
                  actuator command is issued.
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </AppLayout>
  );
}

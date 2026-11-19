import { useState } from "react";

import { AppLayout } from "@/components/AppLayout";

import {
  api,
  type InspectionResult,
} from "@/services/api";

export default function PlantInspection() {
  const [plantId, setPlantId] = useState("PLANT-001");
  const [images, setImages] = useState<File[]>([]);

  const [result, setResult] =
    useState<InspectionResult | null>(null);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function inspect(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setResult(null);

    if (
      !plantId.trim() ||
      images.length < 1 ||
      images.length > 6
    ) {
      setError(
        "Enter a plant ID and select 1–6 photos."
      );
      return;
    }

    setLoading(true);

    try {
      setResult(
        await api.inspectPlant(
          plantId.trim(),
          images
        )
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Inspection failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout>
      <div className="space-y-5">

        <header className="ares-card">
          <h1 className="text-2xl font-bold">
            Multi-angle Plant Inspection
          </h1>

          <p className="text-sm text-muted-foreground mt-2">
            Upload 1–6 photographs of the same plant
            from different viewpoints.

            The backend compares model classifications;
            it does not locate a leaf for physical gripping.
          </p>
        </header>

        <form
          onSubmit={inspect}
          className="ares-card space-y-4"
        >

          <label className="block text-sm font-semibold">
            Plant ID

            <input
              value={plantId}
              onChange={(e) =>
                setPlantId(e.target.value)
              }
              maxLength={64}
              required
              className="block border rounded px-3 py-2 w-full mt-1 bg-background"
            />
          </label>

          <label className="block text-sm font-semibold">
            Plant photographs (1–6)

            <input
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) =>
                setImages(
                  Array.from(e.target.files ?? [])
                )
              }
              className="block mt-2"
            />
          </label>

          <p className="text-sm">
            Selected: {images.length} image(s)
          </p>

          <button
            type="submit"
            disabled={
              loading ||
              images.length < 1 ||
              images.length > 6
            }
            className="ares-button-primary disabled:opacity-50"
          >
            {loading
              ? "Analysing..."
              : "Analyse plant"}
          </button>

          {error && (
            <p role="alert" className="text-red-600">
              {error}
            </p>
          )}
        </form>

        {result && (
          <div className="space-y-4">

            <section className="ares-card space-y-2">
              <h2 className="font-bold text-lg">
                Inspection Result · {result.plant_id}
              </h2>

              <p>
                <b>Identified crop:</b>{" "}
                {result.consensus.crop}
              </p>

              <p>
                <b>Disease class:</b>{" "}
                {result.consensus.disease}
              </p>

              <p>
                <b>Angle agreement:</b>{" "}
                {(
                  result.consensus.agreement_ratio * 100
                ).toFixed(0)}%
              </p>

              <p>
                <b>Leaf localization:</b> Not available
              </p>

              <p className="text-amber-600 font-semibold">
                Robotic leaf removal is NOT authorized
                from image classification alone.
              </p>
            </section>

            <section className="ares-card space-y-2">
              <h2 className="font-bold">
                Agentic AI Proposal
              </h2>

              <p>
                <b>Priority:</b>{" "}
                {result.decision.priority}
              </p>

              <p>
                <b>Action:</b>{" "}
                {result.decision.action}
              </p>

              <p>
                <b>Reason:</b>{" "}
                {result.decision.reason}
              </p>

              <p className="font-semibold mt-3">
                Precautions:
              </p>

              <ul className="list-disc pl-5 space-y-1">
                {result.decision.precautions.map(
                  (item, i) => (
                    <li key={i}>{item}</li>
                  )
                )}
              </ul>
            </section>

            <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.views.map((view, i) => (
                <div
                  className="ares-card space-y-1"
                  key={i}
                >
                  <h3 className="font-bold">
                    View {i + 1}:{" "}
                    {images[i]?.name ?? "Image"}
                  </h3>

                  <p>Crop: {view.crop}</p>
                  <p>Disease: {view.disease}</p>

                  <p>
                    Confidence:{" "}
                    {(view.confidence * 100).toFixed(1)}%
                  </p>

                  <p>Status: {view.health_status}</p>

                  <p className="text-sm">
                    Advice: {view.treatment}
                  </p>
                </div>
              ))}
            </section>

          </div>
        )}

      </div>
    </AppLayout>
  );
}
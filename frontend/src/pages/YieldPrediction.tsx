
import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import {
  api,
  type YieldRequest,
  type YieldPredictionResponse,
} from "@/services/api";

const initialValues: YieldRequest = {
  State_Name: "Maharashtra",
  District_Name: "Pune",
  Crop_Year: 2020,
  Season: "Kharif",
  Crop: "Tomato",
  Area: 1000,
};

export default function YieldPrediction() {
  const [form, setForm] = useState<YieldRequest>(initialValues);
  const [result, setResult] =
    useState<YieldPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (
    field: keyof YieldRequest,
    value: string
  ) => {
    setForm((previous) => ({
      ...previous,
      [field]:
        field === "Crop_Year" || field === "Area"
          ? Number(value)
          : value,
    }));
    setResult(null);
    setError("");
  };

  const handlePredict = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      if (form.Area <= 0) {
        throw new Error("Area must be greater than zero.");
      }

      const response = await api.predictYield(form);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Production prediction failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="ares-card">
          <h1 className="text-3xl font-bold">
            Crop Production Prediction
          </h1>
          <p className="text-muted-foreground mt-2">
            Predict agricultural crop production using
            your trained XGBoost model.
          </p>
          <p className="text-sm text-amber-600 mt-2">
            Current model supports Tomato only.
            Other crop categories require a compatible
            trained model.
          </p>
        </div>

        <form
          onSubmit={handlePredict}
          className="ares-card space-y-5"
        >
          <h2 className="text-xl font-semibold">
            Production Input Parameters
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(
              [
                ["State_Name", "State"],
                ["District_Name", "District"],
                ["Season", "Season"],
                ["Crop", "Crop"],
              ] as const
            ).map(([field, label]) => (
              <label key={field} className="space-y-2">
                <span className="text-sm font-medium">
                  {label}
                </span>
                <input
                  className="w-full border rounded-lg px-3 py-2 bg-background"
                  value={form[field]}
                  onChange={(e) =>
                    update(field, e.target.value)
                  }
                  required
                />
              </label>
            ))}

            <label className="space-y-2">
              <span className="text-sm font-medium">
                Crop Year
              </span>
              <input
                type="number"
                min={1990}
                max={2100}
                className="w-full border rounded-lg px-3 py-2 bg-background"
                value={form.Crop_Year}
                onChange={(e) =>
                  update("Crop_Year", e.target.value)
                }
                required
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">
                Area (hectares)
              </span>
              <input
                type="number"
                min="0.01"
                step="any"
                className="w-full border rounded-lg px-3 py-2 bg-background"
                value={form.Area}
                onChange={(e) =>
                  update("Area", e.target.value)
                }
                required
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="ares-button-primary disabled:opacity-50"
          >
            {loading
              ? "Predicting..."
              : "Predict Crop Production"}
          </button>

          {error && (
            <p className="text-red-600 text-sm" role="alert">
              {error}
            </p>
          )}
        </form>

        {result && (
          <section className="ares-card space-y-4">
            <h2 className="text-xl font-bold">
              Prediction Result
            </h2>

            <div className="rounded-lg bg-muted p-5">
              <p className="text-sm text-muted-foreground">
                Estimated Total Production
              </p>

              <p className="text-3xl font-bold mt-2">
                {Number(
                  result.predicted_production
                ).toLocaleString("en-IN", {
                  maximumFractionDigits: 2,
                })}{" "}
                tonnes
              </p>
            </div>

            <p>
              <strong>Crop:</strong>{" "}
              {result.input_used.Crop}
            </p>

            <p>
              <strong>Area:</strong>{" "}
              {result.input_used.Area} hectares
            </p>

            <p>
              <strong>Model:</strong>{" "}
              {result.method ?? "XGBoost"}
            </p>

            <p className="text-sm text-muted-foreground">
              This is predicted total production, not
              yield per hectare. It is a model estimate,
              not a measured harvest result.
            </p>
          </section>
        )}
      </div>
    </AppLayout>
  );
}

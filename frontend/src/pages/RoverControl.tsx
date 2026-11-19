import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AppLayout } from "@/components/AppLayout";

import {
  api,
  type RoverActionResponse,
} from "@/services/api";

export default function RoverControl() {
  const [distance, setDistance] = useState(90);
  const [moisture, setMoisture] = useState(25);
  const [plantId, setPlantId] = useState("PLANT-001");

  const [response, setResponse] =
    useState<RoverActionResponse | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const status = useQuery({
    queryKey: ["rover-status"],
    queryFn: api.getRoverStatus,
    refetchInterval: 3000,
    retry: false,
  });

  const telemetry = status.data?.telemetry;

  async function run(
    work: () => Promise<unknown>
  ) {
    setBusy(true);
    setError("");

    try {
      await work();
      await status.refetch();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Request failed"
      );
    } finally {
      setBusy(false);
    }
  }

  async function setSimulationTelemetry() {
    await api.simulateTelemetry({
      temperature: 28,
      humidity: 62,
      soil_moisture: moisture,
      distance_cm: distance,
      battery_percent: 82,
      arm_homed: true,
      pump_off: true,
      obstacle_stop: false,
    });

    setResponse(null);
  }

  async function send(
    action: string,
    parameters: Record<string, unknown> = {}
  ) {
    const result = await api.sendRoverCommand(
      action,
      parameters
    );

    setResponse(result);
  }

  return (
    <AppLayout>
      <div className="space-y-5">

        <header className="ares-card">
          <h1 className="text-2xl font-bold">
            ESP32 Rover Control
          </h1>

          <p className="text-sm text-amber-600 mt-2 font-semibold">
            SIMULATION ONLY — no real motor, pump or
            robotic arm command is transmitted.
          </p>

          <p className="mt-2 text-sm">
            Source: {telemetry?.source ?? "NONE"} ·
            Fresh: {telemetry?.fresh ? "Yes" : "No"} ·
            Hardware: NOT COMMISSIONED
          </p>

          {status.isError && (
            <p className="text-red-600">
              Rover API unavailable.
            </p>
          )}
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          <section className="ares-card space-y-4">
            <h2 className="font-bold text-lg">
              1. Simulated ESP32 Sensors
            </h2>

            <label className="block text-sm">
              Obstacle distance (cm)

              <input
                type="number"
                min="0"
                value={distance}
                onChange={(e) =>
                  setDistance(Number(e.target.value))
                }
                className="block w-full border rounded px-3 py-2 mt-1 bg-background"
              />
            </label>

            <label className="block text-sm">
              Soil moisture (%)

              <input
                type="number"
                min="0"
                max="100"
                value={moisture}
                onChange={(e) =>
                  setMoisture(Number(e.target.value))
                }
                className="block w-full border rounded px-3 py-2 mt-1 bg-background"
              />
            </label>

            <button
              disabled={busy}
              onClick={() => run(setSimulationTelemetry)}
              className="ares-button-primary disabled:opacity-50"
            >
              Send simulated telemetry
            </button>

            <p className="text-xs text-muted-foreground">
              Set 90 cm to test ALLOW.
              Set 5 cm to test obstacle HALT.
              Send telemetry again before each command
              if it becomes stale.
            </p>
          </section>

          <section className="ares-card space-y-4">
            <h2 className="font-bold text-lg">
              2. Software Command Gate
            </h2>

            <p className="text-sm">
              Current obstacle:{" "}
              {telemetry?.fresh
                ? `${telemetry.data.distance_cm ?? "Unknown"} cm`
                : "No fresh telemetry"}
            </p>

            <div className="flex flex-wrap gap-2">

              <button
                disabled={busy}
                onClick={() =>
                  run(() =>
                    send("MOVE_FORWARD", {
                      speed_percent: 20,
                      duration_s: 1,
                    })
                  )
                }
                className="ares-button-primary disabled:opacity-50"
              >
                Move forward (test)
              </button>

              <button
                disabled={busy}
                onClick={() =>
                  run(() => send("STOP"))
                }
                className="border px-4 py-2 rounded font-semibold disabled:opacity-50"
              >
                STOP (test)
              </button>

            </div>

            <label className="block text-sm">
              Plant ID

              <input
                value={plantId}
                onChange={(e) =>
                  setPlantId(e.target.value)
                }
                className="block w-full border rounded px-3 py-2 mt-1 bg-background"
              />
            </label>

            <button
              disabled={busy || !plantId.trim()}
              onClick={() =>
                run(() =>
                  send("WATER_PLANT", {
                    plant_id: plantId.trim(),
                    duration_s: 1,
                    manual_confirmed: true,
                    target_verified: true,
                  })
                )
              }
              className="border px-4 py-2 rounded font-semibold disabled:opacity-50"
            >
              Test watering gate
            </button>

            <p className="text-xs text-muted-foreground">
              Watering confirmation and target verification
              here are operator-entered simulation flags,
              not proof of camera localization or real watering.
            </p>
          </section>

        </div>

        {error && (
          <p className="text-red-600" role="alert">
            {error}
          </p>
        )}

        {response && (
          <section className="ares-card space-y-2">
            <h2 className="font-bold text-lg">
              3. Command Result
            </h2>

            <p>
              <b>Security:</b>{" "}
              {response.security.security_status}
            </p>

            <p>
              <b>Gate:</b>{" "}
              {response.action_gate.decision}
            </p>

            <p>
              <b>Reason:</b>{" "}
              {response.action_gate.reason}
            </p>

            <p>
              <b>Execution:</b>{" "}
              {response.hardware.execution}{" "}
              ({response.hardware.mode})
            </p>

            {response.action_gate.alerts.map(
              (alert, i) => (
                <p
                  key={i}
                  className="text-red-600"
                >
                  {alert}
                </p>
              )
            )}
          </section>
        )}

      </div>
    </AppLayout>
  );
}
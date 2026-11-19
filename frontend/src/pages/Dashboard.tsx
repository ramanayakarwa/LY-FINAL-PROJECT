
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AppLayout } from "@/components/AppLayout";
import {
  api,
  type DiseasePredictionResponse,
  type SensorValues,
} from "@/services/api";

const reading = (
  value: number | undefined | null,
  unit = ""
) =>
  value === undefined || value === null
    ? "Not available"
    : `${value}${unit}`;

const errorMessage = (error: unknown): string =>
  error instanceof Error
    ? error.message
    : "An unexpected error occurred";

export default function Dashboard() {
  // =====================================
  // 1. COMPONENT STATE
  // =====================================

  const [cameraImageUrl, setCameraImageUrl] =
    useState<string | null>(null);

  const [capturedImage, setCapturedImage] =
    useState<Blob | null>(null);

  const [cameraLoading, setCameraLoading] =
    useState(false);

  const [cameraError, setCameraError] =
    useState<string | null>(null);

  const [diseaseLoading, setDiseaseLoading] =
    useState(false);

  const [diseaseError, setDiseaseError] =
    useState<string | null>(null);

  const [diseaseResult, setDiseaseResult] =
    useState<DiseasePredictionResponse | null>(
      null
    );

  // =====================================
  // 2. SYSTEM STATUS
  // =====================================

  const systemQuery = useQuery({
    queryKey: ["system"],
    queryFn: api.getSystemStatus,
    refetchInterval: 2000,
    retry: false,
  });

  // =====================================
  // 3. MQTT + COAP STATUS
  // =====================================

  const protocolsQuery = useQuery({
    queryKey: ["ares-protocols"],
    queryFn: api.getProtocolsStatus,
    refetchInterval: 2000,
    retry: false,
  });

  // =====================================
  // 4. CAMERA STATUS
  // =====================================

  const cameraQuery = useQuery({
    queryKey: ["ares-camera-status"],
    queryFn: api.getCameraStatus,
    refetchInterval: 5000,
    retry: false,
  });

  // =====================================
  // 5. RECENT LOGS
  // =====================================

  const logsQuery = useQuery({
    queryKey: ["dashboard-logs"],
    queryFn: () => api.getRecentLogs(20),
    refetchInterval: 4000,
    retry: false,
  });

  // =====================================
  // 6. TELEMETRY
  // =====================================

  const sys = systemQuery.data;

  const protocols = protocolsQuery.data;

  // Prefer the dedicated protocol endpoint
  // for a consistent telemetry + protocol view.
  const telemetry = protocols?.telemetry ??
    sys?.telemetry;

  const mqtt = protocols?.mqtt;
  const coap = protocols?.coap;

  const actualLive = Boolean(
    !protocolsQuery.isError &&
    protocols?.live_verified_telemetry &&
    telemetry?.fresh &&
    telemetry?.verified &&
    (
      telemetry.source === "MQTT_VERIFIED" ||
      telemetry.source === "COAP_SIGNED"
    )
  );

  const simulated = Boolean(
    telemetry?.fresh &&
    telemetry?.source === "SIMULATION"
  );

  const sensor: SensorValues =
    telemetry?.fresh
      ? telemetry.data
      : {};

  const backendOffline =
    systemQuery.isError &&
    protocolsQuery.isError;

  const status = backendOffline
    ? "BACKEND OFFLINE"
    : actualLive
      ? telemetry?.source === "MQTT_VERIFIED"
        ? "LIVE ESP32 · MQTT"
        : "LIVE ESP32 · CoAP SIGNED"
      : simulated
        ? "SIMULATION — NOT REAL SENSORS"
        : telemetry?.received_at
          ? "STALE SENSOR DATA"
          : "WAITING FOR ESP32";

  const dataCards = [
    [
      "Temperature",
      reading(sensor.temperature, " °C"),
    ],
    [
      "Humidity",
      reading(sensor.humidity, " %"),
    ],
    [
      "Soil moisture",
      reading(sensor.soil_moisture, " %"),
    ],
    [
      "Obstacle distance",
      reading(sensor.distance_cm, " cm"),
    ],
    [
      "Light sensor",
      reading(sensor.light),
    ],
    [
      "Battery",
      reading(sensor.battery_percent, " %"),
    ],
  ];

  const gpsAvailable =
    typeof sensor.gps_lat_e6 === "number" &&
    typeof sensor.gps_lon_e6 === "number";

  // =====================================
  // 7. AGENT AND SECURITY LOGS
  // =====================================

  const logs = logsQuery.data?.logs ?? [];

  const latestAgent = [...logs]
    .reverse()
    .find((entry) => entry.decision?.action);

  const latestGate = [...logs]
    .reverse()
    .find(
      (entry) =>
        entry.action_gate?.decision
    );

  const latestSecurity = [...logs]
    .reverse()
    .find(
      (entry) =>
        entry.security?.security_status
    );

  // =====================================
  // 8. CAMERA STATUS
  // =====================================

  const cameraConnected = Boolean(
    !cameraQuery.isError &&
    cameraQuery.data?.connected
  );

  const cameraConfigured = Boolean(
    cameraQuery.data?.configured
  );

  // =====================================
  // 9. CAMERA IMAGE CLEANUP
  // =====================================

  useEffect(() => {
    return () => {
      if (cameraImageUrl) {
        URL.revokeObjectURL(
          cameraImageUrl
        );
      }
    };
  }, [cameraImageUrl]);

  // =====================================
  // 10. CAPTURE REAL CAMERA IMAGE
  // =====================================

  const captureImage = async () => {
    setCameraLoading(true);
    setCameraError(null);
    setDiseaseResult(null);
    setDiseaseError(null);

    try {
      const blob =
        await api.captureCameraImage();

      if (
        !blob.type.includes("image/jpeg")
      ) {
        throw new Error(
          "ESP32-CAM did not return JPEG"
        );
      }

      const imageUrl =
        URL.createObjectURL(blob);

      setCapturedImage(blob);

      setCameraImageUrl(imageUrl);

    } catch (error) {
      setCameraError(
        errorMessage(error)
      );

    } finally {
      setCameraLoading(false);
    }
  };

  // =====================================
  // 11. CAMERA IMAGE -> AI MODEL
  // =====================================

  const analyzeCameraImage = async () => {
    if (!capturedImage) {
      setDiseaseError(
        "Capture a real ESP32-CAM image first"
      );
      return;
    }

    setDiseaseLoading(true);
    setDiseaseError(null);
    setDiseaseResult(null);

    try {
      const file = new File(
        [capturedImage],
        `ares-plant-${Date.now()}.jpg`,
        {
          type: "image/jpeg",
        }
      );

      const result =
        await api.detectDisease(file);

      setDiseaseResult(result);

    } catch (error) {
      setDiseaseError(
        errorMessage(error)
      );

    } finally {
      setDiseaseLoading(false);
    }
  };

  // =====================================
  // 12. DASHBOARD UI
  // =====================================

  return (
    <AppLayout>
      <div className="space-y-5">

        {/* ========================= */}
        {/* MISSION STATUS */}
        {/* ========================= */}

        <section className="ares-card space-y-2">
          <h1 className="text-2xl font-bold">
            ARES Mission Dashboard
          </h1>

          <p className="text-sm text-muted-foreground">
            Six-wheel ESP32 agricultural rover
          </p>

          <p
            className={
              actualLive
                ? "font-semibold text-green-600"
                : "font-semibold text-amber-600"
            }
          >
            {status}
          </p>

          <p className="text-sm">
            Source:{" "}
            {telemetry?.source ?? "NONE"}
            {" · "}
            Device:{" "}
            {telemetry?.device_id ??
              "Not detected"}
          </p>

          <p className="text-sm">
            Last packet age:{" "}
            {telemetry?.age_seconds == null
              ? "Unknown"
              : `${telemetry.age_seconds} seconds`}
          </p>

          <p className="text-xs text-muted-foreground">
            Only fresh measurements are displayed.
            Physical motors, robotic arm and pump
            are not commissioned.
          </p>
        </section>

        {/* ========================= */}
        {/* PROTOCOL MONITORING */}
        {/* ========================= */}

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">

          <div className="ares-card space-y-2">
            <h2 className="font-bold text-lg">
              MQTT · Primary Telemetry
            </h2>

            <p>
              Service:{" "}
              {mqtt?.enabled
                ? "ENABLED"
                : "DISABLED"}
            </p>

            <p>
              Broker:{" "}
              {mqtt?.connected
                ? "CONNECTED"
                : "DISCONNECTED"}
            </p>

            <p>
              Verified packets:{" "}
              {mqtt?.verified_count ?? 0}
            </p>

            <p>
              Rejected packets:{" "}
              {mqtt?.rejected_count ?? 0}
            </p>

            <p>
              Fresh MQTT telemetry:{" "}
              {actualLive &&
              telemetry?.source === "MQTT_VERIFIED"
                ? "YES"
                : "NO"}
            </p>

            <p className="text-xs text-muted-foreground">
              MQTT TLS broker connection and
              HMAC-signed telemetry payloads.
            </p>
          </div>

          <div className="ares-card space-y-2">
            <h2 className="font-bold text-lg">
              CoAP · Secondary Telemetry
            </h2>

            <p>
              Service:{" "}
              {coap?.running
                ? "LISTENING"
                : "NOT RUNNING"}
            </p>

            <p>
              HMAC-accepted recent packet:{" "}
              {coap?.recent &&
              coap?.verified_hmac
                ? "YES"
                : "NO"}
            </p>

            <p>
              Verified packets:{" "}
              {coap?.verified_count ?? 0}
            </p>

            <p>
              Rejected packets:{" "}
              {coap?.rejected_count ?? 0}
            </p>

            <p>
              Last received:{" "}
              {coap?.age_seconds == null
                ? "Never"
                : `${coap.age_seconds} sec ago`}
            </p>

            <p className="text-xs text-amber-600">
              CoAP uses unencrypted UDP on a
              trusted LAN. HMAC protects message
              integrity, not confidentiality.
            </p>
          </div>
        </section>

        {protocolsQuery.isError && (
          <section className="ares-card">
            <p className="text-sm text-red-600">
              Protocol monitoring unavailable:{" "}
              {errorMessage(
                protocolsQuery.error
              )}
            </p>
          </section>
        )}

        {/* ========================= */}
        {/* SENSOR READINGS */}
        {/* ========================= */}

        <section className="space-y-3">
          <h2 className="text-xl font-bold">
            Field Sensor Readings
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {dataCards.map(
              ([label, value]) => (
                <div
                  key={label}
                  className="ares-card"
                >
                  <p className="text-sm text-muted-foreground">
                    {label}
                  </p>

                  <p className="text-xl font-bold mt-2">
                    {value}
                  </p>

                  <p className="text-xs text-muted-foreground mt-1">
                    {actualLive
                      ? "Verified ESP32 packet"
                      : simulated
                        ? "Simulated value"
                        : "No fresh data"}
                  </p>
                </div>
              )
            )}
          </div>

          <p className="text-xs text-muted-foreground">
            Soil moisture requires calibration.
            Missing light or battery sensors
            are not assigned invented values.
          </p>
        </section>

        {/* ========================= */}
        {/* GPS */}
        {/* ========================= */}

        <section className="ares-card">
          <h2 className="font-bold text-lg">
            GPS · Rover Location
          </h2>

          {gpsAvailable ? (
            <div className="text-sm mt-2 space-y-1">
              <p>
                Latitude:{" "}
                {(
                  sensor.gps_lat_e6! /
                  1_000_000
                ).toFixed(6)}
                °
              </p>

              <p>
                Longitude:{" "}
                {(
                  sensor.gps_lon_e6! /
                  1_000_000
                ).toFixed(6)}
                °
              </p>

              <p>
                Satellites:{" "}
                {reading(
                  sensor.gps_satellites
                )}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground mt-2">
              No current GPS coordinates available.
            </p>
          )}
        </section>

        {/* ========================= */}
        {/* ESP32-CAM */}
        {/* ========================= */}

        <section className="ares-card space-y-4">

          <div>
            <h2 className="text-xl font-bold">
              ESP32-CAM · Plant Vision
            </h2>

            <p className="text-sm text-muted-foreground mt-1">
              OV2640 camera over local Wi-Fi.
              Images come only from real hardware.
            </p>
          </div>

          <div className="space-y-1 text-sm">
            <p>
              Configuration:{" "}
              {cameraConfigured
                ? "CONFIGURED"
                : "NOT CONFIGURED"}
            </p>

            <p
              className={
                cameraConnected
                  ? "font-semibold text-green-600"
                  : "font-semibold text-amber-600"
              }
            >
              Connection:{" "}
              {cameraConnected
                ? "CONNECTED"
                : "OFFLINE"}
            </p>
          </div>

          <div className="rounded-xl border border-border bg-muted/30 p-4">

            {cameraImageUrl ? (
              <img
                src={cameraImageUrl}
                alt="Real ESP32-CAM plant capture"
                className="w-full max-h-[400px] object-contain rounded-lg"
              />
            ) : (
              <div className="min-h-[220px] flex items-center justify-center text-center">
                <p className="text-sm text-muted-foreground">
                  No real camera image captured.
                  <br />
                  Connect ESP32-CAM to preview
                  actual plant images.
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-3">

            <button
              type="button"
              onClick={captureImage}
              disabled={
                !cameraConnected ||
                cameraLoading
              }
              className="rounded-lg bg-primary px-4 py-2 text-primary-foreground font-medium disabled:opacity-50"
            >
              {cameraLoading
                ? "Capturing..."
                : "Capture Real Image"}
            </button>

            <button
              type="button"
              onClick={analyzeCameraImage}
              disabled={
                !capturedImage ||
                diseaseLoading
              }
              className="rounded-lg border border-border px-4 py-2 font-medium disabled:opacity-50"
            >
              {diseaseLoading
                ? "Analyzing..."
                : "Analyze Plant Disease"}
            </button>

          </div>

          {cameraError && (
            <p className="text-sm text-red-600">
              Camera error: {cameraError}
            </p>
          )}

          {cameraQuery.isError && (
            <p className="text-sm text-red-600">
              Camera status API unavailable:{" "}
              {errorMessage(
                cameraQuery.error
              )}
            </p>
          )}

          {diseaseError && (
            <p className="text-sm text-red-600">
              Disease analysis error:{" "}
              {diseaseError}
            </p>
          )}

          {/* ===================== */}
          {/* DISEASE RESULT */}
          {/* ===================== */}

          {diseaseResult && (
            <div className="rounded-xl border border-border p-4 space-y-2">

              <h3 className="font-bold text-lg">
                AI Disease Detection Result
              </h3>

              <p>
                Crop:{" "}
                <strong>
                  {diseaseResult.crop}
                </strong>
              </p>

              <p>
                Disease:{" "}
                <strong>
                  {diseaseResult.disease}
                </strong>
              </p>

              <p>
                Confidence:{" "}
                {(
                  diseaseResult.confidence *
                  100
                ).toFixed(2)}
                %
              </p>

              <p>
                Health status:{" "}
                {diseaseResult.health_status}
              </p>

              <p>
                Treatment:{" "}
                {diseaseResult.treatment}
              </p>

              {diseaseResult.precautions.length > 0 && (
                <div>
                  <p className="font-semibold">
                    Precautions
                  </p>

                  <ul className="list-disc pl-5 text-sm">
                    {diseaseResult.precautions.map(
                      (item, index) => (
                        <li key={index}>
                          {item}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}

              {diseaseResult.prevention.length > 0 && (
                <div>
                  <p className="font-semibold">
                    Prevention
                  </p>

                  <ul className="list-disc pl-5 text-sm">
                    {diseaseResult.prevention.map(
                      (item, index) => (
                        <li key={index}>
                          {item}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}

              <p className="text-xs text-muted-foreground">
                AI output is advisory only.
                No robotic removal, spraying
                or physical action is triggered.
              </p>

            </div>
          )}

        </section>

        {/* ========================= */}
        {/* AGENT AND SECURITY */}
        {/* ========================= */}

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          <div className="ares-card space-y-2">
            <h2 className="text-lg font-bold">
              Rule-Based Agent
            </h2>

            <p>
              Proposed action:{" "}
              {latestAgent?.decision?.action ??
                "None"}
            </p>

            <p>
              Priority:{" "}
              {latestAgent?.decision?.priority ??
                "—"}
            </p>

            <p>
              Reason:{" "}
              {latestAgent?.decision?.reason ??
                "—"}
            </p>

            <p className="text-xs text-muted-foreground">
              Proposals only, not physical actions.
            </p>
          </div>

          <div className="ares-card space-y-2">
            <h2 className="text-lg font-bold">
              Security and Action Gate
            </h2>

            <p>
              Latest sensor check:{" "}
              {latestSecurity?.security?.security_status ??
                "Not evaluated"}
            </p>

            <p>
              Last command gate:{" "}
              {latestGate?.action_gate?.decision ??
                "Not requested"}
            </p>

            <p className="text-xs text-muted-foreground">
              Historical gate results are not
              a current emergency-stop state.
            </p>
          </div>

        </section>

      </div>
    </AppLayout>
  );
}

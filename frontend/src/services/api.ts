
import { auth } from "@/lib/auth";

const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

// =====================================
// CROP
// =====================================

export interface CropRequest {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export interface CropAlternative {
  crop: string;
  confidence: number;
}

export interface CropPredictionResponse {
  recommended_crop: string;
  confidence: number;
  alternatives: CropAlternative[];
}

// =====================================
// PRODUCTION / YIELD
// =====================================

export interface YieldRequest {
  State_Name: string;
  District_Name: string;
  Crop_Year: number;
  Season: string;
  Crop: string;
  Area: number;
}

export interface YieldPredictionResponse {
  predicted_production: number;
  input_used: YieldRequest;
  method?: string;
  unit?: string;
}

// =====================================
// DISEASE DETECTION
// =====================================

export interface DiseasePredictionResponse {
  crop: string;
  disease: string;
  raw_label?: string;
  confidence: number;
  health_status: string;
  treatment: string;
  precautions: string[];
  prevention: string[];
  target_localized?: boolean;
}

// =====================================
// AGENTIC AI
// =====================================

export interface AgentDecision {
  priority: string;
  action: string;
  reason: string;
  precautions: string[];
  requires_gate?: boolean;
  execution_status?: string;
  agent_type?: string;
}

// =====================================
// CYBERSECURITY
// =====================================

export interface SecurityResult {
  security_status: string;
  decision: string;
  alerts: string[];
  checks: Record<string, string>;
  scope?: string;
}

// =====================================
// ESP32 SENSOR TELEMETRY
// =====================================

export interface SensorValues {
  temperature?: number;
  humidity?: number;
  soil_moisture?: number;
  light?: number;
  distance_cm?: number;
  battery_percent?: number;
  arm_homed?: boolean;
  pump_off?: boolean;
  obstacle_stop?: boolean;

  gps_lat_e6?: number;
  gps_lon_e6?: number;
  gps_satellites?: number;
}

export interface TelemetryState {
  data: SensorValues;
  source: string;
  received_at: number | null;
  device_id: string | null;
  verified: boolean;
  last_sequence: number | null;
  age_seconds: number | null;
  fresh: boolean;
}

// =====================================
// ROVER
// =====================================

export interface RoverStatus {
  telemetry: TelemetryState;

  last_action: Record<string, unknown>;

  mqtt: {
    enabled: boolean;
    connected: boolean;
    topic?: string;
  };

  mode: string;
  hardware_commissioned: boolean;
}

export interface RoverActionResponse {
  command_id: string;

  security: SecurityResult;

  action_gate: {
    decision: string;
    action: string;
    reason: string;
    alerts: string[];
  };

  hardware: {
    action: string;
    execution: string;
    mode: string;
    parameters?: Record<string, unknown>;
  };
}

// =====================================
// SYSTEM
// =====================================

export interface SystemStatusResponse {
  unit_name: string;
  status: string;
  mode: string;

  battery?: number | null;
  temperature?: number | null;
  humidity?: number | null;
  soil_moisture?: number | null;
  active_command?: string | null;

  telemetry: TelemetryState;

  mqtt: {
    enabled: boolean;
    connected: boolean;
  };

  last_action: Record<string, unknown>;

  live_hardware_commissioned: boolean;
}

// =====================================
// COMBINED PREDICTION
// =====================================

export interface FullPredictionResponse {
  final_crop: string;
  observed_crop: string;
  recommended_crop: string;

  crop_recommendation: CropPredictionResponse;
  disease: DiseasePredictionResponse;

  yield: {
    predicted_production: number | null;
    method: string;
    unit?: string;
    reason?: string;
  };

  sensor: SensorValues;
  sensor_source: string;

  security: SecurityResult;
  decision: AgentDecision;

  action_gate: {
    decision: string;
    reason: string;
  };
}

// =====================================
// MULTI-ANGLE INSPECTION
// =====================================

export interface InspectionResult {
  plant_id: string;

  views: DiseasePredictionResponse[];

  consensus: {
    crop: string;
    disease: string;
    agreement_ratio: number;
    consistent: boolean;
  };

  leaf_target_localized: boolean;
  robotic_removal_allowed: boolean;

  decision: AgentDecision;
}

// =====================================
// LOGS
// =====================================

export interface LogItem {
  timestamp?: string;
  source?: string;
  final_crop?: string;
  plant_id?: string;
  command_action?: string;

  disease?: Partial<DiseasePredictionResponse>;

  yield?: {
    predicted_production?: number | null;
    method?: string;
  };

  decision?: Partial<AgentDecision>;
  security?: Partial<SecurityResult>;

  action_gate?: {
    decision?: string;
    reason?: string;
  };

  hardware?: {
    execution?: string;
  };
}

export interface RecentLogsResponse {
  logs: LogItem[];
}

// =====================================
// MQTT PROTOCOL STATUS
// =====================================

export interface MqttStatus {
  enabled: boolean;
  connected: boolean;
  topic: string;

  received_count: number;
  verified_count: number;
  rejected_count: number;

  last_message_at: number | null;
  last_verified_at: number | null;
  last_verified_age_seconds: number | null;

  last_error: string | null;
}

// =====================================
// COAP PROTOCOL STATUS
// =====================================

export interface CoapStatus {
  enabled: boolean;
  running: boolean;
  recent: boolean;
  verified_hmac: boolean;

  received_count: number;
  verified_count: number;
  rejected_count: number;

  last_received_at: number | null;
  last_device_id: string | null;
  last_sequence: number | null;

  age_seconds: number | null;
  last_error: string | null;

  transport_encrypted: boolean;
  warning: string;
}

// =====================================
// COMBINED PROTOCOL STATUS
// =====================================

export interface ProtocolStatusResponse {
  mqtt: MqttStatus;
  coap: CoapStatus;

  telemetry: TelemetryState;
  telemetry_source: string;

  live_verified_telemetry: boolean;

  hardware_commissioned: boolean;
  physical_actuation_enabled: boolean;
}

export interface ProtocolTelemetryResponse {
  telemetry: TelemetryState;
  source: string;
  fresh: boolean;
  verified: boolean;
  live_verified: boolean;
}

// =====================================
// ESP32-CAM STATUS
// =====================================

export interface CameraStatusResponse {
  configured: boolean;
  connected: boolean;
  camera: string;

  source:
    | "REAL_HARDWARE"
    | "REAL_HARDWARE_ONLY";

  message?: string;

  device_status?: Record<
    string,
    unknown
  >;
}

// =====================================
// CENTRAL REQUEST HELPER
// =====================================

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(
    options.headers
  );

  const token = auth.token();

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  if (
    options.body &&
    !(options.body instanceof FormData)
  ) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  if (!response.ok) {
    let message =
      `Request failed: ${response.status}`;

    try {
      const errorData =
        await response.json();

      if (
        typeof errorData.detail ===
        "string"
      ) {
        message = errorData.detail;
      }
    } catch {
      // Keep HTTP error message.
    }

    if (response.status === 401) {
      auth.logout();
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

// =====================================
// AUTHENTICATED IMAGE FETCH HELPER
// =====================================

async function requestImage(
  path: string
): Promise<Blob> {
  const headers = new Headers();

  const token = auth.token();

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${BASE_URL}${path}`,
    {
      method: "GET",
      headers,
      cache: "no-store",
    }
  );

  if (!response.ok) {
    let message =
      `Camera request failed: ${response.status}`;

    try {
      const errorData =
        await response.json();

      if (
        typeof errorData.detail ===
        "string"
      ) {
        message = errorData.detail;
      }
    } catch {
      // Keep HTTP error message.
    }

    if (response.status === 401) {
      auth.logout();
    }

    throw new Error(message);
  }

  const contentType =
    response.headers.get("content-type") ||
    "";

  if (
    !contentType
      .toLowerCase()
      .includes("image/jpeg")
  ) {
    throw new Error(
      "Camera did not return a JPEG image"
    );
  }

  return response.blob();
}

// =====================================
// API FUNCTIONS
// =====================================

export const api = {

  // ---------------------------------
  // CROP RECOMMENDATION
  // ---------------------------------

  predictCrop(data: CropRequest) {
    return request<CropPredictionResponse>(
      "/predict/crop",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  // ---------------------------------
  // YIELD PREDICTION
  // ---------------------------------

  predictYield(data: YieldRequest) {
    return request<YieldPredictionResponse>(
      "/predict/yield",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  // ---------------------------------
  // DISEASE DETECTION
  // ---------------------------------

  detectDisease(file: File) {
    const form = new FormData();

    form.append("file", file);

    return request<DiseasePredictionResponse>(
      "/predict/disease",
      {
        method: "POST",
        body: form,
      }
    );
  },

  // ---------------------------------
  // COMPLETE AGRICULTURE ANALYSIS
  // ---------------------------------

  predictAll(form: FormData) {
    return request<FullPredictionResponse>(
      "/predict/all",
      {
        method: "POST",
        body: form,
      }
    );
  },

  // ---------------------------------
  // MULTI-ANGLE PLANT INSPECTION
  // ---------------------------------

  inspectPlant(
    plantId: string,
    images: File[]
  ) {
    const form = new FormData();

    form.append(
      "plant_id",
      plantId
    );

    images.forEach((image) => {
      form.append(
        "images",
        image
      );
    });

    return request<InspectionResult>(
      "/inspection/analyze",
      {
        method: "POST",
        body: form,
      }
    );
  },

  // ---------------------------------
  // SYSTEM STATUS
  // ---------------------------------

  getSystemStatus() {
    return request<SystemStatusResponse>(
      "/system/status"
    );
  },

  // ---------------------------------
  // SENSOR TELEMETRY
  // ---------------------------------

  getTelemetry() {
    return request<TelemetryState>(
      "/sensor/latest"
    );
  },

  // ---------------------------------
  // ROVER STATUS
  // ---------------------------------

  getRoverStatus() {
    return request<RoverStatus>(
      "/rover/status"
    );
  },

  // ---------------------------------
  // SIMULATED SENSOR DATA
  // ---------------------------------

  simulateTelemetry(
    data: SensorValues
  ) {
    return request<TelemetryState>(
      "/rover/simulation/telemetry",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  // ---------------------------------
  // ROVER COMMAND
  // ---------------------------------

  sendRoverCommand(
    action: string,
    parameters:
      Record<string, unknown> = {}
  ) {
    return request<RoverActionResponse>(
      "/rover/command",
      {
        method: "POST",
        body: JSON.stringify({
          command_id:
            crypto.randomUUID(),

          action,

          parameters,

          nonce:
            crypto.randomUUID(),

          issued_at:
            Date.now() / 1000,
        }),
      }
    );
  },

  // ---------------------------------
  // LOGS
  // ---------------------------------

  getRecentLogs(limit = 20) {
    return request<RecentLogsResponse>(
      `/logs/recent?limit=${limit}`
    );
  },

  // =================================
  // MQTT STATUS
  // =================================

  getMqttStatus() {
    return request<MqttStatus>(
      "/protocols/mqtt"
    );
  },

  // =================================
  // COAP STATUS
  // =================================

  getCoapStatus() {
    return request<CoapStatus>(
      "/protocols/coap"
    );
  },

  // =================================
  // COMBINED PROTOCOL STATUS
  // =================================

  getProtocolsStatus() {
    return request<ProtocolStatusResponse>(
      "/protocols/status"
    );
  },

  // =================================
  // VERIFIED PROTOCOL TELEMETRY
  // =================================

  getProtocolTelemetry() {
    return request<ProtocolTelemetryResponse>(
      "/protocols/telemetry"
    );
  },

  // =================================
  // ESP32-CAM STATUS
  // =================================

  getCameraStatus() {
    return request<CameraStatusResponse>(
      "/camera/status"
    );
  },

  // =================================
  // REAL ESP32-CAM JPEG CAPTURE
  // =================================

  captureCameraImage() {
    return requestImage(
      "/camera/capture"
    );
  },

  // =================================
  // CAMERA IMAGE -> DISEASE MODEL
  // =================================

  async detectDiseaseFromCamera() {
    const imageBlob =
      await requestImage(
        "/camera/capture"
      );

    const imageFile = new File(
      [imageBlob],
      `ares-camera-${Date.now()}.jpg`,
      {
        type: "image/jpeg",
      }
    );

    return this.detectDisease(
      imageFile
    );
  },
};

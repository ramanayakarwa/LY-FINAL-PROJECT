import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { api } from "@/services/api";

export default function Logs() {
  const {
    data,
    isError,
    isPending,
    refetch,
  } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => api.getRecentLogs(100),
    refetchInterval: 4000,
    retry: false,
  });

  const logs = data?.logs ?? [];

  return (
    <AppLayout>
      <div className="space-y-4">

        <div className="flex justify-between items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold">
              ARES Security & Activity Logs
            </h1>

            <p className="text-sm text-muted-foreground">
              Polling the backend every 4 seconds.
              No WebSocket is configured.
            </p>
          </div>

          <button
            onClick={() => refetch()}
            className="ares-button-primary"
          >
            Refresh
          </button>
        </div>

        <div className="bg-zinc-950 text-green-300 p-5 rounded-lg font-mono text-sm min-h-[360px] space-y-3">

          {isPending && (
            <p>Loading events...</p>
          )}

          {isError && (
            <p className="text-red-400">
              Unable to fetch backend logs.
            </p>
          )}

          {!isPending && !isError && logs.length === 0 && (
            <p>No log events yet.</p>
          )}

          {logs.slice().reverse().map((entry, i) => (
            <article
              key={i}
              className="border-b border-zinc-800 pb-3 break-words"
            >
              <p className="text-green-400">
                [{entry.timestamp ?? "—"}]{" "}
                {entry.source ?? "event"}
              </p>

              {entry.plant_id && (
                <p>Plant: {entry.plant_id}</p>
              )}

              {entry.final_crop && (
                <p>Observed crop: {entry.final_crop}</p>
              )}

              {entry.decision?.action && (
                <p>
                  Agent: {entry.decision.action} —{" "}
                  {entry.decision.reason ?? ""}
                </p>
              )}

              {entry.security && (
                <p>
                  Security:{" "}
                  {entry.security.security_status ??
                    "Not evaluated"}{" "}
                  {entry.security.alerts?.join(", ") ?? ""}
                </p>
              )}

              {entry.action_gate && (
                <p>
                  Gate:{" "}
                  {entry.action_gate.decision ?? "—"} ·{" "}
                  {entry.action_gate.reason ?? ""}
                </p>
              )}

              {entry.hardware && (
                <p>
                  Execution:{" "}
                  {entry.hardware.execution ?? "Unknown"}
                </p>
              )}
            </article>
          ))}

        </div>
      </div>
    </AppLayout>
  );
}
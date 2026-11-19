import { motion } from 'framer-motion';

interface LogEntry {
  time: string;
  message: string;
  level: 'info' | 'warn' | 'error';
}

const defaultLogs: LogEntry[] = [
  { time: '14:02:11', message: 'Executing: /predict/crop', level: 'info' },
  { time: '14:02:12', message: 'Inference complete: Result → Maize (94%)', level: 'info' },
  { time: '14:02:13', message: 'Yield estimation: 4.2 t/ha [3.8-4.6]', level: 'info' },
  { time: '14:02:14', message: 'Reasoning engine: IRRIGATE_ZONE_A', level: 'warn' },
  { time: '14:02:15', message: 'Sensor: soil_moisture=18.4% < threshold(20%)', level: 'warn' },
  { time: '14:02:16', message: 'CMD dispatched: cmd_vel_relay → IRRIGATE', level: 'info' },
  { time: '14:02:18', message: 'ROS2 ACK: cmd_vel_relay confirmed', level: 'info' },
  { time: '14:02:20', message: 'Telemetry sync: GPS lock 28.6139°N, 77.2090°E', level: 'info' },
];

export const SystemLog = ({ logs = defaultLogs }: { logs?: LogEntry[] }) => {
  const colorMap = { info: 'text-success', warn: 'text-warning', error: 'text-critical' };

  return (
    <motion.div
      className="terminal-bg h-64 overflow-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      <div className="opacity-50 border-b border-border/20 pb-2 mb-2 text-inherit">
        SYSTEM_LOG_STREAM
      </div>
      {logs.map((log, i) => (
        <p key={i} className={colorMap[log.level]}>
          [{log.time}] {log.message}
        </p>
      ))}
    </motion.div>
  );
};

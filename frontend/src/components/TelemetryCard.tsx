import { motion } from 'framer-motion';
import { type ReactNode } from 'react';

interface TelemetryCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  status: 'OPTIMAL' | 'WARNING' | 'CRITICAL_LOW' | 'CRITICAL';
  index?: number;
}

const statusColors: Record<string, string> = {
  OPTIMAL: 'bg-success',
  WARNING: 'bg-warning',
  CRITICAL_LOW: 'bg-critical',
  CRITICAL: 'bg-critical',
};

export const TelemetryCard = ({ icon, label, value, status, index = 0 }: TelemetryCardProps) => (
  <motion.div
    className="ares-card flex items-start justify-between"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
  >
    <div className="flex items-start gap-3">
      <div className="mt-0.5">{icon}</div>
      <div>
        <p className="ares-label">{label}</p>
        <p className="ares-value font-mono mt-1">{value}</p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <div className={`h-2 w-2 rounded-full ${statusColors[status]}`} />
      <span className="ares-label">{status}</span>
    </div>
  </motion.div>
);

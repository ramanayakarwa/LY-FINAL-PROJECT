interface StatBlockProps {
  label: string;
  value: string;
}

export const StatBlock = ({ label, value }: StatBlockProps) => (
  <div className="text-right">
    <p className="ares-label">{label}</p>
    <p className="ares-value font-mono">{value}</p>
  </div>
);

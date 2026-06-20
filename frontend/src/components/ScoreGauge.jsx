import "./ScoreGauge.css";

function scoreState(score) {
  if (score >= 75) return { color: "var(--signal-high)", label: "STRONG FIT" };
  if (score >= 50) return { color: "var(--signal-mid)", label: "PARTIAL FIT" };
  return { color: "var(--signal-low)", label: "LOW FIT" };
}

/**
 * Radial "analyzer dial" readout for a job-fit score.
 * size in px, score 0-100.
 */
export default function ScoreGauge({ score, size = 96 }) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);
  const { color, label } = scoreState(clamped);

  return (
    <div className="score-gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          className="gauge-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={6}
        />
        <circle
          className="gauge-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={6}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="gauge-readout">
        <span className="gauge-value">{Math.round(clamped)}</span>
        <span className="gauge-unit">/100</span>
      </div>
      <span className="gauge-label" style={{ color }}>{label}</span>
    </div>
  );
}

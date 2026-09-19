'use client';

interface Props {
  score: number;
  level: string;
  height?: number;
}

const LEVEL_CLASS: Record<string, string> = {
  low: 'cong-fill-low',
  moderate: 'cong-fill-moderate',
  heavy: 'cong-fill-heavy',
  severe: 'cong-fill-severe',
};

export default function CongestionBar({ score, level, height = 4 }: Props) {
  const fillClass = LEVEL_CLASS[level] || LEVEL_CLASS.low;
  return (
    <div className="progress-bar" style={{ height }}>
      <div
        className={`progress-fill ${fillClass}`}
        style={{ width: `${Math.min(score * 100, 100)}%`, transition: 'width 0.6s ease' }}
      />
    </div>
  );
}

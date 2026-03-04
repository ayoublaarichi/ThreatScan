import { cn, getScoreColor, getVerdictColor, getVerdictBg } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  verdict: string;
  size?: "sm" | "md" | "lg";
}

export function ScoreGauge({ score, verdict, size = "md" }: ScoreGaugeProps) {
  const sizeClasses = {
    sm: "h-16 w-16 text-lg",
    md: "h-24 w-24 text-2xl",
    lg: "h-32 w-32 text-3xl",
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Score circle */}
      <div
        className={cn(
          "relative flex items-center justify-center rounded-full border-4",
          sizeClasses[size],
          getVerdictBg(verdict)
        )}
      >
        <span className={cn("font-bold font-mono", getScoreColor(score))}>
          {score}
        </span>
      </div>

      {/* Verdict badge */}
      <span
        className={cn(
          "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider border",
          getVerdictBg(verdict),
          getVerdictColor(verdict)
        )}
      >
        {verdict}
      </span>
    </div>
  );
}

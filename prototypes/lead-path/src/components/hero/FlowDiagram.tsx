import type { Leak } from "@/lib/model";
import { money0 } from "@/lib/model";

/**
 * A stage rail with the leaks hanging off it as bottom-aligned bars.
 *
 * Deliberately NOT a Sankey. A Sankey implies the flow is conserved between
 * stages, and these four leaks are drawn from overlapping-but-different
 * populations — a strict flow diagram would be claiming a precision the
 * arithmetic doesn't have. Bars off a rail say "here is where, and here is
 * how much", which is all that's true.
 *
 * Bar height is the amount leaking. The green portion is the part that comes
 * back. Gray is what stays lost even with everything installed.
 */

const SHORT: Record<string, string> = {
  "missed-calls": "Missed calls",
  "quiet-quotes": "Quiet quotes",
  "no-shows": "Empty driveways",
  reviews: "Reviews",
  lapsed: "Past customers",
};

const W = 1080;
const H = 330;
const RAIL_Y = 62;
const BASE_Y = 262;
const BAR_W = 132;
const MIN_H = 44;
/* Capped so the tallest bar's amount still clears the rail above it. */
const MAX_H = 142;

export function FlowDiagram({ leaks }: { leaks: Leak[] }) {
  const maxLost = Math.max(...leaks.map((l) => l.lostPerMonth), 1);
  const slot = (W - 80) / leaks.length;
  const xOf = (i: number) => 40 + slot * (i + 0.5);

  return (
    <figure className="hidden md:block">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        aria-label="The lead path from the phone ringing to a customer coming back a season later, with the money leaking out at each stage."
      >
        {/* the rail */}
        <line
          x1={40}
          y1={RAIL_Y}
          x2={W - 40}
          y2={RAIL_Y}
          stroke="var(--ink)"
          strokeWidth={3}
        />

        {leaks.map((leak, i) => {
          const x = xOf(i);
          const h = leak.counted
            ? MIN_H + (leak.lostPerMonth / maxLost) * (MAX_H - MIN_H)
            : 58;
          const top = BASE_Y - h;
          const recoveredH =
            leak.lostPerMonth > 0
              ? (leak.recoveredPerMonth / leak.lostPerMonth) * h
              : 0;

          return (
            <g key={leak.id}>
              {/* stage name, above the rail */}
              <text
                x={x}
                y={RAIL_Y - 22}
                textAnchor="middle"
                fill="var(--ink-soft)"
                fontSize={14}
                fontWeight={600}
              >
                {leak.stage}
              </text>

              {/* node on the rail */}
              <circle cx={x} cy={RAIL_Y} r={6} fill="var(--ink)" />

              {/* The drip stops short of the amount, so the line doesn't run
                  straight through the digits. */}
              <line
                x1={x}
                y1={RAIL_Y + 6}
                x2={x}
                y2={leak.counted ? top - 30 : top}
                stroke={leak.counted ? "var(--leak-deep)" : "var(--leak)"}
                strokeWidth={2}
                strokeDasharray={leak.counted ? undefined : "3 4"}
              />

              {leak.counted ? (
                <>
                  {/* The bar is the clip, so the green seats inside it and
                      picks up the same corner radius at any fill level. */}
                  <clipPath id={`clip-${leak.id}`}>
                    <rect
                      x={x - BAR_W / 2}
                      y={top}
                      width={BAR_W}
                      height={h}
                      rx={8}
                    />
                  </clipPath>
                  {/* what leaks */}
                  <rect
                    x={x - BAR_W / 2}
                    y={top}
                    width={BAR_W}
                    height={h}
                    rx={8}
                    fill="var(--leak)"
                  />
                  {/* what comes back */}
                  {recoveredH > 2 && (
                    <rect
                      x={x - BAR_W / 2}
                      y={BASE_Y - recoveredH}
                      width={BAR_W}
                      height={recoveredH}
                      fill="var(--gain)"
                      clipPath={`url(#clip-${leak.id})`}
                    />
                  )}
                  <text
                    x={x}
                    y={top - 14}
                    textAnchor="middle"
                    fill="var(--ink)"
                    fontSize={17}
                    fontWeight={700}
                    style={{ fontVariantNumeric: "tabular-nums" }}
                  >
                    {money0(leak.lostPerMonth)}
                  </text>
                </>
              ) : (
                <>
                  <rect
                    x={x - BAR_W / 2}
                    y={top}
                    width={BAR_W}
                    height={h}
                    rx={8}
                    fill="none"
                    stroke="var(--leak)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                  <text
                    x={x}
                    y={top + h / 2 + 5}
                    textAnchor="middle"
                    fill="var(--ink-soft)"
                    fontSize={13}
                    fontWeight={600}
                  >
                    not counted
                  </text>
                </>
              )}

              {/* leak name and what comes back */}
              <text
                x={x}
                y={BASE_Y + 24}
                textAnchor="middle"
                fill="var(--ink)"
                fontSize={14}
                fontWeight={600}
              >
                {SHORT[leak.id]}
              </text>
              <text
                x={x}
                y={BASE_Y + 46}
                textAnchor="middle"
                fill={leak.counted ? "var(--gain)" : "var(--ink-soft)"}
                fontSize={13.5}
                fontWeight={600}
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {leak.counted
                  ? `${money0(leak.recoveredPerMonth)} back`
                  : "real, unmeasured"}
              </text>
            </g>
          );
        })}

        {/* the floor the bars stand on */}
        <line
          x1={40}
          y1={BASE_Y}
          x2={W - 40}
          y2={BASE_Y}
          stroke="var(--hairline)"
          strokeWidth={1}
        />
      </svg>

      <figcaption className="mt-4 text-[0.875rem] text-ink-soft">
        Bar height is what leaks out each month.{" "}
        <span className="font-semibold text-gain">Green</span> is the part that
        comes back once the follow-up is installed; gray is what stays lost
        anyway.
      </figcaption>
    </figure>
  );
}

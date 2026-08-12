import { Range } from "@/components/hero/Range";
import type { Inputs } from "@/lib/model";
import { money } from "@/lib/model";

type Props = {
  value: Inputs;
  onChange: (next: Inputs) => void;
};

type Row = {
  key: keyof Inputs;
  label: string;
  hint: string;
  min: number;
  max: number;
  step: number;
  format: (n: number) => string;
};

/**
 * Ranges are scaled for exterior cleaning, from a one-van operation up to a
 * few crews — not for a company with an office and a call queue. A slider
 * whose top end is four times bigger than anyone reading the page makes the
 * honest setting look like nothing.
 */
const ROWS: Row[] = [
  {
    key: "callsPerMonth",
    label: "Calls a month",
    hint: "Everything that makes the phone ring — referrals, Google, the van.",
    min: 5,
    max: 120,
    step: 5,
    format: (n) => String(n),
  },
  {
    key: "answeredLive",
    label: "Share you catch live",
    hint: "Honestly. Counting the ones that rang out while the machine was running.",
    min: 0.1,
    max: 1,
    step: 0.05,
    format: (n) => Math.round(n * 100) + "%",
  },
  {
    key: "jobValue",
    label: "Average job",
    hint: "What a typical clean invoices at, before tax.",
    min: 75,
    max: 800,
    step: 25,
    format: (n) => money(n),
  },
  {
    key: "quotesPerMonth",
    label: "Quotes you send a month",
    hint: "The ones that need a number sent over rather than booking on the call.",
    min: 0,
    max: 60,
    step: 1,
    format: (n) => String(n),
  },
];

export function Controls({ value, onChange }: Props) {
  return (
    <div className="rounded-lg bg-surface-alt p-6 sm:p-8">
      <div className="mb-6 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h3 className="text-[1.0625rem] font-semibold tracking-[-0.01em]">
          Four numbers about your business
        </h3>
        <p className="text-[0.9375rem] text-ink-soft">
          Rough is fine. Nothing is sent anywhere.
        </p>
      </div>

      <div className="grid gap-x-10 gap-y-7 sm:grid-cols-2">
        {ROWS.map((row) => {
          const v = value[row.key];
          return (
            <div key={row.key}>
              <div className="mb-1 flex items-baseline justify-between gap-4">
                {/* A <label for> can't point at a slider group, so the
                    association is carried by aria-label on the Slider. */}
                <span className="text-[0.9375rem] font-semibold">
                  {row.label}
                </span>
                <span className="tnum text-[1.0625rem] font-bold tabular-nums">
                  {row.format(v)}
                </span>
              </div>
              <p className="mb-3 text-[0.8125rem] leading-snug text-ink-soft">
                {row.hint}
              </p>
              <Range
                label={row.label}
                value={v}
                min={row.min}
                max={row.max}
                step={row.step}
                onChange={(next) => onChange({ ...value, [row.key]: next })}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

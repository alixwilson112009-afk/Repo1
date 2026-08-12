import { useState } from "react";
import { Range } from "@/components/hero/Range";
import type { Assumption, AssumptionKey, Leak, Step } from "@/lib/model";
import { money0 } from "@/lib/model";

type Props = {
  leak: Leak;
  assumptions: Record<AssumptionKey, Assumption>;
  onAssumptionChange: (key: AssumptionKey, value: number) => void;
};

export function LeakCard({ leak, assumptions, onAssumptionChange }: Props) {
  const [open, setOpen] = useState(false);
  const panelId = `leak-${leak.id}`;

  return (
    <div className="border-t border-hairline py-7 first:border-t-0 first:pt-0">
      {/* Stacked on a phone — side by side there squeezes the title into a
          three-line column. Two columns from sm up. */}
      <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between sm:gap-x-8">
        <div className="min-w-0 max-w-[46ch] sm:flex-1">
          <p className="mb-1 text-[0.8125rem] font-semibold uppercase tracking-[0.07em] text-ink-soft">
            {leak.stage}
          </p>
          <h3 className="mb-2 text-[1.25rem]">{leak.title}</h3>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            {leak.blurb}
          </p>
        </div>

        {leak.counted ? (
          <div className="flex shrink-0 items-baseline gap-9 sm:block sm:text-right">
            <div>
              <p className="tnum text-[1.75rem] font-bold leading-none">
                {money0(leak.lostPerMonth)}
              </p>
              <p className="mt-1 text-[0.8125rem] text-ink-soft">
                leaking, a month
              </p>
            </div>
            <div className="sm:mt-3">
              <p className="tnum text-[1.0625rem] font-bold leading-none text-gain">
                {money0(leak.recoveredPerMonth)}
              </p>
              <p className="mt-1 text-[0.8125rem] text-ink-soft">comes back</p>
            </div>
          </div>
        ) : (
          <p className="shrink-0 text-[0.9375rem] font-semibold text-ink-soft sm:max-w-[22ch] sm:text-right">
            Not counted anywhere on this page
          </p>
        )}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2">
        {leak.counted && (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls={panelId}
            className="hero-focus rounded-sm text-[0.9375rem] font-semibold text-brand underline decoration-brand/30 underline-offset-4 hover:decoration-brand"
          >
            {open ? "Hide the arithmetic" : "Show me the arithmetic"}
          </button>
        )}
        <p className="text-[0.9375rem] text-ink-soft">
          <span className="font-semibold text-ink">Installed:</span>{" "}
          {leak.installed}
        </p>
      </div>

      {leak.counted && open && (
        <div
          id={panelId}
          className="mt-5 rounded-lg bg-surface-alt p-5 sm:p-6"
        >
          <Chain
            steps={leak.steps}
            assumptions={assumptions}
            onAssumptionChange={onAssumptionChange}
          />
          <div className="my-4 border-t border-black/[0.07]" />
          <Chain
            steps={leak.recoverySteps}
            assumptions={assumptions}
            onAssumptionChange={onAssumptionChange}
            tone="gain"
          />
          <p className="mt-5 text-[0.8125rem] leading-relaxed text-ink-soft">
            Every percentage above is a guess until we put your real one in it.
            Drag any of them. If the number only works at settings you don't
            believe, that's worth knowing before you book a call, not after.
          </p>
        </div>
      )}

      {!leak.counted && (
        <p className="mt-4 max-w-[62ch] rounded-lg bg-surface-alt p-5 text-[0.9375rem] leading-relaxed text-ink-soft">
          Reviews are worth real money and I'm not going to put a figure on
          them. They compound into leads months later that nobody can trace
          back to a particular job, so any number here would be invented — and
          then you'd have a reason to doubt the four that aren't.
        </p>
      )}
    </div>
  );
}

function Chain({
  steps,
  assumptions,
  onAssumptionChange,
  tone = "ink",
}: {
  steps: Step[];
  assumptions: Record<AssumptionKey, Assumption>;
  onAssumptionChange: (key: AssumptionKey, value: number) => void;
  tone?: "ink" | "gain";
}) {
  return (
    <div className="space-y-2.5">
      {steps.map((step, i) => {
        const a = step.key ? assumptions[step.key] : undefined;
        const isLast = i === steps.length - 1;
        return (
          <div key={i}>
            <div className="grid grid-cols-[1.6rem_auto_1fr] items-baseline gap-x-2 sm:gap-x-3">
              <span className="tnum text-[0.9375rem] text-ink-soft">
                {step.op === "of which" ? "" : step.op}
              </span>
              <span
                className={
                  "tnum text-[0.9375rem] font-bold " +
                  (step.key ? "text-ink" : "text-ink")
                }
              >
                {step.operand}
              </span>
              <span className="flex flex-wrap items-baseline justify-between gap-x-4 text-[0.9375rem] text-ink-soft">
                <span className="max-w-[38ch]">
                  {step.op === "of which" && (
                    <span className="mr-1 text-ink-soft">of which</span>
                  )}
                  {step.label}
                </span>
                <span
                  className={
                    "tnum font-semibold " +
                    (isLast && tone === "gain"
                      ? "text-gain"
                      : isLast
                        ? "text-ink"
                        : "text-ink-soft")
                  }
                >
                  {step.running}
                </span>
              </span>
            </div>

            {a && step.key && (
              <div className="mt-2 grid grid-cols-[1.6rem_1fr] gap-x-2 sm:gap-x-3">
                <span />
                <div className="max-w-[30rem]">
                  <Range
                    size="sm"
                    label={a.label}
                    value={a.value}
                    min={a.min}
                    max={a.max}
                    step={0.01}
                    onChange={(v) => onAssumptionChange(step.key!, v)}
                  />
                  <p className="mt-1.5 text-[0.8125rem] leading-snug text-ink-soft">
                    {a.note}
                  </p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

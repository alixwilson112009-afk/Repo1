import { useMemo, useState } from "react";
import { Controls } from "@/components/hero/Controls";
import { FlowDiagram } from "@/components/hero/FlowDiagram";
import { LeakCard } from "@/components/hero/LeakCard";
import {
  compute,
  DEFAULT_ASSUMPTIONS,
  DEFAULT_INPUTS,
  money0,
  type Assumption,
  type AssumptionKey,
  type Inputs,
} from "@/lib/model";

const BOOKING = "https://my.herolgo.com/widget/bookings/alexw-calendar";

export default function App() {
  const [inputs, setInputs] = useState<Inputs>(DEFAULT_INPUTS);
  const [assumptions, setAssumptions] =
    useState<Record<AssumptionKey, Assumption>>(DEFAULT_ASSUMPTIONS);

  const model = useMemo(
    () => compute(inputs, assumptions),
    [inputs, assumptions]
  );

  const touched =
    JSON.stringify(inputs) !== JSON.stringify(DEFAULT_INPUTS) ||
    (Object.keys(assumptions) as AssumptionKey[]).some(
      (k) => assumptions[k].value !== DEFAULT_ASSUMPTIONS[k].value
    );

  const setAssumption = (key: AssumptionKey, value: number) =>
    setAssumptions((prev) => ({
      ...prev,
      [key]: { ...prev[key], value },
    }));

  const reset = () => {
    setInputs(DEFAULT_INPUTS);
    setAssumptions(DEFAULT_ASSUMPTIONS);
  };

  return (
    <main className="bg-surface">
      <section className="px-6 py-[clamp(80px,11vw,140px)]">
        <div className="mx-auto max-w-container">
          {/* Left-aligned, like every other section head on the site. */}
          <div className="mb-[clamp(40px,6vw,64px)] max-w-[660px]">
            <span className="mb-4 block text-[0.875rem] font-semibold uppercase tracking-[0.08em] text-brand">
              Your lead path
            </span>
            <h2 className="text-[clamp(1.875rem,4.6vw,3rem)]">
              Where your jobs are going, in your numbers.
            </h2>
            <p className="mt-5 text-[clamp(1.125rem,2.2vw,1.375rem)] leading-[1.55] text-ink-soft">
              This is the walk-through I do on the call, except you're driving.
              Set four sliders to your business and the path fills in. Every
              percentage underneath it is on screen and draggable — there's
              nothing hidden in the arithmetic.
            </p>
          </div>

          <Controls value={inputs} onChange={setInputs} />

          <div className="mt-[clamp(48px,7vw,80px)]">
            <FlowDiagram leaks={model.leaks} />
          </div>

          <div className="mt-[clamp(40px,6vw,72px)]">
            {model.leaks.map((leak) => (
              <LeakCard
                key={leak.id}
                leak={leak}
                assumptions={assumptions}
                onAssumptionChange={setAssumption}
              />
            ))}
          </div>

          {/* ---- The total. Dark band, same treatment as the closing CTA. ---- */}
          <div className="relative mt-[clamp(48px,7vw,80px)] overflow-hidden rounded-lg bg-ink px-6 py-[clamp(44px,6vw,68px)] text-center sm:px-10">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  "radial-gradient(58% 78% at 50% 0%, rgba(124,58,237,0.30), transparent 66%), radial-gradient(40% 60% at 88% 100%, rgba(88,52,200,0.16), transparent 70%)",
              }}
            />
            <div className="relative z-10">
              <span className="mb-4 block text-[0.875rem] font-semibold uppercase tracking-[0.08em] text-[#a78bfa]">
                What's on the floor
              </span>
              <p className="tnum text-[clamp(2rem,6.4vw,3.5rem)] font-bold leading-[1.08] tracking-[-0.03em] text-white">
                {money0(model.low)} – {money0(model.high)}
                <span className="text-[0.44em] font-semibold tracking-normal text-[#a1a1a6]">
                  {" "}
                  a month
                </span>
              </p>
              <p className="mx-auto mt-4 max-w-[46ch] text-[1.0625rem] leading-relaxed text-[#a1a1a6]">
                Roughly{" "}
                <span className="font-semibold text-white">
                  {model.jobsRecovered < 1
                    ? model.jobsRecovered.toFixed(1)
                    : Math.round(model.jobsRecovered)}{" "}
                  jobs a month
                </span>{" "}
                you're already paying to generate and not closing. It's a band
                rather than a figure because the percentages behind it are
                estimates, and a single number would be pretending otherwise.
              </p>

              <a
                href={BOOKING}
                className="hero-focus mt-9 inline-block rounded-full bg-brand px-8 py-[15px] text-[1.0625rem] font-semibold text-white transition-colors hover:bg-brand-hover active:scale-[0.98]"
                style={{ outlineColor: "#fff" }}
              >
                Book a demo
              </a>
              <p className="mx-auto mt-5 max-w-[48ch] text-[0.875rem] leading-relaxed text-[#8e8e93]">
                Fifteen minutes. We put your real numbers in place of these and
                see what's actually there. If there's nothing leaking, I'll tell
                you that.
              </p>
            </div>
          </div>

          {/* ---- The disclaimer, in the same voice as the rest of the page. ---- */}
          <div className="mt-8 flex flex-wrap items-start justify-between gap-x-10 gap-y-4">
            <p className="max-w-[68ch] text-[0.875rem] leading-relaxed text-ink-soft">
              <span className="font-semibold text-ink">
                What this is, and isn't:
              </span>{" "}
              an estimate built from four numbers you supplied and nine
              percentages I chose, all of which are shown and all of which you
              can move. It is not a measurement of your business, and none of
              it is my own trading figures — those are further up the page and
              they're labelled. Nothing you type here is sent anywhere or
              stored.
            </p>
            {touched && (
              <button
                type="button"
                onClick={reset}
                className="hero-focus shrink-0 rounded-sm text-[0.875rem] font-semibold text-brand underline decoration-brand/30 underline-offset-4 hover:decoration-brand"
              >
                Reset everything
              </button>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

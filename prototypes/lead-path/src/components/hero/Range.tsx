/**
 * A native range input wearing Hero's clothes.
 *
 * Deliberately not the shadcn/Radix slider. This has to survive being ported
 * into a static page with no framework, and a native input does that as a
 * copy-paste. It also gets keyboard support, touch targets and screen-reader
 * announcements from the platform rather than from 30kB of JavaScript.
 *
 * WebKit has no ::-webkit-slider-progress, so the filled part of the track is
 * painted with a gradient stop positioned from the current value.
 */

type Props = {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  /** "sm" is the inline one that sits under an assumption in the arithmetic. */
  size?: "md" | "sm";
};

export function Range({
  label,
  value,
  min,
  max,
  step,
  onChange,
  size = "md",
}: Props) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <input
      type="range"
      className={size === "sm" ? "hero-range hero-range-sm" : "hero-range"}
      aria-label={label}
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      style={{ ["--fill" as string]: `${pct}%` }}
    />
  );
}

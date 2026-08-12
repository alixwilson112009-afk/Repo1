/**
 * The whole calculation lives here, in one file, deliberately.
 *
 * Rule the page has to keep: every number a visitor sees is either something
 * they typed, or something derived from what they typed by arithmetic they
 * can read on screen. No constant is buried. Anything that isn't a fact about
 * their business is an `Assumption` — labelled, sourced in plain English, and
 * draggable, so a visitor who disagrees can move it instead of dismissing the
 * whole thing.
 */

export type Inputs = {
  callsPerMonth: number;
  answeredLive: number; // 0..1
  jobValue: number;
  quotesPerMonth: number;
};

/**
 * Pitched at the one-van operation the page is written for, and sanity-checked
 * against the proof section's own figures: "5-7 jobs a month" before, at "50%
 * of inbound calls became jobs", puts that business somewhere near 10-15 calls
 * a month. A default of 60 was describing a company several times the size.
 *
 * At these settings the model has the visitor booking ~7 jobs a month, which
 * lands in the same place the proof section starts from. Anyone bigger drags
 * up.
 */
export const DEFAULT_INPUTS: Inputs = {
  callsPerMonth: 25,
  answeredLive: 0.5,
  // A residential exterior clean: a window round, a driveway, a gutter clear.
  jobValue: 250,
  quotesPerMonth: 8,
};

export type Assumption = {
  label: string; // reads inside the arithmetic chain
  note: string; // why this number, in one sentence
  value: number; // 0..1
  min: number;
  max: number;
};

export type AssumptionKey =
  | "callBackAnyway"
  | "bookRate"
  | "textBackRecovery"
  | "quoteGoesQuiet"
  | "chaseWinRate"
  | "noShowRate"
  | "reminderRecovery"
  | "lapseRate"
  | "reactivationRate";

export const DEFAULT_ASSUMPTIONS: Record<AssumptionKey, Assumption> = {
  callBackAnyway: {
    label: "call back or leave a voicemail anyway",
    note: "The ones you'd have caught regardless. They're taken out before anything is counted as lost.",
    value: 0.3,
    min: 0.05,
    max: 0.7,
  },
  bookRate: {
    label: "would have booked if they'd reached you",
    note: "Your close rate on people you actually speak to. Move this to whatever yours is.",
    value: 0.45,
    min: 0.1,
    max: 0.9,
  },
  textBackRecovery: {
    label: "a text back inside 60 seconds wins back",
    note: "Not all of them. Some have already booked the company that picked up. This is the share that replies.",
    value: 0.55,
    min: 0.2,
    max: 0.9,
  },
  quoteGoesQuiet: {
    label: "go quiet — no yes, no no",
    note: "Quotes that get no answer either way. Not the ones who told you they went elsewhere.",
    value: 0.4,
    min: 0.1,
    max: 0.8,
  },
  chaseWinRate: {
    label: "book when they're chased over the following week",
    note: "Texts and emails that stop the moment they book or say no.",
    value: 0.25,
    min: 0.05,
    max: 0.6,
  },
  noShowRate: {
    label: "nobody home when you get there",
    note: "Bookings that turn into a drive out and a drive back.",
    value: 0.08,
    min: 0.01,
    max: 0.3,
  },
  reminderRecovery: {
    label: "a confirmation and two reminders prevent",
    note: "At booking, 24 hours out, an hour out. Doesn't fix the ones who never meant to be there.",
    value: 0.75,
    min: 0.3,
    max: 0.95,
  },
  lapseRate: {
    label: "don't come back on their own",
    note: "They were happy. They just didn't think of you when the gutters filled again.",
    value: 0.6,
    min: 0.2,
    max: 0.9,
  },
  reactivationRate: {
    label: "book again when you check back",
    note: "One message, months later, to a list of people who already paid you once.",
    value: 0.15,
    min: 0.03,
    max: 0.4,
  },
};

export type Step = {
  op: "" | "×" | "of which";
  operand: string;
  label: string;
  running: string;
  /** Present when this factor is an assumption the visitor can move. */
  key?: AssumptionKey;
  /** Present when this factor came straight off one of the four sliders. */
  fromInput?: boolean;
};

export type Leak = {
  id: string;
  stage: string;
  title: string;
  blurb: string;
  installed: string;
  counted: boolean;
  steps: Step[];
  recoverySteps: Step[];
  jobsLostPerMonth: number;
  lostPerMonth: number;
  recoveredPerMonth: number;
};

export const money = (n: number) =>
  "$" + Math.round(n).toLocaleString("en-US");

const money0 = (n: number) =>
  n >= 10000
    ? "$" + (Math.round(n / 100) / 10).toFixed(1) + "k"
    : "$" + Math.round(n).toLocaleString("en-US");

const pct = (n: number) => Math.round(n * 100) + "%";

const num = (n: number) =>
  n >= 10 ? Math.round(n).toLocaleString("en-US") : (Math.round(n * 10) / 10).toString();

const jobs = (n: number) => `${num(n)} ${Math.abs(n - 1) < 0.05 ? "job" : "jobs"}`;

export type Model = {
  leaks: Leak[];
  bookedPerMonth: number;
  totalLost: number;
  totalRecovered: number;
  jobsRecovered: number;
  /** Deliberately a band, not a point. See the note under the total. */
  low: number;
  high: number;
};

export function compute(
  input: Inputs,
  a: Record<AssumptionKey, Assumption>
): Model {
  const { callsPerMonth: calls, answeredLive, jobValue, quotesPerMonth } = input;

  /* ---- 1. Calls that never reach you ------------------------------- */
  const missed = calls * (1 - answeredLive);
  const gone = missed * (1 - a.callBackAnyway.value);
  const lostCallJobs = gone * a.bookRate.value;
  const lostCalls = lostCallJobs * jobValue;
  const recoveredCalls = lostCalls * a.textBackRecovery.value;

  /* ---- 2. Quotes that go quiet ------------------------------------- */
  const quiet = quotesPerMonth * a.quoteGoesQuiet.value;
  const quoteJobs = quiet * a.chaseWinRate.value;
  const lostQuotes = quoteJobs * jobValue;

  /* ---- 3. Empty driveways ------------------------------------------
     Everyone who got through to you, times your close rate. The quote
     path sits inside this rate rather than beside it, so a job isn't
     counted twice. */
  const reached = calls * answeredLive + missed * a.callBackAnyway.value;
  const booked = reached * a.bookRate.value;
  const noShows = booked * a.noShowRate.value;
  const lostNoShow = noShows * jobValue;
  const recoveredNoShow = lostNoShow * a.reminderRecovery.value;

  /* ---- 4. Customers who never hear from you again ------------------- */
  const servedAYear = booked * 12;
  const lapsed = servedAYear * a.lapseRate.value;
  const reactivated = lapsed * a.reactivationRate.value;
  const lostLapsedMonthly = (reactivated * jobValue) / 12;

  const leaks: Leak[] = [
    {
      id: "missed-calls",
      stage: "The phone rings",
      title: "The call you took at the top of the ladder",
      blurb:
        "Both hands on the pole, phone in the van. By the time you're down it's been forty minutes and they've booked whoever picked up.",
      installed: "Every missed call gets a text back from your number in under a minute, with a link to book.",
      counted: true,
      steps: [
        { op: "", operand: num(calls), label: "calls a month", running: `${num(calls)} calls`, fromInput: true },
        { op: "×", operand: pct(1 - answeredLive), label: "you can't catch live", running: `${num(missed)} missed`, fromInput: true },
        { op: "×", operand: pct(1 - a.callBackAnyway.value), label: "never " + a.callBackAnyway.label, running: `${num(gone)} gone`, key: "callBackAnyway" },
        { op: "×", operand: pct(a.bookRate.value), label: a.bookRate.label, running: jobs(lostCallJobs), key: "bookRate" },
        { op: "×", operand: money(jobValue), label: "average job", running: money(lostCalls) + " a month", fromInput: true },
      ],
      recoverySteps: [
        { op: "of which", operand: pct(a.textBackRecovery.value), label: a.textBackRecovery.label, running: money(recoveredCalls) + " a month", key: "textBackRecovery" },
      ],
      jobsLostPerMonth: lostCallJobs,
      lostPerMonth: lostCalls,
      recoveredPerMonth: recoveredCalls,
    },
    {
      id: "quiet-quotes",
      stage: "Quote sent",
      title: "The quote you sent Friday",
      blurb:
        "They said they'd talk it over with their wife. Nobody chased it, and by Monday it was somebody else's driveway.",
      installed: "Every quote that goes quiet gets chased over the following week, by text and email, stopping the moment they book or say no.",
      counted: true,
      steps: [
        { op: "", operand: num(quotesPerMonth), label: "quotes a month", running: `${num(quotesPerMonth)} quotes`, fromInput: true },
        { op: "×", operand: pct(a.quoteGoesQuiet.value), label: a.quoteGoesQuiet.label, running: `${num(quiet)} unanswered`, key: "quoteGoesQuiet" },
        { op: "×", operand: pct(a.chaseWinRate.value), label: a.chaseWinRate.label, running: jobs(quoteJobs), key: "chaseWinRate" },
        { op: "×", operand: money(jobValue), label: "average job", running: money(lostQuotes) + " a month", fromInput: true },
      ],
      recoverySteps: [
        { op: "of which", operand: "all of it", label: "chasing is the entire mechanism here — there's nothing to discount", running: money(lostQuotes) + " a month" },
      ],
      jobsLostPerMonth: quoteJobs,
      lostPerMonth: lostQuotes,
      recoveredPerMonth: lostQuotes,
    },
    {
      id: "no-shows",
      stage: "Job booked",
      title: "The empty driveway",
      blurb:
        "Half an hour there, half an hour back, and nobody home. The slot is gone whether they showed or not.",
      installed: "Every booked job gets a confirmation, then a reminder 24 hours out, then one an hour out.",
      counted: true,
      steps: [
        { op: "", operand: num(booked), label: "jobs booked a month", running: jobs(booked) },
        { op: "×", operand: pct(a.noShowRate.value), label: a.noShowRate.label, running: jobs(noShows), key: "noShowRate" },
        { op: "×", operand: money(jobValue), label: "average job", running: money(lostNoShow) + " a month", fromInput: true },
      ],
      recoverySteps: [
        { op: "of which", operand: pct(a.reminderRecovery.value), label: a.reminderRecovery.label, running: money(recoveredNoShow) + " a month", key: "reminderRecovery" },
      ],
      jobsLostPerMonth: noShows,
      lostPerMonth: lostNoShow,
      recoveredPerMonth: recoveredNoShow,
    },
    {
      id: "reviews",
      stage: "Job finished",
      title: "The review you didn't ask for",
      blurb:
        "The day after you pack up, while they're still looking at clean windows, is the only time asking is easy.",
      installed: "Every finished job gets asked for a review the next day, and the profile gets watched so it isn't sitting stale.",
      counted: false,
      steps: [],
      recoverySteps: [],
      jobsLostPerMonth: 0,
      lostPerMonth: 0,
      recoveredPerMonth: 0,
    },
    {
      id: "lapsed",
      stage: "A season later",
      title: "The gutters you cleaned last autumn",
      blurb:
        "Same house, same gutters, filling up again. They haven't heard from you since, so this year they'll search.",
      installed: "Every old customer gets a check back months later, when the work needs doing again.",
      counted: true,
      steps: [
        { op: "", operand: num(servedAYear), label: "customers served in a year", running: `${num(servedAYear)} customers` },
        { op: "×", operand: pct(a.lapseRate.value), label: a.lapseRate.label, running: `${num(lapsed)} lapsed`, key: "lapseRate" },
        { op: "×", operand: pct(a.reactivationRate.value), label: a.reactivationRate.label, running: jobs(reactivated) + " a year", key: "reactivationRate" },
        { op: "×", operand: money(jobValue), label: "average job, spread over the year", running: money(lostLapsedMonthly) + " a month" },
      ],
      recoverySteps: [
        { op: "of which", operand: "all of it", label: "nobody is contacting this list today — that's the point of it", running: money(lostLapsedMonthly) + " a month" },
      ],
      jobsLostPerMonth: reactivated / 12,
      lostPerMonth: lostLapsedMonthly,
      recoveredPerMonth: lostLapsedMonthly,
    },
  ];

  const counted = leaks.filter((l) => l.counted);
  const totalLost = counted.reduce((s, l) => s + l.lostPerMonth, 0);
  const totalRecovered = counted.reduce((s, l) => s + l.recoveredPerMonth, 0);
  const jobsRecovered = counted.reduce(
    (s, l) => s + (l.recoveredPerMonth > 0 ? l.recoveredPerMonth / jobValue : 0),
    0
  );

  return {
    leaks,
    bookedPerMonth: booked,
    totalLost,
    totalRecovered,
    jobsRecovered,
    low: totalRecovered * 0.75,
    high: totalRecovered * 1.25,
  };
}

export { money0, pct, num, jobs };

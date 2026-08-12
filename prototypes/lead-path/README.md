# Lead path — prototype

An interactive version of the walk-through described in the site's "We walk
your lead path" step. A visitor sets four numbers about their own business,
and the path fills in with where their jobs are going and what comes back
once the follow-up is installed.

**This is a prototype, not the shipping version.** It is a React app so the
design and the arithmetic could be settled quickly. Nothing here is wired
into `index.html`, and the site is unchanged.

Open `bundle.html` in a browser to look at it. No server needed.

## The rule the thing is built around

Every number on screen is either something the visitor typed or something
derived from it by arithmetic they can read. There are four inputs and nine
assumptions; the assumptions all live in `src/lib/model.ts`, all appear on
screen under "Show me the arithmetic", and all are draggable.

Two consequences worth keeping if this ships:

- **The total is a band, not a figure.** ±25% around the estimate. A single
  number would be claiming a precision that nine guessed percentages don't
  support, and the page already tells people it won't do that.
- **Reviews are deliberately not costed.** They're shown as a stage on the
  path with "not counted" where a number would go. Reviews compound into
  leads months later that nobody can trace to a job, so any figure would be
  invented — and would give a visitor a reason to doubt the four that aren't.

Nothing is sent anywhere. All state is in the page.

## Design

Tokens are lifted verbatim from `index.html` — `--ink`, `--ink-soft`,
`--surface-alt`, `--accent` (CTAs only), `--gain`, `--radius`, and the same
system font stack. Losses are drawn in gray, never red: the site's existing
vocabulary is `--ink-soft` for "before" and `--gain` for "after", and a leak
is a "before".

## Working on it

```sh
pnpm install
pnpm dev         # vite dev server
pnpm typecheck
pnpm bundle      # rebuild bundle.html
```

## If it ships

Port it to vanilla JS against the site's existing CSS variables rather than
dropping this bundle in. `index.html` has no build step, and this bundle is
~250 KB of React and Tailwind next to a page that is currently 41 KB of
hand-written HTML.

The parts that carry over unchanged:

- `src/lib/model.ts` — the whole calculation, no React in it
- `src/index.css` — the `.hero-range` rules, which style a native
  `<input type="range">` and were written for exactly this reason
- `src/components/hero/FlowDiagram.tsx` — plain SVG, no library

The React-shaped work is the state wiring in `App.tsx` and the open/closed
arithmetic panels in `LeakCard.tsx`.

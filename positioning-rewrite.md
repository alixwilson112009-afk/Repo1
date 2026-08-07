# Positioning rewrite — proposed copy (v2)

**Status: proposal only. No source files have been modified.**

v2 replaces v1. The change: the site now shows the whole offer — follow-up,
appointments, quotes and payment, reputation, and the CRM underneath — instead of
selling missed-call text-back alone.

Line numbers refer to the files at commit `bb64ad9`.

**Thesis:** you already pay for leads — ads, SEO, referrals, the truck wrap. They
leak out between "phone rings" and "job gets paid." Hero plugs every leak on that
path, and everything runs on one system.

**Structure:** approved — follow the life of a job. Three bands (before / the job /
after), with the CRM as the spine underneath rather than a feature sitting beside
the others.

**In scope** (confirmed by you, or drawn from your own automation diagram):
missed-call text-back · instant reply to web and Facebook form leads · manual lead
entry · booking link with a week of nudges · confirmations and reminders at 24 hr
and 1 hr · cancellations routed back into follow-up · quotes, invoices, payments ·
review and referral requests · review monitoring and replies · monthly nurture ·
120-day reactivation · lead tags and stages · done-for-you build.

**Deliberately left off** (you didn't claim these): AI or chat handling, paid ads,
website builds, Google Business Profile listing setup. Replying to Google reviews
*is* in scope under reputation; managing the listing itself is not claimed.

---

## 1. Meta and Open Graph — `index.html` lines 6–9

**OLD**
```
<title>Hero — Never Miss Another Lead</title>

<meta name="description" content="Hero builds done-for-you automation for local
service businesses. Missed-call text-back, automated follow-up, and every lead in
one place — so no job slips away.">

<meta property="og:title" content="Hero — Never Miss Another Lead">

<meta property="og:description" content="Done-for-you automation for local service
businesses. Every missed call gets a text back in seconds.">
```

**NEW**
```
<title>Hero — Close More of the Leads You Already Have</title>

<meta name="description" content="You already pay for leads — ads, SEO, referrals,
the truck wrap. Hero handles the follow-up, booking, reminders, quotes, payment,
and reviews that decide whether they turn into paid work. For plumbing, HVAC, tree
service, and garage door companies.">

<meta property="og:title" content="Hero — Close More of the Leads You Already Have">

<meta property="og:description" content="Stop losing leads you already paid for.
Every call answered, every quote chased, every job reminded, every review asked
for — running on one system.">
```

"so no job slips away" is dropped: it's an absolute guarantee, and `terms.html:217`
already disclaims guaranteed outcomes. The old line contradicts your own legal page.

---

## 2. Hero section — `index.html` lines 400–402

**OLD**
> **Never miss another lead.**
>
> Hero texts back every missed call in seconds — so the job that would've gone to a competitor books with you instead.
>
> `[Book a Call]`

**NEW**
> **Stop losing the leads you already paid for.**
>
> Ads, SEO, referrals, the truck wrap — you paid to make that phone ring. Hero handles everything between the first ring and the paid invoice, so fewer of those leads quietly disappear.
>
> `[Book a Call]`

CTA text and `href="#book"` unchanged.

---

## 3. Problem section — `index.html` lines 410–418

**OLD**
> *The problem* · **Every missed call is a paying job walking away.**
>
> You're on a roof, under a sink, or halfway up a tree. The phone rings. It goes to voicemail. That caller doesn't wait — they dial the next company on the list.
>
> - **Callers don't leave voicemails.** They hang up and call your competitor. The first business to respond usually wins the job.
> - **Your ad spend leaks.** You pay to make the phone ring — every unanswered call is marketing money down the drain.
> - **Hiring isn't the answer.** A full-time receptionist costs thousands a month and still clocks out at five.

**NEW**
> *The problem* · **The leads are already coming in. They're leaking out.**
>
> Nobody loses jobs because the phone never rings. They lose them in the gaps — the call that came in mid-crawlspace, the quote nobody followed up on, the appointment nobody confirmed.
>
> - **The call you couldn't take.** Both hands under a sink. It rings out, and they're already dialing the next name on the list.
> - **The callback that came too late.** You call back at six. They booked someone who answered at two.
> - **The quote that went quiet.** You sent the number, they said they'd think about it, and nobody followed up.
> - **The no-show.** Booked Tuesday, forgotten by Thursday. You drove out for nothing.
> - **The leads from three months ago.** A list of people who wanted work done. Nobody has touched it since.
> - **The job that never got a review request.** Good work, happy customer, no review. The next person searching never hears about it.

**Item count goes 3 → 6.** Same component. The grid is
`repeat(auto-fit, minmax(240px, 1fr))` (`index.html:180`), so six items reflow to
3-across × 2 rows on desktop and stack on mobile. No CSS change.

Two old points retire: "your ad spend leaks" is now the hero promise, and "hiring
isn't the answer" has no natural home — say the word if you want it back in the
closing.

---

## 4. How it works — `index.html` lines 426–447

**OLD**
> *How it works* · **The moment you miss a call, Hero answers.**
>
> 01 **A call slips through** — You're on a job. The call rings out or hits voicemail.
> 02 **Hero texts them back** — Within seconds, the caller gets a text from your business number — before they can dial anyone else.
> 03 **The job stays yours** — The conversation continues by text. You reply when you're free, and the lead books with you.

**NEW**
> *How it works* · **We find the leaks, then we plug them.**
>
> 01 **We walk your lead path** — Start to finish, from the first ring to the paid invoice. We find where jobs are falling out.
> 02 **We build it on your setup** — Your number, your calendar, your service area. You don't build anything and you don't learn new software to answer a phone.
> 03 **You just do the work** — The chasing, reminding, and asking runs itself. You pick up the ones worth your time.

### Figure caption — line 446

**OLD**
> The full Hero system: instant text-back, booking nudges, appointment reminders, review and referral requests, and long-term reactivation — every step on autopilot.

**NEW**
> One lead's whole path: the first reply, the booking nudges, the reminders before the appointment, the review ask after the work, and a check back in months later. Every step that used to depend on someone remembering.

### Image alt text — line 440

**OLD**
> Flowchart of the Hero automation. Leads from missed calls, answered calls, or marketing forms get an instant text with a booking link, then a week of booking nudges. Booked appointments get confirmations and reminders; after the job, a review and referral request, then a reactivation text 120 days later. Unbooked leads move into long-term monthly nurture.

**NEW**
> Flowchart of the Hero system. Leads arrive from phone calls, marketing forms, or added by hand. Missed calls get an instant text back with a booking link; answered calls are handled live. Every lead is tagged and enters a week of booking nudges. Booked appointments get confirmations and reminders 24 hours and 1 hour ahead. After the job, a review and referral request goes out, then a reactivation message 120 days later. Leads that never book move into long-term monthly nurture.

### Image link label — line 437

**OLD:** `Open the automation diagram at full size`
**NEW:** `Open the lead path diagram at full size`

The diagram itself needs no redrawing — it already shows the full lifecycle. Its
labels are baked into the PNG, so renaming steps later means re-rendering it.

---

## 5. What you get → the job's life — `index.html` lines 453–483

This is the structural change. Four flat feature cards become three lifecycle
cards, each holding the capabilities that belong to that stage.

**OLD**
> *What you get* · **Built for you. Running in days.**
>
> 1. **Missed-call text-back** — Every unanswered call gets an instant, personal-sounding text from your number. No caller left hanging, ever.
> 2. **Automated follow-up** — Leads that go quiet get a polite nudge automatically. No sticky notes, no "I meant to call them back."
> 3. **Every lead in one place** — Calls, texts, and web leads land in a single inbox on your phone. See who's waiting and reply in one tap.
> 4. **Set up done for you** — We build it, connect it to your number, and hand you the keys. You keep answering calls the way you always have.

**NEW**
> *What you get* · **The whole job, covered.**
>
> From the first ring to the review that wins you the next one — here's what runs without you touching it.
>
> **Before the job — get them in the door**
> - Miss a call and a text goes back in seconds, with a link to book
> - Web and Facebook form leads get an instant reply, day or night
> - A booking link that keeps nudging for a week instead of asking once
> - Add someone by hand and they join the same track
>
> **The job — make sure it happens, and gets paid**
> - Confirmation when they book, reminders 24 hours and 1 hour out
> - Cancellations don't vanish — they drop back into follow-up
> - Quotes go out, and get chased when they go quiet
> - Invoice and payment handled in the same place as everything else
>
> **After the job — turn one job into the next**
> - The review request goes out the day after the work wraps
> - Reviews get watched and answered, so your profile isn't sitting stale
> - Referral asks to the customers who liked the work
> - Monthly touches, and a nudge again at 120 days

### What this needs structurally

- Three `<article class="card">` blocks instead of four — same `.cards` grid,
  `repeat(auto-fit, minmax(250px, 1fr))`, renders 3-across and stacks on mobile.
- Each card gains a `<ul>` under its heading. **This is the only new CSS** —
  roughly eight lines to set list spacing and muted text:
  ```css
  .card ul { margin: 14px 0 0; padding-left: 18px; }
  .card li { font-size: 1rem; color: var(--ink-soft); margin-bottom: 8px; }
  .card li::marker { color: var(--accent); }
  ```
- **No new icons needed.** Reuse three of the four existing SVGs: chat bubble →
  *Before the job*, truck → *The job*, refresh/cycle → *After the job*. The
  check-circle frees up for the CRM section below.
- "Running in days" is gone — it promises a delivery time I can't verify. Tell me
  your real typical turnaround and I'll put a true version back.

---

## 6. NEW section — the CRM spine

Sits between the lifecycle cards and the closing CTA. Reuses the existing gray band
(`.problem`) and its point grid (`.problem-points`) — no new CSS. The class name is
now a misnomer; either reuse it as-is or widen the selector to `.problem, .band`
in one line.

> *Underneath all of it* · **One place for every lead, every text, every job.**
>
> Not sticky notes on the dash and a phone full of half-finished threads. Every call, text, quote, and job sits in one system you can open from the truck.
>
> - **Every conversation in one thread.** Calls, texts, and form leads land together, so you can see what was already said without hunting for it.
> - **You always know where someone stands.** New lead, quoted, booked, paid, past customer — tagged as it happens, not when someone remembers.
> - **It lives on your phone.** Reply between jobs. Nothing to install on a desk you never sit at.

---

## 7. Final CTA — `index.html` lines 488–490

**OLD**
> **Stop paying for leads you never answer.**
>
> Fifteen minutes on a call. We'll show you exactly how many jobs you're missing — and how Hero gets them back.
>
> `[Book a Call]`

**NEW**
> **You already paid for these leads. Let's keep them.**
>
> Fifteen minutes. We'll walk your lead path together and find where jobs are falling out — then you decide whether you want it plugged. We build the whole thing; you keep answering the phone the way you always have.
>
> `[Book a Call]`

Button text and `href="https://my.herolgo.com/widget/bookings/alexw-calendar"`
unchanged. "We'll show you exactly how many jobs you're missing" is rewritten — it
promises a specific number before you've seen anyone's phone records.

---

## 8. Footer line — all three pages

`index.html:498` · `privacy.html:327` · `terms.html:273`

**OLD:** © 2026 Hero. Automation for local service businesses.
**NEW:** © 2026 Hero. Lead follow-up and reputation systems for home service trades.

---

## 9. Service descriptions in the legal pages

These must describe what you actually sell. Both stay accurate and A2P-safe;
nothing in the messaging-consent sections changes.

### `privacy.html:234`

**OLD**
> …We provide done-for-you communication and automation systems to local service businesses, including missed-call text-back, automated follow-up, and lead management.

**NEW**
> …We provide done-for-you lead follow-up and customer communication systems for home service businesses, including instant replies to new leads, appointment reminders, quote and invoice follow-up, review requests and reputation management, and a shared CRM for leads and conversations.

### `terms.html:216`

**OLD**
> Hero builds and manages communication and automation systems for local service businesses, including missed-call text-back, automated follow-up, and lead management. The specific scope…

**NEW**
> Hero builds and manages lead follow-up and customer communication systems for home service businesses, including instant replies to new leads, appointment reminders, quote and invoice follow-up, review requests and reputation management, and a shared CRM for leads and conversations. The specific scope…

`terms.html:217` (results are illustrative, no guaranteed outcomes) stays exactly as
written — it now covers payments and reputation too, which matters more than before.

---

## Claims I had to write around

All five below are in your **current** copy. Each was removed or rewritten rather
than carried forward.

1. **"The first business to respond usually wins the job."** (`index.html:415`) — the standard speed-to-lead claim with no source attached. Dropped. Needs a citable study to return.
2. **"A full-time receptionist costs thousands a month."** (`417`) — an unsourced cost claim about third parties. Dropped.
3. **"Built for you. Running in days."** (`458`) — a delivery-time promise I can't verify. Rewritten.
4. **"We'll show you exactly how many jobs you're missing."** (`489`) — promises a number before seeing their records. Rewritten.
5. **"so no job slips away"** (`7`) and **"No caller left hanging, ever."** (`464`) — absolutes that contradict `terms.html:217`. Both softened.

### New claims I deliberately did *not* write

The expanded offer invites result claims. None of these appear anywhere in the new
copy, and none should be added without proof:

- Anything numeric — percent of leads recovered, revenue added, jobs saved, review counts, star-rating changes.
- **"Get paid faster."** Payments are described as a capability, never as a speed result.
- **"More reviews"** or **"a better rating."** The copy says requests go out and reviews get answered — both true by configuration. It never promises the outcome.
- Client names, testimonials, case studies, years in business, number of businesses served.

The strongest claim on the page is that replies go out in seconds — true because
the system is configured that way, not a performance promise.

### One thing to confirm

**A2P 10DLC registration.** Getting a trades business legally texting is real work
and a genuine differentiator, and there's evidence you handle it for client
sub-accounts — but you didn't confirm it, so it appears nowhere in this draft. If
you do it, it belongs in How it works step 02 and would strengthen the
done-for-you story.

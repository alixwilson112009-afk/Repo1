# Positioning rewrite — proposed copy

**Status: proposal only. No source files have been modified.**

Old copy and proposed new copy, section by section. Line numbers refer to the
files as they stand at commit `ce2a2f0`.

**New thesis:** you already pay for leads — ads, SEO, referrals, the truck wrap.
They leak out between "phone rings" and "job gets paid." Hero plugs the leaks.
Missed calls stay in the copy as one leak among six, not the whole story.

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
the truck wrap. Hero catches the ones that leak out between the first call and the
paid invoice. Built for plumbing, HVAC, tree service, and garage door companies.">

<meta property="og:title" content="Hero — Close More of the Leads You Already Have">

<meta property="og:description" content="Stop losing leads you already paid for.
Hero handles the calls, callbacks, quote follow-ups, reminders, and review requests
that fall through the cracks.">
```

**Note:** "so no job slips away" is dropped deliberately — it is an absolute
guarantee, and `terms.html:217` already disclaims guaranteed outcomes. The old
line and the legal page contradict each other today.

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
> Ads, SEO, referrals, the truck wrap — you paid to make that phone ring. Hero catches the leads that leak out between the first call and the paid invoice.
>
> `[Book a Call]`

CTA text and `href="#book"` unchanged.

---

## 3. Problem section — `index.html` lines 410–418

**OLD**
> *The problem*
>
> **Every missed call is a paying job walking away.**
>
> You're on a roof, under a sink, or halfway up a tree. The phone rings. It goes to voicemail. That caller doesn't wait — they dial the next company on the list.
>
> - **Callers don't leave voicemails.** They hang up and call your competitor. The first business to respond usually wins the job.
> - **Your ad spend leaks.** You pay to make the phone ring — every unanswered call is marketing money down the drain.
> - **Hiring isn't the answer.** A full-time receptionist costs thousands a month and still clocks out at five.

**NEW**
> *The problem*
>
> **The leads are already coming in. They're leaking out.**
>
> Nobody loses jobs because the phone never rings. They lose them in the gaps — the call that came in mid-crawlspace, the quote nobody called back on, the appointment nobody confirmed.
>
> - **The call you couldn't take.** Both hands under a sink. It rings out, and they're already dialing the next name on the list.
> - **The callback that came too late.** You call back at six. They booked someone who answered at two.
> - **The quote that went quiet.** You sent the number, they said they'd think about it, and nobody followed up.
> - **The no-show.** Booked Tuesday, forgotten by Thursday. You drove out for nothing.
> - **The leads from three months ago.** A list of people who wanted work done. Nobody has touched it since.
> - **The job that never got a review request.** Good work, happy customer, no review. The next person searching never hears about it.

### ⚠️ Item count changes here: 3 → 6

This is the only place the number of components changes. The container is
`repeat(auto-fit, minmax(240px, 1fr))` (`index.html:180`), so six items reflow to
3-across × 2 rows on desktop and stack cleanly on mobile — no CSS change, no new
component. But it *is* more markup than exists today, so it needs your yes.

**If you'd rather keep exactly three:** name all six leaks in the lede and keep
three grouped points — *Leads go cold before you call back* / *Quotes and old
leads never get a second try* / *Finished jobs never turn into reviews*. Say the
word and I'll write that version instead.

**Two old points get dropped:** "Your ad spend leaks" is now the site's main
promise, so it moves up to the hero. "Hiring isn't the answer" is a good
objection-handler with nowhere obvious to live — I can re-home it in the closing
section if you want it kept.

---

## 4. How it works — `index.html` lines 426–447

**OLD**
> *How it works*
>
> **The moment you miss a call, Hero answers.**
>
> 01 **A call slips through** — You're on a job. The call rings out or hits voicemail.
> 02 **Hero texts them back** — Within seconds, the caller gets a text from your business number — before they can dial anyone else.
> 03 **The job stays yours** — The conversation continues by text. You reply when you're free, and the lead books with you.

**NEW**
> *How it works*
>
> **We find the leaks, then we plug them.**
>
> 01 **We walk your lead path** — Start to finish, from the first ring to the paid invoice. We find where jobs are falling out.
> 02 **We build the plugs** — Instant replies, follow-up, reminders, review requests — running on your number and your calendar. You don't build anything.
> 03 **You just do the work** — The chasing runs itself. You answer the phone the way you always have and pick up the ones worth your time.

### Figure caption — line 446

**OLD**
> The full Hero system: instant text-back, booking nudges, appointment reminders, review and referral requests, and long-term reactivation — every step on autopilot.

**NEW**
> Every step from first contact to review request: instant replies, follow-up on quiet leads, appointment reminders, and a review ask once the job is done. The parts that used to depend on someone remembering now run on their own.

### Image alt text — line 440

**OLD**
> Flowchart of the Hero automation. Leads from missed calls, answered calls, or marketing forms get an instant text with a booking link, then a week of booking nudges. Booked appointments get confirmations and reminders; after the job, a review and referral request, then a reactivation text 120 days later. Unbooked leads move into long-term monthly nurture.

**NEW**
> Flowchart of the Hero system. Leads arrive from phone calls, marketing forms, or added by hand. Missed calls get an instant text back with a booking link; answered calls are handled live. Every lead is tagged and enters a week of booking nudges. Booked appointments get confirmations and reminders 24 hours and 1 hour ahead. After the job, a review and referral request goes out, then a reactivation message 120 days later. Leads that never book move into long-term monthly nurture.

### Image link label — line 437

**OLD:** `Open the automation diagram at full size`
**NEW:** `Open the lead path diagram at full size`

**Good news on the diagram itself:** `assets/automation-flow.png` already shows the
whole lifecycle — booking nudges, reminders, review requests, 120-day reactivation
— so it supports the new angle without being redrawn. Its labels are baked into
the PNG, so if you later rename steps, the image has to be re-rendered.

---

## 5. What you get — `index.html` lines 457–479

**OLD**
> *What you get* · **Built for you. Running in days.**
>
> 1. **Missed-call text-back** — Every unanswered call gets an instant, personal-sounding text from your number. No caller left hanging, ever.
> 2. **Automated follow-up** — Leads that go quiet get a polite nudge automatically. No sticky notes, no "I meant to call them back."
> 3. **Every lead in one place** — Calls, texts, and web leads land in a single inbox on your phone. See who's waiting and reply in one tap.
> 4. **Set up done for you** — We build it, connect it to your number, and hand you the keys. You keep answering calls the way you always have.

**NEW**
> *What you get* · **Built for you. Running on your number.**
>
> 1. **Every lead gets an answer** — Missed call, web form, nine at night — a reply goes out from your number in seconds with a link to book. Nobody sits around waiting on a callback.
> 2. **Quotes and old leads get chased** — Quiet quotes get a nudge. Leads from months back get another look. No sticky notes, no "I meant to call them back."
> 3. **Fewer empty driveways** — Confirmations and reminders go out ahead of the appointment, so fewer people forget you're coming.
> 4. **Reviews after the job** — When the work wraps, the review request goes out on its own. Good jobs turn into the reviews that win the next one.

Card count, icons, and order of components unchanged — copy only.

### Two decisions inside this section

**a) "Running in days" → "Running on your number."** The original promises a
delivery time. I can't verify your typical setup time, so I wrote around it. If
days is genuinely what you deliver, say so and I'll put it back.

**b) Two features lose their card.** "Every lead in one place" (single inbox) and
"Set up done for you" get displaced by the leak-plug cards. Done-for-you survives
in How it works step 02 ("You don't build anything") and in the closing. The
single inbox currently appears nowhere in the new copy. Options: fold it into card
1 as a closing line, or expand to six cards — the grid is
`repeat(auto-fit, minmax(250px, 1fr))` and would reflow to 3×2 without CSS
changes. Your call.

---

## 6. Final CTA — `index.html` lines 488–490

**OLD**
> **Stop paying for leads you never answer.**
>
> Fifteen minutes on a call. We'll show you exactly how many jobs you're missing — and how Hero gets them back.
>
> `[Book a Call]`

**NEW**
> **You already paid for these leads. Let's keep them.**
>
> Fifteen minutes. We'll walk your lead path together and find where jobs are falling out — then you decide whether you want it plugged.
>
> `[Book a Call]`

Button text and `href="https://my.herolgo.com/widget/bookings/alexw-calendar"`
unchanged. "We'll show you exactly how many jobs you're missing" is rewritten
because it promises a specific number before you've seen their phone records.

---

## 7. Footer line — all three pages

`index.html:498` · `privacy.html:327` · `terms.html:273`

**OLD:** © 2026 Hero. Automation for local service businesses.
**NEW:** © 2026 Hero. Lead follow-up systems for home service trades.

---

## 8. Service descriptions in the legal pages

These describe the business and should match how you now describe it. Both stay
accurate and A2P-compliant; nothing in the messaging-consent sections changes.

### `privacy.html:234`

**OLD**
> …We provide done-for-you communication and automation systems to local service businesses, including missed-call text-back, automated follow-up, and lead management.

**NEW**
> …We provide done-for-you lead follow-up systems for home service businesses, including instant replies to new leads, follow-up on quotes and older leads, appointment reminders, and review requests.

### `terms.html:216`

**OLD**
> Hero builds and manages communication and automation systems for local service businesses, including missed-call text-back, automated follow-up, and lead management. The specific scope…

**NEW**
> Hero builds and manages lead follow-up systems for home service businesses, including instant replies to new leads, follow-up on quotes and older leads, appointment reminders, and review requests. The specific scope…

`terms.html:217` (the "results are illustrative, we don't guarantee outcomes"
disclaimer) stays exactly as written — it covers the new copy too.

---

## Unchanged on purpose

- All CTA text (`Book a Call`) and every `href` — nav, hero, closing, footer, policy links.
- Nav wordmark, logo, favicon, `aria-label="Hero — home"`.
- All eyebrow labels (*The problem*, *How it works*, *What you get*).
- Every section's structure, classes, reveal delays, and styling.
- Skip links, the mobile zoom hint, and the image fallback string.
- Everything in `privacy.html` and `terms.html` except the two service
  descriptions and the footer line — the A2P-critical mobile opt-in clause,
  STOP/HELP instructions, and consent language are untouched.

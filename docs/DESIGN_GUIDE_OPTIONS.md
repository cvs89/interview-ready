# Interview Ready: design directions and competitor guide
Date: 4 October 2026
Status: user approved **Direction 04 — The Confidence Club** on 4 October 2026. Application styling remains unchanged; detailed mockups and implementation are pending.
Visual comparison: [Open four concept boards](design-options.html).

## Brief and reference
The supplied five-page BeHired PDF is a reference for presentation quality and a coherent design system: restrained palettes, clear typography, component specimens, a landing page, candidate dashboard, mobile layouts and an operational workspace. Its green palette, logo, subscription plans and managed-job-application workflow are not Interview Ready requirements.

Interview Ready is a paid human mock-interview marketplace: discover an approved interviewer, select a time, pay for that slot, join through the desktop application, then receive structured feedback. The local project tracker reports Modules 01–13 implemented; that implementation status has not been independently re-audited for this design exercise.

Proposed positioning: “Real interview practice. Specific feedback. A clearer next step.”
Do not promise hiring outcomes. Explain what platform approval means rather than implying every employment claim has been independently verified.

## Four directions
| Direction | Personality | Core palette | Typography proposal | Best use |
|---|---|---|---|---|
| 01 — The Human Coach | Calm, human, reassuring | Emerald #176B52; mint #D9F0E3; cream #F5F1E8; ink #17251F | Hanken Grotesk with Instrument Serif accent words | Broad candidate audience; closest to the supplied reference |
| 02 — The Career Studio | Clear, polished, professional | Cobalt #304EC8; pale blue #E4EAFE; cloud #F7F8FC; ink #17243C | Manrope headings; Inter interface | Unselected alternative |
| 03 — The Interview Lab | Focused, technical, precise | Lime #B5E56A; forest #27352D; slate #131B20; white #F1F5F2 | Space Grotesk headings; Inter UI; monospace timers | Engineering and system-design audience |
| 04 — The Confidence Club | Warm, editorial, encouraging | Terracotta #9B3B25; peach #F8DDC9; ivory #FFF8F0; ink #342523 | Lora editorial headings; DM Sans interface | Career switchers and behavioural interview practice |

These are distinct visual directions, not four product concepts. The HTML compares the same sample journey to make selection easier. Proposed font families are not downloaded; the preview uses system-font approximations.

### 01 — The Human Coach
Use generous whitespace, authentic interviewer portraits, rounded 20px cards and pill buttons. Serif emphasis belongs in marketing headlines only. Candidate dashboard: next session first, useful feedback second. Desktop: warm light panels around a neutral dark video stage.
Hero: “Go into your next interview with confidence.”
Risk: resembles familiar career-service branding. Differentiate through expert specialisms, useful feedback samples and clear session details rather than decorative green shapes.

### 02 — The Career Studio — unselected alternative
Use a restrained blue identity, 16px cards, 10px buttons and strong alignment. Expert cards lead with relevant skills, role, session price and next available time. A two-column booking page pairs a calendar with a stable price summary. Candidate dashboard uses compact session rows; the desktop room uses the same components with dark video surfaces.
Hero: “Your next interview. Practised properly.”
Risk: generic SaaS appearance. Give real interviewer identity and actual rubric examples more prominence than abstract illustrations.

### 03 — The Interview Lab
Use a dark slate foundation with lime for primary actions, crisp 8px panels and restrained borders. Use tabular numbers for time and duration; keep ordinary UI in a readable sans-serif. Marketplace filters are compact; the interview room gives video, workspace and notes clear boundaries.
Hero: “Practice under pressure. Learn with clarity.”
Risk: a dark-first product may narrow perceived relevance to engineers. Offer a light reading surface for long feedback and avoid terminal-like styling for ordinary forms.

### 04 — The Confidence Club — approved
Use ivory, terracotta, expressive editorial headlines and 24px cards. Marketing can feature candid portraits and gentle organic shapes. Booking and payments retain straightforward tables, labels and clear totals. Desktop uses quieter surfaces than the landing page.
Hero: “Big ambitions. A little more practice.”
Risk: excessive warmth can reduce the feeling of precision. Keep session logistics, prices and feedback scales explicit.

## Recommended shared design system
Use the approved Confidence Club direction and the same component vocabulary across web and desktop. The other three directions are retained for reference only.

- Spacing: 4, 8, 12, 16, 24, 32, 48, 64 and 96px.
- Typography: marketing display 48–64px desktop / 36–40px mobile; page heading 32px; section heading 24px; body 16px with 1.5 line-height; secondary labels 14px.
- Layout: 1200px content width, 24–32px desktop gutters, 16px mobile gutters. Long feedback text should remain approximately 60–75 characters per line.
- Components: primary/secondary/destructive buttons, labelled fields, filter chips, interviewer cards, slot selectors, booking summary, countdown, status badge, feedback rubric, dialogs, toasts and empty states.
- Accessibility acceptance targets: 4.5:1 normal text contrast; 3:1 large text and essential UI boundaries; visible keyboard focus; 44px touch targets as a product target; reduced-motion support. Verify every actual token combination before approval.
- Status is conveyed through text and icon as well as colour. Brand accents must not replace semantic success, warning and error treatments.
- Motion: short 120–180ms transitions; avoid movement or animation during an active interview.
- Logo: explore a simple “ir” monogram or conversation/check symbol after direction selection. Do not reuse BeHired’s logo. Keep the product name Interview Ready unless a rename is separately approved.

## Screen guide
### Public home
1. Plain-language promise and “Find an interviewer” action.
2. Real sample of an interviewer card and feedback report.
3. Four steps: choose an expert, book a slot, practise live, review feedback.
4. Relevant interview categories.
5. Verified customer evidence when available; omit invented statistics and logos.
6. FAQ covering preparation, cancellation and desktop requirements.

### Marketplace and booking
Show speciality, experience, approval badge, real review count when available, session length, price and next available slot. Mobile filters open in a labelled sheet and retain selections. State the timezone beside all time choices. Show currency and full total clearly. Explain the desktop requirement before payment.

Slot selection progresses to a server-backed reservation countdown. A successful checkout redirect must not imply payment confirmation: show “Payment processing” until trusted backend confirmation. Handle expiry with “Choose another time” and preserve relevant search context.

### Candidate dashboard and mobile
Prioritise the next confirmed session, its timezone and a preparation checklist. Separate upcoming, completed and cancelled sessions. Provide direct feedback access from completed sessions. Mobile supports discovery, booking and feedback; the current live interview flow requires desktop. Explain how to continue on a computer instead of presenting a broken mobile join button.

### Desktop live room
Device check before joining; visible microphone, camera and leave controls. Interviewer layout: video beside rubric and explicitly private notes. Candidate layout: video and authorised shared workspace only. Never show private interviewer notes to candidates. Make connection loss, reconnecting, permissions denied and session ended visibly distinct. Recording indicators should exist only if recording is actually implemented and consent is handled.

### Feedback
Show the rubric scale, concrete examples, strengths and prioritised next steps. Distinguish draft from submitted feedback. Do not invent readiness percentages or trend charts without valid comparable data.

### Interviewer and admin
Interviewer: upcoming sessions, availability calendar, pricing and verification state. Reserved/booked slots have protected actions. Admin: denser tables, clear review decisions and audit context; avoid visual clutter and accidental destructive actions.

## Required state designs
| Area | States to design |
|---|---|
| Search | Loading, results, no matches, unavailable service |
| Verification | Pending, in review, approved, rejected |
| Slot | Available, selected locally, reserved, booked, blocked, expired reservation |
| Payment | Pending, processing, confirmed, failed; cancellation/refund labels aligned to backend |
| Join | Too early with opening time, eligible, ticket expired/retry, app missing, window closed |
| Session | Device permission needed, connecting, connected, reconnecting, ended |
| Feedback | Awaiting submission, draft for interviewer, submitted for candidate, no feedback yet |

## Competitor research

Expanded research: [Competitor report — 4 October 2026](COMPETITOR_RESEARCH_2026-10-04.md). This supersedes the limited categorisation below: Aced also offers paid human coaching and is a direct competitor, not only a peer/AI practice alternative.

Researched 4 October 2026 from official public pages. Capabilities below are observations; design lessons and positioning opportunities are recommendations. No purchase, logged-in product inspection or full competitor usability audit was performed. Pricing is deliberately not compared because currencies, packages and services differ.

| Competitor | Relationship | Observed offering | What Interview Ready can learn |
|---|---|---|---|
| [IGotAnOffer](https://igotanoffer.com/en/interview-coaching) | Direct | Coach discovery with role/company/availability filters; scheduled mock interviews and expert feedback | Put coach fit, availability and trust evidence close to the booking action. Its credit mechanism is not part of this project's per-slot payment model. |
| [interviewing.io](https://interviewing.io/) | Direct, especially technical | Anonymous technical practice, human mentorship and an AI interviewer offering | Explain the realism and format of a session clearly. Make privacy expectations and feedback tangible. Do not imply Interview Ready already supports anonymity or AI interviews. |
| [Aced, formerly Exponent](https://www.aced.io/practice) | Alternative practice ecosystem | Peer and AI mock-interview practice; the Exponent practice URL redirects to Aced | Help candidates pick the appropriate practice type. Paid human expertise must have a clear, credible reason to choose it. |
| [Topmate](https://topmate.io/) / [interview-prep example](https://topmate.io/interviewprep) | Adjacent expert-booking marketplace | Creator storefronts and bookable services, including interview-prep providers | Keep expert identity, service description and booking simple. Interview Ready can focus its interface on interview-specific logistics and structured feedback. |

Upwork and scale.jobs appear in the supplied reference because BeHired is a different product. They are not the primary competitive set for this human mock-interview marketplace.

## Positioning opportunity
Make the complete practice loop visible: choose the right interviewer, know the exact price and time, prepare for the desktop session, then receive specific feedback. This is a proposed emphasis, not a claim that competitors lack those capabilities.

## Next design deliverable
Produce one detailed system and five high-fidelity screens in the chosen direction: public home, marketplace/profile and booking, candidate dashboard, mobile booking/feedback, and desktop interview workspace. Include type scale, colour tokens, component states, accessibility checks and real responsive variants.

## Handoff to another AI or designer
Read this guide and PROJECT_STATUS.md. Direction 04, The Confidence Club, is already selected; do not ask the user to select again. Develop detailed mockups in that direction; application restyling remains pending. Use docs/design-options.html as a concept reference, not as production components. All sample names, prices, times and scores are illustrative. Preserve backend-driven payment/join/role rules. Update the project tracker when detailed design or implementation begins.

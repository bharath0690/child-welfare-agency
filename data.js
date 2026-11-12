/* Priority personas. ts = how the stage feels today, ps = intended feeling with the product, scale -2 to 2. ns = needs a surface not described on the platform's public site. */
var PRI = [
 { name: "Caseworker", cat: "Daily operators",
   why: "Carries the largest administrative load and touches the most modules, so time returned here helps every other team. Your priority is work that feels rewarding, so this journey follows one case from the first day to close, with reward moments built in.",
   pr: ["Capture once, reuse everywhere. Anything said or recorded in the field feeds notes, plans, court reports and state reporting.",
        "Reward with time and progress. Show hours returned and steps completed for families, and keep scores and rankings away from child outcomes.",
        "Keep the worker in charge. AI drafts, and the worker reviews and signs."],
   extra: { t: "Reward moments to design in", items: [
     "Time back: a weekly view of minutes saved per visit note and per court report.",
     "Progress made visible: relatives found, services started and plan steps completed for each family.",
     "Milestones: a quiet marker when a child is placed with kin, a family is reunified or a case closes at permanency, shared with the supervisor.",
     "Specific recognition: a prompt for supervisors to acknowledge named work, such as a thorough kin search.",
     "Avoid points, streaks and rankings tied to child outcomes."] },
   st: [
    { n: "Start the day", g: "Know what matters today.", fr: "Builds the day from spreadsheets, sticky notes and email.", fl: "Scattered", ts: -1, ps: 1, ns: 1,
      pd: "A My day view lists today's visits, court dates, overdue tasks and referrals awaiting a reply, ordered by urgency, with one tap to open the family.", m: "cm,prv", sg: "Minutes to plan the day, overdue tasks" },
    { n: "Accept a new case", g: "Understand the family before the first visit.", fr: "The handoff packet is thin or scattered, and history sits in other systems.", fl: "Uneasy", ts: -1, ps: 1,
      pd: "A case summary pulls together prior reports, investigation findings, the family network found so far and open questions, with a note from the supervisor.", m: "cm,int,inv,ffe", sg: "Questions re-asked of the family or colleagues" },
    { n: "Build the plan with the family", g: "Agree goals and services the family will use.", fr: "Plans live in documents and referrals go out by email.", fl: "Slowed down", ts: 0, ps: 1,
      pd: "A guided plan turns goals into dated tasks. Referrals go to providers from the plan, and their status comes back to the caseworker.", m: "cm,prv", sg: "Plans completed on time, referrals confirmed" },
    { n: "Visit and capture", g: "Spend the visit with the family, not the keyboard.", fr: "Notes are written in the field and again in the system.", fl: "Behind", ts: -1, ps: 2,
      pd: "Record the visit and Agency AI drafts the note and form fields for the worker to review and sign. Design for patchy signal in the field (to confirm).", m: "cm,ai", sg: "Minutes from visit to finished note" },
    { n: "Find and engage kin", g: "Find a relative who can care for the child.", fr: "Searches run across separate tools, trees are drawn by hand and outreach is tracked by hand.", fl: "Frustrated", ts: -1, ps: 2,
      pd: "Search records, see a genogram that updates itself, send templated outreach in the relative's language and see who has responded, all on the child's record.", m: "ffe,ai", sg: "Relatives identified and responding" },
    { n: "Prepare for court", g: "Give the court a clear, accurate report.", fr: "Facts are pulled from many places the night before.", fl: "Pressured", ts: -2, ps: 0,
      pd: "A court report drafts itself from visit notes, plan progress, services and kin efforts. The worker edits and approves, and efforts to find relatives are already documented.", m: "cm,ffe,ai", sg: "Hours to prepare a report" },
    { n: "Reach permanency and close", g: "Finish well and move on.", fr: "Closing data and reports are re-entered, and nothing marks the outcome.", fl: "Drained", ts: 0, ps: 2,
      pd: "A closing checklist pre-fills from the case, compliance data has been captured as the work happened, and the case shows its outcome, such as a child placed with kin, to the worker and supervisor.", m: "cm,rpt", sg: "Time to close, data corrections" }
   ] },
 { name: "Prospective foster or adoptive parent", cat: "People served and caregivers",
   why: "Your priority is new parents applying for a license. This journey is the supply of homes, so every delay here is a child waiting longer. It also sits wholly inside the licensing module, which makes it the clearest place to improve.",
   pr: ["Always show where I am, what is left and what happens next.",
        "Ask once. Reuse everything the family has already given.",
        "Mobile first, plain language, and in the family's own language."],
   st: [
    { n: "Explore", g: "Decide whether to foster or adopt, and what it takes.", fr: "The process is hard to understand and the timeline is unclear.", fl: "Curious, unsure", ts: 0, ps: 1, ns: 1,
      pd: "A plain-language page shows the steps, a typical timeline and what each step asks of the family, with a clear way to start on a phone.", m: "lic", sg: "Visitors who start an inquiry" },
    { n: "Inquire", g: "Get a person and a next step.", fr: "Finds the agency, submits an inquiry, then waits.", fl: "Waiting", ts: -1, ps: 1,
      pd: "A short inquiry captures the basics and routes to a named worker, with an acknowledgement and the next step.", m: "lic", sg: "Time to first response" },
    { n: "Apply", g: "Finish the application without starting over.", fr: "Paper forms and repeated entry.", fl: "Frustrated", ts: -1, ps: 1,
      pd: "A mobile application saves as the family goes, resumes on any device and shows progress. What is entered once feeds every later form.", m: "lic,ai", sg: "Completion rate, time to submit" },
    { n: "Complete requirements", g: "Know exactly what is outstanding.", fr: "Unsure what is outstanding, and documents are requested again.", fl: "Anxious", ts: -2, ps: 1,
      pd: "A checklist shows consents, background checks, references and training with their status. References are requested automatically.", m: "lic,api", sg: "Document requests per family" },
    { n: "Home study", g: "Prepare for the visit and get through it.", fr: "The family does not know in advance what the visit checks (to validate).", fl: "Nervous", ts: -1, ps: 1,
      pd: "A booking step and a checklist of what the visit covers. The worker completes the forms digitally during the visit, with a draft from Agency AI.", m: "lic,ai", sg: "Days from booking to completed study" },
    { n: "Approval and wait", g: "Know when a decision will come.", fr: "A long, unclear wait with little visibility.", fl: "Left waiting", ts: -2, ps: 0,
      pd: "Status shows where the application sits, what remains and an expected timeframe. The approval notice arrives with the next steps.", m: "lic", sg: "Status enquiries by phone, days to approval" },
    { n: "Get matched", g: "Start with confidence.", fr: "Little guidance on a first placement.", fl: "Uncertain", ts: 0, ps: 2,
      pd: "Preferences and capacity go to placement. The family gets a placement call that describes the child's needs in plain terms, and a named contact for the first weeks.", m: "lic,plc,ai", sg: "Placements accepted, support contacts in month one" }
   ] },
 { name: "Kin caregiver", cat: "People served and caregivers",
   why: "Your third priority is a persona with heavy friction today. Kin caregivers meet friction at every stage, from the first call to the long-term plan, and kin placement is a stated goal of the platform. Most of the fix uses modules that already exist.",
   pr: ["Meet them in the moment. The first contact is often a shock, so explain it in plain words and in their language.",
        "Show what is needed now and what can wait.",
        "Treat them as caregivers who need support, not only as applicants."],
   st: [
    { n: "The first contact", g: "Understand why they are being contacted.", fr: "Contacted late. The notice is hard to understand or in the wrong language.", fl: "Shocked", ts: -2, ps: 0,
      pd: "Outreach in the relative's language explains who is asking, why, and what the options are, and gives a person to talk to.", m: "ffe,ai", sg: "Response rate, time to response" },
    { n: "Weigh the decision", g: "Know what saying yes involves.", fr: "Requirements are unclear and each option is poorly explained.", fl: "Overwhelmed", ts: -2, ps: 0, ns: 1,
      pd: "A short guide sets out the options (care, contact, support), the approval steps, the financial help available and the legal paths, in plain terms.", m: "ffe", sg: "Questions put to the worker" },
    { n: "Say yes", g: "Get the child safely into their care.", fr: "The child may be placed while approval is still running.", fl: "Stretched", ts: -2, ps: 0,
      pd: "Shows what is required now and what can follow, and records the response in the child's family network. Rules for placing before approval vary by jurisdiction.", m: "ffe,plc", sg: "Time from yes to placement" },
    { n: "Get approved", g: "Complete approval without repeating themselves.", fr: "Checks and home requirements start from zero.", fl: "Anxious", ts: -1, ps: 1,
      pd: "Information already gathered in family finding carries into the approval steps, with a checklist and status the caregiver can see.", m: "lic,ffe", sg: "Days to approval, repeated requests" },
    { n: "The first weeks", g: "Get money and services in place.", fr: "Fewer supports than licensed parents, and financial strain.", fl: "Strained", ts: -2, ps: 0, ns: 1,
      pd: "One list of what the caregiver can apply for (financial help, services, supports), with applications started from what the agency already knows and a named contact.", m: "elg,prv", sg: "Time to first payment, supports in use" },
    { n: "Everyday care", g: "Handle school, health, visits and court.", fr: "Information arrives by phone or email.", fl: "Stretched", ts: -1, ps: 1, ns: 1,
      pd: "A caregiver view with the child's appointments, visits, court dates and contacts.", m: "cm", sg: "Missed appointments, calls to the worker" },
    { n: "Plan the long term", g: "Understand and choose a permanent path.", fr: "The legal path to guardianship or adoption is unclear.", fl: "Uncertain", ts: -1, ps: 1, ns: 1,
      pd: "Options explained with next steps and who to talk to, linked to the case plan.", m: "cm", sg: "Caregivers with a documented permanency plan" }
   ] }
];

/* Module names, keyed by the ids used in the "m" field above. */
var MODN = {
  int: "Intake", inv: "Investigations", lic: "Licensing", plc: "Placement", cm: "Case management",
  ffe: "Family finding and engagement", prv: "Provider network", elg: "Eligibility and payments",
  rpt: "Reporting", api: "Integrations", ai: "Agency AI", cfg: "Configuration"
};

/* Caseworker journey: Maya Alvarez, Cedar County Child Welfare. The Harper family is fictional. */
(function () {
  var S = H.S, ACT = H.ACT, esc = H.esc, card = H.card, btn = H.btn, has = H.has;
  var SC = H.SCR.caseworker;

  H.CHATS.cw = {
    intro: "Ask me about your cases. I answer from the case record and show where each answer comes from.",
    fallback: "I can't find that in the Harper record. Try one of the suggested questions, or open the case file.",
    qa: [
      { q: "What changed on the Harper case this week?", k: ["change", "week", "new"], s: "Visit note 14 Oct, referral log, school email 15 Oct",
        a: "Three things: Dana and the children are now staying with Dana's mother, Rosa Delgado. Eli is back at school. The counseling referral to Bright Path has no reply yet." },
      { q: "Which tasks are overdue?", k: ["overdue", "late", "task"], s: "Task list, case plan v2",
        a: "One: the school-records consent for Eli, due 12 Oct. Two items are due this week: the Bright Path follow-up and the court report on Thursday." },
      { q: "Who could the children stay with?", k: ["kin", "relative", "who", "family"], s: "Genogram, Dana's emergency contacts",
        a: "Rosa Delgado (maternal grandmother) is already housing the family and is listed as Dana's emergency contact. Marco Delgado (maternal uncle) is a possible second contact, not yet reached. The father's whereabouts are unknown." },
      { q: "What did Dana say about the counselor?", k: ["counsel", "dana", "bright"], s: "Visit note 14 Oct",
        a: "Dana left Bright Path a message on Monday and is waiting for a reply. She is open to counseling." }
    ]
  };

  /* 0 · Start the day */
  SC[0] = function () {
    var tasks = [
      ["t1", "9:00 Home visit, Harper family", "Eli (7), Nora (4), Dana Harper"],
      ["t2", "School-records consent for Eli", "2 days overdue"],
      ["t3", "Follow up with Bright Path", "Referral sent 3 days ago, no reply"],
      ["t4", "Court report, Harper", "Due Thursday"]
    ];
    var t = tasks.map(function (x) {
      return "<label class='task" + (has(x[0]) ? " done" : "") + "'><input type='checkbox' data-act='toggle' data-arg='" + x[0] + "'" + (has(x[0]) ? " checked" : "") + "><span class='t'><b>" + x[1] + "</b><br><span class='small muted'>" + x[2] + "</span></span></label>";
    }).join("");
    return "<div class='row between'><h3>Good morning, Maya</h3><span class='muted small'>Tuesday</span></div>" +
      H.aiBanner("Built from your calendar, tasks and case notes.") +
      card("Your day in short", "<p>Four things need you today. The 9:00 Harper visit matters most: the counseling referral has had no reply in three days, so ask Dana whether she has heard from Bright Path. The school-records consent is two days overdue and Eli's school asked for it twice.</p><div style='margin-top:8px'>" + H.rate("cw-day", "Start-of-day summary", [10, 2]) + "</div>") +
      "<div class='grid2'>" + card("Today, ordered by urgency", t) + card("What your week looks like", "<div class='stack'><div class='tile'><b>3 h 40 min</b>returned to you this week (illustrative)</div><div class='tile'><b>6 of 9</b>Harper plan steps completed</div><div class='tile'><b>2</b>relatives found on the Harper case</div></div><p class='small muted' style='margin-top:8px'>Time and progress only. No scores or rankings.</p>") + "</div>" +
      H.chat("cw", "Chat with Agency AI");
  };

  /* 1 · Accept a new case */
  SC[1] = function () {
    return "<div class='row between'><h3>Harper family · new assignment</h3>" + (has("reviewed") ? "<span class='chip'>Reviewed</span>" : btn("Mark as reviewed", "toggle", "reviewed", "pri")) + "</div>" +
      H.aiBanner("Summary of prior reports, investigation findings and the family network. Check it against the full file.") +
      "<div class='grid2'>" +
      card("Why the family is here", "<p class='small'>Housing instability and missed school days. No injuries reported. Investigation closed 3 Oct with services recommended.</p><p class='small muted' style='margin-top:6px'>Sources: " + H.src("Intake 18 Sep") + " " + H.src("Investigation 3 Oct") + "</p>") +
      card("History", "<p class='small'>Two earlier reports (2023, 2024), both screened out. No prior placements.</p><p class='small muted' style='margin-top:6px'>Sources: " + H.src("Intake log") + "</p>") +
      card("Family network so far", "<p class='small'><b>Dana Harper</b>, mother. <b>Rosa Delgado</b>, maternal grandmother, not yet contacted. Father's whereabouts unknown.</p>") +
      card("Open questions", "<ul class='small' style='margin:0;padding-left:18px'><li>Is there a safe relative who could help?</li><li>Language preferences: Dana, English. Rosa, Spanish.</li><li>School records not yet released</li></ul>") + "</div>" +
      card("Note from your supervisor", "<p class='small'>Sam Whitfield: \"Dana is engaged. Please look at kin early, and call me after the first visit.\"</p>") +
      H.rate("cw-case", "Case summary", [30, 5]) + H.chat("cw", "Chat with Agency AI");
  };

  /* 2 · Plan: referrals with closed-loop status */
  var REF = ["Not sent", "Sent", "Received", "Intake booked"];
  SC[2] = function () {
    var r = +(S.f.ref || 0);
    var steps = REF.map(function (_, i) { return "<i class='" + (i <= r ? "on" : "") + "'></i>"; }).join("");
    var tl = ["Plan v2 agreed with Dana, 10 Oct", "Referral to Bright Path (family counseling)", "School-records consent signed", "Visit schedule: weekly until 5 Nov"];
    return "<div class='row between'><h3>Case plan · Harper</h3><span class='chip'>6 of 9 steps done</span></div>" +
      card("Goals and dated tasks", "<div class='tl'>" + tl.map(function (x, i) { return "<div class='" + (i < 3 ? "on" : "") + "'><span>" + x + "</span></div>"; }).join("") + "</div>") +
      card("Referral: Bright Path family counseling", "<p class='small muted'>Status comes back to you. No more chasing by email.</p><div class='steps' style='margin:10px 0'>" + steps + "</div><p><b>" + REF[r] + "</b></p><div class='row' style='margin-top:8px'>" +
        (r === 0 ? btn("Send referral from plan", "adv", null, "pri") : r < 3 ? btn("Simulate provider update", "adv", null) : "<span class='chip'>Intake booked 21 Oct. Dana notified.</span>") + (r > 0 ? btn("Reset", "advReset", null, "sm") : "") + "</div>");
  };
  ACT.adv = function () { S.f.ref = Math.min(3, +(S.f.ref || 0) + 1); H.render(); };
  ACT.advReset = function () { S.f.ref = 0; H.render(); };

  /* 3 · Visit and capture */
  var LINES = [
    ["Maya", "How have the last two weeks been?"],
    ["Dana", "Better. We're staying with my mom, Rosa, until the lease is sorted. Eli's back at school."],
    ["Maya", "Has Bright Path called you?"],
    ["Dana", "Not yet. I left them a message Monday."],
    ["Dana", "Nora keeps asking about her dad. I don't know where he is."]
  ];
  var DRAFT_BAD = "Visit 14 Oct, 9:00, at the home of Rosa Delgado. Dana reports the family is staying with her mother while housing is resolved. Eli has returned to school. Dana failed to follow up with Bright Path. Nora has asked about her father, whose whereabouts are unknown.";
  var DRAFT_FIX = "Visit 14 Oct, 9:00, at the home of Rosa Delgado. Dana reports the family is staying with her mother while housing is resolved. Eli has returned to school. Dana left a message for Bright Path on Monday and is waiting for a reply. Nora has asked about her father, whose whereabouts are unknown.";
  SC[3] = function () {
    var rec = +(S.f.rec || 0), h = "<div class='row between'><h3>Home visit · Harper</h3><span class='chip" + (rec === 1 ? " gap" : "") + "'>" + (rec === 0 ? "Not recording" : rec === 1 ? "Recording" : "Recording stopped") + "</span></div>";
    h += card("Before you start", "<label class='task'><input type='checkbox' data-act='toggle' data-arg='consent'" + (has("consent") ? " checked" : "") + "><span>Dana agreed to the visit being recorded and transcribed, and knows she can say no. <span class='muted small'>Nothing records without this.</span></span></label><div class='row' style='margin-top:6px'>" +
      (rec === 0 ? btn("Start recording", "recStart", null, "pri", !has("consent")) : rec === 1 ? btn("Stop and draft note", "recStop", null, "pri") : btn("Start over", "recReset", null, "sm")) + "</div>" +
      "<p class='small muted' style='margin-top:6px'>Works offline in the field and syncs when signal returns (to confirm).</p>");
    if (rec >= 1) {
      var n = rec === 2 ? LINES.length : +(S.f.recN || 0);
      h += card("Live transcript", LINES.slice(0, n).map(function (l) { return "<div class='tr'><b>" + l[0] + ":</b> " + esc(l[1]) + "</div>"; }).join("<div style='height:6px'></div>") || "<p class='small muted'>Listening…</p>");
    }
    if (rec === 2) {
      var fixed = has("fix"), draft = fixed ? DRAFT_FIX : DRAFT_BAD;
      var shown = fixed ? esc(draft) : esc(draft).replace("Dana failed to follow up with Bright Path.", "<mark>Dana failed to follow up with Bright Path.</mark>");
      h += H.aiBanner("Drafted from the transcript. You decide what goes in the record.") +
        "<div class='grid2'>" + card("Visit note", "<p>" + shown + "</p>" +
        (fixed ? "<p class='small' style='margin-top:8px'><span class='chip'>Language check passed</span></p>" : "<div class='ai-box' style='margin-top:10px'><b>Language check</b><p class='small'>\"Failed to follow up\" puts the blame on Dana. In the transcript she says she left a message on Monday.</p>" + btn("Use suggested wording", "toggle", "fix", "ai") + "</div>")) +
        card("Form fields, filled from the visit", "<table class='t'><tr><td>Visit date</td><td class='prefill'>14 Oct, 9:00</td></tr><tr><td>Location</td><td class='prefill'>Home of Rosa Delgado</td></tr><tr><td>Present</td><td class='prefill'>Dana, Eli, Nora</td></tr><tr><td>School attendance</td><td class='prefill'>Eli back at school</td></tr><tr><td>Referral follow-up</td><td class='prefill'>Pending reply</td></tr></table><p class='small muted' style='margin-top:6px'>Shaded fields were filled by Agency AI.</p>") + "</div>" +
        H.rate("cw-note", "Visit note and form fields", [45, 12]) +
        "<div class='row'>" + (has("signed") ? "<span class='chip'>Signed. Note done in 11 min against about 45 today (illustrative).</span>" : "<label class='row small'><input type='checkbox' data-act='toggle' data-arg='read'" + (has("read") ? " checked" : "") + "> I have read and edited this draft</label>" + btn("Sign and submit", "toggle", "signed", "pri", !has("read"))) + "</div>";
    }
    return h;
  };
  ACT.recStart = function () {
    S.f.rec = 1; S.f.recN = 0; H.render();
    (function tick() {
      if (S.p !== "caseworker" || S.i !== 3 || +S.f.rec !== 1) return;
      if (S.f.recN < LINES.length) { S.f.recN++; H.render(); H.timers.push(setTimeout(tick, 900)); }
    })();
  };
  ACT.recStop = function () { S.f.rec = 2; H.render(); };
  ACT.recReset = function () { ["rec", "recN", "fix", "read", "signed"].forEach(function (k) { delete S.f[k]; }); delete S.rate["cw-note"]; H.render(); };

  /* 4 · Find and engage kin */
  var MSG_EN = "Hi Rosa, I'm Maya Alvarez, a social worker with Cedar County. Your daughter Dana gave us your name as someone who supports Eli and Nora. You are not in trouble. I'd like to talk about how you might help the family. When is a good time to call?";
  var MSG_ES = "Hola Rosa, soy Maya Alvarez, trabajadora social del condado de Cedar. Su hija Dana nos dio su nombre como una persona que apoya a Eli y Nora. Usted no está en problemas. Me gustaría hablar sobre cómo podría ayudar a la familia. ¿Cuándo es un buen momento para llamarla?";
  SC[4] = function () {
    var sent = has("sent");
    var gen = "<svg viewBox='0 0 360 150' style='max-width:100%;height:auto' role='img' aria-label='Family tree'>" +
      "<g stroke='currentColor' fill='none' stroke-width='1.4'><line x1='110' y1='30' x2='250' y2='30'/><line x1='180' y1='30' x2='180' y2='70'/><line x1='180' y1='70' x2='180' y2='85'/><line x1='110' y1='30' x2='110' y2='70' stroke-dasharray='4 3'/></g>" +
      "<g font-size='11' text-anchor='middle' fill='currentColor'><rect x='70' y='12' width='80' height='36' rx='6' fill='none' stroke='currentColor' stroke-dasharray='4 3'/><text x='110' y='34'>Father (unknown)</text>" +
      "<rect x='210' y='12' width='80' height='36' rx='6' fill='none' stroke='var(--accent)' stroke-width='2'/><text x='250' y='34'>Rosa Delgado</text>" +
      "<rect x='140' y='85' width='80' height='36' rx='6' fill='none' stroke='currentColor'/><text x='180' y='107'>Dana Harper</text>" +
      "<rect x='20' y='85' width='70' height='36' rx='6' fill='none' stroke='currentColor'/><text x='55' y='107'>Marco D.</text>" +
      "<text x='180' y='142'>Eli (7) · Nora (4)</text></g><line x1='90' y1='103' x2='140' y2='103' stroke='currentColor' stroke-dasharray='2 3'/></svg>";
    var h = "<div class='row between'><h3>Family finding · Eli and Nora</h3><span class='chip'>2 relatives found</span></div>";
    h += "<div class='grid2'>" + card("Search results", "<div class='opt'><b>Rosa Delgado, 61</b><span class='small muted'>Maternal grandmother. Dana's emergency contact. Lives at the address of the 14 Oct visit.</span><div class='chips' style='margin-top:6px'><span class='chip'>Strong match</span>" + H.src("Emergency contact") + H.src("School record") + "</div></div><div style='height:8px'></div><div class='opt'><b>Marco Delgado, 34</b><span class='small muted'>Maternal uncle. Possible. Address needs checking.</span><div class='chips' style='margin-top:6px'><span class='chip warn'>Low confidence</span>" + H.src("Public record") + "</div></div>") +
      card("Genogram", gen + "<p class='small muted'>Updates itself as relatives are added.</p>") + "</div>";
    h += card("Outreach to Rosa", "<div class='row'><div class='lang'><button type='button' data-act='lang' data-arg='en' aria-pressed='" + (S.lang === "en") + "'>English</button><button type='button' data-act='lang' data-arg='es' aria-pressed='" + (S.lang === "es") + "'>Español</button></div>" + (S.lang === "es" ? "<span class='chip ai'>Translated by Agency AI</span>" : "") + "</div><p style='margin:10px 0'>" + esc(S.lang === "es" ? MSG_ES : MSG_EN) + "</p>" + (S.lang === "es" ? H.aiBanner("Have a Spanish speaker check it before sending.") + "<div style='margin-top:6px'>" + H.rate("cw-es", "Spanish outreach translation", [20, 4]) + "</div>" : "") +
      "<div class='row' style='margin-top:10px'>" + (sent ? "<span class='chip'>Sent to Rosa in " + (S.lang === "es" ? "Spanish" : "English") + "</span>" + (has("replied") ? "<span class='chip'>Rosa replied: \"Yes, call me after 4.\"</span>" : btn("Simulate reply", "toggle", "replied", "sm")) : btn("Send", "toggle", "sent", "pri")) + "</div>");
    return h;
  };

  /* 5 · Court report */
  SC[5] = function () {
    var d = has("drafted"), h = "<div class='row between'><h3>Court report · Harper · due Thursday</h3>" + (d ? "<span class='chip ai'>Assembled in 2 min</span>" : "") + "</div>";
    if (!d) return h + card("", "<p>Pull the report together from visit notes, plan progress, services and kin efforts.</p><div class='row' style='margin-top:10px'>" + btn("Draft report", "toggle", "drafted", "ai") + "</div><p class='small muted' style='margin-top:6px'>Today this takes about 4 hours the night before (illustrative).</p>");
    var rec = S.f.recTxt || "", ok = rec.trim().length > 20;
    h += H.aiBanner("Facts only, each with its source. You write the recommendation and approve the report.");
    [["Family background", "Dana Harper and her children Eli (7) and Nora (4) are staying with maternal grandmother Rosa Delgado since 8 Oct.", ["Intake 18 Sep", "Visit 14 Oct"]],
     ["Progress and services", "Plan v2 agreed 10 Oct. Six of nine steps complete. Referral to Bright Path sent; intake booked for 21 Oct.", ["Case plan", "Referral log"]],
     ["Efforts to find relatives", "Two relatives identified. Rosa Delgado contacted in Spanish on 15 Oct and replied the same day. Marco Delgado not yet reached. Efforts are documented automatically.", ["Family finding log"]]
    ].forEach(function (s) { h += "<div class='card sec-n'><h4>" + s[0] + "</h4><p class='small'>" + s[1] + "</p><div class='chips' style='margin-top:6px'>" + s[2].map(H.src).join("") + "</div></div>"; });
    h += "<div class='card sec-n manual'><h4>Recommendation <span class='chip warn'>Written by you</span></h4><p class='small muted'>Agency AI does not draft placement or custody recommendations.</p><div class='field' style='margin-top:6px'><textarea data-bind='recTxt' aria-label='Recommendation' placeholder='Write your recommendation'>" + esc(rec) + "</textarea></div></div>";
    h += H.rate("cw-court", "Court report draft", [240, 60]) + "<div class='row'>" + (has("filed") ? "<span class='chip'>Approved for filing</span>" : btn("Approve for filing", "fileRep", null, "pri", false)) + (ok || has("filed") ? "" : "<span class='small muted'>Write the recommendation first.</span>") + "</div>";
    return h;
  };
  ACT.fileRep = function () { if ((S.f.recTxt || "").trim().length > 20) { S.f.filed = true; } H.render(); };

  /* 6 · Reach permanency and close */
  SC[6] = function () {
    var items = ["Final home visit documented", "Compliance data captured as the work happened (12 of 12 fields)", "Services closed out with providers", "Court order received and attached"];
    var done = has("closed");
    return "<div class='row between'><h3>Close case · Harper</h3>" + (done ? "<span class='chip'>Closed</span>" : "") + "</div>" +
      card("Closing checklist, filled from the case", items.map(function (x) { return "<div class='task done'><input type='checkbox' checked disabled><span class='t'>" + x + "</span></div>"; }).join("")) +
      card("Outcome", "<p><b>Eli and Nora placed with kin.</b> They live with their grandmother, Rosa Delgado. Dana sees them weekly.</p>" + (done ? "" : "<div class='row' style='margin-top:10px'>" + btn("Close the case", "toggle", "closed", "pri") + "</div>")) +
      (done ? "<div class='card' style='background:var(--accent-soft)'><h4>A quiet milestone</h4><p class='small'>Shared with Sam Whitfield. Across this case Child Welfare Agency returned about 9 h 20 min of paperwork time to you (illustrative).</p><div class='field' style='margin-top:8px'><label for='rec-n'>Prompt for your supervisor: name something specific</label><input id='rec-n' data-bind='kudo' value='" + esc(S.f.kudo || "Maya's early kin search made this placement possible.") + "'></div></div>" : "");
  };
})();

/* Family journeys, shown in a phone frame. Priya and Marcus Shah (prospective parents) and Rosa Delgado (kin caregiver) are fictional. */
(function () {
  var S = H.S, ACT = H.ACT, esc = H.esc, card = H.card, btn = H.btn, has = H.has;
  var SP = H.SCR.parent, SK = H.SCR.kin;
  function bar(n, of) { var s = ""; for (var i = 0; i < of; i++) s += "<i class='" + (i < n ? "on" : "") + "'></i>"; return "<div class='steps'>" + s + "</div>"; }
  function field(label, key, ph, val) {
    return "<div class='field'><label>" + label + "</label><input data-bind='" + key + "' placeholder='" + esc(ph || "") + "' value='" + esc(S.f[key] != null ? S.f[key] : (val || "")) + "'></div>";
  }
  function tl(items) { return "<div class='tl'>" + items.map(function (x) { return "<div class='" + (x[1] ? "on" : "") + "'><span>" + x[0] + "</span></div>"; }).join("") + "</div>"; }

  /* ---------- Prospective parent ---------- */
  H.CHATS.pa = {
    intro: "Hi, I'm the Cedar County assistant. I can explain the steps. I can't make decisions about your application.",
    fallback: "I'm not sure about that one. Jordan Ellis, your licensing worker, can answer it.",
    qa: [
      { q: "How long does it usually take?", k: ["long", "time", "how many"], a: "Many agencies take several months from application to approval, but it depends on training dates and paperwork. The status page shows your expected timeframe once you apply." },
      { q: "What does the home visit check?", k: ["visit", "home", "check"], a: "Safety basics like smoke alarms, safe storage and sleeping space, plus a conversation about your family. Nobody is judging your housekeeping." },
      { q: "Can I do this on my phone?", k: ["phone", "mobile"], a: "Yes. Your application saves as you go, so you can stop and pick it up on any device." }
    ]
  };

  SP[0] = function () {
    return "<h3>Thinking about fostering or adopting?</h3><p class='muted small'>Here is what the road looks like in Cedar County. Most families take several months.</p>" +
      card("The steps", tl([["Tell us you're interested", 1], ["Apply online, about 30 minutes", 0], ["Training and paperwork", 0], ["Home visit", 0], ["Approval", 0], ["Get matched", 0]])) +
      card("What it asks of you", "<p class='small'>A safe home, time for training, background checks for adults in the home, and references. You do not need to own your home or be married.</p>") +
      H.chat("pa", "Questions") + btn("Start an inquiry", "stage", 1, "pri");
  };

  SP[1] = function () {
    if (has("inq")) {
      return "<h3>Thanks, Priya</h3>" + card("", "<p>Your inquiry is with <b>Jordan Ellis</b>, a licensing worker at Cedar County. Jordan will call you within 2 working days.</p><p class='small muted' style='margin-top:8px'>We sent a confirmation to priya@example.com.</p>") +
        card("What happens next", tl([["Inquiry received", 1], ["Call from Jordan", 0], ["Application opens", 0]])) + btn("Continue to application", "stage", 2, "pri");
    }
    return "<h3>Tell us about you</h3><p class='muted small'>Four quick questions. You can add more later.</p>" +
      field("Your name", "pn", "", "Priya Shah") + field("Email", "pe", "", "priya@example.com") + field("Phone (optional)", "pp", "", "") +
      "<div class='field'><label>I'm interested in</label><select data-bind='pt'><option>Fostering</option><option>Adopting</option><option>Not sure yet</option></select></div>" +
      btn("Send inquiry", "toggle", "inq", "pri");
  };

  var DESC_IN = "3 bed house, quiet street\nBack garden, near school\nI work from home; Marcus works days\nWe have a dog, Pepper";
  var DESC_OUT = "We live in a three-bedroom house on a quiet street, close to a primary school and with a fenced back garden. I work from home, and Marcus works days, so a parent is usually around. Our dog, Pepper, is gentle and has lived with children before.";
  SP[2] = function () {
    var d = has("home");
    return "<div class='row between'><h3>Application</h3><span class='small muted'>Saved just now</span></div>" + bar(3, 6) +
      "<p class='small muted'>Step 3 of 6: your home. Name, email and household were filled in from your inquiry.</p>" +
      card("Already filled in", "<table class='t'><tr><td>Name</td><td class='prefill'>Priya Shah</td></tr><tr><td>Email</td><td class='prefill'>priya@example.com</td></tr><tr><td>Partner</td><td class='prefill'>Marcus Shah</td></tr></table>") +
      card("Describe your home", "<div class='field'><label>Your notes</label><textarea data-bind='homeIn' aria-label='Notes about your home'>" + esc(S.f.homeIn != null ? S.f.homeIn : DESC_IN) + "</textarea></div><div class='row' style='margin-top:8px'>" + btn("Help me write this", "toggle", "home", "ai") + "</div>" +
        (d ? "<div style='margin-top:10px'>" + H.aiBanner("Your words, tidied up. Edit anything. Only you can submit.") + "<p style='margin-top:8px'>" + esc(DESC_OUT) + "</p><div style='margin-top:8px'>" + H.rate("pa-home", "Home description draft", [20, 6]) + "</div></div>" : "")) +
      btn("Save and continue", "stage", 3, "pri");
  };

  SP[3] = function () {
    var ref = has("refs");
    var items = [["Background checks", "Marcus done · Priya waiting for fingerprints", "warn"], ["Medical statements", "Complete", ""], ["Training (PRIDE)", "2 of 4 sessions · next Sat 9 Nov", "warn"], ["Personal references", ref ? "Requests sent to 3 people. You'll see replies here." : "Not started", ref ? "" : "gap"]];
    return "<h3>What's left</h3><p class='small muted'>Four items. Nothing here gets asked twice.</p>" + bar(2, 4) +
      items.map(function (x) { return "<div class='card'><div class='row between'><b>" + x[0] + "</b><span class='chip " + x[2] + "'>" + (x[2] === "" ? "Done" : x[2] === "warn" ? "In progress" : "To do") + "</span></div><p class='small muted'>" + x[1] + "</p></div>"; }).join("") +
      (ref ? "" : btn("Ask my references for me", "toggle", "refs", "pri")) + btn("Next: home visit", "stage", 4, "");
  };

  SP[4] = function () {
    var b = S.f.slot;
    return "<h3>Book your home visit</h3>" +
      card("Pick a time", ["Tue 12 Nov · 10:00", "Thu 14 Nov · 16:30", "Sat 16 Nov · 9:00"].map(function (x) { return "<div class='row' style='margin-bottom:6px'>" + btn(x, "set", "slot=" + x, b === x ? "pri" : "") + "</div>"; }).join("")) +
      (b ? "<div class='card' style='background:var(--accent-soft)'><b>Booked: " + b + "</b><p class='small'>Jordan will bring the checklist below. A calendar invite is on its way.</p></div>" : "") +
      card("What the visit covers", "<ul class='small' style='margin:0;padding-left:18px'><li>Smoke and carbon monoxide alarms</li><li>A bed and space for each child</li><li>Safe storage for medicines and cleaning products</li><li>A conversation with every adult and child in the home</li></ul>") +
      "<p class='small muted'>Behind the scenes: Jordan completes the forms on a tablet during the visit, and Binti AI drafts the report for Jordan to review.</p>" + btn("Next: approval", "stage", 5, "");
  };

  SP[5] = function () {
    return "<h3>Where you are</h3>" + card("", tl([["Application submitted", 1], ["Training and checks", 1], ["Home visit · done", 1], ["Supervisor review · now", 1], ["Decision", 0]])) +
      card("Expected timeframe", "<p><b>About 3 weeks</b> from the visit. Most families in Cedar County hear back in 2 to 4 weeks.</p><p class='small muted'>Nothing is needed from you right now.</p>") +
      (has("appr") ? "<div class='card' style='background:var(--accent-soft)'><h4>You're approved 🎉</h4><p class='small'>Your license is active. Next, we'll talk about the kind of child you can welcome.</p></div>" + btn("Next: get matched", "stage", 6, "pri") : btn("Simulate approval notice", "toggle", "appr", "pri"));
  };

  SP[6] = function () {
    var acc = has("acc");
    return "<h3>A placement call</h3>" +
      card("What we'd like to ask you", H.aiBanner("The placement worker's call, in plain words.") +
        "<p style='margin-top:8px'>Two siblings, ages <b>6 and 3</b>, could come to you this week. They have been together all along. The older child likes drawing and has speech therapy on Tuesdays. The younger one sleeps best with a night light.</p>" +
        "<p class='small muted' style='margin-top:6px'>Names are shared once you say yes.</p><div style='margin-top:8px'>" + H.rate("pa-match", "Plain-language placement summary", [10, 2]) + "</div>") +
      (acc ? "<div class='card' style='background:var(--accent-soft)'><b>Thank you. They're Ben and Ana.</b><p class='small'>Your named contact for the first weeks is <b>Jordan Ellis</b>. A support call is booked for day 3.</p></div>" :
        "<div class='row'>" + btn("Say yes", "toggle", "acc", "pri") + btn("Ask a question", "toggle", "ask") + btn("Not this time", "toggle", "no") + "</div>" + (has("ask") ? "<p class='small'>Jordan will call you in the next hour.</p>" : "") + (has("no") ? "<p class='small'>That's fine. Your preferences stay on file for the next match.</p>" : ""));
  };

  /* ---------- Kin caregiver ---------- */
  H.CHATS.kc = {
    intro: "Ask me anything about what this means. I explain in plain words. Your worker makes the decisions with you.",
    fallback: "I don't have an answer I trust for that. Maya Alvarez, your worker, can answer it. You can ask her to call.",
    qa: [
      { q: "Will I get money to help?", k: ["money", "pay", "cost", "financial"], a: "Many relatives can get financial help, and the amount depends on the kind of care and on state rules. Maya will check which payments you could apply for, and the First weeks step has the list." },
      { q: "Can I say yes before I'm fully approved?", k: ["before", "approved", "approval", "yes"], a: "Often yes. Agencies can sometimes place a child with a relative while approval is still in progress. Rules differ by state, so Maya will tell you what applies here." },
      { q: "What if I can't take both children?", k: ["both", "sibling", "one"], a: "Tell Maya. Keeping brothers and sisters together is a goal, but nobody expects you to say yes to more than you can do. There are other ways to help, like regular visits." }
    ]
  };

  var T = {
    en: { h: "A message from Cedar County", p1: "Hello Rosa. Your daughter Dana gave us your name. Her children, Eli and Nora, are safe, and Dana is working with us. We would like to talk with you about how you might help the family.", p2: "You are not in trouble. You do not have to decide anything today.", call: "Call me", more: "Tell me more" },
    es: { h: "Un mensaje del condado de Cedar", p1: "Hola Rosa. Su hija Dana nos dio su nombre. Sus hijos, Eli y Nora, están a salvo y Dana está trabajando con nosotros. Nos gustaría hablar con usted sobre cómo podría ayudar a la familia.", p2: "Usted no está en problemas. No tiene que decidir nada hoy.", call: "Llámenme", more: "Cuéntenme más" }
  };
  function lang() { return "<div class='lang' role='group' aria-label='Language'><button type='button' data-act='lang' data-arg='en' aria-pressed='" + (S.lang === "en") + "'>English</button><button type='button' data-act='lang' data-arg='es' aria-pressed='" + (S.lang === "es") + "'>Español</button></div>"; }

  SK[0] = function () {
    var t = T[S.lang];
    return "<div class='row between'>" + lang() + "</div><h3>" + t.h + "</h3>" + card("", "<p>" + t.p1 + "</p><p style='margin-top:8px'><b>" + t.p2 + "</b></p>") +
      (S.lang === "es" ? "<div class='ai-banner'><b>Translated by Binti AI.</b> <span>Maya checked the Spanish before sending.</span></div>" : "") +
      "<div class='row'>" + btn(t.call, "toggle", "call", "pri") + btn(t.more, "stage", 1) + "</div>" +
      (has("call") ? "<p class='small'>" + (S.lang === "es" ? "Maya la llamará hoy después de las 4." : "Maya will call you today after 4.") + "</p>" : "") + (S.lang === "es" ? H.rate("kc-first", "Spanish first-contact message", [20, 4]) : "");
  };

  SK[1] = function () {
    return "<h3>What saying yes could mean</h3><p class='small muted'>Three ways to help. You can choose one, and you can change later.</p>" +
      [["Care for the children", "They would live with you. Financial help may be available."], ["Stay close", "Regular visits and calls while they live elsewhere."], ["Support from the side", "Help Dana and the children with rides, meals and time."]].map(function (o) { return "<div class='opt'><b>" + o[0] + "</b><span class='small muted'>" + o[1] + "</span></div>"; }).join("") +
      card("Getting approved", "<p class='small'>A short home check, background checks for adults in the home, and a few forms. Anything you've already told us is reused.</p>") +
      H.chat("kc", "Ask a question") + btn("I'd like to say yes", "stage", 2, "pri");
  };

  SK[2] = function () {
    var done = has("yes");
    return "<h3>Saying yes</h3>" + card("Needed now", "<ul class='small' style='margin:0;padding-left:18px'><li>A safe place for each child to sleep</li><li>Your ID and a phone number</li><li>Permission for a quick safety check of the home</li></ul>") +
      card("Can follow within weeks", "<ul class='small' style='margin:0;padding-left:18px'><li>Full approval paperwork</li><li>Training sessions</li><li>Financial applications</li></ul><p class='small muted' style='margin-top:6px'>Rules for placing a child before full approval vary by state.</p>") +
      (done ? "<div class='card' style='background:var(--accent-soft)'><b>Your yes is recorded.</b><p class='small'>Maya will call you to plan the move. It's saved in the children's family network.</p></div>" + btn("Next: approval", "stage", 3, "pri") : btn("Yes, I can care for Eli and Nora", "toggle", "yes", "pri"));
  };

  SK[3] = function () {
    return "<h3>Getting approved</h3><p class='small muted'>You already gave us a lot. We brought it across.</p>" + bar(3, 5) +
      [["Your contact details", "Brought from family finding", 1], ["Household members", "Brought from family finding", 1], ["Home safety check", "Booked for Friday, 14:00", 1], ["Background checks", "Fingerprints this week", 0], ["Training", "Starts next month", 0]].map(function (x) {
        return "<div class='card'><div class='row between'><b>" + x[0] + "</b><span class='chip " + (x[2] ? "" : "warn") + "'>" + (x[2] ? "Done" : "To do") + "</span></div><p class='small muted'>" + x[1] + "</p></div>";
      }).join("") + btn("Next: first weeks", "stage", 4, "");
  };

  SK[4] = function () {
    var items = [["monthly", "Monthly care payment", "Helps with food, clothing and housing costs"], ["child", "Child care help", "If you work or study"], ["med", "Health coverage", "Covers the children's doctor visits"], ["school", "School supplies and clothes", "One-time start-up help"]];
    return "<h3>Help you can apply for</h3><p class='small muted'>One list. We start each form from what we already know.</p>" +
      items.map(function (x) {
        var a = has("ap-" + x[0]);
        return "<div class='card'><b>" + x[1] + "</b><p class='small muted'>" + x[2] + "</p><div class='row' style='margin-top:6px'>" + (a ? "<span class='chip'>Started. Name and address filled in</span>" : btn("Start application", "toggle", "ap-" + x[0], "sm")) + "</div></div>";
      }).join("") + "<p class='small muted'>Your contact for the first weeks: <b>Maya Alvarez</b>.</p>" + btn("Next: everyday care", "stage", 5, "");
  };

  SK[5] = function () {
    return "<h3>This week</h3><p class='small muted'>Eli and Nora's appointments, visits and court dates in one place.</p>" +
      [["Mon 18", "Eli · school pickup 15:10", ""], ["Tue 19", "Nora · pediatrician 10:00", ""], ["Wed 20", "Visit with Dana · 16:00, library", "Supervised"], ["Thu 21", "Court hearing · 9:30", "Maya will meet you there"]].map(function (x) {
        return "<div class='card'><div class='row between'><b>" + x[0] + "</b>" + (x[2] ? "<span class='chip none'>" + x[2] + "</span>" : "") + "</div><p>" + x[1] + "</p></div>";
      }).join("") + "<div class='row'>" + btn("Message Maya", "toggle", "msg", "sm") + "</div>" + (has("msg") ? "<p class='small'>Maya usually replies within a day.</p>" : "") + btn("Next: long term", "stage", 6, "");
  };

  SK[6] = function () {
    return "<h3>Where this could lead</h3><p class='small muted'>No decision needed now. Here are the paths in plain words.</p>" +
      [["Stay as kin caregiver", "The children live with you while the court and Dana work toward what comes next. Support continues."], ["Guardianship", "You become the children's legal guardian without ending Dana's parental rights."], ["Adoption", "A permanent legal family. It changes parental rights, so it is usually considered only when return home isn't possible."]].map(function (o) {
        return "<div class='opt'><b>" + o[0] + "</b><span class='small muted'>" + o[1] + "</span></div>";
      }).join("") + card("Who to talk to", "<p class='small'>Maya Alvarez is your first call. For legal questions she can arrange time with a family law advisor.</p>") +
      "<p class='small muted'>Concept: linked to the case plan, so what you choose shows up for Maya too.</p>";
  };
})();

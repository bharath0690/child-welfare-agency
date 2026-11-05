/* Case workspace: case list (caseworker landing tab), case/child page, application page and the Binti AI panel.
   Talks to the Python API in /api. The persona switcher stands in for sign-in in this prototype. */
(function () {
  var esc = H.esc;
  var TOOL_LABEL = {
    case_get: "Case record", relationships_list: "Relationships", placements_list: "Placements", history_list: "Case history",
    tasks_list: "Task list", court_dates_list: "Court calendar", visits_list: "Visit log", visit_get: "Visit transcript",
    notes_search: "Notes and transcripts", referrals_list: "Referral log", plan_get: "Case plan", proposals_list: "AI drafts",
    memory_note: "Case memory", program_search: "Agency guide", application_get: "Your application", checklist_get: "Your checklist",
    child_details_get: "Child record", child_schedule_get: "Schedule", worker_contact_get: "Worker contact",
    load_skill: null, safety_escalate: "Safety escalation"
  };
  var STAGE_COUNT = 6;
  var B = {
    as: load("bw.as") || { persona: "caseworker", user: "cw1" },
    people: null, health: null, view: null, caseId: null, tab: "relationships",
    cases: null, briefing: null, filters: { q: "", stage: "", flag: "", due: "" },
    detail: null, findings: {}, app: null, appDraft: null, triage: null, audit: null,
    panel: { open: false, data: null, msgs: [], busy: false, err: null, draft: "" },
    home: { data: null, msgs: [], busy: false, err: null, draft: "" }, full: !!load("bw.full"), toast: null, err: null
  };

  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } }

  function api(path, body) {
    var opt = { method: body ? "POST" : "GET", headers: { "X-Persona": B.as.persona, "X-User": B.as.user } };
    if (body) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    return fetch("/api" + path, opt).then(function (r) {
      return r.json().catch(function () { return { error: "The server sent an unexpected response." }; }).then(function (j) {
        if (!r.ok) throw new Error(j.error || ("HTTP " + r.status));
        return j;
      });
    });
  }
  function fail(e) { B.err = (e && e.message) || "Couldn't reach the API. Run `python dev.py` locally, or check the Vercel function logs."; render(); }
  function toast(t) { B.toast = t; render(); setTimeout(function () { if (B.toast === t) { B.toast = null; render(); } }, 3200); }

  /* ---------- formatting ---------- */
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function d(iso) { if (!iso || !/^\d{4}-/.test(iso)) return esc(iso || "—"); var p = iso.split("-"); return MON[+p[1] - 1] + " " + (+p[2]); }
  function days(iso) { var t = new Date(); t.setHours(0, 0, 0, 0); return Math.round((new Date(iso + "T00:00:00") - t) / 864e5); }
  function rel(iso) { var n = days(iso); return n === 0 ? "today" : n > 0 ? "in " + n + " day" + (n === 1 ? "" : "s") : (-n) + " day" + (n === -1 ? "" : "s") + " ago"; }
  function initials(n) { return esc(n.split(/\s+/).map(function (w) { return w[0]; }).slice(0, 2).join("").toUpperCase()); }
  function pill(s) { var c = s === "Successfully Contacted" ? "ok" : s === "Attempted Contact" ? "warn" : "none"; return "<span class='bw-pill " + c + "'>" + esc(s) + "</span>"; }
  function stage(st) {
    var seg = ""; for (var i = 1; i <= STAGE_COUNT; i++) seg += "<i class='" + (i <= st.index ? "on" : "") + "'></i>";
    return "<span class='bw-stage' title='Stage " + st.index + " of " + STAGE_COUNT + "'><span class='seg' aria-hidden='true'>" + seg + "</span>" + esc(st.name) + "</span>";
  }
  function flagChip(f) { var c = /overdue|Court soon|Draft to sign/i.test(f) ? "bad" : /ICWA|Interpreter|Recording/.test(f) ? "blue" : /Allergy|Medical/.test(f) ? "warn" : ""; return "<span class='bw-chip " + c + "'>" + esc(f) + "</span>"; }
  function btn(label, act, arg, cls, extra) { return "<button type='button' class='bw-btn " + (cls || "") + "' data-bw='" + act + "'" + (arg != null ? " data-arg='" + esc(arg) + "'" : "") + (extra || "") + ">" + label + "</button>"; }
  var SPARK = "<span class='spark' aria-hidden='true'>✦</span>";

  /* ---------- markdown (safe subset: escaped first, then bold, italic, code, headings, lists, tables, rules) ---------- */
  function inline(t) {
    return t.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:!?]|$)/g, "$1<em>$2</em>").replace(/(^|[\s(])_([^_\s][^_]*?)_(?=[\s).,;:!?]|$)/g, "$1<em>$2</em>");
  }
  function md(src) {
    var lines = esc(src || "").split("\n"), out = [], para = [], list = null, table = null;
    function fp() { if (para.length) { out.push("<p>" + para.map(inline).join("<br>") + "</p>"); para = []; } }
    function fl() { if (list) { out.push("<" + list.t + ">" + list.items.map(function (i) { return "<li>" + inline(i) + "</li>"; }).join("") + "</" + list.t + ">"); list = null; } }
    function ft() {
      if (!table) return;
      var rows = table.filter(function (r) { return !/^\s*\|?\s*:?-{2,}/.test(r); }).map(function (r) { return r.replace(/^\s*\||\|\s*$/g, "").split("|"); });
      out.push("<div class='md-t'><table>" + rows.map(function (cells, i) {
        return "<tr>" + cells.map(function (c) { return (i ? "<td>" : "<th>") + inline(c.trim()) + (i ? "</td>" : "</th>"); }).join("") + "</tr>";
      }).join("") + "</table></div>");
      table = null;
    }
    lines.forEach(function (l) {
      var m;
      if (/^\s*\|.*\|\s*$/.test(l)) { fp(); fl(); (table = table || []).push(l); return; }
      ft();
      if (/^\s*$/.test(l)) { fp(); fl(); return; }
      if ((m = l.match(/^\s*#{1,4}\s+(.*)$/))) { fp(); fl(); out.push("<h4>" + inline(m[1]) + "</h4>"); return; }
      if (/^\s*(-{3,}|\*{3,})\s*$/.test(l)) { fp(); fl(); out.push("<hr>"); return; }
      if ((m = l.match(/^\s*[-*•]\s+(.*)$/))) { fp(); if (!list || list.t !== "ul") { fl(); list = { t: "ul", items: [] }; } list.items.push(m[1]); return; }
      if ((m = l.match(/^\s*\d+[.)]\s+(.*)$/))) { fp(); if (!list || list.t !== "ol") { fl(); list = { t: "ol", items: [] }; } list.items.push(m[1]); return; }
      if (list && /^\s{2,}\S/.test(l)) { list.items[list.items.length - 1] += "<br>" + l.trim(); return; }
      fl(); para.push(l);
    });
    ft(); fp(); fl();
    return out.join("");
  }

  /* ---------- rating (feeds the AI quality drawer in the header) ---------- */
  function rate(id, label) {
    H.AIITEMS[id] = { label: label, minutes: [25, 6] };
    var r = H.S.rate[id];
    function b(v, t) { return "<button type='button' data-bw='rate' data-arg='" + esc(id) + "|" + v + "' aria-pressed='" + (r === v) + "'>" + t + "</button>"; }
    return "<div class='bw-rate'><span class='muted'>How was this draft?</span>" + b("ok", "Accurate") + b("edit", "Needs edits") + b("bad", "Wrong") + "</div>";
  }

  /* ---------- app bar ---------- */
  function bar() {
    var opts = "";
    if (B.people) {
      opts += "<optgroup label='Caseworker'>" + B.people.caseworker.map(function (p) { return opt("caseworker", p.id, p.name + " · " + p.cases + " cases"); }).join("") + "</optgroup>";
      opts += "<optgroup label='Kin caregiver'>" + B.people.kin.map(function (p) { return opt("kin", p.id, p.name + " · caring for " + p.caring_for); }).join("") + "</optgroup>";
      opts += "<optgroup label='Prospective parent'>" + B.people.applicant.map(function (p) { return opt("applicant", p.id, p.name); }).join("") + "</optgroup>";
    }
    function opt(per, id, label) { var v = per + ":" + id; return "<option value='" + v + "'" + (B.as.persona === per && B.as.user === id ? " selected" : "") + ">" + esc(label) + "</option>"; }
    var mode = B.health ? (B.health.mode === "live" ? "AI: live · " + esc(B.health.model) : "AI: scripted (no API key)") : "";
    return (mode ? "<span class='bw-mode'>" + mode + "</span>" : "") +
      "<label class='bw-as'>Viewing as <select data-bw-change='as' aria-label='Viewing as'>" + opts + "</select></label>";
  }

  /* ---------- case list ---------- */
  function viewList() {
    if (B.as.persona === "applicant") return "<div class='bw-card'><div class='bd'>Your application lives on <a class='bw-link' href='#/application'>My application</a>.</div></div>";
    if (B.as.persona === "kin") {
      if (!B.cases) return loading();
      var c = B.cases[0];
      return "<div class='bw-card'><div class='hd'><h2>The child in your care</h2></div><div class='bd'><a class='bw-link' href='#/case/" + esc(c.case_id) + "' style='display:flex;gap:12px;align-items:center'>" +
        "<span class='bw-av lg'>" + c.avatar_svg + "</span><span><b style='font-size:18px'>" + esc(c.child) + "</b><br><span class='muted'>Age " + c.age + "</span></span></a></div></div>";
    }
    if (!B.cases) return loading();
    var f = B.filters, flags = {};
    B.cases.forEach(function (c) { c.flags.forEach(function (x) { flags[x] = 1; }); });
    var rows = B.cases.filter(function (c) {
      if (f.q && (c.child + " " + c.case_no).toLowerCase().indexOf(f.q.toLowerCase()) < 0) return false;
      if (f.stage && String(c.stage.index) !== f.stage) return false;
      if (f.flag && c.flags.indexOf(f.flag) < 0) return false;
      if (f.due && (!c.next_due || days(c.next_due) > +f.due)) return false;
      return true;
    }).sort(function (a, b) { return (a.next_due || "9") < (b.next_due || "9") ? -1 : 1; });
    var table = "<table class='bw-t'><thead><tr><th>Child</th><th>Age</th><th>Stage</th><th>Next due</th><th>Flags</th><th>Last visit</th></tr></thead><tbody>" +
      rows.map(function (c) {
        var od = c.next_due && days(c.next_due) < 0;
        return "<tr data-bw='open-case' data-arg='" + esc(c.case_id) + "' tabindex='0'>" +
          "<td class='who-td'><div class='who'><span class='bw-av'>" + c.avatar_svg + "</span><span><b>" + esc(c.child) + "</b><span class='muted small'>" + esc(c.case_no) + " · " + esc(c.gender) + "</span></span></div></td>" +
          "<td data-l='Age'>" + c.age + "</td><td data-l='Stage'>" + stage(c.stage) + "</td>" +
          "<td data-l='Next due'>" + (c.next_due ? "<span class='" + (od ? "bw-od" : "") + "'>" + d(c.next_due) + " · " + rel(c.next_due) + "</span><br><span class='muted small'>" + esc(c.next_due_what || "") + "</span>" : "—") + "</td>" +
          "<td data-l='Flags'>" + (c.flags.map(flagChip).join("") || "<span class='muted'>—</span>") + "</td>" +
          "<td data-l='Last visit'>" + (c.last_visit ? "<span class='" + (c.days_since_visit > 28 ? "bw-od" : "") + "'>" + d(c.last_visit) + "</span><br><span class='muted small'>" + c.days_since_visit + " days ago</span>" : "—") + "</td></tr>";
      }).join("") + "</tbody></table>" + (rows.length ? "" : "<div class='bw-empty'>No cases match these filters.</div>");
    var stageOpts = "<option value=''>All stages</option>" + [1, 2, 3, 4, 5, 6].map(function (i) {
      var n = (B.cases.filter(function (c) { return c.stage.index === i; })[0] || {}).stage; return n ? "<option value='" + i + "'" + (f.stage === String(i) ? " selected" : "") + ">" + esc(n.name) + "</option>" : "";
    }).join("");
    var flagOpts = "<option value=''>All flags</option>" + Object.keys(flags).sort().map(function (x) { return "<option" + (f.flag === x ? " selected" : "") + ">" + esc(x) + "</option>"; }).join("");
    var dueOpts = "<option value=''>Any due date</option>" + [["0", "Overdue or today"], ["7", "Due within 7 days"], ["14", "Due within 14 days"]].map(function (o) { return "<option value='" + o[0] + "'" + (f.due === o[0] ? " selected" : "") + ">" + o[1] + "</option>"; }).join("");
    return "<div class='bw-grid'><div class='bw-card'><div class='hd'><h2>My cases <span class='muted' style='font-weight:400'>(" + rows.length + " of " + B.cases.length + ")</span></h2>" +
      "<div class='bw-filters'><input type='search' placeholder='Search child or case number' value='" + esc(f.q) + "' data-bw-input='f-q' aria-label='Search'>" +
      "<select data-bw-change='f-stage' aria-label='Stage'>" + stageOpts + "</select><select data-bw-change='f-flag' aria-label='Flag'>" + flagOpts + "</select>" +
      "<select data-bw-change='f-due' aria-label='Due'>" + dueOpts + "</select></div></div>" + table + "</div>" + briefingCard() + "</div>";
  }
  function briefingCard() {
    var b = B.briefing;
    if (!b) return "<div class='bw-card'><div class='bd muted'>Building your day…</div></div>";
    return "<div class='bw-card'><div class='hd'><h3>" + SPARK + " Your day</h3><span class='bw-chip blue'>Binti AI</span></div><div class='bd bw-brief'>" +
      "<p>" + esc(b.summary) + "</p>" +
      b.items.map(function (i) { return "<button class='item' data-bw='open-case' data-arg='" + esc(i.case_id) + "'><span><b>" + esc(i.child) + "</b>: " + esc(i.title) + "<br><span class='muted small'>" + esc(i.why) + "</span></span></button>"; }).join("") +
      "<div class='bw-tile'><b>" + b.time_back.minutes + " min</b>returned to you by signed AI-drafted notes</div><p class='muted small'>" + esc(b.time_back.note) + "</p></div></div>";
  }

  /* ---------- case page ---------- */
  function viewCase() {
    var x = B.detail;
    if (!x) return loading();
    if (x.view === "kin") return viewKinCase(x);
    var c = x.case, ch = c.child, p = c.placement || {};
    var tabs = [["relationships", "Relationships"], ["placements", "Placements"], ["history", "History"], ["visits", "Visits and notes"], ["tasks", "Tasks and court"], ["audit", "Audit log"]];
    var head = "<div class='bw-card'><div class='bd bw-prof'><span class='bw-av lg'>" + ch.avatar_svg + "</span><div class='grow'><h1>" + esc(ch.name) + "<span>, age " + ch.age + "</span></h1>" +
      "<div class='meta'>" + esc(ch.gender) + " · " + esc(ch.pronouns) + " · " + esc(ch.language) + " · " + esc(c.case_no) + "</div>" +
      "<div style='margin-top:6px;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>" + stage({ index: x.stage[0], name: stageName(x.stage[0]) }) +
      (x.flags || c.flags).map(flagChip).join("") + "</div></div>" +
      btn(SPARK.replace("spark", "") + " Ask Binti AI", "panel-open", null, "ai") + "</div>" +
      "<nav class='bw-tabs' role='tablist'>" + tabs.map(function (t) { return "<button role='tab' data-bw='tab' data-arg='" + t[0] + "' aria-selected='" + (B.tab === t[0]) + "'>" + t[1] + "</button>"; }).join("") + "</nav>" +
      "<div class='bd'>" + tabBody(x) + "</div></div>";
    var drafts = x.proposals.length ? "<div class='bw-card'><div class='hd'><h3>" + SPARK + " Binti AI drafts to review (" + x.proposals.length + ")</h3><span class='muted small'>Nothing is filed until you approve it.</span></div><div class='bd' style='display:flex;flex-direction:column;gap:12px'>" +
      x.proposals.map(draftBox).join("") + "</div></div>" : "";
    var side = "<div class='bw-card'><div class='hd'><h3>Child and case</h3></div><div class='bd'><dl class='bw-dl'>" +
      dl("Placement", esc(p.caregiver || "—") + " <span class='muted'>(" + esc(p.kind || "") + ", since " + d(p.start_on) + ")</span>") + dl("Goal", esc(c.permanency_goal)) +
      dl("Opened", d(c.opened_on)) + dl("Reason", esc(c.removal_reason || "—")) + dl("School", esc(ch.school) + ", grade " + esc(ch.grade)) +
      dl("Health", esc(ch.medical)) + dl("Allergies", esc(ch.allergies)) + dl("ICWA", esc(ch.icwa)) + dl("Race/ethnicity", esc(ch.race_ethnicity)) +
      dl("Parent contact", esc(ch.parent_contact || "—")) + dl("Worker", esc(c.worker)) + "</dl></div></div>";
    return "<div><button class='bw-link' data-bw='go' data-arg='#/cases'>← My cases</button></div>" + "<div class='bw-grid'><div style='display:flex;flex-direction:column;gap:16px;min-width:0'>" + head + drafts + "</div>" + side + "</div>";
  }
  function stageName(i) { return ["", "Accept a new case", "Build the plan with the family", "Visit and capture", "Find and engage kin", "Prepare for court", "Reach permanency and close"][i]; }
  function dl(k, v) { return "<dt>" + k + "</dt><dd>" + v + "</dd>"; }

  function tabBody(x) {
    if (B.tab === "relationships") {
      return "<div>" + x.relationships.map(function (r) {
        return "<div class='bw-rel'><span class='bw-ini'>" + initials(r.name) + "</span><div class='nm'><b>" + esc(r.name) + "</b><span class='muted'>" + esc(r.relation) +
          (r.language !== "English" ? " · prefers " + esc(r.language) : "") + (r.last_contact_on ? " · last contact " + d(r.last_contact_on) : "") + "</span></div>" + pill(r.contact_status) +
          (r.contact_status !== "Successfully Contacted" && r.relation !== "Tribe" ? btn(SPARK + " Draft first contact", "first-contact", r.id, "sm") : "") + "</div>";
      }).join("") + "</div>";
    }
    if (B.tab === "placements") {
      return "<ul class='bw-list'>" + x.placements.map(function (p) {
        return "<li><span><b>" + esc(p.caregiver) + "</b> <span class='muted'>· " + esc(p.kind) + " · " + esc(p.city) + "</span></span><span>" + d(p.start_on) + " – " + (p.current ? "<span class='bw-pill ok'>Current</span>" : d(p.end_on)) + "</span></li>";
      }).join("") + "</ul>";
    }
    if (B.tab === "history") {
      return "<ul class='bw-list bw-tl'>" + x.history.map(function (h) { return "<li><time>" + d(h.on_date) + "</time><span><span class='bw-chip'>" + esc(h.kind) + "</span> " + esc(h.text) + "</span></li>"; }).join("") + "</ul>";
    }
    if (B.tab === "visits") {
      return "<ul class='bw-list'>" + x.visits.map(function (v) {
        var rec = v.has_recording && v.consent;
        var acts = rec && v.note_status === "none" ? btn(SPARK + " Draft note", "visit-note", v.id, "sm") + btn(SPARK + " Pre-fill visit form", "prefill", v.id, "sm") :
          rec && v.note_status === "draft" ? "<span class='bw-pill warn'>AI draft waiting for you</span>" + btn(SPARK + " Pre-fill visit form", "prefill", v.id, "sm") : "";
        return "<li><span><b>" + d(v.on_date) + "</b> · " + esc(v.kind) + " <span class='muted'>at " + esc(v.location) + "</span><br><span class='small muted'>" +
          (rec ? "Recorded with consent" : v.consent ? "Consent given, not recorded" : "Not recorded") + " · Note: " + esc(v.note_status) + "</span></span><span style='display:flex;gap:6px;flex-wrap:wrap'>" + acts + "</span></li>";
      }).join("") + "</ul>";
    }
    if (B.tab === "tasks") {
      var t = x.tasks.map(function (t) { var od = days(t.due_on) < 0; return "<li><span>" + esc(t.title) + "</span><span class='" + (od ? "bw-od" : "") + "'>" + d(t.due_on) + " · " + rel(t.due_on) + "</span></li>"; }).join("");
      var c = x.court.map(function (h) { return "<li><span><b>" + esc(h.hearing) + "</b> <span class='muted'>· report " + esc(h.report_status) + "</span></span><span>" + d(h.on_date) + " · " + rel(h.on_date) + "</span></li>"; }).join("");
      var r = x.referrals.map(function (f) { return "<li><span>" + esc(f.provider) + " <span class='muted'>· " + esc(f.service) + "</span></span><span class='bw-pill " + (f.status === "active" ? "ok" : f.status === "awaiting reply" ? "warn" : "none") + "'>" + esc(f.status) + "</span></li>"; }).join("");
      var g = x.plan.map(function (p) { return "<li><span>" + esc(p.goal) + "</span><span class='bw-pill " + (p.status === "done" ? "ok" : p.status === "draft" ? "none" : "blue") + "'>" + esc(p.status) + "</span></li>"; }).join("");
      return "<h4>Tasks</h4><ul class='bw-list'>" + (t || "<li class='muted'>None</li>") + "</ul><h4 style='margin-top:14px'>Court</h4><ul class='bw-list'>" + (c || "<li class='muted'>No hearings scheduled</li>") +
        "</ul><h4 style='margin-top:14px'>Referrals</h4><ul class='bw-list'>" + (r || "<li class='muted'>None</li>") + "</ul><h4 style='margin-top:14px'>Case plan</h4><ul class='bw-list'>" + (g || "<li class='muted'>No plan yet</li>") + "</ul>";
    }
    if (B.tab === "audit") {
      if (!B.audit) { api("/audit?case_id=" + encodeURIComponent(B.caseId)).then(function (a) { B.audit = a.entries; render(); }).catch(fail); return loading(); }
      return "<p class='muted small'>Every tool call goes through the gateway: who asked, which fields were returned and whether it was allowed. Newest first.</p><table class='bw-t'><thead><tr><th>When</th><th>Who</th><th>Tool</th><th>Decision</th><th>Fields returned</th></tr></thead><tbody>" +
        B.audit.map(function (a) { return "<tr><td data-l='When'>" + esc(a.at.replace("T", " ")) + "</td><td data-l='Who'>" + esc(a.persona + ":" + a.user_id) + "</td><td data-l='Tool'>" + esc(a.tool) + "</td><td data-l='Decision'><span class='bw-chip " + (a.decision === "deny" ? "bad" : "") + "'>" + esc(a.decision) + "</span> " + esc(a.reason || "") + "</td><td data-l='Fields' class='small muted'>" + esc(JSON.parse(a.fields || "[]").slice(0, 12).join(", ")) + "</td></tr>"; }).join("") + "</tbody></table>";
    }
    return "";
  }

  function draftBox(p) {
    var pl = p.payload, k = p.kind, id = "prop-" + p.id;
    var head = "<div class='t'>" + SPARK + " Binti AI draft · " + esc(p.summary) + "</div><div class='small muted'>Review and edit before you approve. AI never files anything on its own.</div>";
    if (k === "note") {
      var f = B.findings[p.id];
      var fl = f ? (f.count ? f.findings.map(function (x) { return "<div class='bw-find'><b>\"" + esc(x.phrase) + "\"</b>: try " + esc(x.suggestion) + ". <span class='muted'>" + esc(x.why) + "</span></div>"; }).join("") :
        "<div class='small muted'>Language check: no fault-assigning wording found.</div>") : "";
      return "<div class='bw-ai' id='" + id + "'>" + head + "<textarea data-bw-input='edit-" + p.id + "' aria-label='Draft note'>" + esc(pl.body) + "</textarea>" +
        "<div style='display:flex;gap:6px;flex-wrap:wrap'>" + btn("Check language", "lang-check", p.id, "sm") + "</div>" + fl +
        "<div style='display:flex;gap:8px;flex-wrap:wrap'>" + btn("Approve and sign", "approve", p.id, "pri") + btn("Discard", "reject", p.id) + "</div>" + rate(id, "Visit note " + pl.on_date) + "</div>";
    }
    if (k === "form") {
      var rows = Object.keys(pl.fields).map(function (key) {
        var v = pl.fields[key];
        return "<tr><th>" + esc(key.replace(/_/g, " ")) + "</th><td>" + (esc(v.value) || "<span class='muted'>needs your input</span>") + (v.quote ? "<div class='small muted'>“" + esc(v.quote) + "” " + esc(v.ts || "") + "</div>" : "<div class='small muted'>" + esc(v.source) + "</div>") +
          "</td><td><span class='bw-conf " + v.confidence + "'>" + v.confidence + "</span></td></tr>";
      }).join("");
      return "<div class='bw-ai' id='" + id + "'>" + head + "<div style='overflow-x:auto'><table class='bw-form-t'>" + rows + "</table></div><div style='display:flex;gap:8px;flex-wrap:wrap'>" +
        btn("Approve form", "approve", p.id, "pri") + btn("Discard", "reject", p.id) + "</div>" + rate(id, pl.form_type) + "</div>";
    }
    if (k === "outreach") {
      return "<div class='bw-ai' id='" + id + "'>" + head + "<div class='small'>To <b>" + esc(pl.to) + "</b> · " + esc(pl.language) + (pl.language !== "English" ? " · <span class='bw-chip warn'>bilingual check needed</span>" : "") + "</div>" +
        "<textarea data-bw-input='edit-" + p.id + "' aria-label='Message'>" + esc(pl.body) + "</textarea><div style='display:flex;gap:8px;flex-wrap:wrap'>" +
        btn("Approve and send", "approve", p.id, "pri") + btn("Discard", "reject", p.id) + "</div>" + rate(id, "First contact to " + pl.to) + "</div>";
    }
    return "<div class='bw-ai' id='" + id + "'>" + head + "<pre class='small' style='white-space:pre-wrap;margin:0'>" + esc(JSON.stringify(pl, null, 2)) + "</pre><div style='display:flex;gap:8px'>" +
      btn("Approve", "approve", p.id, "pri") + btn("Discard", "reject", p.id) + "</div></div>";
  }

  function viewKinCase(x) {
    var c = x.child;
    var rows = [["School", c.school ? esc(c.school) + ", grade " + esc(c.grade) : null], ["Allergies", c.allergies && esc(c.allergies)], ["Health", c.medical && esc(c.medical)],
      ["Birthday", c.dob && d(c.dob)], ["Language", c.language && esc(c.language)]].filter(function (r) { return r[1]; }).map(function (r) { return dl(r[0], r[1]); }).join("");
    return "<div class='bw-grid'><div style='display:flex;flex-direction:column;gap:16px'><div class='bw-card'><div class='bd bw-prof'><span class='bw-av lg'>" + c.avatar_svg + "</span><div class='grow'><h1>" + esc(c.name) + "<span>, age " + c.age + "</span></h1>" +
      "<div class='meta'>" + esc(c.gender) + " · " + esc(c.pronouns) + "</div></div>" + btn("✦ Ask Binti AI", "panel-open", null, "ai") + "</div>" +
      "<div class='bd' style='border-top:1px solid var(--bw-line)'><dl class='bw-dl'>" + rows + "</dl><p class='small muted' style='margin-top:10px'>" + esc(x.hidden_note) + "</p></div></div>" +
      "<div class='bw-card'><div class='hd'><h3>Coming up</h3></div><div class='bd'><ul class='bw-list bw-tl'>" + x.schedule.map(function (s) { return "<li><time>" + d(s.date) + "</time><span>" + esc(s.what) + "</span></li>"; }).join("") + "</ul></div></div></div>" +
      "<div class='bw-card'><div class='hd'><h3>Your caseworker</h3></div><div class='bd'><div style='display:flex;gap:10px;align-items:center'><span class='bw-ini'>" + initials(x.worker.name) + "</span><div><b>" + esc(x.worker.name) + "</b><br><span class='muted small'>" + esc(x.worker.phone) + " · " + esc(x.worker.email) + "</span></div></div></div></div></div>";
  }

  /* ---------- application (prospective parent) ---------- */
  function viewApp() {
    if (B.as.persona !== "applicant") return "<div class='bw-card'><div class='bd'>Switch to the prospective parent in “Viewing as” to see the application.</div></div>";
    var a = B.app;
    if (!a) return loading();
    var ap = a.application.application, f = ap.fields;
    var steps = "<ol class='bw-steps'>" + ap.steps.map(function (s) {
      var cls = s.status === "done" ? "done" : s.status === "in progress" ? "cur" : "";
      return "<li class='" + cls + "'><span class='dot'>" + (s.status === "done" ? "✓" : "") + "</span>" + esc(s.title) + "</li>";
    }).join("") + "</ol>";
    var draft = B.appDraft ? "<div class='bw-ai'><div class='t'>" + SPARK + " Binti AI draft from your notes</div><div class='small muted'>" + esc(B.appDraft.banner) + "</div>" +
      "<textarea data-bw-input='appdraft' aria-label='Draft answer'>" + esc(B.appDraft.draft) + "</textarea><div style='display:flex;gap:8px;flex-wrap:wrap'>" +
      btn("Use this answer", "app-accept", B.appDraft.proposal.proposal_id, "pri") + btn("Discard", "app-reject", B.appDraft.proposal.proposal_id) + "</div>" + rate("app-" + B.appDraft.proposal.proposal_id, "Application answer") + "</div>" : "";
    var tri = B.triage ? "<div class='bw-ai'><div class='t'>" + SPARK + " Triage result</div><dl class='bw-dl'>" + dl("Intent", esc(B.triage.intent)) + dl("Urgency", esc(B.triage.urgency)) + dl("Language", esc(B.triage.language)) + dl("Routed to", esc(B.triage.routed_to)) + "</dl><div class='small'><b>Acknowledgement sent:</b> " + esc(B.triage.acknowledgement) + "</div></div>" : "";
    var check = a.checklist.map(function (i) { return "<li><span>" + esc(i.item) + (i.note ? " <span class='muted small'>· " + esc(i.note) + "</span>" : "") + "</span><span class='bw-pill " + (i.status === "done" ? "ok" : i.status === "missing" ? "bad" : i.status === "not booked" ? "none" : "warn") + "'>" + esc(i.status) + "</span></li>"; }).join("");
    return "<div class='row between' style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px'><div><h1 style='font-size:24px;margin:0'>Initial application form</h1><p class='muted'>" + esc(a.application.household) + " · Licensing worker: " + esc(a.application.licensing_worker.name) + "</p></div>" + btn("✦ Ask Binti AI", "panel-open", null, "ai") + "</div>" +
      "<div class='bw-app'><div class='bw-card'><div class='bd'>" + steps + "</div></div><div style='display:flex;flex-direction:column;gap:16px;min-width:0'>" +
      "<div class='bw-card'><div class='hd'><h3>Home information</h3></div><div class='bd'>" +
      "<div class='bw-field'><label>Address</label><input value='" + esc(f.address) + "' readonly></div>" +
      "<div class='bw-field'><label>Household members</label><input value='" + esc(f.household_members) + "' readonly></div>" +
      "<div class='bw-field'><label>Home description</label><textarea readonly>" + esc(f.home_description) + "</textarea></div></div></div>" +
      "<div class='bw-card'><div class='hd'><h3>Narrative: Why do you want to foster?</h3></div><div class='bd'>" +
      (f.why_foster ? "<div class='bw-field'><label>Your submitted answer</label><textarea readonly>" + esc(f.why_foster) + "</textarea></div>" : "") +
      "<div class='bw-field'><label for='bw-notes'>Write a few notes in your own words. Binti AI turns them into a draft you can edit.</label><textarea id='bw-notes' data-bw-input='notes' placeholder='e.g. we have a spare room, my sister fostered, we love kids, flexible work'>" + esc(B.notes || "") + "</textarea></div>" +
      btn("✦ Help me write this", "app-help", "why_foster", "pri") + "<div style='margin-top:12px'>" + draft + "</div></div></div>" +
      "<div class='bw-grid' style='grid-template-columns:minmax(0,1fr) minmax(0,1fr)'><div class='bw-card'><div class='hd'><h3>Your checklist</h3></div><div class='bd'><ul class='bw-list'>" + check + "</ul></div></div>" +
      "<div class='bw-card'><div class='hd'><h3>Inquiry triage (demo)</h3></div><div class='bd'><p class='small muted'>What a new family's inquiry looks like when it arrives. Binti AI detects language, intent and urgency, routes it to a named worker and sends an acknowledgement.</p>" +
      "<div class='bw-field'><label>Name</label><input data-bw-input='tri-name' value='" + esc(B.triName || "Alex Rivera") + "'></div><div class='bw-field'><label>Message</label><textarea data-bw-input='tri-text'>" + esc(B.triText || "Hi, my partner and I are thinking about fostering teens. How do we start?") + "</textarea></div>" +
      btn("Submit inquiry", "triage") + "<div style='margin-top:12px'>" + tri + "</div></div></div></div></div></div>";
  }

  /* ---------- caseworker home: full-screen Binti AI over the whole caseload ---------- */
  var LEVEL = { urgent: "Urgent", soon: "Soon", routine: "Routine" };
  function viewHome() {
    if (B.as.persona !== "caseworker") return "<div class='bw-card'><div class='bd'>Binti AI home is for caseworkers. Use the sidebar.</div></div>";
    var H2 = B.home, x = H2.data;
    var first = B.people ? ((B.people.caseworker.filter(function (p) { return p.id === B.as.user; })[0] || {}).name || "").split(" ")[0] : "";
    var body;
    if (H2.err) body = "<div class='bw-err'>" + esc(H2.err) + "</div>";
    else if (!x) body = "<div class='muted'>Reading your caseload…</div>";
    else {
      var cards = x.cards.map(function (c) {
        return "<div class='bw-ucard " + c.level + "'><button type='button' class='main' data-bw='home-ask' data-arg='" + esc(c.prompt) + "'>" +
          "<span class='ctop'><span class='lvl'>" + LEVEL[c.level] + "</span><span class='bw-av sm'>" + c.avatar_svg + "</span><b>" + esc(c.child) + "</b></span>" +
          "<span class='tt'>" + esc(c.title) + "</span><span class='why'>" + esc(c.why) + "</span></button>" +
          "<a class='open' href='#/case/" + esc(c.case_id) + "'>Open case ↗</a></div>";
      }).join("");
      body = "<div class='bw-home-intro'><div class='bw-msg assistant md'>" + md(x.greeting) + "</div></div>" +
        "<div class='bw-home-cards'><div class='hd'><h2>Your day</h2><span class='legend'><i class='urgent'></i>Urgent <i class='soon'></i>Soon <i class='routine'></i>Routine</span>" +
        "<span class='muted small'>" + x.time_back.minutes + " min returned by signed AI drafts</span></div><div class='grid'>" + cards + "</div></div>" +
        "<div class='bw-msgs'>" + H2.msgs.map(msg).join("") + (H2.busy ? "<div class='bw-msg assistant muted'>Thinking…</div>" : "") + "</div>" +
        "<div class='bw-sugg'>" + x.suggestions.map(function (q) { return "<button type='button' data-bw='home-ask' data-arg='" + esc(q) + "'>" + esc(q) + "</button>"; }).join("") + "</div>";
    }
    return "<section class='bw-home'><div class='bw-home-scroll' id='bw-home-scroll'><div class='bw-home-in'>" +
      "<h1 class='bw-home-h'>" + SPARK + " Binti AI" + (first ? "<span>for " + esc(first) + "'s caseload</span>" : "") + "</h1>" + body + "</div></div>" +
      "<form data-bw-form='home-chat' class='bw-composer'><textarea name='q' rows='1' data-bw-input='home-draft' placeholder='Ask about any child or your whole caseload' aria-label='Message Binti AI. Enter to send, Shift+Enter for a new line'" + (H2.busy ? " disabled" : "") + ">" + esc(H2.draft || "") + "</textarea>" +
      "<button class='bw-btn pri' type='submit'" + (H2.busy ? " disabled" : "") + ">Send</button><span class='hint'>Enter to send · Shift+Enter for a new line · Answers name the child they're about</span></form></section>";
  }
  function homeAsk(text) {
    var H2 = B.home;
    if (!text || H2.busy) return;
    H2.msgs.push({ role: "user", content: text }); H2.busy = true; render(); scrollHome();
    api("/ai/chat", { object_type: "caseload", message: text }).then(function (r) {
      H2.busy = false; H2.msgs.push({ role: "assistant", content: r.reply, meta: r.meta }); render(); scrollHome();
    }).catch(function (e) { H2.busy = false; H2.msgs.push({ role: "assistant", content: "Sorry, that didn't work: " + e.message }); render(); });
  }
  function scrollHome() { var el = document.getElementById("bw-home-scroll"); if (el) el.scrollTop = el.scrollHeight; }
  function loadHome() {
    B.home.data = null; B.home.err = null; render();
    api("/ai/open", { object_type: "caseload" }).then(function (x) { B.home.data = x; B.home.msgs = x.history; render(); if (x.history.length) scrollHome(); })
      .catch(function (e) { B.home.err = e.message; render(); });
  }
  function sidebar() {
    var v = B.view, per = B.as.persona, items;
    function it(href, label, on, extra) { return "<a href='" + href + "'" + (on ? " aria-current='page'" : "") + ">" + label + (extra || "") + "</a>"; }
    if (per === "caseworker") {
      var n = B.people ? ((B.people.caseworker.filter(function (p) { return p.id === B.as.user; })[0] || {}).cases || "") : "";
      items = it("#/home", SPARK + " Binti AI", v === "home") + it("#/cases", "My cases", v === "list" || v === "case", n ? "<span class='n'>" + n + "</span>" : "");
    } else if (per === "kin") items = it("#/cases", "My family", v === "list" || v === "case");
    else items = it("#/application", "My application", v === "app");
    return "<nav class='bw-sidenav' aria-label='Workspace'><div class='grp'>Product experience</div>" + items +
      "<div class='grp'>Journey study</div>" + it("#/caseworker/0", "Caseworker") + it("#/parent/0", "Prospective parent") + it("#/kin/0", "Kin caregiver") + "</nav>";
  }

  /* ---------- Binti AI panel ---------- */
  function panel() {
    var P = B.panel;
    if (!P.open) return "";
    var x = P.data, body;
    if (P.err) body = "<div class='bw-err'>" + esc(P.err) + "</div>";
    else if (!x) body = loading();
    else {
      var ctx = B.as.persona === "caseworker" && B.detail && B.detail.case ? "Context: " + esc(B.detail.case.child.name) + " · " + esc(B.detail.case.case_no) :
        B.as.persona === "kin" ? "Context: the child in your care" : "Context: your application";
      var side = "<div class='bw-ctx'>" + ctx + " · " + (x.mode === "live" ? "live model" : "scripted mode") + (x.memory && x.memory.length ? " · " + x.memory.length + " saved memories" : "") + "</div>";
      if (x.stage) {
        side += "<div class='bw-sec'><h3>Stage</h3>" + stage(x.stage) + "<ul class='small muted' style='margin:6px 0 0;padding-left:18px'>" + x.stage.evidence.map(function (e) { return "<li>" + esc(e) + "</li>"; }).join("") + "</ul></div>";
        side += "<div class='bw-sec'><h3>Suggested next actions</h3><div style='display:flex;flex-direction:column;gap:6px'>" + (x.actions.length ? x.actions.map(actionCard).join("") : "<span class='muted small'>Nothing due right now.</span>") + "</div></div>";
      } else if (x.next_steps) {
        side += "<div class='bw-sec'><h3>" + (B.as.persona === "kin" ? "Coming up" : "Still to do") + "</h3><ul class='bw-list'>" + x.next_steps.map(function (s) { return "<li><span>" + esc(s.title) + "</span><span class='muted small'>" + (/^\d{4}-/.test(s.when) ? d(s.when) : esc(s.when)) + "</span></li>"; }).join("") + "</ul></div>";
      }
      var chat = "<div class='bw-sec'><h3>Chat</h3><div class='bw-msgs' id='bw-msgs'><div class='bw-msg assistant md'>" + md(x.greeting) + "</div>" + P.msgs.map(msg).join("") +
        (P.busy ? "<div class='bw-msg assistant muted'>Thinking…</div>" : "") + "</div></div>";
      chat += "<div class='bw-sugg'>" + x.suggestions.map(function (s) { return "<button type='button' data-bw='ask' data-arg='" + esc(s) + "'>" + esc(s) + "</button>"; }).join("") + "</div>";
      body = "<div class='ai-side' id='bw-side'>" + side + "</div><div class='ai-chat' id='bw-chat'>" + chat + "</div>";
    }
    var what = B.as.persona === "caseworker" ? "this case" : B.as.persona === "kin" ? "the child, help, or next steps" : "your application";
    var toggle = btn(B.full ? "⤡ Panel view" : "⤢ Full screen", "panel-full", null, "sm", " aria-pressed='" + B.full + "' title='" + (B.full ? "Back to the side panel" : "Open Binti AI full screen") + "'");
    return (B.full ? "" : "<div class='bw-scrim' data-bw='panel-close'></div>") + "<aside class='bw-panel" + (B.full ? " full" : "") + "' aria-label='Binti AI'><div class='ph'><h2>" + SPARK + " Binti AI</h2>" + toggle + btn("Close", "panel-close", null, "sm ghost") + "</div>" +
      "<div class='pb' id='bw-pb'>" + body + "</div><form data-bw-form='chat'><textarea name='q' rows='1' data-bw-input='chat-draft' placeholder='Ask about " + what + "' aria-label='Message Binti AI. Enter to send, Shift+Enter for a new line'" + (P.busy ? " disabled" : "") + ">" + esc(P.draft || "") + "</textarea>" +
      "<button class='bw-btn pri' type='submit'" + (P.busy ? " disabled" : "") + ">Send</button><span class='hint'>Enter to send · Shift+Enter for a new line</span></form></aside>";
  }
  function actionCard(a) {
    var doIt = a.ui ? btn("Do it", "do", a.ui, "sm pri") : "";
    return "<div class='bw-act" + (a.pinned ? " pinned" : "") + "'><div class='tt'>" + (a.pinned ? "📌 " : "") + esc(a.title) + "</div><div class='why'>" + esc(a.why) + "</div><div class='small'><span class='bw-chip'>Source: " + esc(a.source) + "</span>" + (a.skill ? "<span class='bw-chip blue'>skill: " + esc(a.skill) + "</span>" : "") + "</div>" +
      "<div class='ops'>" + doIt + btn(a.pinned ? "Unpin" : "Pin as priority", "act", a.id + "|" + (a.pinned ? "unpin" : "pin"), "sm") +
      (a.pinned ? btn("↑", "act", a.id + "|up", "sm", " aria-label='Move up'") + btn("↓", "act", a.id + "|down", "sm", " aria-label='Move down'") : "") +
      btn("Ask", "ask", "Help me with: " + a.title, "sm") + btn("Done", "act", a.id + "|done", "sm") + btn("Dismiss", "act", a.id + "|dismiss", "sm ghost") + "</div></div>";
  }
  function msg(m) {
    var meta = m.meta || {}, src = (meta.sources || []).map(function (t) { return TOOL_LABEL[t]; }).filter(Boolean);
    src = src.filter(function (s, i) { return src.indexOf(s) === i; });
    var alert = meta.escalated ? " alert" : "";
    var refs = (meta.case_refs || []).map(function (r) { return "<a class='bw-ref' href='#/case/" + esc(r.case_id) + "'>" + esc(r.child) + " · " + esc(r.case_no) + " ↗</a>"; }).join("");
    if (m.role !== "assistant") return "<div class='bw-msg user'>" + esc(m.content) + "</div>";
    return "<div class='bw-msg assistant md" + alert + "'>" + md(m.content) + (refs ? "<div class='bw-refs'>" + refs + "</div>" : "") +
      "<span class='src'>" + (meta.escalated ? "Escalated to " + esc(meta.routed_to) + " · " : "") +
      (src.length ? "Looked at: " + esc(src.join(", ")) + " · " : "") + esc(meta.mode || "") + ((meta.flags || []).length ? " · " + esc(meta.flags.join(", ")) : "") + "</span></div>";
  }
  function objRef() {
    return B.as.persona === "caseworker" ? { object_type: "case", object_id: B.caseId } : B.as.persona === "kin" ? { object_type: "case", object_id: B.caseId } : { object_type: "application", object_id: null };
  }
  function openPanel() {
    B.panel = { open: true, data: null, msgs: [], busy: false, err: null, draft: B.panel.draft || "" };
    render();
    return api("/ai/open", objRef()).then(function (x) { B.panel.data = x; B.panel.msgs = x.history; render(); var pb = document.getElementById("bw-pb"); if (pb) pb.scrollTop = 0; })
      .catch(function (e) { B.panel.err = e.message; render(); });
  }
  function ask(text) {
    var P = B.panel;
    if (!text || P.busy) return;
    P.msgs.push({ role: "user", content: text }); P.busy = true; render(); scrollChat();
    var body = objRef(); body.message = text;
    api("/ai/chat", body).then(function (r) {
      P.busy = false; P.msgs.push({ role: "assistant", content: r.reply, meta: r.meta });
      if (r.actions && P.data) P.data.actions = r.actions;
      render(); scrollChat();
    }).catch(function (e) { P.busy = false; P.msgs.push({ role: "assistant", content: "Sorry, that didn't work: " + e.message }); render(); });
  }
  function chatScroller() { var c = document.getElementById("bw-chat"); return c && getComputedStyle(c).overflowY === "auto" ? c : document.getElementById("bw-pb"); }
  function scrollChat() { var el = chatScroller(); if (el) el.scrollTop = el.scrollHeight; }
  function autosize() {
    document.querySelectorAll("#bw textarea[name='q']").forEach(function (t) {
      var max = t.closest(".bw-composer") ? 240 : B.full ? 260 : 180;
      t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight + 2, max) + "px";
    });
  }

  /* ---------- actions ---------- */
  var A = {
    "open-case": function (id) { location.hash = "#/case/" + id; },
    "home-ask": function (t) { homeAsk(t); },
    go: function (h) { location.hash = h; },
    tab: function (t) { B.tab = t; if (t === "audit") B.audit = null; render(); },
    "panel-open": openPanel,
    "panel-close": function () { B.panel.open = false; render(); },
    "panel-full": function () {
      B.full = !B.full; save("bw.full", B.full); render(); scrollChat();
      var t = document.querySelector(".bw-panel textarea[name='q']"); if (t) { t.focus(); t.setSelectionRange(t.value.length, t.value.length); }
    },
    ask: function (t) { if (!B.panel.open || !B.panel.data) openPanel().then(function () { ask(t); }); else ask(t); },
    act: function (arg) {
      var p = arg.split("|");
      api("/cases/" + B.caseId + "/actions/" + p[0], { op: p[1] }).then(function (r) { B.panel.data.actions = r.actions; render(); }).catch(fail);
    },
    "do": function (ui) {
      var p = ui.split(":");
      if (p[0] === "visit-note") A["visit-note"](p[1]);
      else if (p[0] === "prefill") A.prefill(p[1]);
      else if (p[0] === "outreach") A["first-contact"](p[1]);
      else if (p[0] === "proposal") { B.panel.open = false; render(); var el = document.getElementById("prop-" + p[1]); if (el) el.scrollIntoView({ behavior: "smooth", block: "center" }); }
    },
    "visit-note": function (vid) { runWf("/workflows/visit-note", { case_id: B.caseId, visit_id: +vid }, "Draft note ready for your review."); },
    prefill: function (vid) { runWf("/workflows/prefill", { case_id: B.caseId, visit_id: +vid }, "Visit form pre-filled. Review each field."); },
    "first-contact": function (rid) { runWf("/workflows/first-contact", { case_id: B.caseId, relationship_id: +rid }, "First-contact message drafted for your review."); },
    "lang-check": function (pid) {
      var ta = document.querySelector("[data-bw-input='edit-" + pid + "']");
      api("/workflows/language-check", { text: ta ? ta.value : "" }).then(function (r) { B.findings[pid] = r; render(); }).catch(fail);
    },
    approve: function (pid) { decide(pid, "approve"); },
    reject: function (pid) { decide(pid, "reject"); },
    rate: function (arg) { var x = arg.split("|"); H.S.rate[x[0]] = H.S.rate[x[0]] === x[1] ? undefined : x[1]; if (!H.S.rate[x[0]]) delete H.S.rate[x[0]]; H.renderDrawer(); render(); },
    "app-help": function (field) {
      api("/workflows/application-help", { field: field, notes: B.notes || "" }).then(function (r) {
        if (r.error) return toast(r.error); B.appDraft = r; render();
      }).catch(fail);
    },
    "app-accept": function (pid) {
      var ta = document.querySelector("[data-bw-input='appdraft']");
      api("/proposals/" + pid, { op: "approve", edited: { value: ta ? ta.value : B.appDraft.draft } }).then(function () { B.appDraft = null; B.notes = ""; toast("Answer saved to your application."); loadApp(); }).catch(fail);
    },
    "app-reject": function (pid) { api("/proposals/" + pid, { op: "reject" }).then(function () { B.appDraft = null; render(); }).catch(fail); },
    triage: function () {
      api("/workflows/inquiry-triage", { name: B.triName || "Alex Rivera", text: B.triText || "Hi, my partner and I are thinking about fostering teens. How do we start?" })
        .then(function (r) { B.triage = r; render(); }).catch(fail);
    }
  };
  function runWf(path, body, done) {
    toast("Binti AI is working…");
    api(path, body).then(function (r) {
      if (r.error) return toast(r.error);
      toast(done); reloadCase(true);
    }).catch(fail);
  }
  function decide(pid, op) {
    var ta = document.querySelector("[data-bw-input='edit-" + pid + "']"), edited = null;
    if (ta) { var prop = (B.detail.proposals || []).filter(function (p) { return p.id === +pid; })[0]; edited = prop && prop.kind === "note" ? { body: ta.value } : { body: ta.value }; }
    api("/proposals/" + pid, { op: op, edited: edited }).then(function () { toast(op === "approve" ? "Approved and filed. Thank you." : "Draft discarded."); reloadCase(true); }).catch(fail);
  }

  /* ---------- data loading ---------- */
  function boot() {
    if (!B.people) api("/people").then(function (p) { B.people = p; render(); }).catch(fail);
    if (!B.health) api("/health").then(function (h) { B.health = h; render(); }).catch(function () { /* shown by other calls */ });
  }
  function loadList() {
    B.cases = null; B.briefing = null;
    api("/cases").then(function (r) { B.cases = r.cases; render(); }).catch(fail);
    if (B.as.persona === "caseworker") api("/briefing").then(function (r) { B.briefing = r; render(); }).catch(fail);
  }
  function reloadCase(keepPanel) {
    api("/cases/" + B.caseId).then(function (x) {
      B.detail = x; B.audit = null;
      (x.proposals || []).forEach(function (p) {
        if (p.kind === "note" && !B.findings[p.id]) api("/workflows/language-check", { text: p.payload.body }).then(function (r) { B.findings[p.id] = r; render(); });
      });
      render();
      if (keepPanel && B.panel.open) api("/ai/open", objRef()).then(function (d) { B.panel.data = d; render(); });
    }).catch(fail);
  }
  function loadApp() { api("/application").then(function (a) { B.app = a; render(); }).catch(fail); }
  function loading() { return "<div class='bw-card'><div class='bd muted'>Loading…</div></div>"; }

  /* ---------- render + routing ---------- */
  function render() {
    var root = document.getElementById("bw");
    if (!root || root.hidden) return;
    var body = B.err ? "<div class='bw-err'>" + esc(B.err) + "</div>" : B.view === "home" ? viewHome() : B.view === "case" ? viewCase() : B.view === "app" ? viewApp() : viewList();
    var y = window.scrollY, keep = {};
    ["bw-pb", "bw-side", "bw-chat", "bw-home-scroll"].forEach(function (id) { var el = document.getElementById(id); if (el) keep[id] = el.scrollTop; });
    var focus = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.bwInput : null, caret = focus ? document.activeElement.selectionStart : 0;
    var tools = document.getElementById("hdr-tools"); if (tools) tools.innerHTML = bar();
    document.body.classList.toggle("bw-full", B.panel.open && B.full);
    document.body.classList.toggle("bw-homeview", B.view === "home");
    root.innerHTML = "<div class='bw-shell'>" + sidebar() + "<main class='bw-main" + (B.view === "home" ? " home" : "") + "'>" + body + "</main></div>" + panel() + (B.toast ? "<div class='bw-toast' role='status'>" + esc(B.toast) + "</div>" : "");
    window.scrollTo(0, y);
    Object.keys(keep).forEach(function (id) { var el = document.getElementById(id); if (el) el.scrollTop = keep[id]; });
    autosize();
    if (focus) { var el = root.querySelector("[data-bw-input='" + focus + "']"); if (el) { el.focus(); try { el.setSelectionRange(caret, caret); } catch (e) { /* not a text field */ } } }
  }

  function route(hash) {
    B.err = null;
    var m;
    boot();
    if (/^#\/home/.test(hash) || hash === "" || hash === "#/") {
      if (B.as.persona === "applicant") { location.replace("#/application"); return; }
      if (B.as.persona === "kin") { location.replace("#/cases"); return; }
      B.view = "home"; B.panel.open = false; render(); loadHome();
    } else if ((m = hash.match(/^#\/case\/([\w-]+)$/))) {
      if (B.caseId !== m[1]) { B.panel.open = false; B.tab = "relationships"; B.detail = null; B.findings = {}; }
      B.view = "case"; B.caseId = m[1]; render(); reloadCase(false);
    } else if (/^#\/application/.test(hash)) {
      B.view = "app"; B.panel.open = false; render(); if (B.as.persona === "applicant") loadApp();
    } else {
      if (B.as.persona === "applicant") { location.replace("#/application"); return; }
      B.view = "list"; B.panel.open = false; render(); loadList();
    }
  }

  function switchAs(v) {
    var p = v.split(":"); B.as = { persona: p[0], user: p[1] }; save("bw.as", B.as);
    B.panel.open = false; B.detail = null; B.caseId = null; B.app = null; B.appDraft = null; B.findings = {};
    if (p[0] === "applicant") location.hash = "#/application";
    else if (p[0] === "kin") api("/cases").then(function (r) { location.hash = "#/case/" + r.cases[0].case_id; }).catch(fail);
    else { B.home = { data: null, msgs: [], busy: false, err: null, draft: "" }; if (location.hash === "#/home") route("#/home"); else location.hash = "#/home"; }
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-bw]");
    if (!el || el.disabled || !document.getElementById("bw").contains(el)) return;
    var fn = A[el.dataset.bw]; if (fn) { e.preventDefault(); fn(el.dataset.arg); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target.matches && e.target.matches("tr[data-bw='open-case']")) A["open-case"](e.target.dataset.arg);
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.target.matches && e.target.matches("#bw textarea[name='q']")) {
      e.preventDefault();
      var f = e.target.form;
      if (f.requestSubmit) f.requestSubmit(); else f.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
    if (e.key === "Escape" && B.panel.open && !document.querySelector("details.menu[open]")) { B.panel.open = false; render(); }
  });
  document.addEventListener("change", function (e) {
    var k = e.target.dataset && e.target.dataset.bwChange; if (!k) return;
    if (k === "as") return switchAs(e.target.value);
    if (k.indexOf("f-") === 0) { B.filters[k.slice(2)] = e.target.value; render(); }
  });
  document.addEventListener("input", function (e) {
    var k = e.target.dataset && e.target.dataset.bwInput; if (!k) return;
    if (k === "f-q") { B.filters.q = e.target.value; render(); }
    else if (k === "chat-draft") { B.panel.draft = e.target.value; autosize(); }
    else if (k === "home-draft") { B.home.draft = e.target.value; autosize(); }
    else if (k === "notes") B.notes = e.target.value;
    else if (k === "tri-name") B.triName = e.target.value;
    else if (k === "tri-text") B.triText = e.target.value;
    else if (k.indexOf("edit-") === 0) delete B.findings[k.slice(5)];
  });
  document.addEventListener("submit", function (e) {
    var f = e.target.closest("form[data-bw-form]"); if (!f) return;
    e.preventDefault(); var q = f.q.value.trim(); if (!q) return;
    f.q.value = "";
    if (f.dataset.bwForm === "home-chat") { B.home.draft = ""; homeAsk(q); } else { B.panel.draft = ""; ask(q); }
  });

  window.BW = { route: route, render: render };
})();

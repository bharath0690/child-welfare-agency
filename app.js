/* Core: state, routing, shell rendering, actions, chat and AI-quality helpers. */
(function () {
  var KEYS = ["caseworker", "parent", "kin"];
  var LABEL = { caseworker: "Caseworker", parent: "Prospective parent", kin: "Kin caregiver" };
  var S = { p: "caseworker", i: 0, f: {}, lang: "en", chat: {}, typing: {}, rate: {}, drawer: false };
  var SCR = { caseworker: [], parent: [], kin: [] };
  var ACT = {};
  var H = { S: S, SCR: SCR, ACT: ACT, CHATS: {}, AIITEMS: {}, timers: [] };

  H.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var esc = H.esc;

  H.face = function (v, cls) {
    var m = v > 0 ? "M7 13.5 Q12 18.5 17 13.5" : v < 0 ? "M7 17 Q12 12 17 17" : "M7 15.5 H17";
    var w = v > 0 ? "Positive" : v < 0 ? "Negative" : "Neutral";
    return "<svg class='face " + cls + "' viewBox='0 0 24 24' role='img' aria-label='" + w + "'><circle cx='12' cy='12' r='10.5'/><circle class='eye' cx='8.6' cy='9.5' r='1.2'/><circle class='eye' cx='15.4' cy='9.5' r='1.2'/><path d='" + m + "' fill='none' stroke-width='1.6' stroke-linecap='round'/></svg>";
  };

  /* small building blocks used by the screens */
  H.card = function (title, body, cls) { return "<div class='card " + (cls || "") + "'>" + (title ? "<h4>" + title + "</h4>" : "") + body + "</div>"; };
  H.aiBanner = function (text) { return "<div class='ai-banner'><b>Binti AI draft.</b> <span>" + (text || "Review and edit before you use it.") + "</span></div>"; };
  H.btn = function (label, act, arg, cls, disabled) {
    return "<button type='button' class='btn " + (cls || "") + "' data-act='" + act + "'" + (arg != null ? " data-arg='" + esc(arg) + "'" : "") + (disabled ? " disabled" : "") + ">" + label + "</button>";
  };
  H.src = function (t) { return "<span class='src-chip'>" + esc(t) + "</span>"; };
  H.has = function (k) { return !!S.f[k]; };

  /* Rating row. Each rated item feeds the AI quality drawer. */
  H.rate = function (id, label, minutes) {
    H.AIITEMS[id] = { label: label, minutes: minutes || null };
    var r = S.rate[id];
    function b(v, t, c) { return "<button type='button' class='" + (c || "") + "' data-act='rate' data-arg='" + id + "|" + v + "' aria-pressed='" + (r === v) + "'>" + t + "</button>"; }
    return "<div class='rate'><span class='muted'>How was this draft?</span>" + b("ok", "Accurate") + b("edit", "Needs edits") + b("bad", "Wrong", "bad") + "</div>";
  };

  /* Chat. Scripted: chips are suggested questions, typed text is matched by keyword. */
  H.chat = function (id, title) {
    var c = H.CHATS[id];
    var msgs = S.chat[id] || (S.chat[id] = [{ r: "a", t: c.intro }]);
    var h = "<div class='chat'><div class='chat-h'><span class='chip ai'>AI</span>" + esc(title) + "</div><div class='chat-m' id='cm-" + id + "'>";
    msgs.forEach(function (m) {
      h += "<div class='msg " + (m.r === "u" ? "u" : "a") + "'>" + esc(m.t) + (m.s ? "<span class='src'>Source: " + esc(m.s) + "</span>" : "") + "</div>";
    });
    if (S.typing[id]) h += "<div class='msg a muted'>Thinking…</div>";
    h += "</div><div class='chat-c'>";
    c.qa.forEach(function (q, i) { h += "<button type='button' data-act='chip' data-arg='" + id + "|" + i + "'>" + esc(q.q) + "</button>"; });
    h += "</div><form class='chat-f' data-chat='" + id + "'><input name='q' placeholder='Ask a question' aria-label='Ask a question' autocomplete='off'><button type='submit'>Send</button></form></div>";
    return h;
  };
  function ask(id, text, idx) {
    var c = H.CHATS[id], msgs = S.chat[id] || (S.chat[id] = [{ r: "a", t: c.intro }]);
    if (S.typing[id]) return;
    var hit = idx != null ? c.qa[idx] : null;
    if (!hit) {
      var low = text.toLowerCase();
      c.qa.forEach(function (q) { if (!hit && (q.k || []).some(function (k) { return low.indexOf(k) > -1; })) hit = q; });
    }
    msgs.push({ r: "u", t: text });
    S.typing[id] = true;
    render();
    var t = setTimeout(function () {
      S.typing[id] = false;
      msgs.push({ r: "a", t: hit ? hit.a : c.fallback, s: hit ? hit.s : null });
      render();
    }, 700);
    H.timers.push(t);
  }

  /* Shell */
  function stages() { return PRI[KEYS.indexOf(S.p)].st; }
  function renderTabs() {
    document.getElementById("tabs").innerHTML = KEYS.map(function (k) {
      return "<button class='tab' role='tab' type='button' data-act='persona' data-arg='" + k + "' aria-selected='" + (k === S.p) + "'>" + LABEL[k] + "</button>";
    }).join("");
  }
  function renderRail() {
    var st = stages();
    document.getElementById("rail").innerHTML = "<h3>" + esc(PRI[KEYS.indexOf(S.p)].name) + "</h3>" + st.map(function (s, i) {
      return "<button class='st' type='button' data-act='stage' data-arg='" + i + "'" + (i === S.i ? " aria-current='step'" : "") + ">" + H.face(s.ts, "t") + "<span class='arrow'>→</span>" + H.face(s.ps, "p") + "<span>" + esc(s.n) + "</span></button>";
    }).join("");
  }
  function renderNotes() {
    var s = stages()[S.i], last = S.i === stages().length - 1;
    var mods = s.m.split(",").map(function (m) { return "<span class='chip" + (m === "ai" ? " ai" : "") + "'>" + esc(MODN[m] || m) + "</span>"; }).join("");
    document.getElementById("notes").innerHTML =
      "<div class='card'><span class='mono'>Journey notes</span><h4 style='margin-top:4px'>" + esc(s.n) + "</h4><p class='small muted'>" + esc(s.g) + "</p>" +
      "<div class='pair' style='margin-top:12px'>" + H.face(s.ts, "t lg") + "<div><span class='chip gap'>Today: " + esc(s.fl) + "</span><p class='small'>" + esc(s.fr) + "</p></div></div>" +
      "<div class='pair'>" + H.face(s.ps, "p lg") + "<div><span class='chip'>With the product</span><p class='small'>" + esc(s.pd) + "</p></div></div>" +
      (s.ns ? "<p class='small' style='margin-top:10px'><span class='chip warn'>New surface</span> Not described on Binti's site, so this screen is a proposal.</p>" : "") +
      "<div class='chips' style='margin-top:10px'>" + mods + "</div><p class='small muted' style='margin-top:8px'>Signal to watch: " + esc(s.sg) + "</p></div>" +
      "<div class='row'>" + H.btn("Back", "stage", S.i - 1, "", S.i === 0) + H.btn(last ? "Back to start" : "Next stage", "stage", last ? 0 : S.i + 1, "pri") + "</div>";
  }
  function renderScreen() {
    var fn = SCR[S.p][S.i], body = fn ? fn() : "<div class='card'>Screen not built yet.</div>";
    var el = document.getElementById("screen");
    if (S.p === "caseworker") {
      el.innerHTML = "<div class='frame desk'><div class='desk-bar'><span class='dots'><i></i><i></i><i></i></span>Cedar County Child Welfare · Maya Alvarez</div><div class='desk-body stack'>" + body + "</div></div>";
    } else {
      var who = S.p === "parent" ? "Priya Shah" : "Rosa Delgado";
      el.innerHTML = "<div class='frame phone'><div class='phone-bar'><b>Cedar County Fostering</b><span class='muted'>" + who + "</span></div><div class='phone-body'>" + body + "</div></div>";
    }
  }
  function renderDrawer() {
    var d = document.getElementById("drawer");
    d.hidden = !S.drawer;
    if (!S.drawer) return;
    var tally = { ok: 0, edit: 0, bad: 0 }, rows = "", saved = 0, n = 0;
    Object.keys(S.rate).forEach(function (id) {
      var it = H.AIITEMS[id] || { label: id }, v = S.rate[id];
      tally[v]++; n++;
      var lbl = v === "ok" ? "Accurate" : v === "edit" ? "Needs edits" : "Wrong";
      rows += "<tr><td>" + esc(it.label) + "</td><td>" + lbl + "</td></tr>";
      if (it.minutes && v !== "bad") saved += it.minutes[0] - it.minutes[1];
    });
    d.innerHTML = "<div class='row between'><h3>AI quality</h3>" + H.btn("Close", "drawer", null, "sm") + "</div>" +
      "<p class='small muted'>Every AI draft in the prototype can be rated. This is a sketch of the evals a team would watch: draft accuracy, edit rate and time saved.</p>" +
      "<div class='grid2'><div class='tile'><b>" + (n ? Math.round(100 * tally.ok / n) + "%" : "–") + "</b>accepted as accurate</div><div class='tile'><b>" + (n ? Math.round(100 * tally.edit / n) + "%" : "–") + "</b>needed edits</div></div>" +
      "<div class='tile'><b>" + saved + " min</b>illustrative time saved on rated drafts</div>" +
      (n ? "<table class='t'><tr><th>Draft</th><th>Rating</th></tr>" + rows + "</table>" : "<p class='small muted'>No drafts rated yet. Rate a draft on any screen to see it here.</p>") +
      "<div class='card'><h4>Evals to build next</h4><ul class='small' style='margin:0;padding-left:18px'><li>Draft accuracy against a worker-approved note</li><li>Edit distance between draft and final</li><li>Biased or fault-assigning language caught</li><li>Minutes from visit to signed note</li></ul></div>" +
      "<p class='small muted'>Minutes are illustrative and need measuring with real workers.</p>";
  }

  function render() {
    renderTabs(); renderRail(); renderScreen(); renderNotes(); renderDrawer();
    Object.keys(S.chat).forEach(function (id) { var m = document.getElementById("cm-" + id); if (m) m.scrollTop = m.scrollHeight; });
  }
  H.render = render;

  function clearTimers() { H.timers.forEach(clearTimeout); H.timers = []; }
  function route() {
    var m = (location.hash || "").match(/^#\/(caseworker|parent|kin)\/(\d)$/);
    var p = m ? m[1] : "caseworker", i = m ? +m[2] : 0;
    if (i > 6) i = 0;
    if (p !== S.p || i !== S.i) clearTimers();
    S.p = p; S.i = i;
    render();
    if (!document.body.dataset.ready) document.body.dataset.ready = "1"; else window.scrollTo(0, 0);
  }
  H.go = function (p, i) { location.hash = "#/" + p + "/" + i; };

  ACT.persona = function (a) { H.go(a, 0); };
  ACT.stage = function (a) { H.go(S.p, +a); };
  ACT.drawer = function () { S.drawer = !S.drawer; render(); };
  ACT.rate = function (a) { var x = a.split("|"); S.rate[x[0]] = S.rate[x[0]] === x[1] ? undefined : x[1]; if (!S.rate[x[0]]) delete S.rate[x[0]]; render(); };
  ACT.chip = function (a) { var x = a.split("|"); ask(x[0], H.CHATS[x[0]].qa[+x[1]].q, +x[1]); };
  ACT.toggle = function (a) { S.f[a] = !S.f[a]; render(); };
  ACT.set = function (a) { var x = a.split("="); S.f[x[0]] = x[1]; render(); };
  ACT.lang = function (a) { S.lang = a; render(); };

  H.init = function () {
    document.addEventListener("click", function (e) {
      var el = e.target.closest("[data-act]");
      if (!el || el.disabled) return;
      var fn = ACT[el.dataset.act];
      if (fn) fn(el.dataset.arg, el);
    });
    document.addEventListener("submit", function (e) {
      var f = e.target.closest("form[data-chat]");
      if (!f) return;
      e.preventDefault();
      var q = f.q.value.trim();
      if (q) ask(f.dataset.chat, q, null);
    });
    document.addEventListener("input", function (e) {
      var el = e.target;
      if (el.dataset && el.dataset.bind) S.f[el.dataset.bind] = el.value;
    });
    window.addEventListener("hashchange", route);
    route();
  };
  window.H = H;
})();

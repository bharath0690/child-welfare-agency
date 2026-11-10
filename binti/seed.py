"""Schema and fictional seed data. Run directly to rebuild the local database:

    python -m binti.seed            # rebuilds data/binti.db

All names, cases and events are fictional. Dates are relative to today so the data never goes stale.
"""
import json
from datetime import date, timedelta

SCHEMA = """
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE workers (id TEXT PRIMARY KEY, name TEXT, role TEXT, agency TEXT, email TEXT, phone TEXT, supervisor_id TEXT);
CREATE TABLE children (id TEXT PRIMARY KEY, first TEXT, last TEXT, dob TEXT, gender TEXT, pronouns TEXT,
  race_ethnicity TEXT, language TEXT, icwa TEXT, school TEXT, grade TEXT, medical TEXT, allergies TEXT, avatar TEXT);
CREATE TABLE cases (id TEXT PRIMARY KEY, case_no TEXT, child_id TEXT REFERENCES children(id), worker_id TEXT REFERENCES workers(id),
  opened_on TEXT, removal_reason TEXT, permanency_goal TEXT, status TEXT, jurisdiction TEXT, flags TEXT, parent_contact TEXT);
CREATE TABLE relationships (id INTEGER PRIMARY KEY, child_id TEXT, name TEXT, relation TEXT, contact_status TEXT,
  language TEXT, phone TEXT, last_contact_on TEXT, notes TEXT);
CREATE TABLE placements (id INTEGER PRIMARY KEY, child_id TEXT, caregiver TEXT, kind TEXT, start_on TEXT, end_on TEXT, city TEXT, current INTEGER);
CREATE TABLE history (id INTEGER PRIMARY KEY, case_id TEXT, on_date TEXT, kind TEXT, text TEXT);
CREATE TABLE tasks (id INTEGER PRIMARY KEY, case_id TEXT, title TEXT, due_on TEXT, status TEXT, kind TEXT);
CREATE TABLE court_dates (id INTEGER PRIMARY KEY, case_id TEXT, on_date TEXT, hearing TEXT, report_status TEXT);
CREATE TABLE visits (id INTEGER PRIMARY KEY, case_id TEXT, on_date TEXT, kind TEXT, location TEXT, consent INTEGER,
  transcript TEXT, note_status TEXT);
CREATE TABLE notes (id INTEGER PRIMARY KEY, case_id TEXT, visit_id INTEGER, on_date TEXT, author TEXT, body TEXT, status TEXT, ai_drafted INTEGER);
CREATE TABLE referrals (id INTEGER PRIMARY KEY, case_id TEXT, provider TEXT, service TEXT, status TEXT, sent_on TEXT);
CREATE TABLE plan_goals (id INTEGER PRIMARY KEY, case_id TEXT, goal TEXT, status TEXT);
CREATE TABLE forms (id INTEGER PRIMARY KEY, case_id TEXT, visit_id INTEGER, form_type TEXT, fields TEXT, status TEXT);
CREATE TABLE applicants (id TEXT PRIMARY KEY, name TEXT, household TEXT, language TEXT, worker_id TEXT, stage TEXT,
  application TEXT, checklist TEXT);
CREATE TABLE kin_users (id TEXT PRIMARY KEY, name TEXT, relationship_id INTEGER, child_id TEXT, language TEXT, phone TEXT,
  placed_on TEXT, approval TEXT, supports TEXT, first_payment_on TEXT);
CREATE TABLE foster_users (id TEXT PRIMARY KEY, name TEXT, household TEXT, child_id TEXT, phone TEXT, licensed_on TEXT,
  payments TEXT, supports TEXT, adoption TEXT);
CREATE TABLE agency_contacts (id INTEGER PRIMARY KEY, role TEXT, name TEXT, phone TEXT, hours TEXT, use_for TEXT, audience TEXT, sort INTEGER);
CREATE TABLE care_needs (child_id TEXT PRIMARY KEY, routines TEXT, health TEXT, school TEXT, comfort TEXT, avoid TEXT, updated_on TEXT, source TEXT);
CREATE TABLE worker_messages (id INTEGER PRIMARY KEY, idem_key TEXT UNIQUE, owner_type TEXT, owner_id TEXT, from_name TEXT, worker_id TEXT,
  text TEXT, sent_at TEXT, answered_at TEXT, answer TEXT, escalated_to TEXT, escalated_at TEXT);
CREATE TABLE recognitions (id INTEGER PRIMARY KEY, worker_id TEXT, from_name TEXT, case_id TEXT, text TEXT, on_date TEXT);
CREATE TABLE inquiries (id INTEGER PRIMARY KEY, name TEXT, text TEXT, language TEXT, intent TEXT, urgency TEXT,
  routed_to TEXT, ack TEXT, created_at TEXT);
CREATE TABLE program_docs (id INTEGER PRIMARY KEY, title TEXT, audience TEXT, jurisdiction TEXT, body TEXT, source TEXT);
CREATE TABLE disclosure (field TEXT PRIMARY KEY, caseworker INTEGER, kin INTEGER, applicant INTEGER, foster INTEGER, setting TEXT, note TEXT);
CREATE TABLE agency_settings (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE chat_messages (id INTEGER PRIMARY KEY, object_type TEXT, object_id TEXT, persona TEXT, user_id TEXT,
  role TEXT, content TEXT, meta TEXT, created_at TEXT);
CREATE TABLE case_memory (id INTEGER PRIMARY KEY, object_type TEXT, object_id TEXT, fact TEXT, source TEXT, created_at TEXT);
CREATE TABLE case_actions (id INTEGER PRIMARY KEY, case_id TEXT, key TEXT, title TEXT, why TEXT, source TEXT, skill TEXT,
  ui TEXT, due_on TEXT, score REAL, status TEXT, pinned INTEGER DEFAULT 0, rank INTEGER DEFAULT 0, updated_at TEXT,
  UNIQUE(case_id, key));
CREATE TABLE proposals (id INTEGER PRIMARY KEY, idem_key TEXT UNIQUE, object_type TEXT, object_id TEXT, kind TEXT,
  payload TEXT, summary TEXT, status TEXT, created_by TEXT, created_at TEXT, decided_by TEXT, decided_at TEXT);
CREATE TABLE escalations (id INTEGER PRIMARY KEY, object_type TEXT, object_id TEXT, persona TEXT, user_id TEXT, text TEXT,
  routed_to TEXT, status TEXT, created_at TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, at TEXT, persona TEXT, user_id TEXT, tool TEXT, args TEXT, object TEXT,
  fields TEXT, decision TEXT, reason TEXT);
"""

AGENCY = "Cedar County Child Welfare (fictional)"
JURIS = "Cedar County, fictional state"


def d(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def dob(age_years: int, extra_days: int = 0) -> str:
    return (date.today() - timedelta(days=int(age_years * 365.25) + 40 + extra_days)).isoformat()


WORKERS = [  # id, name, role, email, phone, supervisor
    ("cw1", "Maya Alvarez", "caseworker", "maya.alvarez@cedar.example", "555-0101", "sv1"),
    ("cw2", "Daniel Okafor", "caseworker", "daniel.okafor@cedar.example", "555-0102", "sv1"),
    ("cw3", "Grace Lin", "caseworker", "grace.lin@cedar.example", "555-0103", "sv1"),
    ("lw1", "Priya Natarajan", "licensing worker", "priya.natarajan@cedar.example", "555-0110", "sv2"),
    ("sv1", "Robert Hale", "supervisor", "robert.hale@cedar.example", "555-0120", None),
    ("sv2", "Dana Price", "licensing supervisor", "dana.price@cedar.example", "555-0121", None),
]

# --- Visit transcripts (speaker-labelled, consent recorded at the start) -----------------------------
T_JAYLEN = """[00:00] Worker (Maya): Before we start, is it still okay that I record today so I can write my notes later?
[00:04] Caregiver (Mrs. Thompson): Yes, that's fine.
[00:06] Child (Jaylen): Yeah, okay.
[00:30] Worker (Maya): Jaylen, how has school been since we last talked?
[00:34] Child (Jaylen): Better. I got a B on my math test. I like Mr. Ortiz.
[01:10] Caregiver (Mrs. Thompson): He's been going every day. One late morning last week because of the bus.
[01:40] Worker (Maya): How has your breathing been? Are you using your inhaler?
[01:45] Child (Jaylen): Only once, after soccer.
[02:20] Caregiver (Mrs. Thompson): His asthma check-up is booked for the 28th.
[03:05] Worker (Maya): Can we talk alone for a few minutes, Jaylen? (Caregiver leaves the room.)
[03:10] Child (Jaylen): I miss my mom. I want more visits with her and with Grandma Denise.
[03:40] Child (Jaylen): I feel safe here. Mrs. Thompson makes pancakes on Saturdays.
[04:30] Worker (Maya): Your mom has started her counseling sessions. We're asking the court on Friday about longer visits.
[05:15] Caregiver (Mrs. Thompson): The Bright Path counselor hasn't called us back about family sessions yet.
[05:50] Worker (Maya): I'll follow up with Bright Path. Next visit, same time in about four weeks.
"""

T_MATEO = """[00:00] Worker (Daniel): Is it okay if I record today's visit for my notes? You can say stop anytime.
[00:05] Caregiver (Mr. Garcia): Sure.
[00:06] Child (Mateo): Okay.
[00:40] Worker (Daniel): Mateo, how's sixth grade going?
[00:44] Child (Mateo): Good. I joined the robotics club on Wednesdays.
[01:20] Caregiver (Mr. Garcia): Attendance has been perfect this month. He has a dentist appointment on the 3rd.
[02:00] Worker (Daniel): Any health worries? Sleeping okay?
[02:04] Child (Mateo): I sleep fine. Sometimes I get headaches at school.
[02:30] Caregiver (Mr. Garcia): We told the school nurse. We think he might need glasses.
[03:15] Worker (Daniel): Can we talk on our own for a bit, Mateo? (Caregiver steps outside.)
[03:20] Child (Mateo): I like it here. I want to keep seeing Aunt Ana on Sundays.
[03:55] Child (Mateo): Can my grandpa Jorge come to my robotics show?
[04:40] Worker (Daniel): I'll try to reach your grandpa again this week and ask about the show.
[05:30] Worker (Daniel): I'll set up an eye exam referral. Next visit in about four weeks.
"""

T_ZOE = """[00:00] Worker (Grace): Okay to record today so I can write notes later?
[00:03] Caregiver (Ms. Park): Yes.
[00:04] Child (Zoe): Yes.
[00:30] Worker (Grace): How's fifth grade, Zoe?
[00:34] Child (Zoe): Reading is hard. My tutor hasn't started yet.
[01:10] Caregiver (Ms. Park): We're still waiting on the tutoring program to call back.
[02:00] Worker (Grace): Can we talk alone, Zoe? (Caregiver leaves the room.)
[02:05] Child (Zoe): I'm okay here. I want to call my dad more.
[03:00] Worker (Grace): I'll ask about adding a weekly phone call. Next visit in about four weeks.
"""

T_SOFIA = """[00:00] Worker (Maya): ¿Está bien si grabo la visita para mis notas? Is it okay if I record for my notes?
[00:05] Caregiver (Lucia): Sí, está bien.
[00:40] Worker (Maya): Lucia, how is Sofia settling in?
[00:45] Caregiver (Lucia): She is sleeping in my room for now. She asks for her mamá every night.
[01:30] Caregiver (Lucia): I don't know what papers I need or if I can get help with clothes and food.
[02:10] Worker (Maya): I'll bring the kinship guide in Spanish and we'll go through the options together.
[03:00] Worker (Maya): Can I talk with Sofia for a minute? (Caregiver steps into the kitchen.)
[03:05] Child (Sofia): I like Tía Lucia's dog. I want to go back to my school.
[04:00] Worker (Maya): I'll check on keeping Sofia at her school. Next visit within a week.
"""

AI_DRAFT_JAYLEN = """Monthly visit, foster home (Thompson). Jaylen was seen with his caregiver and alone.

School: Jaylen reports his school is going better and he received a B on a math test [00:34]. Caregiver reports daily attendance with one late arrival due to the bus [01:10].
Health: Jaylen used his inhaler once, after soccer [01:45]. Asthma check-up booked for the 28th [02:20].
Child's views (seen alone): Jaylen said he feels safe in the home [03:40]. He asked for more visits with his mother and with his grandmother, Denise Brooks [03:10].
Services: Mother has started counseling [04:30]. Bright Path has not yet returned the call about family sessions [05:15].
Next steps: Worker to follow up with Bright Path. Next visit in about four weeks [05:50]."""

# --- Children and their cases ------------------------------------------------------------------------
# avatar: (skin, hair, style, bg, shirt, freckles, glasses)
CHILDREN = [
    dict(id="ch01", first="Jaylen", last="Brooks", age=9, gender="Male", pronouns="he/him", race="Black", lang="English",
         icwa="No reason to know", school="Cedar Elementary", grade="4", medical="Asthma, uses inhaler as needed",
         allergies="None known", avatar=(4, 0, "buzz", 0, 0, False, False),
         case=dict(no="CW-2026-1042", worker="cw1", opened=-128, reason="Neglect allegation: lack of supervision",
                   goal="Reunification", status="open", flags=["Medical needs"], parent="Kiara Brooks (mother) · 555-0141"),
         placement=("Thompson family", "foster", -120, "Cedar City"),
         rel=[("Denise Brooks", "Grandparent", "Successfully Contacted", "English", -6),
              ("Marcus Brooks", "Uncle", "Attempted Contact", "English", -21),
              ("Tanya Reed", "Aunt", "Successfully Contacted", "English", -14),
              ("Ray Ellis", "Family Friend (soccer coach)", "Attempted Contact", "English", -30)],
         tasks=[("School records consent for Jaylen", -2, "consent"), ("Court report: review hearing", 3, "court")],
         court=(4, "Review hearing", "not started"),
         visits=[(-12, "Home visit", "Thompson home", 1, T_JAYLEN, "draft"), (-41, "Home visit", "Thompson home", 1, None, "signed")],
         referrals=[("Bright Path Counseling", "Family therapy", "awaiting reply", -9)],
         goals=[("Mother completes counseling intake and attends sessions", "in progress"),
                ("Increase family time to unsupervised weekend visits", "not started")]),
    dict(id="ch02", first="Sofia", last="Ramirez", age=6, gender="Female", pronouns="she/her", race="Latina", lang="Spanish, English",
         icwa="No reason to know", school="Riverside Elementary", grade="1", medical="None known", allergies="Peanuts",
         avatar=(2, 1, "puffs", 3, 3, False, False),
         case=dict(no="CW-2026-1107", worker="cw1", opened=-6, reason="Parent hospitalized, no other caregiver available",
                   goal="Reunification", status="open", flags=["Interpreter: Spanish", "Allergy"], parent="Elena Ramirez (mother) · 555-0142"),
         placement=("Lucia Ramirez (aunt)", "kin", -6, "Cedar City"),
         rel=[("Lucia Ramirez", "Aunt", "Successfully Contacted", "Spanish", -1),
              ("Ernesto Ramirez", "Grandparent", "Not Yet Contacted", "Spanish", None),
              ("Carmen Ortiz", "Family Friend", "Attempted Contact", "Spanish", -4)],
         tasks=[("Kin home safety walk-through", 2, "kin"), ("Initial case plan meeting", 10, "plan")],
         court=(18, "Jurisdiction hearing", "not started"),
         visits=[(-3, "Initial home visit", "Lucia Ramirez home", 1, T_SOFIA, "signed")],
         referrals=[], goals=[]),
    dict(id="ch03", first="Ethan", last="Nguyen", age=14, gender="Male", pronouns="he/him", race="Vietnamese American",
         lang="English, Vietnamese", icwa="No reason to know", school="Cedar Middle School", grade="8",
         medical="ADHD, daily medication", allergies="None known", avatar=(1, 5, "short", 4, 4, False, True),
         case=dict(no="CW-2025-0871", worker="cw1", opened=-305, reason="Physical abuse allegation (household member)",
                   goal="Guardianship with kin", status="open", flags=["Medical needs"], parent="Hoa Nguyen (mother) · 555-0143"),
         placement=("Bennett family (therapeutic foster home)", "foster", -300, "Maple Falls"),
         rel=[("Linh Tran", "Grandparent", "Attempted Contact", "Vietnamese", -15),
              ("Bao Nguyen", "Uncle", "Not Yet Contacted", "Vietnamese", None),
              ("Alicia Grant", "Mentor", "Successfully Contacted", "English", -10)],
         tasks=[("Update kin search: second attempt with Linh Tran", -1, "kin")],
         court=(40, "Permanency hearing", "not started"),
         visits=[(-33, "Home visit", "Bennett home", 0, None, "signed")],
         referrals=[("Cedar Youth Services", "Individual therapy", "active", -200)],
         goals=[("Identify and approve a relative for guardianship", "in progress")]),
    dict(id="ch04", first="Lily", last="Morgan", age=3, gender="Female", pronouns="she/her", race="White", lang="English",
         icwa="No reason to know", school="Little Oaks Daycare", grade="Pre-K", medical="Eczema", allergies="None known",
         avatar=(0, 4, "bun", 1, 2, True, False),
         case=dict(no="CW-2025-0412", worker="cw1", opened=-410, reason="Caregiver substance use",
                   goal="Guardianship with kin (finalized)", status="closing", flags=[], parent="Amber Morgan (mother) · 555-0144"),
         placement=("Patricia Morgan (grandmother)", "kin", -400, "Cedar City"),
         rel=[("Patricia Morgan", "Grandparent", "Successfully Contacted", "English", -8),
              ("Kevin Morgan", "Uncle", "Successfully Contacted", "English", -60)],
         tasks=[("Closing summary", 7, "closing")],
         court=None,
         visits=[(-8, "Home visit", "Patricia Morgan home", 0, None, "signed")],
         referrals=[], goals=[("Finalize guardianship with grandmother", "done")]),
    dict(id="ch05", first="Mateo", last="Silva", age=11, gender="Male", pronouns="he/him", race="Latino", lang="Spanish, English",
         icwa="No reason to know", school="Cedar Middle School", grade="6", medical="Possible vision issue (headaches)",
         allergies="None known", avatar=(2, 0, "short", 5, 1, False, False),
         case=dict(no="CW-2026-0988", worker="cw2", opened=-64, reason="Neglect allegation: unsafe housing",
                   goal="Reunification", status="open", flags=[], parent="Rafael Silva (father) · 555-0145"),
         placement=("Garcia family", "foster", -60, "Cedar City"),
         rel=[("Ana Silva", "Aunt", "Successfully Contacted", "Spanish", -5),
              ("Jorge Silva", "Grandparent", "Attempted Contact", "Spanish", -18)],
         tasks=[("Eye exam referral", 5, "health")],
         court=(45, "Review hearing", "not started"),
         visits=[(-2, "Home visit", "Garcia home", 1, T_MATEO, "none")],
         referrals=[("Cedar Housing Partners", "Housing support for father", "active", -40)],
         goals=[("Father secures stable housing", "in progress")]),
    dict(id="ch06", first="Aaliyah", last="Johnson", age=16, gender="Female", pronouns="she/her", race="Black", lang="English",
         icwa="No reason to know", school="Cedar High School", grade="11", medical="None known", allergies="None known",
         avatar=(5, 0, "long", 2, 6, False, False),
         case=dict(no="CW-2025-0733", worker="cw2", opened=-214, reason="Neglect allegation: lack of supervision",
                   goal="Reunification", status="open", flags=["Sibling group"], parent="Monique Johnson (mother) · 555-0146"),
         placement=("Reyes family", "foster", -210, "Maple Falls"),
         rel=[("Gloria Johnson", "Grandparent", "Attempted Contact", "English", -25),
              ("Terrence Johnson", "Uncle", "Successfully Contacted", "English", -12),
              ("Ruth Allen", "Family Friend (pastor)", "Successfully Contacted", "English", -20)],
         tasks=[("Independent living skills referral", -4, "services"), ("Court report: permanency hearing", 8, "court")],
         court=(10, "Permanency hearing", "not started"),
         visits=[(-19, "Home visit", "Reyes home", 0, None, "signed")],
         referrals=[("Next Step Youth", "Independent living skills", "not sent", None)],
         goals=[("Mother completes parenting program", "in progress")]),
    dict(id="ch07", first="Malik", last="Johnson", age=12, gender="Male", pronouns="he/him", race="Black", lang="English",
         icwa="No reason to know", school="Cedar Middle School", grade="7", medical="None known", allergies="Shellfish",
         avatar=(5, 5, "curly", 6, 0, False, False),
         case=dict(no="CW-2025-0734", worker="cw2", opened=-214, reason="Neglect allegation: lack of supervision",
                   goal="Reunification", status="open", flags=["Sibling group", "Allergy"], parent="Monique Johnson (mother) · 555-0146"),
         placement=("Reyes family", "foster", -210, "Maple Falls"),
         rel=[("Gloria Johnson", "Grandparent", "Attempted Contact", "English", -25),
              ("Terrence Johnson", "Uncle", "Successfully Contacted", "English", -12)],
         tasks=[("Court report: permanency hearing", 8, "court")],
         court=(10, "Permanency hearing", "not started"),
         visits=[(-19, "Home visit", "Reyes home", 0, None, "signed")],
         referrals=[], goals=[("Mother completes parenting program", "in progress")]),
    dict(id="ch08", first="Noah", last="Whitehorse", age=8, gender="Male", pronouns="he/him", race="American Indian",
         lang="English", icwa="Reason to know: tribe notified, response pending", school="Cedar Elementary", grade="3",
         medical="None known", allergies="None known", avatar=(3, 5, "long", 0, 5, False, False),
         case=dict(no="CW-2026-1013", worker="cw2", opened=-92, reason="Neglect allegation: caregiver incapacity",
                   goal="Reunification", status="open", flags=["ICWA"], parent="Leah Whitehorse (mother) · 555-0148"),
         placement=("Sarah Whitehorse (aunt)", "kin", -90, "Cedar City"),
         rel=[("Sarah Whitehorse", "Aunt", "Successfully Contacted", "English", -7),
              ("Joseph Whitehorse", "Grandparent", "Successfully Contacted", "English", -15),
              ("Tribal ICWA representative", "Tribe", "Attempted Contact", "English", -11)],
         tasks=[("Document active efforts for ICWA", 5, "court"), ("Finalize case plan with family", -3, "plan")],
         court=(30, "Review hearing", "not started"),
         visits=[(-16, "Home visit", "Sarah Whitehorse home", 0, None, "signed")],
         referrals=[("Cedar Family Wellness", "Substance use assessment for mother", "awaiting reply", -12)],
         goals=[("Mother completes assessment and follows recommendations", "draft"),
                ("Maintain connection with tribe and extended family", "draft")]),
    dict(id="ch09", first="Zoe", last="Kim", age=10, gender="Female", pronouns="she/her", race="Korean American", lang="English",
         icwa="No reason to know", school="Lakeview Elementary", grade="5", medical="None known", allergies="None known",
         avatar=(0, 5, "wavy", 4, 3, False, True),
         case=dict(no="CW-2026-0950", worker="cw3", opened=-95, reason="Parent incarcerated, no other caregiver available",
                   goal="Reunification", status="open", flags=[], parent="David Kim (father) · 555-0149"),
         placement=("Park family", "foster", -95, "Lakeview"),
         rel=[("Sun-hee Kim", "Grandparent", "Successfully Contacted", "Korean", -22),
              ("Jenna Kim", "Aunt", "Attempted Contact", "English", -35)],
         tasks=[("Arrange weekly phone call with father", 6, "family time")],
         court=(52, "Review hearing", "not started"),
         visits=[(-20, "Home visit", "Park home", 1, T_ZOE, "signed")],
         referrals=[("Bright Futures Tutoring", "Reading tutor", "awaiting reply", -14)],
         goals=[("Maintain weekly contact with father", "in progress")]),
    dict(id="ch10", first="Elijah", last="Carter", age=15, gender="Male", pronouns="he/him", race="Black", lang="English",
         icwa="No reason to know", school="Cedar High School", grade="9", medical="None known", allergies="None known",
         avatar=(4, 0, "short", 5, 4, False, False),
         case=dict(no="CW-2025-0802", worker="cw3", opened=-260, reason="Physical abuse allegation (parent)",
                   goal="Guardianship with kin", status="open", flags=["School attendance"], parent="Andre Carter (father) · 555-0150"),
         placement=("Hope House (group home)", "group home", -150, "Maple Falls"),
         rel=[("Bernice Carter", "Grandparent", "Attempted Contact", "English", -28),
              ("Leon Carter", "Uncle", "Not Yet Contacted", "English", None),
              ("Tasha Green", "Cousin", "Attempted Contact", "English", -9)],
         tasks=[("School attendance meeting", -1, "education")],
         court=(60, "Permanency hearing", "not started"),
         visits=[(-27, "Placement visit", "Hope House", 0, None, "signed")],
         referrals=[("Cedar Youth Services", "Mentoring", "active", -100)],
         goals=[("Find a relative for guardianship", "in progress")]),
    dict(id="ch11", first="Isabella", last="Rossi", age=1, gender="Female", pronouns="she/her", race="White", lang="English",
         icwa="No reason to know", school="Not in school", grade="-", medical="Born early, early intervention services",
         allergies="None known", avatar=(0, 3, "short", 3, 5, False, False),
         case=dict(no="CW-2025-0690", worker="cw3", opened=-420, reason="Prenatal substance exposure",
                   goal="Adoption", status="open", flags=["Medical needs"], parent="Not shared in prototype"),
         placement=("Hughes family (foster-adopt)", "foster", -415, "Lakeview"),
         rel=[("Carol Rossi", "Grandparent", "Attempted Contact", "English", -40)],
         tasks=[("Court report: permanency planning hearing", 5, "court")],
         court=(7, "Permanency planning hearing", "not started"),
         visits=[(-10, "Home visit", "Hughes home", 0, None, "signed")],
         referrals=[("Cedar Early Intervention", "Physical therapy", "active", -300)],
         goals=[("Complete adoption home study update", "in progress")]),
    dict(id="ch12", first="Amir", last="Haddad", age=7, gender="Male", pronouns="he/him", race="Arab American",
         lang="Arabic, English", icwa="No reason to know", school="Riverside Elementary", grade="2", medical="None known",
         allergies="None known", avatar=(2, 0, "curly", 6, 2, False, False),
         case=dict(no="CW-2026-1095", worker="cw3", opened=-14, reason="Domestic violence in the home",
                   goal="Reunification", status="open", flags=["Interpreter: Arabic"], parent="Rania Haddad (mother) · 555-0152"),
         placement=("Karim Haddad (uncle)", "kin", -14, "Cedar City"),
         rel=[("Karim Haddad", "Uncle", "Successfully Contacted", "Arabic", -2),
              ("Layla Haddad", "Grandparent", "Not Yet Contacted", "Arabic", None)],
         tasks=[("Initial case plan meeting", 4, "plan")],
         court=(21, "Jurisdiction hearing", "not started"),
         visits=[(-5, "Home visit", "Karim Haddad home", 0, None, "signed")],
         referrals=[], goals=[]),
]

DISCLOSURE = [
    # field, caseworker, kin, applicant, foster, agency setting that can switch caregiver access, note
    ("name", 1, 1, 0, 1, None, "Kin caregiver may see the placed child's name."),
    ("age", 1, 1, 0, 1, None, ""),
    ("dob", 1, 1, 0, 1, None, "Needed for school and medical appointments."),
    ("gender", 1, 1, 0, 1, None, ""),
    ("pronouns", 1, 1, 0, 1, None, ""),
    ("photo", 1, 1, 0, 1, None, ""),
    ("language", 1, 1, 0, 1, None, ""),
    ("school", 1, 1, 0, 1, None, ""),
    ("medical", 1, 1, 0, 1, "kin_medical", "Shared with kin when the agency setting allows."),
    ("allergies", 1, 1, 0, 1, None, "Always shared with the person caring for the child."),
    ("court_dates", 1, 1, 0, 1, None, ""),
    ("visit_schedule", 1, 1, 0, 1, None, ""),
    ("worker_contact", 1, 1, 0, 1, None, ""),
    ("race_ethnicity", 1, 0, 0, 0, None, ""),
    ("icwa", 1, 0, 0, 0, None, "Tribal status is discussed by the worker."),
    ("parent_contact", 1, 0, 0, 0, None, "Contact with parents is arranged by the worker."),
    ("removal_reason", 1, 0, 0, 0, None, "Reason for removal is shared by the worker, not the AI."),
    ("case_notes", 1, 0, 0, 0, None, ""),
    ("relationships", 1, 0, 0, 0, None, "Other relatives' details are not shared."),
    ("care_needs", 1, 1, 0, 1, "care_needs_sharing", "What the caregiver needs to care for the child day to day. On by default in the prototype; counsel must approve before real use."),
    ("reporter_identity", 0, 0, 0, 0, None, "Never available to anyone through the AI."),
]

PROGRAM_DOCS = [
    ("Steps to become a foster parent", "applicant",
     "The steps are: inquiry, orientation, application, pre-service training, background checks and fingerprints, "
     "references, a home study, then an approval decision. Most families finish in three to six months. Your licensing "
     "worker can tell you what is left for your family."),
    ("What the home study checks", "applicant",
     "The home study is a few visits and interviews. The worker looks at safety basics such as smoke detectors, "
     "safe storage of medicines and firearms, sleeping space for a child, and talks with everyone in the household "
     "about their routines, support network and parenting experience. It is not a test of how tidy your home is."),
    ("Background checks and fingerprints", "applicant",
     "Every adult in the home completes a background check and fingerprinting (Live Scan in many places). Results "
     "usually take two to four weeks. A past record does not always stop an application. Talk to your worker."),
    ("References", "applicant",
     "You need three references who know you well, such as a friend, neighbor, coworker or faith leader. You choose "
     "who to ask. The agency sends each person a short form once you confirm their contact details."),
    ("Pre-service training", "applicant",
     "Training covers trauma, child development, working with birth families and agency rules. Hours are set by the "
     "state. Sessions are offered evenings and weekends, in person and online."),
    ("Your options as a relative", "kin",
     "When a child in your family enters care, you can be asked to: care for the child in your home, stay in contact "
     "through visits or calls, or support the family in other ways. Saying you can't take the child does not stop you "
     "from staying in their life. Ask the caseworker which options fit your situation."),
    ("Caring for a child before you are approved", "kin",
     "Many agencies can place a child with a relative quickly, before full approval, after a home safety check and "
     "background checks. The rest of the approval steps then happen while the child is with you. The rules vary by "
     "state, so ask your caseworker what applies here."),
    ("Financial help for relative caregivers", "kin",
     "Help can include a monthly payment if you become an approved foster home, a child-only cash grant, food "
     "assistance, health coverage for the child and help with clothing or a bed. What you qualify for depends on "
     "your state and your approval status. The eligibility team decides, and your caseworker can help you apply."),
    ("Court hearings: what caregivers should know", "kin",
     "Caregivers usually get notice of hearings and can share how the child is doing. You can ask the caseworker "
     "what the next hearing is about and whether you should attend."),
    ("School for children in care", "all",
     "Children in care can often stay in their school of origin if it is in their best interest, with transport "
     "arranged. The caseworker and school work this out together."),
    ("Health care for children in care", "all",
     "Children in foster care are usually covered by public health insurance. The caseworker can share the child's "
     "card and doctor details with the caregiver."),
    ("Foster care payments and reimbursement", "applicant",
     "Licensed foster parents get a monthly payment for each child to cover food, clothing, transport and daily costs. The first "
     "payment usually arrives 30 to 45 days after placement, then monthly. Clothing allowances and some costs, such as mileage to "
     "visits, are reimbursed when you submit receipts. If a payment is late or wrong, call the caregiver payments unit. "
     "Rates in this prototype are fictional."),
    ("Payments and benefits once a child is placed with you", "foster",
     "You get a monthly payment for each child, plus reimbursements you claim with receipts. The child keeps their own health "
     "coverage. Respite care gives you planned breaks. If you adopt, an adoption assistance agreement can continue support after "
     "finalization; it is agreed before the adoption is final. The caregiver payments unit handles late or wrong payments."),
    ("When a child's behavior is hard to manage", "foster",
     "Call the behavioral support line any time, day or night, if a child's behavior is hard to manage or you worry the placement "
     "may not hold. Tell your caseworker the next working day. For anything dangerous, call 911. Asking for help early is part of "
     "the job, not a sign you are failing."),
    ("Legal questions as a caregiver", "foster",
     "You get notice of court hearings and can tell the court how the child is doing. For questions about your rights, court "
     "notices, guardianship or adoption, call the caregiver legal help line. Binti AI can explain how things usually work, but it "
     "does not give legal advice."),
    ("Help you can get before you are licensed", "kin",
     "You do not have to wait for a license to get some help. Many relatives can apply right away for a child-only cash grant, "
     "food assistance and help with clothing or a bed. The child keeps health coverage. A monthly foster care payment usually "
     "starts only after you are approved as a foster home, so start the other applications now. Your caseworker or the kinship "
     "navigator can help you apply."),
    ("Paths to a permanent home", "kin",
     "If a child cannot return home, the main long-term paths are guardianship and adoption. Each has different "
     "legal steps and supports. A family law advisor or the caseworker can explain which may apply."),
]

APPLICATION = {
    "steps": [
        {"key": "family", "title": "Family information", "status": "done"},
        {"key": "home", "title": "Home information", "status": "in progress"},
        {"key": "narrative", "title": "Narrative questions", "status": "not started"},
        {"key": "consent", "title": "Consent and confirmation", "status": "not started"},
    ],
    "fields": {
        "household_members": "Jordan Bennett, Casey Bennett",
        "address": "214 Alder Lane, Cedar City",
        "years_at_address": "",
        "home_description": "",
        "why_foster": "",
        "support_network": "",
    },
}
CHECKLIST = [  # since: days ago the item reached its current status; typical: usual range in days
    {"item": "Orientation", "status": "done", "holder": "Done", "since": 40},
    {"item": "Background checks (both adults)", "status": "done", "holder": "Done", "since": 12},
    {"item": "Fingerprints for Casey", "status": "pending", "note": "Appointment needed", "holder": "Your family: book an appointment", "since": 18, "typical": [3, 14]},
    {"item": "References (1 of 3 received)", "status": "pending", "holder": "Two references have not replied", "since": 21, "typical": [7, 21]},
    {"item": "Medical statement", "status": "missing", "holder": "Your doctor: the agency form needs a signature", "since": 25, "typical": [7, 21]},
    {"item": "Pre-service training", "status": "scheduled", "note": "Starts Saturday", "holder": "Scheduled", "since": 5},
    {"item": "Home study", "status": "not booked", "holder": "Priya Natarajan (licensing): books it once checks clear", "since": 30, "typical": [14, 45]},
]


# Kin approval for Lucia (placed day -6). since/typical in days; reused = carried over from family finding.
KIN_APPROVAL = [
    {"item": "Household and relationship details", "status": "reused", "holder": "Carried over from family finding", "since": 6},
    {"item": "Fingerprints (Lucia)", "status": "done", "holder": "Done", "since": 4},
    {"item": "Home safety walk-through", "status": "scheduled", "holder": "Maya Alvarez (caseworker)", "since": 6, "typical": [1, 7]},
    {"item": "State background check", "status": "in progress", "holder": "State background check unit", "since": 5, "typical": [10, 30]},
    {"item": "Relative home study", "status": "ready to start", "holder": "Priya Natarajan (licensing)", "since": 6, "typical": [30, 60],
     "note": "Can start now, in parallel with the background check."},
    {"item": "Caregiver training (kin track)", "status": "not started", "holder": "Lucia: evening and online sessions", "since": 6, "typical": [14, 28]},
]
KIN_SUPPORTS = [
    {"name": "Child-only cash grant", "status": "ready to apply", "license": False,
     "note": "No license needed. Binti AI can start the application from what the agency already knows; you submit it."},
    {"name": "Health coverage for Sofia", "status": "active", "license": False, "note": "Sofia is covered. Her card is with Maya."},
    {"name": "Emergency clothing and bed voucher", "status": "available now", "license": False, "note": "Ask Maya. Issued the same week."},
    {"name": "Food assistance", "status": "check eligibility", "license": False, "note": "Depends on household income."},
    {"name": "Kinship navigator", "status": "available now", "license": False, "note": "Help applying, and local support groups."},
    {"name": "Monthly foster care payment", "status": "after approval", "license": True,
     "note": "Starts only after you are approved as a foster home. The other supports above do not wait."},
]
FOSTER_PAYMENTS = {"monthly": "$812 a month for Isabella (fictional prototype rate)", "last_paid": -5, "next_due": 25,
                   "pending": [{"item": "Mileage to early intervention, October", "submitted": -12, "typical": [20, 30]}]}
FOSTER_SUPPORTS = [
    {"name": "Monthly foster care payment", "status": "active", "license": True, "note": "Paid on the 1st."},
    {"name": "Health coverage for Isabella", "status": "active", "license": False, "note": "Continues after adoption."},
    {"name": "Early intervention (physical therapy)", "status": "active", "license": False, "note": "Weekly, through Cedar Early Intervention."},
    {"name": "Respite care", "status": "available", "license": True, "note": "Up to two weekends a month. Book through Grace."},
    {"name": "Adoption assistance agreement", "status": "not started", "license": True,
     "note": "Ongoing support after adoption. It must be agreed before the adoption is final."},
]
ADOPTION_STEPS = [
    {"item": "Goal changed to adoption", "status": "done", "holder": "Court", "since": 60},
    {"item": "Termination of parental rights", "status": "petition filed", "holder": "Agency attorney and court", "since": 45, "typical": [90, 180]},
    {"item": "Appeal period after the order", "status": "not started", "holder": "Court", "since": 0, "typical": [30, 30],
     "note": "Length varies by state."},
    {"item": "Adoption home study update", "status": "in progress", "holder": "Priya Natarajan (licensing)", "since": 30, "typical": [30, 60]},
    {"item": "Adoption assistance agreement", "status": "not started", "holder": "Adoption assistance unit", "since": 0, "typical": [30, 90]},
    {"item": "Finalization hearing", "status": "not scheduled", "holder": "Court, once the steps above are done", "since": 0},
]
# role, name, phone, hours, use for, audiences
AGENCY_CONTACTS = [
    ("Emergency", "911", "911", "Any time", "A child is in immediate danger.", "kin,foster,applicant"),
    ("After-hours line", "Cedar County after-hours line", "555-0199", "Evenings, weekends and holidays",
     "Urgent placement problems when your worker's office is closed.", "kin,foster"),
    ("Behavior support", "Cedar Youth Behavioral Support line", "555-0177", "24 hours",
     "A child's behavior is hard to manage, or you worry the placement may not hold.", "kin,foster"),
    ("Legal questions", "Caregiver Legal Help Line (Cedar Legal Aid)", "555-0166", "Weekdays 9 to 5",
     "Your rights, court notices, guardianship and adoption questions.", "kin,foster,applicant"),
    ("Payments", "Caregiver payments unit", "555-0140", "Weekdays 8 to 5",
     "A payment is late or wrong, or a reimbursement is stuck.", "kin,foster,applicant"),
    ("Kinship navigator", "Cedar Kinship Navigator", "555-0155", "Weekdays 9 to 6",
     "Help applying for supports, and local support groups.", "kin"),
    ("Peer mentor", "Cedar Foster Families Association mentor", "555-0188", "Evenings",
     "Talk to someone who has fostered before.", "foster,applicant"),
]
# child: routines, health, school, comfort, avoid, updated (days), source
CARE_NEEDS = {
    "ch02": ("Bed by 8. Likes a night light and her stuffed rabbit, Coco. Eats breakfast before school.",
             "Peanut allergy: epinephrine auto-injector must go to school with her. No regular medicines.",
             "Riverside Elementary, grade 1. Teacher: Ms. Alvarado. The school can keep her placement if she stays in the area.",
             "Speaks Spanish at home. Calms down with drawing and with Tía Lucia's dog.",
             "Loud arguments upset her. Talk calmly about her mom's hospital stay; Maya will explain what to say.",
             -2, "Caseworker notes and initial visit"),
    "ch11": ("Two naps a day (about 9:30 and 1:30). Bottle before bed. Early riser.",
             "Born early. Weekly physical therapy through early intervention. Next pediatric check in three weeks.",
             "Not in school. Early intervention visits on Tuesdays.",
             "Settles with rocking and white noise.",
             "Bright, busy rooms overstimulate her near nap time.",
             -10, "Caseworker notes and early intervention plan"),
    "ch01": ("Soccer on Saturdays. Homework after dinner works best.",
             "Asthma: inhaler as needed, especially after exercise. Check-up booked on the 28th.",
             "Cedar Elementary, grade 4. Likes his teacher, Mr. Ortiz.",
             "Pancakes on Saturdays. Talking about his grandma, Denise.",
             "Missed visits with his mom are hard; tell him early if a visit changes.",
             -12, "Visit transcript, Oct 24"),
}
# owner type, owner id, from, worker, text, sent (days), answered (days or None), answer
MESSAGES = [
    ("applicant", "ap1", "Jordan Bennett", "lw1", "How do I book Casey's fingerprint appointment? The link in the email doesn't work.", -6, None, None),
    ("kin", "kin1", "Lucia Ramirez", "cw1", "Does Sofia need a doctor's note for her peanut allergy at school?", -2, -1,
     "Yes. I'll bring the school form on Thursday and help you fill it in. – Maya"),
    ("foster", "fp1", "Megan Hughes", "cw3", "When will we hear about the adoption assistance agreement?", 0, None, None),
]
# worker, from, case, text, days ago
RECOGNITIONS = [
    ("cw1", "Robert Hale (supervisor)", "case-02", "Thorough kin search on Sofia's case: her aunt reached and caring for her within a day.", -1),
    ("cw2", "Robert Hale (supervisor)", "case-05", "Mateo's visit write-up was clear and on time.", -3),
    ("cw3", "Robert Hale (supervisor)", "case-11", "Isabella's adoption steps are moving on schedule. Thank you.", -2),
]


def seed(conn):
    conn.executescript(SCHEMA)
    ins = conn.execute
    for w in WORKERS:
        ins("INSERT INTO workers VALUES (?,?,?,?,?,?,?)", (w[0], w[1], w[2], AGENCY, w[3], w[4], w[5]))

    for c in CHILDREN:
        av = c["avatar"]
        ins("INSERT INTO children VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["id"], c["first"], c["last"], dob(c["age"], int(c["id"][-2:]) * 9), c["gender"], c["pronouns"],
             c["race"], c["lang"], c["icwa"], c["school"], c["grade"], c["medical"], c["allergies"],
             json.dumps(dict(skin=av[0], hair=av[1], style=av[2], bg=av[3], shirt=av[4], freckles=av[5], glasses=av[6]))))
        k = c["case"]
        case_id = "case-" + c["id"][2:]
        ins("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (case_id, k["no"], c["id"], k["worker"], d(k["opened"]), k["reason"], k["goal"], k["status"], JURIS,
             json.dumps(k["flags"]), k["parent"]))
        p = c["placement"]
        ins("INSERT INTO placements (child_id, caregiver, kind, start_on, end_on, city, current) VALUES (?,?,?,?,?,?,1)",
            (c["id"], p[0], p[1], d(p[2]), None, p[3]))
        if k["opened"] < p[2] - 1:  # an earlier emergency placement
            ins("INSERT INTO placements (child_id, caregiver, kind, start_on, end_on, city, current) VALUES (?,?,?,?,?,?,0)",
                (c["id"], "Cedar Emergency Shelter", "shelter", d(k["opened"]), d(p[2]), "Cedar City"))
        for i, r in enumerate(c["rel"]):
            ins("INSERT INTO relationships (child_id, name, relation, contact_status, language, phone, last_contact_on, notes) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (c["id"], r[0], r[1], r[2], r[3], f"555-02{int(c['id'][-2:]):02d}{i}", d(r[4]) if r[4] is not None else None, ""))
        for t in c["tasks"]:
            ins("INSERT INTO tasks (case_id, title, due_on, status, kind) VALUES (?,?,?,?,?)",
                (case_id, t[0], d(t[1]), "open", t[2]))
        if c["court"]:
            ins("INSERT INTO court_dates (case_id, on_date, hearing, report_status) VALUES (?,?,?,?)",
                (case_id, d(c["court"][0]), c["court"][1], c["court"][2]))
        for v in c["visits"]:
            vid = ins("INSERT INTO visits (case_id, on_date, kind, location, consent, transcript, note_status) VALUES (?,?,?,?,?,?,?)",
                      (case_id, d(v[0]), v[1], v[2], v[3], v[4], v[5])).lastrowid
            if v[5] == "signed":
                ins("INSERT INTO notes (case_id, visit_id, on_date, author, body, status, ai_drafted) VALUES (?,?,?,?,?,?,0)",
                    (case_id, vid, d(v[0]), k["worker"], f"{v[1]} at {v[2]}. Child seen and doing well overall. "
                     "See the case plan for follow-ups.", "signed"))
            if v[5] == "draft" and c["id"] == "ch01":
                ins("INSERT INTO proposals (idem_key, object_type, object_id, kind, payload, summary, status, created_by, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (f"note:{vid}", "case", case_id, "note",
                     json.dumps({"visit_id": vid, "body": AI_DRAFT_JAYLEN, "on_date": d(v[0])}),
                     f"Visit note draft for {d(v[0])}", "pending", "binti-ai", d(v[0]) + "T17:00:00"))
        for r in c["referrals"]:
            ins("INSERT INTO referrals (case_id, provider, service, status, sent_on) VALUES (?,?,?,?,?)",
                (case_id, r[0], r[1], r[2], d(r[3]) if r[3] is not None else None))
        for g in c["goals"]:
            ins("INSERT INTO plan_goals (case_id, goal, status) VALUES (?,?,?)", (case_id, g[0], g[1]))
        # History
        ins("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
            (case_id, d(k["opened"]), "case", f"Case opened. {k['reason']}."))
        ins("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
            (case_id, d(p[2]), "placement", f"Placed with {p[0]}."))
        for v in c["visits"]:
            ins("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
                (case_id, d(v[0]), "visit", f"{v[1]} at {v[2]}."))
        if k["opened"] < -90:
            ins("INSERT INTO history (case_id, on_date, kind, text) VALUES (?,?,?,?)",
                (case_id, d(k["opened"] + 60), "court", "Disposition hearing held. Case plan ordered."))

    # Kin caregiver persona: Lucia Ramirez, caring for Sofia since day -6.
    lucia = conn.execute("SELECT id FROM relationships WHERE name='Lucia Ramirez'").fetchone()[0]
    ins("INSERT INTO kin_users VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("kin1", "Lucia Ramirez", lucia, "ch02", "Spanish, English", "555-0230", d(-6), json.dumps(KIN_APPROVAL), json.dumps(KIN_SUPPORTS), None))
    # Licensed foster parent persona: the Hughes family, adopting Isabella.
    ins("INSERT INTO foster_users VALUES (?,?,?,?,?,?,?,?,?)",
        ("fp1", "Megan Hughes", "Megan and Chris Hughes", "ch11", "555-0260", d(-800),
         json.dumps(FOSTER_PAYMENTS), json.dumps(FOSTER_SUPPORTS), json.dumps(ADOPTION_STEPS)))
    for i, c in enumerate(AGENCY_CONTACTS):
        ins("INSERT INTO agency_contacts (role, name, phone, hours, use_for, audience, sort) VALUES (?,?,?,?,?,?,?)", c + (i,))
    for cid, n in CARE_NEEDS.items():
        ins("INSERT INTO care_needs VALUES (?,?,?,?,?,?,?,?)", (cid, n[0], n[1], n[2], n[3], n[4], d(n[5]), n[6]))
    for m in MESSAGES:
        ins("INSERT INTO worker_messages (idem_key, owner_type, owner_id, from_name, worker_id, text, sent_at, answered_at, answer) "
            "VALUES (?,?,?,?,?,?,?,?,?)", (f"seed-{m[0]}-{m[5]}", m[0], m[1], m[2], m[3], m[4],
                                          d(m[5]) + "T10:00:00", (d(m[6]) + "T15:00:00") if m[6] is not None else None, m[7]))
    for r in RECOGNITIONS:
        ins("INSERT INTO recognitions (worker_id, from_name, case_id, text, on_date) VALUES (?,?,?,?,?)", r[:4] + (d(r[4]),))
    # Applicant persona: the Bennetts.
    ins("INSERT INTO applicants VALUES (?,?,?,?,?,?,?,?)",
        ("ap1", "Jordan Bennett", "Jordan and Casey Bennett", "English", "lw1", "Complete requirements",
         json.dumps(APPLICATION), json.dumps(CHECKLIST)))

    for row in DISCLOSURE:
        ins("INSERT INTO disclosure VALUES (?,?,?,?,?,?,?)", row)
    ins("INSERT INTO agency_settings VALUES ('kin_medical', 'true')")
    ins("INSERT INTO agency_settings VALUES ('care_needs_sharing', 'true')")
    ins("INSERT INTO agency_settings VALUES ('kin_license_target_days', '90')")
    ins("INSERT INTO agency_settings VALUES ('message_response_business_days', '2')")
    for t, aud, body in PROGRAM_DOCS:
        ins("INSERT INTO program_docs (title, audience, jurisdiction, body, source) VALUES (?,?,?,?,?)",
            (t, aud, JURIS, body, f"Cedar County caregiver guide (fictional): {t}"))
    ins("INSERT INTO meta VALUES ('seeded_on', ?)", (date.today().isoformat(),))
    conn.commit()


if __name__ == "__main__":
    import os
    from . import db
    path = db.db_path()
    if path != ":memory:" and os.path.exists(path):
        os.remove(path)
    db.connect()
    print("Seeded", path)

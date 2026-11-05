"""Loads Agent Skills from skills/<name>/SKILL.md (Anthropic Agent Skills format).

Frontmatter: name, description, allowed-tools (comma separated) and metadata (persona, kind, phase, feature).
Progressive disclosure: the agent sees each skill's name and description; it calls `load_skill` to read the body.
"""
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"


def _parse(text):
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    _, fm, body = text.split("---", 2)
    meta, cur = {}, None
    for line in fm.strip().splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and cur:
            k, v = line.strip().split(":", 1)
            meta[cur][k.strip()] = v.strip()
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "":
            meta[k], cur = {}, k
        else:
            meta[k], cur = v.strip('"'), None
    tools = [t.strip() for t in meta.get("allowed-tools", "").split(",") if t.strip()]
    md = meta.get("metadata", {})
    return {"name": meta["name"], "description": meta["description"], "allowed_tools": tools,
            "personas": [p.strip() for p in md.get("persona", "").split(",") if p.strip()],
            "kind": md.get("kind", ""), "phase": md.get("phase", ""), "feature": md.get("feature", ""),
            "body": body.strip()}


@lru_cache(maxsize=1)
def all_skills():
    out = {}
    for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        s = _parse(p.read_text(encoding="utf-8"))
        if s["name"] != p.parent.name:
            raise ValueError(f"Skill name {s['name']!r} must match its folder {p.parent.name!r}")
        out[s["name"]] = s
    return out


def for_persona(persona):
    return {n: s for n, s in all_skills().items() if persona in s["personas"]}


def index_text(persona):
    return "\n".join(f"- {n}: {s['description']}" for n, s in for_persona(persona).items())


def load(persona, name):
    s = for_persona(persona).get(name)
    if not s:
        return {"error": f"Skill {name!r} is not available to the {persona} agent."}
    return {"name": name, "allowed_tools": s["allowed_tools"], "instructions": s["body"]}

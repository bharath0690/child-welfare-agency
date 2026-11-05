"""Illustrated SVG avatars for fictional children. No photos of real children are used anywhere."""

SKIN = ["#f6d7c3", "#eac3a2", "#d9a37e", "#b97c55", "#8d5a3b", "#5e3b28"]
HAIR = ["#2b1d14", "#4a2e1d", "#7a4a26", "#c58b4b", "#e2c27a", "#1c1c1c", "#8b3a24"]
BG = ["#dbeafe", "#dcfce7", "#fef3c7", "#fce7f3", "#e0e7ff", "#ccfbf1", "#ffedd5"]
SHIRT = ["#2563eb", "#16a34a", "#f59e0b", "#db2777", "#7c3aed", "#0d9488", "#ea580c"]
STYLES = ["short", "curly", "long", "puffs", "buzz", "bun", "wavy"]


def svg(skin=0, hair=0, style="short", bg=0, shirt=0, freckles=False, glasses=False, label="Child avatar") -> str:
    s, h, b, sh = SKIN[skin % 6], HAIR[hair % 7], BG[bg % 7], SHIRT[shirt % 7]
    back = {
        "long": f"<path d='M26 52 Q24 92 34 104 L86 104 Q96 92 94 52 Z' fill='{h}'/>",
        "wavy": f"<path d='M28 50 Q22 80 30 98 Q40 92 36 80 L84 80 Q80 92 90 98 Q98 80 92 50 Z' fill='{h}'/>",
        "puffs": f"<circle cx='30' cy='38' r='13' fill='{h}'/><circle cx='90' cy='38' r='13' fill='{h}'/>",
        "bun": f"<circle cx='60' cy='18' r='12' fill='{h}'/>",
    }.get(style, "")
    top = {
        "short": f"<path d='M34 50 Q34 24 60 24 Q86 24 86 50 Q80 36 60 36 Q42 36 34 50 Z' fill='{h}'/>",
        "curly": "".join(f"<circle cx='{x}' cy='{y}' r='9' fill='{h}'/>" for x, y in
                         [(38, 40), (46, 30), (58, 26), (70, 28), (80, 36), (85, 46), (35, 50)]),
        "long": f"<path d='M33 54 Q32 24 60 24 Q88 24 87 54 Q78 34 60 34 Q42 34 33 54 Z' fill='{h}'/>",
        "puffs": f"<path d='M35 48 Q36 28 60 28 Q84 28 85 48 Q76 36 60 36 Q44 36 35 48 Z' fill='{h}'/>",
        "buzz": f"<path d='M36 46 Q37 28 60 28 Q83 28 84 46 Q78 36 60 35 Q42 36 36 46 Z' fill='{h}' opacity='.75'/>",
        "bun": f"<path d='M34 50 Q34 26 60 26 Q86 26 86 50 Q78 34 60 34 Q42 34 34 50 Z' fill='{h}'/>",
        "wavy": f"<path d='M32 54 Q30 24 60 24 Q90 24 88 54 Q82 36 70 38 Q60 30 50 38 Q38 36 32 54 Z' fill='{h}'/>",
    }[style]
    extra = ""
    if freckles:
        extra += "".join(f"<circle cx='{x}' cy='66' r='1.2' fill='#a0522d' opacity='.55'/>" for x in (46, 50, 70, 74))
    if glasses:
        extra += ("<g fill='none' stroke='#1f2937' stroke-width='2'><circle cx='50' cy='57' r='7'/>"
                  "<circle cx='70' cy='57' r='7'/><path d='M57 57 H63'/></g>")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' role='img' aria-label='{label}'>"
        f"<circle cx='60' cy='60' r='60' fill='{b}'/>{back}"
        f"<path d='M22 120 Q24 90 60 88 Q96 90 98 120 Z' fill='{sh}'/>"
        f"<rect x='52' y='76' width='16' height='14' rx='6' fill='{s}'/>"
        f"<ellipse cx='60' cy='56' rx='25' ry='28' fill='{s}'/>"
        f"<circle cx='35' cy='58' r='5' fill='{s}'/><circle cx='85' cy='58' r='5' fill='{s}'/>{top}"
        f"<circle cx='50' cy='58' r='2.6' fill='#1f2937'/><circle cx='70' cy='58' r='2.6' fill='#1f2937'/>"
        f"<path d='M51 70 Q60 77 69 70' fill='none' stroke='#7c2d12' stroke-width='2.4' stroke-linecap='round'/>"
        f"<circle cx='44' cy='67' r='4' fill='#f87171' opacity='.18'/><circle cx='76' cy='67' r='4' fill='#f87171' opacity='.18'/>"
        f"{extra}</svg>"
    )

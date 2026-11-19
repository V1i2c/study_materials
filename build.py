#!/usr/bin/env python3
"""
build.py -- merge data/<subject>/*.json into template.html -> jac_pyqs.html
Everything (KaTeX JS, CSS, woff2 fonts as data URIs, question DB) is inlined so the
output is a single self-contained file that works fully offline.
"""
import base64
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ROOT, "template.html")
OUT = os.path.join(ROOT, "jac_pyqs.html")
ASSETS = os.path.join(ROOT, "assets")

WHITELIST_ORDER = {
    "Physics": [
        "Electric Charges and Fields", "Electrostatic Potential and Capacitance",
        "Current Electricity", "Moving Charges and Magnetism", "Magnetism and Matter",
        "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves",
        "Ray Optics and Optical Instruments", "Wave Optics",
        "Dual Nature of Radiation and Matter", "Atoms", "Nuclei",
        "Semiconductor Electronics: Materials, Devices and Simple Circuits",
        "Deleted / Old Syllabus",
    ],
    "Chemistry": [
        "Solutions", "Electrochemistry", "Chemical Kinetics",
        "The d- and f-Block Elements", "Coordination Compounds",
        "Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers",
        "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules",
        "Deleted / Old Syllabus",
    ],
    "Mathematics": [
        "Relations and Functions", "Inverse Trigonometric Functions", "Matrices",
        "Determinants", "Continuity and Differentiability", "Application of Derivatives",
        "Integrals", "Application of Integrals", "Differential Equations",
        "Vector Algebra", "Three Dimensional Geometry", "Linear Programming",
        "Probability",
    ],
    "English Core": [
        "Reading Comprehension", "Creative Writing Skills", "The Last Lesson",
        "Lost Spring", "Deep Water", "The Rattrap", "Indigo", "Poets and Pancakes",
        "The Interview", "Going Places", "My Mother at Sixty-Six", "Keeping Quiet",
        "A Thing of Beauty", "A Roadside Stand", "Aunt Jennifer's Tigers",
        "The Third Level", "The Tiger King", "Journey to the End of the Earth",
        "The Enemy", "On the Face of It", "Memories of Childhood",
        "Deleted / Old Syllabus",
    ],
}
SUBJ_ORDER = ["Physics", "Chemistry", "Mathematics", "English Core"]


def fonts_css():
    """Inline every woff2 in assets/fonts as a data URI."""
    path = os.path.join(ASSETS, "fonts")
    if not os.path.isdir(path):
        return ""
    out = []
    for f in sorted(os.listdir(path)):
        if not f.endswith(".woff2"):
            continue
        fam, style = f[:-6], "normal"
        # e.g. KaTeX_Main-Bold -> family KaTeX_Main, weight bold
        if "-" in fam:
            fam, style = fam.split("-", 1)
        weight = "normal"
        famstyle = "normal"
        low = style.lower()
        if "bold" in low:
            weight = "bold"
        if "italic" in low:
            famstyle = "italic"
        with open(os.path.join(path, f), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        out.append(
            "@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:swap;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % (fam, famstyle, weight, b64)
        )
    return "\n".join(out)


def strip_css_font_urls(css):
    """Drop remote @font-face src urls; replaced by inlined data URIs."""
    css = re.sub(r"url\((['\"]?)fonts/[^)]*\)", "url(about:blank)", css)
    return css


def load_questions():
    questions, papers = [], []
    for subject in SUBJ_ORDER:
        folder = os.path.join(ROOT, "data", {
            "Physics": "physics", "Chemistry": "chemistry",
            "Mathematics": "mathematics", "English Core": "english"}[subject])
        files = sorted(glob.glob(os.path.join(folder, "*.json")))
        for pth in files:
            paper = json.load(open(pth, encoding="utf-8"))
            papers.append({
                "key": paper["key"], "subject": paper["subject"],
                "year": paper["year"], "count": len(paper["questions"]),
            })
            for q in paper["questions"]:
                q = dict(q)
                q["_k"] = paper["key"]
                q["_s"] = paper["subject"]
                q.setdefault("diagramSvg", "")
                questions.append(q)
    questions.sort(key=lambda q: (
        SUBJ_ORDER.index(q["_s"]),
        WHITELIST_ORDER[q["_s"]].index(q["chapter"]) if q["chapter"] in WHITELIST_ORDER[q["_s"]] else 99,
        q["year"], q["_k"], _qno_sort(q["qno"]),
    ))
    return questions, papers


def _qno_sort(qno):
    m = re.match(r"\d+", str(qno))
    return (int(m.group(0)) if m else 999, str(qno))


def main():
    questions, papers = load_questions()
    if not questions:
        raise SystemExit("FAIL: no question JSON found in data/ — nothing to build")

    db = {
        "chapters": WHITELIST_ORDER,
        "papers": papers,
        "questions": questions,
    }
    payload = json.dumps(db, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</script", "<\\/script").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    tpl = open(TEMPLATE, encoding="utf-8").read()
    kcss = open(os.path.join(ASSETS, "katex.min.css"), encoding="utf-8").read()
    kjs = open(os.path.join(ASSETS, "katex.min.js"), encoding="utf-8").read()
    ajs = open(os.path.join(ASSETS, "auto-render.min.js"), encoding="utf-8").read()

    css = strip_css_font_urls(kcss) + "\n" + fonts_css()

    out = tpl.replace("/*__KATEX_CSS__*/", css)
    out = out.replace("/*__KATEX_JS__*/", kjs)
    out = out.replace("/*__AUTORENDER_JS__*/", ajs)
    out = out.replace("/*__DB_JSON__*/", payload)

    for marker in ("__KATEX_CSS__", "__KATEX_JS__", "__AUTORENDER_JS__", "__DB_JSON__"):
        if marker in out:
            raise SystemExit("FAIL: placeholder %s not replaced" % marker)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)

    size = os.path.getsize(OUT) / (1024 * 1024)
    print("built %s" % OUT)
    print("  questions: %d   papers: %d   size: %.2f MB" % (len(questions), len(papers), size))
    per = {}
    for q in questions:
        per[q["_s"]] = per.get(q["_s"], 0) + 1
    for s in SUBJ_ORDER:
        print("  %-14s %d" % (s, per.get(s, 0)))


if __name__ == "__main__":
    main()

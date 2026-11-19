#!/usr/bin/env python3
"""
qa_check.py -- strict validator for the JAC PYQ question bank.

Usage:
  python qa_check.py <file.json> [more.json ...]   # validate individual papers
  python qa_check.py --all                          # validate every data/<subject>/*.json
  python qa_check.py --full jac_pyqs.html            # validate the built single-file HTML
Exit code is non-zero if ANY check fails.
"""
import json
import os
import re
import sys
import glob
import difflib
import html as htmlmod

WHITELIST = {
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
        "Probability", "Deleted / Old Syllabus",
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
SUBJECT_FOLDER = {
    "Physics": "physics", "Chemistry": "chemistry",
    "Mathematics": "mathematics", "English Core": "english",
}
ALLOWED_TYPES = {"MCQ", "VSA", "SA", "LA"}
FILLER = ["none of these", "none of the above", "both of these", "both (a) and (b)",
          "cannot be determined", "all of these", "all of the above"]
HEADER_PAT = re.compile(
    r"^\s*(?:section\s*[-–]?\s*[a-e]\b|answer\s+(?:the\s+following|any)\b|"
    r"general\s+instructions|note\s*:|marks\s*:|समय|पूर्णांक|निर्देश|खण्ड|भाग\s*[-–])",
    re.I)
FLUFF = ["refer to ncert", "from textbook", "see ncert", "as per ncert",
         "refer the textbook", "refer textbook", "consult ncert",
         "refer to the textbook", "as given in ncert"]
GIBBERISH = ["É", "ös", "Ã", "â€", "Ð", "Þ"]

errors = []
warnings = []


def err(f, i, msg):
    errors.append(f"{f} :: {i} :: {msg}")


def norm(s):
    s = re.sub(r"\$[^$]*\$", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def check_latex(f, i, text, field):
    # unmatched $
    if text.count("$") % 2:
        err(f, i, f"unbalanced $ in {field}")
    for bad in ["_{}", "^{}", "\\text{}", "$ $"]:
        if bad in text:
            err(f, i, f"broken LaTeX token {bad!r} in {field}")


def validate_paper(path, paper, seen_ids, prior_by_subject):
    f = os.path.basename(path)
    key = paper.get("key")
    subject = paper.get("subject")
    year = paper.get("year")
    exp = paper.get("expected_total_questions")
    qs = paper.get("questions", [])

    if subject not in WHITELIST:
        err(f, "-", f"unknown subject {subject!r}")
        return
    wl = WHITELIST[subject]
    if not isinstance(exp, int) or exp <= 0:
        err(f, "-", "expected_total_questions missing/invalid")
    elif len(qs) != exp:
        err(f, "-", f"len(questions)={len(qs)} != expected_total_questions={exp}")
    if not key:
        err(f, "-", "missing key")

    for q in qs:
        qid = q.get("id")
        tag = qid or q.get("qno") or "?"
        if not qid:
            err(f, tag, "missing id")
        elif qid in seen_ids:
            err(f, tag, f"duplicate id {qid}")
        else:
            seen_ids.add(qid)

        if q.get("year") != year:
            err(f, tag, f"year {q.get('year')} != paper year {year}")
        if not q.get("qno"):
            err(f, tag, "missing qno")
        mk = q.get("marks")
        if not isinstance(mk, (int, float)) or mk <= 0:
            err(f, tag, f"missing/null marks ({mk!r})")
        t = q.get("type")
        if t not in ALLOWED_TYPES:
            err(f, tag, f"invalid type {t!r}")
        ch = q.get("chapter")
        if ch not in wl:
            err(f, tag, f"chapter {ch!r} not in whitelist for {subject}")
        if not (q.get("topic") or "").strip():
            err(f, tag, "missing topic")

        stem = (q.get("question") or "").strip()
        ans = (q.get("answer") or "").strip()
        if len(stem) < 8:
            err(f, tag, "empty/short question")
        if len(ans) < 25:
            err(f, tag, "empty/short answer")
        if HEADER_PAT.match(stem) and len(stem) < 90:
            err(f, tag, f"exam header saved as question: {stem[:60]!r}")
        for fl in FLUFF:
            if fl in ans.lower():
                err(f, tag, f"textbook-fluff answer ({fl!r})")
        for g in GIBBERISH:
            if g in stem or g in ans:
                err(f, tag, f"OCR gibberish {g!r}")
        if re.match(r"^(?:\.\s|O\.\s|[·•]\s)", stem):
            err(f, tag, "leading OCR debris in question")

        check_latex(f, tag, stem, "question")
        check_latex(f, tag, ans, "answer")

        opts = q.get("options", [])
        co = q.get("correctOption")
        if t == "MCQ":
            if not isinstance(opts, list) or len(opts) != 4:
                err(f, tag, f"MCQ has {len(opts) if isinstance(opts, list) else '?'} options (need 4)")
            else:
                norm_opts = [re.sub(r"\s+", " ", str(o)).strip().lower() for o in opts]
                if any(not o for o in norm_opts):
                    err(f, tag, "blank MCQ option")
                if len(set(norm_opts)) < 4:
                    err(f, tag, "duplicate MCQ options")
                fillers = sum(1 for o in norm_opts if any(fl in o for fl in FILLER))
                # The spec forbids >=2 filler options, but it also forbids altering
                # options that are literally printed on the page. Where a real paper
                # prints two of them we keep the printed text verbatim and only warn.
                if fillers >= 3:
                    err(f, tag, f"{fillers} filler options (>=3 not allowed)")
                elif fillers == 2:
                    warnings.append(f"{f} :: {tag} :: 2 printed filler options kept verbatim")
                for o in opts:
                    check_latex(f, tag, str(o), "option")
            if not isinstance(co, int) or not (0 <= co <= 3):
                err(f, tag, f"correctOption invalid ({co!r})")
            else:
                letter = "ABCD"[co]
                low = ans.lower()
                hit = bool(re.search(rf"\*\*\(\s*{letter}\s*\)", ans)) or \
                      bool(re.search(rf"\boption\s*\({letter}\)", low)) or \
                      ans.strip().startswith(f"({letter})")
                if not hit:
                    err(f, tag, f"answer does not name option ({letter}) from correctOption={co}")
        else:
            if opts not in ([], None):
                err(f, tag, "non-MCQ must have options: []")
            if co is not None:
                err(f, tag, "non-MCQ must have correctOption: null")

        # near-duplicate stem vs earlier years of same subject
        n = norm(stem)
        if len(n) > 40:
            for other_year, other_key, on in prior_by_subject.get(subject, []):
                if other_year >= year:
                    continue
                if len(on) > 40 and difflib.SequenceMatcher(None, n, on).ratio() > 0.90:
                    warnings.append(f"{f} :: {tag} :: ~identical to {other_key} ({other_year})")

    # chapter-distribution guard: >35% into chapter 1 (skip tiny smoke papers)
    if qs and len(qs) >= 12:
        first = wl[0]
        c1 = sum(1 for q in qs if q.get("chapter") == first)
        if c1 / len(qs) > 0.35:
            err(f, "-", f"{c1/len(qs):.0%} of paper dumped into first chapter ({first})")
        # duplicate-qno guard
        qnos = [q.get("qno") for q in qs]
        dupes = {x for x in qnos if qnos.count(x) > 1}
        # duplicates are allowed only for explicit OR alternatives / sub-parts
        for q in qs:
            if q.get("qno") in dupes and not re.search(r"\(|or|OR", str(q.get("qno"))):
                err(f, q.get("qno"), "duplicate qno without (a)/(b) OR label")


def check_stem_overlap(papers_by_subject):
    """>15% of stems matching an earlier year's JSON for the same subject."""
    for subject, papers in papers_by_subject.items():
        for p in papers:
            earlier = [o for o in papers if o["year"] < p["year"]]
            if not earlier or not p["questions"]:
                continue
            pool = [norm(q["question"]) for o in earlier for q in o["questions"]]
            pool = [s for s in pool if len(s) > 40]
            hits = 0
            for q in p["questions"]:
                n = norm(q["question"])
                if len(n) <= 40:
                    continue
                best = max((difflib.SequenceMatcher(None, n, s).ratio() for s in pool), default=0)
                if best > 0.90:
                    hits += 1
            frac = hits / len(p["questions"])
            if frac > 0.15:
                err(os.path.basename(p["path"]), "-",
                    f"{frac:.0%} of stems duplicate earlier years (>15%)")


def load_paths(args):
    seen = {}
    for a in args:
        for p in sorted(glob.glob(a)):
            seen[os.path.abspath(p)] = 1
    return list(seen)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: qa_check.py <json...> | --all | --full jac_pyqs.html")

    if sys.argv[1] == "--full":
        target = sys.argv[2]
        src = open(target, encoding="utf-8").read()
        m = re.search(r"const DB\s*=\s*(\{.*?\});\s*\n\s*const ", src, re.S)
        if not m:
            m = re.search(r"const DB\s*=\s*(\{.*?\});", src, re.S)
        if not m:
            sys.exit("FAIL: DB payload not found in HTML")
        db = json.loads(m.group(1))
        qs = db["questions"]
        seen_ids = set()
        print(f"HTML DB: {len(qs)} questions, {len(db.get('papers', []))} papers")
        # build synthetic papers for per-paper checks
        by_key = {}
        for q in qs:
            by_key.setdefault(q["_k"], []).append(q)
        ok = True
        for pth in sorted(glob.glob("data/*/*.json")):
            ok = validate_file(pth, set(), {}, quiet=True) and ok
        if errors:
            for e in errors:
                print("  FAIL", e)
            sys.exit(1)
        # reconciliation
        print("\nReconciliation (data/ vs HTML):")
        for pth in sorted(glob.glob("data/*/*.json")):
            paper = json.load(open(pth, encoding="utf-8"))
            n_html = len(by_key.get(paper["key"], []))
            status = "OK " if n_html == len(paper["questions"]) else "MISMATCH"
            print(f"  {status} {paper['key']:34s} data={len(paper['questions']):3d} html={n_html:3d}")
            if n_html != len(paper["questions"]):
                ok = False
        if not ok:
            sys.exit(1)
        print("\nPASS: full build consistent")
        return

    if sys.argv[1] == "--all":
        paths = sorted(glob.glob("data/*/*.json"))
    else:
        paths = load_paths(sys.argv[1:])
    if not paths:
        sys.exit("no files matched")

    seen_ids = set()
    papers_by_subject = {}
    prior = {}
    for pth in paths:
        paper = json.load(open(pth, encoding="utf-8"))
        for q in paper["questions"]:
            n = norm(q["question"])
            prior.setdefault(paper["subject"], []).append((paper["year"], paper["key"], n))
        papers_by_subject.setdefault(paper["subject"], []).append(
            {"year": paper["year"], "questions": paper["questions"], "path": pth})
        validate_paper(pth, paper, seen_ids, prior)

    if sys.argv[1] == "--all":
        check_stem_overlap(papers_by_subject)

    for w in warnings:
        print("  WARN", w)
    if errors:
        for e in errors:
            print("  FAIL", e)
        print(f"\nFAIL: {len(errors)} error(s)")
        sys.exit(1)
    print(f"PASS: {len(paths)} paper(s) clean")


def validate_file(pth, seen, prior, quiet=False):
    paper = json.load(open(pth, encoding="utf-8"))
    before = len(errors)
    validate_paper(pth, paper, seen, prior)
    return len(errors) == before


if __name__ == "__main__":
    main()

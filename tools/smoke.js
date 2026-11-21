#!/usr/bin/env node
/**
 * smoke.js -- headless walk of the built jac_pyqs.html in jsdom.
 *
 * Drives the real UI: subject tabs -> every chapter -> open every marks /
 * category / topic bucket (row count must match the header badge) -> open a
 * question -> select an option, check the answer, reveal the solution, star,
 * prev/next -> back. Then the Starred tab and "All Starred". Any thrown error,
 * console error or empty render fails the run.
 *
 *   node tools/smoke.js [jac_pyqs.html]
 */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const file = path.resolve(process.argv[2] || 'jac_pyqs.html');
const html = fs.readFileSync(file, 'utf8');

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', (e) => errors.push('jsdomError: ' + (e.detail || e.message)));
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  virtualConsole: vc,
  beforeParse(win) {
    win.scrollTo = () => {};
    win.HTMLCanvasElement.prototype.getContext = () => null;
    win.HTMLElement.prototype.scrollIntoView = () => {};
  },
});

const win = dom.window;
const doc = win.document;
const $ = (s) => doc.querySelector(s);
const $$ = (s) => Array.from(doc.querySelectorAll(s));
const click = (el, what) => {
  if (!el) throw new Error('missing element: ' + what);
  el.dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
};
const fail = (m) => errors.push(m);
const txt = (el) => (el ? el.textContent.replace(/\s+/g, ' ').trim() : '');

/** open every bucket in screen 2 and verify each renders its stated count */
function checkBuckets(where) {
  const heads = $$('#s2 [data-bkt]');
  if (!heads.length) return fail(where + ': screen 2 has no buckets');
  heads.forEach((b) => {
    const key = b.dataset.bkt;
    click(b, `${where}/${key} header`);
    const holder = b.parentElement.querySelector('.bc');
    const rows = holder.querySelectorAll('[data-id]');
    const stated = Number(holder.dataset.count);
    if (rows.length !== stated)
      fail(`${where}/${key}: rendered ${rows.length} rows, badge says ${stated}`);
  });
  return heads.length;
}

function practiceOne(where, db, mathOnly) {
  const bucket = $('#s2 [data-bkt="all"]');
  if (!bucket) return fail(where + ': no "All Questions" bucket');
  click(bucket, where + '/all');
  const rows = $$('#s2 .bc[data-bkc="all"] [data-id]');
  if (!rows.length) return fail(where + ': "All Questions" rendered nothing');
  let pick = rows[0];
  if (mathOnly) {
    const index = {};
    db.questions.forEach((q) => { index[q.id] = q; });
    const hit = rows.find((r) => {
      const q = index[r.dataset.id];
      return q && /\$/.test((q.question || '') + (q.answer || '') + (q.options || []).join(' '));
    });
    if (!hit) return { kind: 'nomath' };
    pick = hit;
  }
  click(pick, where + '/question');
  if (!$('#s3').classList.contains('on')) return fail(where + ': screen 3 never opened');

  const info = txt($('.qinfo'));
  if (!txt($('#qb'))) fail(where + ': question body empty');
  let kind = 'descriptive';
  const opts = $$('#opts .opt');
  if (opts.length) {
    if (opts.length !== 4) fail(`${where}: MCQ has ${opts.length} options`);
    click(opts[2], where + '/option C');
    if (!opts[2].classList.contains('sel')) fail(where + ': option C did not select');
    click($('#actBtn'), where + '/check answer');
    if ($('#ast').classList.contains('hidden')) fail(where + ': solution still hidden after Check');
    const good = $('.opt.good');
    const sel = $('.opt.bad') || good;
    if (!good) fail(where + ': no .opt.good after checking an MCQ');
    if (!sel || !/sel|good|bad/.test(sel.className)) fail(where + ': checked option not marked');
    if ($$('#opts .opt').some((o) => !o.disabled && o.classList.contains('opt'))) {
      // options must lock after grading
      const locked = $$('#opts .opt').every((o) => o.disabled);
      if (!locked) fail(where + ': options not disabled after grading');
    }
    kind = 'mcq';
  } else {
    click($('#actBtn'), where + '/view solution');
    if ($('#ast').classList.contains('blurred')) fail(where + ': solution still blurred after View Solution');
    kind = 'descriptive';
  }
  if (!txt($('#ac'))) fail(where + ': answer text empty');

  // math must actually be typeset by the bundled KaTeX
  const hasMath = /\$/.test(txt($('#qb')) + txt($('#ac')) + txt($('#opts')));
  const k = $$('#s3 .katex').length;
  const kerr = $$('#s3 .katex-error');
  if (kerr.length) fail(`${where}: KaTeX error in ` + kerr.slice(0, 2).map((e) => e.textContent.slice(0, 60)).join(' | '));
  if (hasMath && !k) fail(where + ': math delimiters present but nothing typeset');
  const stats = { katex: k, kerr: kerr.length };

  const before = txt($('#starBtn'));
  click($('#starBtn'), where + '/star');
  if (txt($('#starBtn')) === before) fail(where + ': star did not toggle');

  const first = txt($('.qhead .qnum'));
  click($('#nextBtn'), where + '/next');
  if (txt($('.qhead .qnum')) === first) fail(where + ': Next did not advance');
  click($('#prevBtn'), where + '/prev');
  if (txt($('.qhead .qnum')) !== first) fail(where + ': Previous did not go back');
  click($('#back3'), where + '/back');
  return { kind, info, ...stats };
}

function run() {
  const subjects = ['Physics', 'Chemistry', 'Mathematics', 'English Core'];
  // `const DB` in a classic script lives in the global lexical scope, not on window
  const db = win.eval('DB');
  let chapters = 0;
  let buckets = 0;
  let practiced = { mcq: 0, descriptive: 0 };
  let katexSpans = 0;
  let mathQuestions = 0;
  let mathNone = 0;
  let mathNoneWhere = [];

  for (const subj of subjects) {
    click($(`[data-tab="${subj}"]`), 'tab ' + subj);
    if (!$('#s1').classList.contains('on')) fail(subj + ': screen 1 not shown');
    const sum = txt($('#s1 .sum .txt'));
    const m = /(\d+) papers · (\d+) questions/.exec(sum);
    if (!m) fail(`${subj}: summary line wrong ("${sum}")`);
    else {
      const papers = db.papers.filter((p) => p.subject === subj).length;
      const qs = db.questions.filter((q) => q._s === subj).length;
      if (Number(m[1]) !== papers) fail(`${subj}: summary says ${m[1]} papers, DB has ${papers}`);
      if (Number(m[2]) !== qs) fail(`${subj}: summary says ${m[2]} questions, DB has ${qs}`);
    }

    const names = $$('#s1 [data-ch]').map((r) => r.dataset.ch);
    if (!names.length) { fail(subj + ': no chapter rows'); continue; }

    let nonEmpty = 0;
    for (const name of names) {
      const row = $$('#s1 [data-ch]').find((r) => r.dataset.ch === name);
      if (/opacity/.test(row.getAttribute('style') || '')) continue; // syllabus chapter with 0 Qs
      click(row, subj + '/' + name);
      chapters++;
      nonEmpty++;
      if (!/on/.test($('#s2').className)) fail(`${subj}/${name}: screen 2 not shown`);
      if (!txt($('#s2 h2')).includes(name)) fail(`${subj}/${name}: wrong chapter title`);
      buckets += checkBuckets(subj + '/' + name);
      const got = practiceOne(subj + '/' + name, db);
      practiced[got.kind]++;
      katexSpans += got.katex || 0;
      // second pass per subject: open a question that actually contains math,
      // so KaTeX rendering is exercised (English Core has none by nature)
      const firstFilled = names.find((n) => {
        const el = $('#s1 [data-ch="' + n + '"]');
        return el && !/opacity/.test(el.getAttribute('style') || '');
      });
      if (subj !== 'English Core' && name === firstFilled) {
        const m = practiceOne(subj + '/' + name, db, true);
        if (m.kind === 'nomath') { mathNone++; mathNoneWhere.push(subj); }
        else { mathQuestions++; katexSpans += m.katex || 0; }
      }
      click($('#b2'), subj + ': back to subjects');
    }
    if (!nonEmpty) fail(subj + ': every chapter row is empty');
  }

  // --- sort modes
  const sortBtn = $('#s1 #sortBtn');
  const seen = [];
  for (let i = 0; i < 3; i++) { click($('#s1 #sortBtn'), 'sort'); seen.push(txt($('#s1 #sortBtn'))); }
  if (new Set(seen).size !== 3) fail('sort button does not cycle through 3 modes: ' + seen.join(' / '));

  // --- starred tab
  click($('[data-tab="__star"]'), 'starred tab');
  const starSum = txt($('#s1 .sum .txt'));
  if (!/starred question/.test(starSum)) fail('starred tab summary missing ("' + starSum + '")');
  const starRows = $$('#s1 [data-ch]').length;
  if (!starRows) fail('starred tab lists no chapters after starring questions');
  if (!$('#s1 [data-allstar]')) fail('starred tab has no "All Starred" row');
  else {
    click($('#s1 [data-allstar]'), 'all starred');
    buckets += checkBuckets('All Starred');
    const rows = $$('#s2 .bc[data-bkc="all"] [data-id]').length;
    if (!rows) fail('All Starred practice list is empty');
    // open a starred chapter path too
    click($('#b2'), 'back from All Starred');
    click($('[data-tab="__star"]'), 'starred tab again');
    const chRow = $('#s1 [data-ch]');
    if (chRow) {
      click(chRow, 'starred chapter');
      checkBuckets('starred chapter ' + chRow.dataset.ch);
      click($('#b2'), 'back');
    }
  }

  // every question reachable? compare rendered DB against reality
  const kinds = {};
  db.questions.forEach((q) => { const k = q.type + (q.options && q.options.length === 4 ? '/4opt' : ''); kinds[k] = (kinds[k] || 0) + 1; });
  console.log(`DB                : ${db.papers.length} papers, ${db.questions.length} questions`);
  console.log(`subject totals    : ` + subjects.map((s) =>
    `${s} ${db.papers.filter((p) => p.subject === s).length}p/${db.questions.filter((q) => q._s === s).length}q`).join('  '));
  console.log(`chapters exercised: ${chapters}`);
  console.log(`buckets opened    : ${buckets}`);
  console.log(`questions driven  : ${practiced.mcq} MCQ + ${practiced.descriptive} descriptive`);
  console.log(`starred summary   : ${starSum}`);
  const mathQs = db.questions.filter((q) =>
    /\$/.test((q.question || '') + (q.answer || '') + (q.options || []).join(' '))).length;
  console.log(`math questions    : ${mathQs} of ${db.questions.length} in DB, ${mathQuestions} driven with math`);
  if (mathNone) console.log(`  no math found in : ${mathNoneWhere.join(', ')}`);
  console.log(`math rendered     : ${katexSpans} KaTeX spans across driven questions (0 = unresolved)`);
  if (!katexSpans) fail('no KaTeX output rendered anywhere');
  if (mathNone) fail('no math question found in a science/maths subject: ' + mathNoneWhere.join(', '));
  console.log(`types             : ` + Object.entries(kinds).map(([k, v]) => `${k}=${v}`).join(' '));

  if (errors.length) {
    console.log(`\nFAIL (${errors.length})`);
    errors.slice(0, 40).forEach((e) => console.log('  - ' + e));
    process.exit(1);
  }
  console.log('\nPASS: UI smoke test clean');
  dom.window.close(); // stop the page's setInterval so node can exit
}

try { run(); } catch (e) {
  console.log('FAIL: ' + e.message);
  errors.slice(0, 20).forEach((x) => console.log('  - ' + x));
  process.exit(1);
}

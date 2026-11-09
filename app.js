// app/app.js — செந்தமிழ் மரபு: v2 தொகுப்பு ஏற்றி (build/bundle_v2.json, schema 2.0)
// பயன்பாடு: <script src="app/app.js"></script>; பின் SenthamilApp.init()
// v2 புலங்கள்: id, pindam, padalam, othu, sutra, moolam,
//   kaandigai{porul, ethu, eduthukkaattu[], en}, nilai, kanini{kind,…}, links[],
//   urai{vagai, vilakkukkuriyathu[], iyaipu[], text, thunivu, maruthalai[]}
const SenthamilApp = (() => {
  let bundle = null;
  let index = null;

  const ADH = { ezhuthu: 'எழு.', sol: 'சொல்.', porul: 'பொருள்.' };

  // --- ஏற்றலும் அட்டவணையும் --------------------------------------------
  async function init(bundleUrl = './build/bundle_v2.json') {
    const res = await fetch(bundleUrl);
    if (!res.ok) throw new Error(`தொகுப்பு ஏற்றல் தோல்வி: ${res.status}`);
    bundle = await res.json();
    if (!bundle.meta || bundle.meta.schema !== '2.0') {
      throw new Error('v2 தொகுப்பு (schema 2.0) தேவை — make build-v2');
    }
    index = buildIndexes(bundle);
    return { meta: bundle.meta, counts: bundle.counts };
  }

  function buildIndexes(b) {
    const byId = new Map();
    const byOthu = new Map();
    const byKind = new Map();
    const byNilai = new Map();
    const byVagai = new Map();
    const byLetter = new Map();
    const iyaipuOf = new Map();   // id → அதன் உரை இயைபாகக் காட்டும் நூற்பாக்கள் (649)
    const vilakkuOf = new Map();  // id → இதனை விலக்கும் நூற்பாக்கள் (645)
    const citations = new Map();  // id → இதனைச் சுட்டும் நூற்பாக்கள்
    for (const r of b.sutras) {
      byId.set(r.id, r);
      pushTo(byOthu, `${r.padalam}.${r.othu}`, r.id);
      pushTo(byKind, (r.kanini || {}).kind || '', r.id);
      pushTo(byNilai, r.nilai || '', r.id);
      const u = r.urai || {};
      pushTo(byVagai, u.vagai || '', r.id);
      pushTo(byLetter, tamilFirstLetter(r.moolam), r.id);
      for (const t of u.vilakkukkuriyathu || []) pushTo(vilakkuOf, t, r.id);
      const refs = new Set([...(r.links || []), ...(u.iyaipu || []), ...(u.vilakkukkuriyathu || [])]);
      for (const l of refs) if (l !== r.id) pushTo(citations, l, r.id);
      iyaipuOf.set(r.id, u.iyaipu || []);
    }
    return { byId, byOthu, byKind, byNilai, byVagai, byLetter, iyaipuOf, vilakkuOf, citations };
  }

  function pushTo(map, key, val) {
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(val);
  }

  const recs = (ids) => (ids || []).map(id => index.byId.get(id)).filter(Boolean);

  // --- வினவல் -----------------------------------------------------------
  function get(id) { return index.byId.get(id) || null; }
  function getOthu(padalam, othu) { return recs(index.byOthu.get(`${padalam}.${othu}`)); }
  function getKind(kind) { return recs(index.byKind.get(kind)); }
  function getNilai(nilai) { return recs(index.byNilai.get(nilai)); }
  function getVagai(vagai) { return recs(index.byVagai.get(vagai)); }
  function getByLetter(ch) { return recs(index.byLetter.get(ch)); }
  function iyaipu(id) { return recs(index.iyaipuOf.get(id)); }
  function vilakkuFor(id) { return recs(index.vilakkuOf.get(id)); }
  function citedBy(id) { return recs(index.citations.get(id)); }

  // பெயர் — எ.கா. "பொருள். 2"
  function label(id) {
    const r = get(id);
    return r ? `${ADH[r.padalam] || r.padalam} ${r.sutra}` : id;
  }

  // --- முழு உரைத் தேடல் (இடைவெளி நீக்கி) ---------------------------------
  function search(q) {
    if (!q || !q.trim()) return [];
    const needle = normalize(q);
    const out = [];
    for (const r of bundle.sutras) {
      const k = r.kaandigai || {}, u = r.urai || {};
      const hay = normalize([r.moolam, k.porul, k.ethu, u.text].join(' '));
      if (hay.includes(needle)) out.push({ id: r.id, score: scoreResult(r, needle) });
    }
    return out.sort((a, b) => b.score - a.score).map(x => index.byId.get(x.id));
  }

  function scoreResult(r, needle) {
    const k = r.kaandigai || {}, u = r.urai || {};
    let s = 0;
    if (normalize(r.moolam).includes(needle)) s += 10;
    if (normalize(k.porul).includes(needle)) s += 5;
    if (normalize(k.ethu).includes(needle)) s += 4;
    if (normalize(u.text).includes(needle)) s += 3;
    return s;
  }

  function normalize(s) { return (s || '').replace(/\s+/g, ''); }

  // முதல் எழுத்து (உயிர்மெய்யாயின் மெய்யும் உயிர்க்குறியும் சேர்ந்தே)
  function tamilFirstLetter(t) {
    const m = (t || '').trim().match(/^[஀-௿][ா-்ௗ]*/);
    return m ? m[0] : (t || '').trim().charAt(0);
  }

  // --- காட்சி உதவி -------------------------------------------------------
  function renderRecord(id) {
    const r = get(id);
    if (!r) return null;
    const k = r.kaandigai || {}, u = r.urai || {};
    const edu = (k.eduthukkaattu || []).map(e => `"${e.text}" (${label(e.from)})`).join('; ');
    const vagai = (u.vagai || '') + ((u.vilakkukkuriyathu || []).length
      ? ` (${u.vilakkukkuriyathu.map(label).join(', ')}-க்கு)` : '');
    return {
      header: `${label(r.id)} · ${r.nilai || ''}`,
      layers: [
        { name: 'நூற்பா', body: r.moolam },
        { name: 'காண்டிகை', body: k.porul || '' },
        { name: 'ஏது (648)', body: k.ethu || '' },
        { name: 'எடுத்துக்காட்டு (648)', body: edu || '' },
        { name: 'வகை (645)', body: vagai },
        { name: 'உரை (649)', body: u.text || '' },
        { name: 'துணிவு (650)', body: u.thunivu || '' },
        { name: 'நிலை', body: r.nilai || '' },
      ],
      iyaipu: (u.iyaipu || []).map(label),
      vilakku: vilakkuFor(id).map(x => label(x.id)),
      cited_by: citedBy(id).map(x => label(x.id)),
    };
  }

  // --- பொது இடைமுகம் ----------------------------------------------------
  return {
    init, get, getOthu, getKind, getNilai, getVagai, getByLetter,
    iyaipu, vilakkuFor, citedBy, search, renderRecord, label,
    get bundle() { return bundle; },
  };
})();

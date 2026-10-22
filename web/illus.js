/* Step illustrations for the stations that have no place to look at (before arrival, end of Umrah).
   Flat, faceless figures on the dark scene; one SVG per step, labels in EN / AR. */
const ILLUS_TEXT = {
  en: {
    bath: ['Full bath'], nails: ['Trim nails'], perfume: ['Perfume', 'on the body only'],
    men: 'Men', women: 'Women', miqat: 'Miqat',
    avoid_perfume: ['Perfume'], avoid_hair: ['Cutting hair', 'or nails'], avoid_marital: ['Marital', 'relations'], avoid_head: ['Covering', 'the head (men)'],
    shave: ['Men', 'Shave (best)'], shorten: ['Men', 'Shorten evenly'], women_cut: ['Women', 'A fingertip’s length'],
    accept: 'May Allah accept it from you', aloud: 'aloud', softly: 'softly',
  },
  ar: {
    bath: ['الاغتسال'], nails: ['تقليم الأظافر'], perfume: ['الطيب', 'في البدن فقط'],
    men: 'الرجال', women: 'النساء', miqat: 'الميقات',
    avoid_perfume: ['الطيب'], avoid_hair: ['قص الشعر', 'أو الأظافر'], avoid_marital: ['الجماع'], avoid_head: ['تغطية الرأس', '(للرجال)'],
    shave: ['الرجال', 'الحلق (أفضل)'], shorten: ['الرجال', 'التقصير'], women_cut: ['النساء', 'قدر أنملة'],
    accept: 'تقبّل الله منك', aloud: 'جهرًا', softly: 'سرًّا',
  },
};

const ILLUS = (() => {
  const C = { ivory: '#f2eee6', ivory2: '#dcd6ca', gold: '#d6ad5e', muted: '#8d8576', skin: '#b88a68', raise: 'rgba(32,39,44,.92)',
              line: 'rgba(255,255,255,.16)', blue: '#8cc4e8', red: '#e8826a', green: '#5fd38a', sand: '#c9b79c', dark: '#0b0b0c' };
  const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  let AR = false;
  const font = () => AR ? `font-family="Noto Naskh Arabic, Geeza Pro, serif" direction="rtl"` : `font-family="Atkinson Hyperlegible, system-ui, sans-serif"`;
  const text = (x, y, s, size = 18, fill = C.ivory, weight = 700) =>
    `<text x="${x}" y="${y}" text-anchor="middle" font-size="${size}" font-weight="${weight}" fill="${fill}" ${font()}>${esc(s)}</text>`;
  const arabic = (x, y, s, size = 22, fill = C.gold) =>
    `<text x="${x}" y="${y}" text-anchor="middle" font-size="${size}" fill="${fill}" font-family="Amiri, Noto Naskh Arabic, serif" direction="rtl">${esc(s)}</text>`;
  const svg = (inner) => `<svg viewBox="0 0 480 320" role="img" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
  const shadow = (x, y, w = 34) => `<ellipse cx="${x}" cy="${y}" rx="${w}" ry="6" fill="rgba(0,0,0,.35)"/>`;

  /* ---- icons, centred on (0,0), roughly 90 units tall */
  const I = {
    shower: () => `<path d="M-34,-44 H2 V-30" fill="none" stroke="${C.muted}" stroke-width="6" stroke-linecap="round"/>
      <path d="M-18,-30 H22 L15,-18 H-11 Z" fill="${C.ivory2}"/>
      ${[[-10, -4], [2, 2], [14, -6], [-4, 18], [8, 24], [20, 12], [-14, 32], [2, 40]].map(([x, y]) => `<path d="M${x},${y - 7} q4,6 0,9 q-4,-3 0,-9z" fill="${C.blue}"/>`).join('')}`,
    clipper: () => `<g transform="rotate(-18)"><rect x="-38" y="-2" width="70" height="12" rx="6" fill="${C.ivory2}"/>
      <rect x="-38" y="-14" width="70" height="10" rx="5" fill="${C.ivory}"/>
      <path d="M-30,-18 Q4,-44 34,-22" fill="none" stroke="${C.gold}" stroke-width="6" stroke-linecap="round"/>
      <circle cx="-30" cy="-16" r="4" fill="${C.gold}"/><rect x="26" y="-10" width="10" height="16" rx="2" fill="${C.muted}"/></g>`,
    bottle: () => `<rect x="-24" y="-12" width="48" height="52" rx="12" fill="${C.gold}" opacity=".9"/>
      <rect x="-14" y="-6" width="10" height="34" rx="5" fill="#fff" opacity=".25"/>
      <rect x="-8" y="-26" width="16" height="14" fill="${C.ivory2}"/><rect x="-12" y="-38" width="24" height="12" rx="3" fill="${C.ivory}"/>
      <path d="M22,-34 l4,-4 M28,-28 l6,-1 M24,-44 l1,-6" stroke="${C.ivory}" stroke-width="3" stroke-linecap="round"/>`,
    scissors: () => `<circle cx="-14" cy="26" r="10" fill="none" stroke="${C.gold}" stroke-width="6"/><circle cx="14" cy="26" r="10" fill="none" stroke="${C.gold}" stroke-width="6"/>
      <path d="M-8,16 L16,-40 M8,16 L-16,-40" stroke="${C.ivory}" stroke-width="7" stroke-linecap="round"/><circle cx="0" cy="-3" r="3.5" fill="${C.muted}"/>`,
    rings: () => `<circle cx="-12" cy="6" r="20" fill="none" stroke="${C.gold}" stroke-width="6"/><circle cx="12" cy="6" r="20" fill="none" stroke="${C.gold}" stroke-width="6"/>
      <path d="M-12,-24 l6,8 h-12 z" fill="${C.ivory}"/>`,
    cap: () => `<path d="M-36,14 A36,34 0 0 1 36,14 Z" fill="${C.ivory2}"/><rect x="-40" y="12" width="80" height="10" rx="5" fill="${C.ivory}"/>
      <path d="M-20,-8 Q0,-18 20,-8 M-28,4 Q0,-6 28,4" fill="none" stroke="${C.muted}" stroke-width="2"/>`,
    razor: () => `<rect x="-30" y="-36" width="60" height="16" rx="4" fill="${C.ivory}"/><rect x="-26" y="-22" width="52" height="4" fill="${C.muted}"/>
      <rect x="-6" y="-18" width="12" height="58" rx="6" fill="${C.gold}"/>${[0, 10, 20, 30].map((y) => `<rect x="-6" y="${y - 4}" width="12" height="3" fill="rgba(0,0,0,.25)"/>`).join('')}`,
    strand: () => `<path d="M-8,-44 C-22,-20 10,-6 -6,14 C-16,26 -2,34 -6,40" fill="none" stroke="#3b2a20" stroke-width="12" stroke-linecap="round"/>
      <path d="M-8,-44 C-22,-20 10,-6 -6,14 C-16,26 -2,34 -6,40" fill="none" stroke="#6b4a36" stroke-width="5" stroke-linecap="round"/>
      <path d="M-30,30 H26" stroke="${C.gold}" stroke-width="3" stroke-dasharray="6 5"/><path d="M18,30 v12 M18,42 h-6 M18,30 h-6" stroke="${C.ivory}" stroke-width="3" fill="none"/>`,
  };
  const cross = () => `<circle r="42" fill="none" stroke="${C.red}" stroke-width="6"/><path d="M-30,30 L30,-30" stroke="${C.red}" stroke-width="6" stroke-linecap="round"/>`;

  /* tile: rounded card with an icon and one or two label lines */
  function tile(x, y, w, h, icon, label, { crossed = false, scale = 1 } = {}) {
    const lines = Array.isArray(label) ? label : [label];
    const short = h < 200;
    const iy = h * (short ? 0.34 : 0.4);
    const ly = h - 18 - (lines.length - 1) * 22;
    return `<g transform="translate(${x},${y})"><rect width="${w}" height="${h}" rx="18" fill="${C.raise}" stroke="${C.line}"/>
      <g transform="translate(${w / 2},${iy}) scale(${short ? scale * 0.86 : scale * 1.15})">${icon}${crossed ? cross() : ''}</g>
      ${lines.map((l, i) => text(w / 2, ly + i * 22, l, i ? 16 : 21, i ? C.ivory2 : C.ivory, i ? 400 : 700)).join('')}</g>`;
  }

  /* faceless figures, feet at (0,0) */
  const man = (x, y, s = 1, extra = '') => `<g transform="translate(${x},${y}) scale(${s})">${shadow(0, 0, 30)}
    <rect x="-17" y="-16" width="11" height="14" rx="4" fill="${C.skin}"/><rect x="6" y="-16" width="11" height="14" rx="4" fill="${C.skin}"/>
    <path d="M-20,-1 h16 M4,-1 h16" stroke="#5a3b28" stroke-width="5" stroke-linecap="round"/>
    <path d="M-30,-80 H30 L34,-16 H-34 Z" fill="${C.ivory2}"/><path d="M-30,-60 L30,-42" stroke="${C.muted}" stroke-width="1.5" opacity=".6"/>
    <path d="M-28,-124 Q0,-132 28,-124 L38,-72 Q0,-62 -38,-72 Z" fill="${C.ivory}"/>
    <path d="M-12,-120 L24,-74" stroke="${C.muted}" stroke-width="1.5" opacity=".5"/>
    <circle cx="-38" cy="-70" r="7" fill="${C.skin}"/><circle cx="38" cy="-70" r="7" fill="${C.skin}"/>
    <rect x="-6" y="-134" width="12" height="10" fill="${C.skin}"/><circle cx="0" cy="-146" r="16" fill="${C.skin}"/>${extra}</g>`;
  const woman = (x, y, s = 1, extra = '') => `<g transform="translate(${x},${y}) scale(${s})">${shadow(0, 0, 32)}
    <path d="M-12,-4 h8 M4,-4 h8" stroke="#3a2a20" stroke-width="6" stroke-linecap="round"/>
    <path d="M-22,-122 Q0,-130 22,-122 L40,-6 H-40 Z" fill="${C.sand}"/>
    <path d="M-22,-118 L-36,-64 M22,-118 L36,-64" stroke="${C.sand}" stroke-width="16" stroke-linecap="round"/>
    <circle cx="-37" cy="-58" r="6.5" fill="${C.skin}"/><circle cx="37" cy="-58" r="6.5" fill="${C.skin}"/>
    <path d="M-20,-124 Q0,-110 20,-124 L16,-150 Q0,-172 -16,-150 Z" fill="#8e7f69"/>
    <circle cx="0" cy="-146" r="18" fill="#8e7f69"/><ellipse cx="0" cy="-142" rx="10.5" ry="13" fill="${C.skin}"/>${extra}</g>`;
  const kaaba = (x, y, s = 1, glow = false) => `<g transform="translate(${x},${y}) scale(${s})">
    ${glow ? `<ellipse cx="18" cy="-46" rx="110" ry="80" fill="url(#glow)"/>` : ''}
    <ellipse cx="18" cy="4" rx="76" ry="9" fill="rgba(0,0,0,.4)"/>
    <path d="M-44,-100 L-8,-118 L82,-118 L46,-100 Z" fill="#2a2a2e"/>
    <path d="M46,-100 L82,-118 L82,-18 L46,0 Z" fill="#17171a"/>
    <rect x="-44" y="-100" width="90" height="100" fill="${C.dark}"/>
    <rect x="-44" y="-80" width="90" height="9" fill="${C.gold}"/><path d="M46,-80 L82,-98 L82,-89 L46,-71 Z" fill="#a8843f"/>
    <rect x="22" y="-46" width="16" height="34" fill="${C.gold}"/></g>`;
  const bubble = (x, y, w, s, size = 22) => `<g transform="translate(${x},${y})"><rect x="${-w / 2}" y="-26" width="${w}" height="44" rx="22" fill="${C.raise}" stroke="rgba(214,173,94,.6)"/>
    <path d="M-10,18 L-20,32 L4,18 Z" fill="${C.raise}"/>${arabic(0, 5, s, size)}</g>`;
  const defs = `<defs><radialGradient id="glow"><stop offset="0" stop-color="#d6ad5e" stop-opacity=".45"/><stop offset="1" stop-color="#d6ad5e" stop-opacity="0"/></radialGradient></defs>`;

  return {
    prep: (L) => svg(tile(12, 30, 144, 260, I.shower(), L.bath) + tile(168, 30, 144, 260, I.clipper(), L.nails) + tile(324, 30, 144, 260, I.bottle(), L.perfume)),
    clothes: (L) => svg(`<rect x="12" y="20" width="456" height="290" rx="22" fill="${C.raise}" stroke="${C.line}"/>
      <path d="M240,40 V290" stroke="${C.line}" stroke-width="2"/>
      ${man(126, 262, 1.18)}${woman(354, 262, 1.18)}
      ${text(126, 298, L.men, 19, C.gold)}${text(354, 298, L.women, 19, C.gold)}`),
    niyyah: (L) => svg(`${defs}<rect x="12" y="20" width="456" height="290" rx="22" fill="${C.raise}" stroke="${C.line}"/>
      <path d="M24,250 H456" stroke="${C.muted}" stroke-width="2"/>
      <path d="M40,150 Q120,128 180,118" fill="none" stroke="${C.ivory2}" stroke-width="3" stroke-dasharray="2 9" stroke-linecap="round"/>
      <g transform="translate(205,112) rotate(-8)"><ellipse rx="40" ry="8" fill="${C.ivory}"/><path d="M-6,-2 L-22,-30 H-12 L10,-2 Z M-6,2 L-22,30 H-12 L10,2 Z" fill="${C.ivory2}"/>
        <path d="M-36,-2 L-44,-18 H-38 L-28,-2 Z" fill="${C.ivory2}"/><circle cx="30" cy="-2" r="2" fill="${C.muted}"/></g>
      <path d="M300,62 V250" stroke="${C.gold}" stroke-width="4" stroke-dasharray="10 8"/>
      <rect x="248" y="34" width="104" height="30" rx="15" fill="${C.gold}"/>${text(300, 55, L.miqat, 17, '#1a1408')}
      ${kaaba(408, 250, 0.42, true)}
      ${bubble(150, 196, 220, 'لَبَّيْكَ اللَّهُمَّ عُمْرَةً')}`),
    ishtirat: () => svg(`<rect x="12" y="20" width="456" height="290" rx="22" fill="${C.raise}" stroke="${C.line}"/>
      ${man(150, 286, 1.1, `<path d="M44,-70 L54,0" stroke="#7a5a3a" stroke-width="5" stroke-linecap="round"/><path d="M38,-72 h10" stroke="#7a5a3a" stroke-width="5" stroke-linecap="round"/>`)}
      <g transform="translate(330,170)"><path d="M0,-58 L46,-40 V2 C46,34 22,52 0,62 C-22,52 -46,34 -46,2 V-40 Z" fill="rgba(95,211,138,.16)" stroke="${C.green}" stroke-width="4"/>
        <path d="M0,24 C-26,6 -24,-18 -10,-20 C-4,-21 0,-16 0,-12 C0,-16 4,-21 10,-20 C24,-18 26,6 0,24 Z" fill="${C.green}"/></g>
      ${bubble(240, 60, 300, 'اللَّهُمَّ مَحِلِّي حَيْثُ حَبَسْتَنِي', 21)}`),
    talbiyah: (L) => svg(`${defs}<rect x="12" y="20" width="456" height="290" rx="22" fill="${C.raise}" stroke="${C.line}"/>
      <path d="M24,268 H456" stroke="${C.muted}" stroke-width="2"/>
      <path d="M150,276 Q260,252 360,262" fill="none" stroke="${C.gold}" stroke-width="3" stroke-dasharray="2 10" stroke-linecap="round"/>
      ${man(84, 268, 0.95)}${woman(176, 268, 0.82)}
      ${[0, 1, 2].map((i) => `<path d="M${110 + i * 9},${118 - i * 2} q${10 + i * 6},${16} 0,${32 + i * 4}" fill="none" stroke="${C.gold}" stroke-width="3" stroke-linecap="round" opacity="${1 - i * .25}"/>`).join('')}
      <path d="M196,${144} q8,12 0,24" fill="none" stroke="${C.gold}" stroke-width="3" stroke-linecap="round" opacity=".5"/>
      ${text(84, 298, L.aloud, 15, C.ivory2, 400)}${text(176, 298, L.softly, 15, C.ivory2, 400)}
      ${kaaba(392, 262, 0.62, true)}
      ${bubble(246, 66, 260, 'لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ')}`),
    avoid: (L) => svg(tile(12, 12, 222, 142, I.bottle(), L.avoid_perfume, { crossed: true, scale: .72 }) +
      tile(246, 12, 222, 142, I.scissors(), L.avoid_hair, { crossed: true, scale: .72 }) +
      tile(12, 166, 222, 142, I.rings(), L.avoid_marital, { crossed: true, scale: .72 }) +
      tile(246, 166, 222, 142, I.cap(), L.avoid_head, { crossed: true, scale: .72 })),
    halq: (L) => svg(tile(12, 30, 144, 260, I.razor(), L.shave) + tile(168, 30, 144, 260, I.scissors(), L.shorten) + tile(324, 30, 144, 260, I.strand(), L.women_cut)),
    complete: (L) => svg(`${defs}<rect x="12" y="20" width="456" height="290" rx="22" fill="${C.raise}" stroke="${C.line}"/>
      ${kaaba(222, 222, 1.2, true)}
      <g transform="translate(352,92)"><circle r="26" fill="${C.green}"/><path d="M-12,0 L-3,10 L14,-10" fill="none" stroke="#07160d" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>
      ${text(240, 280, L.accept, 21, C.gold)}`),
    setLang(ar) { AR = ar; },
  };
})();

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const R = require('../web/runtime.js');
const app = fs.readFileSync('web/app.html', 'utf8'), explore = fs.readFileSync('web/explore.html', 'utf8');
function section(source, from, to) { return source.slice(source.indexOf(from), source.indexOf(to, source.indexOf(from))); }

test('scene preparation preserves exported cloth normal and roughness maps', () => {
  const normal = {}, roughness = {}, cloth = { name: 'X_Kiswa', userData: { umrahRole: 'cloth' }, normalMap: normal, roughnessMap: roughness, roughness: .75 };
  const glass = { name: 'X_Maqam clear glass', userData: { umrahRole: 'glass' } };
  const meshes = [cloth, glass].map(material => ({ isMesh: true, material }));
  const c = vm.createContext({ worlds: {}, renderer: { capabilities: { getMaxAnisotropy: () => 8 } } });
  vm.runInContext(section(explore, 'function prepWorld(', '\n/* ======================================================================= crowd'), c);
  c.prepWorld({ scene: { traverse(fn) { meshes.forEach(fn); } } }, 'haram');
  assert.equal(meshes[0].material, cloth); assert.equal(cloth.normalMap, normal); assert.equal(cloth.roughnessMap, roughness);
  assert.equal(meshes[1].castShadow, false); assert.equal(glass.depthWrite, false);
});

test('real guided navigation ignores an older load finishing after the latest selection', async () => {
  const pending = {}, timers = new Map(); let id = 0;
  const context = vm.createContext({
    TourRuntime: R, state: { s: 0, k: 0, playing: true }, STATIONS: [0, 1, 2].map(i => ({ pano: String(i), steps: [{}] })),
    curPano: '0', tex: [1], tween: null, glAvailable: true, camera: null, runs: 0,
    navigation: R.createScope(), playback: R.createScope(fn => { timers.set(++id, fn); return id; }, id => timers.delete(id)),
    stopSpeech() { context.playback.next(); }, saveLesson() {}, render() {}, buildHotspots() {},
    $() { return { classList: { toggle() {} } }; }, panoFor: s => s.pano, stepTarget: s => s.pano,
    lookAt: target => { context.camera = target; }, showPano: name => new Promise(resolve => { pending[name] = resolve; }),
    wantsHD: () => false, runStep: () => context.runs++,
  });
  vm.runInContext(section(app, 'async function go(', '\nfunction advance('), context);
  const old = context.go(1, 0), current = context.go(2, 0);
  pending['2'](); await current; pending['1'](); await old;
  for (const fn of timers.values()) fn();
  assert.equal(context.state.s, 2); assert.equal(context.camera, '2'); assert.equal(context.runs, 1);
});

function simulation() {
  const context = vm.createContext({
    Math, Set, game: { mi: 2, tawaf: R.freshTawaf(), sai: R.freshSai() }, player: { x: 0, y: 0 }, input: { guide: true, ff: false },
    START_ANG: Math.PI / 4, HIJR: { cx: -5.85, rin: 8.4 / 9.1 }, MASA: { green: [150, 205] },
    simT: 0, TAWAF_SCRIPT: {}, SAI_SCRIPT: [], T: { circuit: n => n, length: n => n },
    warned: 0, advanced: 0, finished: 0, saves: 0, cues: [],
    hijrState: () => ({ inArc: false, rho: 2 }), setProg() {}, cue() {}, showWarn() { context.warned++; },
    banner() {}, chime() {}, updateHud() {}, stopAudio() {}, say(a) { context.cues.push(...a); },
    saveExplore() { context.saves++; }, nextMission() { context.advanced++; }, finish() { context.finished++; },
    $() { return { hidden: true }; },
  });
  vm.runInContext(explore.match(/^const wrapA = .*$/m)[0] + '\n' + section(explore, 'function tawafTick(', '\nfunction cue('), context);
  return context;
}
function point(ctx, angle, radius = 13) {
  ctx.player.x = Math.cos(angle) * radius; ctx.player.y = Math.sin(angle) * radius;
  ctx.simT += .05; ctx.tawafTick(.05);
}
test('actual Tawaf logic completes exactly seven counter-clockwise circuits', () => {
  const c = simulation();
  for (let i = 0; i <= 1401 && !c.advanced; i++) point(c, Math.PI / 4 + i * 2 * Math.PI / 200);
  assert.equal(c.game.tawaf.count, 7); assert.equal(c.advanced, 1); assert.equal(c.saves, 7);
});
test('clockwise walking and repeated start-line jitter cannot create circuits', () => {
  const c = simulation();
  for (let i = 0; i < 1000; i++) point(c, Math.PI / 4 - i * .02);
  assert.equal(c.game.tawaf.count, 0); assert.ok(c.warned > 0);
  for (let i = 0; i < 1000; i++) point(c, Math.PI / 4 + (i % 2 ? .01 : -.01));
  assert.equal(c.game.tawaf.count, 0);
});
test('entering the Hijr penalizes a circuit once, then seven valid circuits are still required', () => {
  const c = simulation();
  let inside = false;
  c.hijrState = () => ({ inArc: inside, rho: inside ? .5 : 2 });
  for (let i = 0; i <= 1602 && !c.advanced; i++) {
    inside = i > 85 && i < 105; point(c, Math.PI / 4 + i * 2 * Math.PI / 200);
  }
  assert.equal(c.game.tawaf.penalty, 1); assert.equal(c.game.tawaf.count, 7); assert.equal(c.advanced, 1);
});
test('resuming partway through Tawaf preserves completed circuits and remaining distance', () => {
  const c = simulation(), angle = Math.PI / 4 + .4 * 2 * Math.PI;
  Object.assign(c.game.tawaf, { count: 5, acc: 5.4 * 2 * Math.PI, last: Math.atan2(Math.sin(angle), Math.cos(angle)) });
  const raw = R.exploreSnapshot(c.game, { x: 13 * Math.cos(angle), y: 13 * Math.sin(angle), yaw: 0, pitch: 0, z: 0 }, ['enter','stone','tawaf','maqam','zamzam','masa','safa','sai'].map(id => ({id})), 120);
  c.game.tawaf = R.exploreState(JSON.parse(JSON.stringify(raw)), ['enter','stone','tawaf','maqam','zamzam','masa','safa','sai'].map(id => ({id}))).tawaf;
  for (let i = 1; i <= 321 && !c.advanced; i++) point(c, angle + i * 2 * Math.PI / 200);
  assert.equal(c.game.tawaf.count, 7); assert.equal(c.advanced, 1);
});
test('actual Sa’i logic counts alternating endpoints and finishes at Marwah on length seven', () => {
  const c = simulation();
  for (let i = 0; i < 7; i++) {
    c.player.x = i % 2 ? 0 : 400; c.saiTick();
    assert.equal(c.game.sai.count, i + 1);
    for (let n = 0; n < 10; n++) c.saiTick();
    assert.equal(c.game.sai.count, i + 1);
  }
  assert.equal(c.game.sai.last, 'marwa'); assert.equal(c.finished, 1);
});
test('resumed Sa’i reaches the correct next endpoint without resetting length count', () => {
  const c = simulation(); Object.assign(c.game.sai, { count: 5, last: 'marwa' });
  c.player.x = 200; c.saiTick(); assert.equal(c.game.sai.count, 5);
  c.player.x = 0; c.saiTick(); assert.equal(c.game.sai.count, 6);
  c.player.x = 400; c.saiTick(); assert.equal(c.game.sai.count, 7); assert.equal(c.finished, 1);
});

test('all inline player scripts parse after generated content is separated', () => {
  for (const html of [app, explore]) for (const [, attrs, body] of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (!attrs.includes('importmap')) assert.doesNotThrow(() => new vm.Script(body.replace(/^import .*;\n/gm, '')));
  }
});

test('failed guided audio exposes retry without silently advancing the lesson', async () => {
  let failed = 0, completed = 0;
  const context = vm.createContext({
    runId: 1, state: { playing: true }, AUDIO: ['rabbana'],
    player: { play: () => Promise.reject(Error('missing audio')) },
    setListen() {}, retryStepAudio() {},
    audioFailed(retry) { failed++; context.runId++; assert.equal(retry, context.retryStepAudio); },
  });
  vm.runInContext(section(app, 'function playDua(', '\n/* Speak one line:'), context);
  context.playDua('rabbana', () => completed++);
  await Promise.resolve(); await Promise.resolve();
  assert.equal(failed, 1); assert.equal(completed, 0);
  context.playFile('missing.mp3', () => completed++);
  await Promise.resolve(); await Promise.resolve();
  assert.equal(failed, 2); assert.equal(completed, 0);
});

test('a rejected audio request from a previous lesson cannot interrupt the current lesson', async () => {
  let reject, failed = 0;
  const context = vm.createContext({
    runId: 1, state: { playing: true }, AUDIO: [],
    player: { play: () => new Promise((_, r) => { reject = r; }) },
    audioFailed() { failed++; }, retryStepAudio() {},
  });
  vm.runInContext(section(app, 'function playFile(', '\n/* Speak one line:'), context);
  context.playFile('old.mp3', () => assert.fail('stale completion'));
  context.runId++; reject(Error('aborted after navigation'));
  await Promise.resolve(); await Promise.resolve();
  assert.equal(failed, 0);
});

test('3D boot loads only the required world, including sessions resumed in the Mas’a', async () => {
  const content = require('../web/tour.json');
  for (const saved of [null, { mi: 6 }]) {
    const requested = [], elements = new Map();
    const context = vm.createContext({
      saved, M: content.practice.missions, LANG: 'en', T: { loading: 'haram', ready: 'ready', resume: () => 'resume' }, EXTRA: { masa: 'masa' },
      $: id => { if (!elements.has(id)) elements.set(id, { style: {} }); return elements.get(id); },
      ensureWorld: async name => { requested.push(name); return {}; }, loadModel: async name => { requested.push(name); return { scene: {} }; },
      skyP: Promise.resolve(), skyTex: null, pilgrimProto: null, envDay: null, envNight: {}, progressKeys: [],
      setWorld() {}, player: {}, spawnFor: mi => ({ mi }), booted: false, loopStarted: false, requestAnimationFrame() {}, frame() {},
      loadFailure() { assert.fail('boot should succeed'); },
    });
    vm.runInContext(section(explore, 'async function boot()', '\nboot();'), context);
    await context.boot();
    assert.deepEqual(requested, [saved ? 'masa' : 'haram', 'pilgrims']);
    assert.equal(context.booted, true);
  }
});

test('failed world downloads are removed from the load cache and retry successfully', async () => {
  let attempts = 0;
  const context = vm.createContext({
    worlds: {}, worldLoads: {},
    loadModel: async () => { if (++attempts === 1) throw Error('offline'); return {}; },
    prepWorld: (_, name) => { context.worlds[name] = { loaded: true }; },
  });
  vm.runInContext(section(explore, 'async function ensureWorld(', '\nfunction loadFailure('), context);
  await assert.rejects(context.ensureWorld('masa'), /offline/);
  const [a, b] = await Promise.all([context.ensureWorld('masa'), context.ensureWorld('masa')]);
  assert.equal(attempts, 2); assert.equal(a, b); assert.equal(a.loaded, true);
});

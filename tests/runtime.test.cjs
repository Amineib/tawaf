const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../web/runtime.js');
const content = require('../web/tour.json');
test('unloading a model releases shared GPU resources exactly once', () => {
  const disposed = [], texture = { isTexture: true, dispose() { disposed.push('texture'); } };
  const material = { map: texture, normalMap: texture, dispose() { disposed.push('material'); } };
  const geometry = { dispose() { disposed.push('geometry'); } };
  const nodes = [{ material, geometry }, { material: [material], geometry }, { isInstancedMesh: true, material, geometry, dispose() { disposed.push('instances'); } }];
  R.disposeModel({ traverse(fn) { nodes.forEach(fn); } });
  assert.deepEqual(disposed.sort(), ['geometry', 'instances', 'material', 'texture']);
});
test('Mas’a crowd remains continuous at both end-hall turns and loop closure', () => {
  const masa = { safa: 0, marwa: 400 }, r = 17, length = 384, turn = Math.PI * r;
  for (const boundary of [length, length + turn, 2 * length + turn, 2 * length + 2 * turn]) {
    const a = R.masaCrowdPose(boundary - .01, r, masa), b = R.masaCrowdPose(boundary + .01, r, masa);
    assert.ok(Math.hypot(a.x-b.x, a.y-b.y) <= .02001, 'Crowd must not teleport at an endpoint');
  }
});
test('Mas’a crowd never walks through the Safa or Marwah rock', () => {
  const masa = { safa: 0, marwa: 400 };
  for (const r of [3.4, 8, 12.5, 19.9]) {
    const total = 2 * 384 + 2 * Math.PI * r;
    for (let d = 0; d < total; d += .25) {
      const p = R.masaCrowdPose(d, r, masa);
      for (const cx of [-15, 415]) assert.ok(((p.x - cx) / 9.5) ** 2 + (p.y / 8) ** 2 > 1, `inside rock at x=${p.x.toFixed(1)}, y=${p.y.toFixed(1)}`);
    }
  }
});
const missions = ['enter', 'stone', 'tawaf', 'maqam', 'zamzam', 'masa', 'safa', 'sai'].map(id => ({ id }));

test('lesson save restores a stable station ID, step and both counters', () => {
  const state = { s: 4, k: 2, started: true, counts: { tawaf: 5, sai: 2 } };
  assert.deepEqual(R.guidedState(R.guidedSnapshot(state, content.stations), content.stations), state);
});
test('corrupt and unknown lesson saves reset safely', () => {
  const saved = R.guidedState({ version: 1, station: 'missing', step: -1, counts: { tawaf: 200, sai: '3' } }, content.stations);
  assert.equal(saved.s, 0); assert.equal(saved.k, 0);
  assert.deepEqual(saved.counts, { tawaf: 7, sai: 0 });
  assert.equal(R.guidedState({ version: 999, station: 'start' }, content.stations).s, 0);
});
test('storage failures and invalid JSON do not prevent either player starting', () => {
  const store = R.createStore({ getItem() { throw Error('denied'); }, setItem() { throw Error('full'); } });
  assert.equal(store.get('guided', null), null); assert.doesNotThrow(() => store.set('guided', {}));
  assert.equal(R.createStore({ getItem: () => '{bad' }).get('x', 7), 7);
});
test('3D round trip preserves fractional Tawaf, position, cue history, and elapsed time', () => {
  const tw = R.freshTawaf(); Object.assign(tw, { count: 5, acc: 5.4 * 2 * Math.PI, last: 0.9, penalty: 0 }); tw.fired.add('5:n:start_1');
  const game = { mi: 2, tawaf: tw, sai: R.freshSai() }, player = { x: 12, y: 4, yaw: 1.2, pitch: 0.1, z: 0 };
  const restored = R.exploreState(JSON.parse(JSON.stringify(R.exploreSnapshot(game, player, missions, 250))), missions);
  assert.equal(restored.mi, 2); assert.equal(restored.tawaf.acc, tw.acc); assert.equal(restored.tawaf.count, 5);
  assert.ok(restored.tawaf.fired.has('5:n:start_1')); assert.deepEqual(restored.position, player); assert.equal(restored.elapsed, 250);
});
test('3D round trip preserves Sa’i direction and length progress', () => {
  const game = { mi: 7, tawaf: { ...R.freshTawaf(), count: 7, acc: 14 * Math.PI }, sai: { ...R.freshSai(), count: 3, last: 'marwa', inGreen: true, fired: new Set([0, 1, 2]) } };
  const restored = R.exploreState(R.exploreSnapshot(game, { x: 180, y: -6, z: 0, yaw: 3, pitch: 0 }, missions, 70), missions);
  assert.equal(restored.sai.count, 3); assert.equal(restored.sai.last, 'marwa'); assert.ok(restored.sai.fired.has(2)); assert.equal(restored.position.x, 180);
});
test('resume preserves backward travel and recovers a save at the final circuit boundary', () => {
  const source = { version: 2, mission: 'tawaf', tawaf: { count: 5, acc: 4.9 * 2 * Math.PI } };
  assert.equal(R.exploreState(source, missions).tawaf.acc, source.tawaf.acc);
  source.tawaf.count = 7; source.tawaf.acc = 14 * Math.PI;
  assert.equal(R.exploreState(source, missions).mi, 3);
  assert.equal(R.exploreState({ version: 2, mission: 'sai', sai: { count: 7 } }, missions), null);
});
test('old mission-only saves migrate, unknown versions and unsafe positions do not', () => {
  assert.equal(R.exploreState({ mi: 3 }, missions).mi, 3);
  assert.equal(R.exploreState({ version: 99 }, missions), null);
  assert.equal(R.exploreState({ version: 2, mission: 'missing' }, missions), null);
  const restored = R.exploreState({ version: 2, mission: 'sai', position: { x: 1e99, y: 0, z: 0, yaw: 0, pitch: 0 } }, missions);
  assert.equal(restored.position, null); assert.equal(restored.sai.count, 0);
});
test('generation change cancels delayed autoplay and rejects stale completions', () => {
  const queue = new Map(); let id = 0, calls = 0;
  const scope = R.createScope(fn => { queue.set(++id, fn); return id; }, id => queue.delete(id));
  const old = scope.next(); scope.later(old, () => calls++, 250);
  const current = scope.next(); scope.later(current, () => calls++, 250);
  assert.equal(scope.current(old), false);
  for (const fn of queue.values()) fn();
  assert.equal(calls, 1);
});
test('LRU frees GPU resources while protecting the displayed texture', async () => {
  const disposed = [], cache = R.createResourceCache(2, value => disposed.push(value));
  await cache.get('shown', () => 1); await cache.get('old', () => 2);
  await cache.get('next', () => 3, () => ['shown']);
  assert.deepEqual(disposed, [2]); assert.equal(cache.size, 2);
  assert.equal(await cache.get('shown', () => assert.fail('must reuse')), 1);
  cache.clear(); assert.deepEqual(disposed.sort(), [1, 2, 3]);
});
test('failed texture loads can be retried; clearing in-flight loads frees late resources', async () => {
  const disposed = [], cache = R.createResourceCache(2, value => disposed.push(value));
  await assert.rejects(cache.get('x', () => Promise.reject(Error('offline'))));
  assert.equal(await cache.get('x', () => 1), 1);
  let resolve; const pending = cache.get('y', () => new Promise(r => resolve = r));
  await Promise.resolve(); cache.clear(); resolve(2);
  await assert.rejects(pending, /cancelled/); assert.deepEqual(disposed, [1, 2]);
});

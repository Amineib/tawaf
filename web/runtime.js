/* Shared, browser-independent state and resource helpers. No storage access at import time. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TourRuntime = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const finite = (n, fallback = 0) => typeof n === 'number' && Number.isFinite(n) ? n : fallback;
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, finite(n, lo)));
  const count = (n) => Math.floor(clamp(n, 0, 7));
  function createStore(storage) {
    return {
      get(key, fallback) { try { const value = storage.getItem('umrah:' + key); return value === null ? fallback : JSON.parse(value); } catch { return fallback; } },
      set(key, value) { try { storage.setItem('umrah:' + key, JSON.stringify(value)); } catch {} },
    };
  }
  function guidedState(raw, stations) {
    raw = raw && raw.version === 1 ? raw : {};
    let s = stations.findIndex((station) => station.id === raw.station);
    if (s < 0) s = 0;
    return { s, k: Math.floor(clamp(raw.step, 0, stations[s].steps.length - 1)), started: raw.started === true,
      counts: { tawaf: count(raw.counts?.tawaf), sai: count(raw.counts?.sai) } };
  }
  function guidedSnapshot(state, stations) {
    return { version: 1, station: stations[state.s].id, step: state.k, started: state.started, counts: { ...state.counts } };
  }
  function freshTawaf() { return { acc: 0, last: null, count: 0, penalty: 0, voided: -1, wrongT: 0, warnAt: -99, fired: new Set() }; }
  function freshSai() { return { count: 0, last: 'safa', fired: new Set(), inGreen: false }; }
  const events = (items) => new Set(Array.isArray(items) ? items.filter((v) => typeof v === 'string' || Number.isInteger(v)).slice(0, 500) : []);
  function exploreState(raw, missions) {
    if (!raw || typeof raw !== 'object') return null;
    // Migrate the original mission-only save without pretending it includes counters or a position.
    if (!raw.version && Number.isInteger(raw.mi) && raw.mi > 0 && raw.mi < missions.length)
      return { mi: raw.mi, tawaf: freshTawaf(), sai: freshSai(), position: null, elapsed: 0 };
    if (raw.version !== 2) return null;
    let mi = missions.findIndex((m) => m.id === raw.mission);
    if (mi < 0) return null;
    const tw = freshTawaf(), sai = freshSai(), source = raw.tawaf || {};
    tw.penalty = Math.floor(clamp(source.penalty, 0, 1000));
    tw.count = count(source.count);
    tw.acc = clamp(source.acc, 0, (tw.count + tw.penalty + 1) * 2 * Math.PI);
    tw.last = typeof source.last === 'number' && Number.isFinite(source.last) ? source.last : null;
    tw.voided = Number.isInteger(source.voided) ? source.voided : -1;
    tw.fired = events(source.fired);
    sai.count = count(raw.sai?.count); sai.last = sai.count % 2 ? 'marwa' : 'safa';
    sai.fired = events(raw.sai?.fired); sai.inGreen = raw.sai?.inGreen === true;
    // A page can close between saving the seventh count and saving the following mission.
    if (missions[mi].id === 'tawaf' && tw.count === 7) mi++;
    if (missions[mi]?.id === 'sai' && sai.count === 7) return null;
    const p = raw.position, masa = mi >= missions.findIndex((m) => m.id === 'safa');
    const position = p && ['x', 'y', 'yaw', 'pitch', 'z'].every((k) => typeof p[k] === 'number' && Number.isFinite(p[k]))
      && p.x >= (masa ? -24 : -65) && p.x <= (masa ? 424 : 65) && Math.abs(p.y) <= (masa ? 21 : 65)
      ? { x: p.x, y: p.y, yaw: p.yaw, pitch: clamp(p.pitch, -1.2, 1.2), z: clamp(p.z, 0, 2) } : null;
    return { mi, tawaf: tw, sai, position, elapsed: clamp(raw.elapsed, 0, 86400) };
  }
  function exploreSnapshot(game, player, missions, elapsed) {
    return { version: 2, mission: missions[game.mi]?.id, elapsed,
      position: { x: player.x, y: player.y, yaw: player.yaw, pitch: player.pitch, z: player.z },
      tawaf: { ...game.tawaf, fired: [...game.tawaf.fired] }, sai: { ...game.sai, fired: [...game.sai.fired] } };
  }
  function createScope(schedule = setTimeout, unschedule = clearTimeout) {
    let generation = 0;
    const timers = new Set();
    return {
      next() { generation++; for (const timer of timers) unschedule(timer); timers.clear(); return generation; },
      current(token) { return token === generation; },
      token() { return generation; },
      later(token, fn, ms) { const timer = schedule(() => { timers.delete(timer); if (token === generation) fn(); }, ms); timers.add(timer); return timer; },
    };
  }
  // LRU eviction calls the supplied GPU cleanup hook. Pending loads count against the budget too.
  function createResourceCache(limit, dispose) {
    const entries = new Map();
    function trim(protectedKeys = []) {
      const protectedSet = new Set(typeof protectedKeys === 'function' ? protectedKeys() : protectedKeys);
      for (const [key, entry] of entries) {
        if (entries.size <= limit) break;
        if (protectedSet.has(key) || !entry.ready) continue;
        entries.delete(key); dispose(entry.value);
      }
    }
    return {
      get(key, load, protectedKeys = []) {
        if (entries.has(key)) { const entry = entries.get(key); entries.delete(key); entries.set(key, entry); return entry.promise; }
        const entry = { ready: false };
        entry.promise = Promise.resolve().then(load).then((value) => {
          if (entries.get(key) !== entry) { dispose(value); throw new Error('Resource load cancelled'); }
          entry.value = value; entry.ready = true;
          trim([...(typeof protectedKeys === 'function' ? protectedKeys() : protectedKeys), key]); return value;
        }, (error) => { if (entries.get(key) === entry) entries.delete(key); throw error; });
        entries.set(key, entry); return entry.promise;
      },
      trim,
      clear() { for (const entry of entries.values()) if (entry.ready) dispose(entry.value); entries.clear(); },
      get size() { return entries.size; },
    };
  }
  // Continuous crowd path: straight lanes joined by rounded end-hall turns.
  function masaCrowdPose(distance, lane, masa) {
    const r = lane, length = masa.marwa - masa.safa - 16, turn = Math.PI * r;
    const total = 2 * length + 2 * turn, d = ((distance % total) + total) % total;
    if (d < length) return { x: masa.safa + 8 + d, y: r, rot: -Math.PI / 2 };
    if (d < length + turn) { const a = (d - length) / r; return { x: masa.marwa - 8 + r * Math.sin(a), y: r * Math.cos(a), rot: Math.atan2(-Math.cos(a), -Math.sin(a)) }; }
    if (d < 2 * length + turn) return { x: masa.marwa - 8 - (d - length - turn), y: -r, rot: Math.PI / 2 };
    const a = (d - 2 * length - turn) / r;
    return { x: masa.safa + 8 - r * Math.sin(a), y: -r * Math.cos(a), rot: Math.atan2(Math.cos(a), Math.sin(a)) };
  }
  function disposeModel(root) {
    const geometries = new Set(), materials = new Set(), textures = new Set();
    root.traverse(o => {
      if (o.geometry) geometries.add(o.geometry);
      for (const m of o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []) materials.add(m);
      if (o.isInstancedMesh) o.dispose(); // instance buffers, separate from shared geometry
      if (o.customDepthMaterial) materials.add(o.customDepthMaterial);
    });
    for (const m of materials) for (const value of Object.values(m)) if (value?.isTexture) textures.add(value);
    for (const t of textures) t.dispose();
    for (const m of materials) m.dispose();
    for (const g of geometries) g.dispose();
  }
  return { createStore, guidedState, guidedSnapshot, exploreState, exploreSnapshot, freshTawaf, freshSai, createScope, createResourceCache, masaCrowdPose, disposeModel };
});

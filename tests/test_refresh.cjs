const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('web/refresh.js', 'utf8');
function harness() {
  const elements = Object.fromEntries(['refresh-dragon', 'refresh-status', 'cancel-refresh', 'dragon-stats'].map(id => [id, {hidden: true, textContent: '', events: {}, addEventListener(type, callback) {this.events[type] = callback;}}]));
  elements['dragon-stats'].textContent = JSON.stringify({updated_at: '2026-11-22T00:00:00Z'});
  const intervals = new Map(), requests = [], navigations = [], replies = [];
  let now = Date.parse('2026-11-22T12:00:00Z'), id = 0;
  const document = {hidden: false, events: {}, getElementById: id => elements[id], addEventListener(type, callback) {this.events[type] = callback;}};
  const location = {href: 'https://example.test/dragon/?old=1', replace: url => navigations.push(url)};
  vm.runInNewContext(source, {document, location, URL, AbortController,
    Date: class extends Date {static now() {return now;}},
    window: {addEventListener() {}},
    setInterval: fn => {intervals.set(++id, fn); return id;}, clearInterval: id => intervals.delete(id),
    setTimeout: () => ++id, clearTimeout() {},
    fetch: async (url, options) => {
      requests.push({url, options});
      const result = replies.shift();
      if (result instanceof Error) throw result;
      return {ok: true, json: async () => result || {version: 1, updated_at: '2026-11-22T00:00:00Z'}};
    }
  });
  const flush = () => new Promise(resolve => setImmediate(resolve));
  return {elements, intervals, requests, navigations, replies, document, flush,
    start: async () => {elements['refresh-dragon'].events.click(); await flush();},
    tick: async () => {for (const fn of [...intervals.values()]) await fn();},
    advance: duration => {now += duration;}};
}

test('owner flow watches public deployment without dispatch credentials or duplicate watchers', async () => {
  const h = harness(); await h.start(); await h.start();
  assert.equal(h.intervals.size, 1);
  assert.match(h.elements['refresh-status'].textContent, /Run workflow on main/);
  assert.equal(h.requests[0].url.pathname, '/dragon/stats.json');
  assert.equal(h.requests[0].options.cache, 'no-store');
  assert.equal(h.requests[0].options.credentials, 'omit');
  assert.equal(h.requests[0].options.headers, undefined);
  assert.equal(h.navigations.length, 0);
});
test('new deployment reloads the whole portrait with a cache-busting timestamp', async () => {
  const h = harness(); await h.start();
  h.replies.push({version: 1, updated_at: '2026-11-22T12:01:00Z'});
  await h.tick();
  assert.equal(h.navigations.length, 1);
  const destination = new URL(h.navigations[0]);
  assert.equal(destination.origin, 'https://example.test');
  assert.equal(destination.searchParams.get('refresh'), String(Date.parse('2026-11-22T12:01:00Z')));
  assert.equal(h.intervals.size, 0);
});
test('network and malformed responses keep the existing dragon and allow retry', async () => {
  const h = harness(); h.replies.push(new Error('offline')); await h.start();
  assert.match(h.elements['refresh-status'].textContent, /unchanged/);
  h.replies.push({version: 1, updated_at: 'invalid'}); await h.tick();
  assert.equal(h.navigations.length, 0);
  assert.equal(h.intervals.size, 1);
  h.elements['cancel-refresh'].events.click();
  assert.equal(h.intervals.size, 0);
  assert.match(h.elements['refresh-status'].textContent, /will continue/);
});
test('hidden pages pause checks and watching expires after twenty minutes', async () => {
  const h = harness(); await h.start();
  h.document.hidden = true; await h.tick();
  assert.equal(h.requests.length, 1);
  h.document.hidden = false; h.advance(20 * 60 * 1000); await h.tick();
  assert.equal(h.intervals.size, 0);
  assert.match(h.elements['refresh-status'].textContent, /No new deployment/);
});

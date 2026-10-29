import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getSpeechRecognitionConstructor, startBanglaDictation } from './m5-voice.ts';
import { nativeRecognitionAvailable, startNativeBanglaDictation } from './m5-voice-native-core.ts';

test('speech recognition detection supports standard and WebKit browser APIs', () => {
  class StandardRecognizer {}
  class WebKitRecognizer {}
  assert.equal(getSpeechRecognitionConstructor({ SpeechRecognition: StandardRecognizer }), StandardRecognizer);
  assert.equal(getSpeechRecognitionConstructor({ webkitSpeechRecognition: WebKitRecognizer }), WebKitRecognizer);
  assert.equal(getSpeechRecognitionConstructor({}), null);
});

test('dictation starts only on explicit call and captures one Bangla transcript', () => {
  let instance;
  class FakeRecognizer {
    constructor() { instance = this; }
    start() { this.started = true; }
    stop() { this.stopped = true; }
  }
  const states = [];
  const transcripts = [];
  const callbacks = {
    onTranscript: value => transcripts.push(value),
    onState: (state, message) => states.push({ state, message }),
  };

  const session = startBanglaDictation(callbacks, { SpeechRecognition: FakeRecognizer });

  assert.equal(instance.started, true);
  assert.equal(instance.lang, 'bn-BD');
  assert.equal(instance.continuous, false);
  assert.deepEqual(states.map(item => item.state), ['listening']);
  instance.onresult({ results: [[{ transcript: 'আগামীকাল বৃষ্টি হবে কি' }]] });
  instance.onend();
  assert.deepEqual(transcripts, ['আগামীকাল বৃষ্টি হবে কি']);
  assert.deepEqual(states.map(item => item.state), ['listening', 'idle']);
  session.stop();
});

test('unsupported or denied microphone use leaves tap-to-type as an explicit fallback', () => {
  const states = [];
  const callbacks = { onTranscript() {}, onState: state => states.push(state) };
  assert.equal(startBanglaDictation(callbacks, {}), null);
  assert.deepEqual(states, ['unavailable']);

  class DeniedRecognizer {
    start() { this.onerror({ error: 'not-allowed' }); }
    stop() {}
  }
  const deniedStates = [];
  assert.equal(startBanglaDictation({ ...callbacks, onState: (state, message) => deniedStates.push({ state, message }) }, {
    SpeechRecognition: DeniedRecognizer,
  }), null);
  assert.equal(deniedStates.at(-1).state, 'unavailable');
  assert.match(deniedStates.at(-1).message, /type your question/);
});

test('recognition stops safely when the browser start operation throws', () => {
  class FailingRecognizer { start() { throw new Error('permission is required'); } stop() {} }
  const states = [];
  const session = startBanglaDictation({ onTranscript() {}, onState: (state, message) => states.push({ state, message }) }, {
    SpeechRecognition: FailingRecognizer,
  });
  assert.equal(session, null);
  assert.equal(states.at(-1).state, 'error');
  assert.match(states.at(-1).message, /permission/);
});

function nativeModule(overrides = {}) {
  const listeners = new Map();
  return {
    listeners,
    options: null,
    startCount: 0,
    stopCount: 0,
    abortCount: 0,
    requestCount: 0,
    isRecognitionAvailable: () => true,
    supportsOnDeviceRecognition: () => false,
    getSupportedLocales: async () => ({ installedLocales: [] }),
    requestMicrophonePermissionsAsync: async () => ({ granted: true }),
    requestPermissionsAsync: async () => ({ granted: true }),
    addListener(event, listener) {
      const entries = listeners.get(event) ?? new Set();
      entries.add(listener);
      listeners.set(event, entries);
      return { remove: () => entries.delete(listener) };
    },
    start(options) { this.startCount += 1; this.options = options; },
    stop() { this.stopCount += 1; },
    abort() { this.abortCount += 1; },
    emit(event, value) { for (const listener of listeners.get(event) ?? []) listener(value); },
    ...overrides,
  };
}

const flushNativeEvents = () => new Promise(resolve => setTimeout(resolve, 0));

test('native dictation uses installed Bangla on-device recognition and removes listeners after end', async () => {
  let localeOptions;
  const module = nativeModule({
    supportsOnDeviceRecognition: () => true,
    getSupportedLocales: async options => {
      localeOptions = options;
      return { installedLocales: ['bn-BD'] };
    },
    requestMicrophonePermissionsAsync: async () => ({ granted: true }),
    requestPermissionsAsync: async () => { throw new Error('network permission path should not be used'); },
  });
  const states = [];
  const transcripts = [];
  const session = startNativeBanglaDictation(module, {
    onTranscript: value => transcripts.push(value),
    onState: state => states.push(state),
  });

  await flushNativeEvents();
  assert.equal(module.startCount, 1);
  assert.deepEqual(localeOptions, {});
  assert.equal(module.options.lang, 'bn-BD');
  assert.equal(module.options.requiresOnDeviceRecognition, true);
  assert.deepEqual(states, ['listening']);
  module.emit('result', { results: [{ transcript: 'আগামীকাল বৃষ্টি হবে' }] });
  module.emit('end');
  assert.deepEqual(transcripts, ['আগামীকাল বৃষ্টি হবে']);
  assert.deepEqual(states, ['listening', 'idle']);
  assert.equal(module.listeners.get('end').size, 0);
  session.cancel();
  assert.equal(module.abortCount, 0);
});

test('native dictation discloses network-capable recognition through permission request and has a tap fallback', async () => {
  const module = nativeModule({
    supportsOnDeviceRecognition: () => true,
    getSupportedLocales: async () => ({ installedLocales: ['en-US'] }),
    requestPermissionsAsync: async () => ({ granted: false }),
  });
  const states = [];
  assert.equal(nativeRecognitionAvailable(module), true);
  const session = startNativeBanglaDictation(module, {
    onTranscript() {},
    onState: (state, message) => states.push({ state, message }),
  });
  await flushNativeEvents();

  assert.equal(module.startCount, 0);
  assert.equal(states.at(-1).state, 'unavailable');
  assert.match(states.at(-1).message, /type your question/);
  session.cancel();
});

test('native interruption aborts without retaining or returning a transcript', async () => {
  const module = nativeModule();
  const states = [];
  const transcripts = [];
  const session = startNativeBanglaDictation(module, {
    onTranscript: value => transcripts.push(value),
    onState: state => states.push(state),
  });
  await flushNativeEvents();
  session.cancel();
  module.emit('result', { results: [{ transcript: 'must not be appended' }] });
  module.emit('end');

  assert.equal(module.abortCount, 1);
  assert.deepEqual(transcripts, []);
  assert.deepEqual(states, ['listening', 'idle']);
});

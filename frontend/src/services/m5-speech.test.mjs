import assert from 'node:assert/strict';
import { test } from 'node:test';
import { M5SpeechAdapter } from './m5-speech-core.ts';

function fakeSpeech(voices, maxSpeechInputLength = 3000) {
  const calls = [];
  let activeOptions;
  return {
    calls,
    module: {
      maxSpeechInputLength,
      async getAvailableVoicesAsync() { return voices; },
      speak(text, options) { calls.push({ text, options }); activeOptions = options; },
      async stop() { activeOptions?.onStopped(); },
    },
  };
}

test('speech uses the device Bengali voice and resolves when spoken text completes', async () => {
  const speech = fakeSpeech([
    { identifier: 'english-voice', language: 'en-US' },
    { identifier: 'bangla-voice', language: 'bn-BD' },
  ]);
  const adapter = new M5SpeechAdapter(speech.module);
  const result = adapter.speak('আগামীকাল জমি দেখুন।', 'bn');
  await new Promise(resolve => setImmediate(resolve));

  assert.equal(speech.calls[0].options.voice, 'bangla-voice');
  speech.calls[0].options.onDone();
  assert.equal(await result, 'available');
});

test('speech never reads Bengali text with an unrelated English voice', async () => {
  const speech = fakeSpeech([{ identifier: 'english-voice', language: 'en-US' }]);
  const adapter = new M5SpeechAdapter(speech.module);

  assert.equal(await adapter.speak('ফসল দেখুন।', 'bn'), 'unavailable');
  assert.equal(speech.calls.length, 0);
});

test('text over the device limit and voice lookup failures fail safely', async () => {
  const speech = fakeSpeech([{ identifier: 'bangla-voice', language: 'bn-BD' }], 8);
  const adapter = new M5SpeechAdapter(speech.module);
  assert.equal(await adapter.speak('এই লেখা বেশি বড়', 'bn'), 'unavailable');

  const failingAdapter = new M5SpeechAdapter({
    ...speech.module,
    async getAvailableVoicesAsync() { throw new Error('voice service unavailable'); },
  });
  assert.equal(await failingAdapter.speak('ছোট লেখা', 'bn'), 'unavailable');
});

test('stopping playback resolves the request as stopped instead of successful', async () => {
  const speech = fakeSpeech([{ identifier: 'bangla-voice', language: 'bn-BD' }]);
  const adapter = new M5SpeechAdapter(speech.module);
  const result = adapter.speak('পড়ে শোনান।', 'bn');
  await new Promise(resolve => setImmediate(resolve));

  await adapter.stop();

  assert.equal(await result, 'unavailable');
});

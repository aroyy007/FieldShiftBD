import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getChallengeNamespaceLabel } from './i18n.ts';
import { challengeNavigationMounts } from './navigation.ts';
import {
  DisabledCache,
  DisabledOutbox,
  DisabledSpeech,
  DeniedConsent,
  FoundationUnavailableError,
  TapConsentAdapter,
} from './runtime.ts';

test('module strings are registered in English and Bangla', () => {
  assert.equal(getChallengeNamespaceLabel('m2', 'en'), 'Crop advisor');
  assert.equal(getChallengeNamespaceLabel('m2', 'bn'), 'ফসল পরামর্শ');
});

test('shared navigation mounts point at the existing Expo Router screens', () => {
  assert.equal(challengeNavigationMounts.farmlandList, '/farmlands');
  assert.equal(challengeNavigationMounts.cropHealth, '/farmlands/[id]/crop-health');
});

test('disabled cache and outbox fail closed instead of acknowledging writes', async () => {
  await assert.rejects(new DisabledCache().write('key', 'value'), FoundationUnavailableError);
  await assert.rejects(new DisabledOutbox().enqueue({ id: 'action-1' }), FoundationUnavailableError);
  await assert.rejects(new DisabledOutbox().listPending(), FoundationUnavailableError);
});

test('denied consent and disabled speech never imply a successful side effect', async () => {
  assert.equal(await new DeniedConsent().request('speech_audio_transcription'), 'denied');
  const speech = new DisabledSpeech();
  assert.equal(await speech.speak('test', 'bn'), 'unavailable');
  assert.equal(speech.availability, 'unavailable');
});

test('tap consent records only the explicit UI choice', async () => {
  assert.equal(await new TapConsentAdapter(async () => true).request('offline_storage'), 'granted');
  assert.equal(await new TapConsentAdapter(async () => false).request('offline_storage'), 'denied');
});

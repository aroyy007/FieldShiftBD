import { ExpoSpeechRecognitionModule } from 'expo-speech-recognition';
import type { DictationCallbacks, DictationState } from './m5-voice';
import {
  nativeRecognitionAvailable,
  startNativeBanglaDictation,
  type NativeSpeechRecognitionPort,
} from './m5-voice-native-core';

const nativeSpeech = ExpoSpeechRecognitionModule as unknown as NativeSpeechRecognitionPort;

export type { DictationState };

export function isBanglaDictationAvailable(): boolean {
  return nativeRecognitionAvailable(nativeSpeech);
}

export function startBanglaDictation(callbacks: DictationCallbacks) {
  return startNativeBanglaDictation(nativeSpeech, callbacks);
}

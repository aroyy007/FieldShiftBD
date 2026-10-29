import * as ExpoSpeech from 'expo-speech';
import { M5SpeechAdapter, type SpeechModule } from './m5-speech-core';

export { M5SpeechAdapter } from './m5-speech-core';

export const m5Speech = new M5SpeechAdapter(ExpoSpeech as SpeechModule);

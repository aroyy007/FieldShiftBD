import type { Availability, SpeechPort } from '../modules/shared/ports';

export type Voice = { identifier: string; language: string };
export type SpeechModule = {
  maxSpeechInputLength: number;
  getAvailableVoicesAsync: () => Promise<Voice[]>;
  speak: (text: string, options: {
    language: string;
    voice: string;
    rate: number;
    onDone: () => void;
    onStopped: () => void;
    onError: () => void;
  }) => void;
  stop: () => Promise<void>;
};

export class M5SpeechAdapter implements SpeechPort {
  readonly availability: Availability = 'available';
  private readonly speech: SpeechModule;

  constructor(speech: SpeechModule) {
    this.speech = speech;
  }

  async speak(text: string, language: 'bn' | 'en'): Promise<Availability> {
    const content = text.trim();
    if (!content || content.length > this.speech.maxSpeechInputLength) return 'unavailable';

    let voice: Voice | undefined;
    try {
      const voices = await this.speech.getAvailableVoicesAsync();
      voice = voices.find(item => item.language.toLowerCase() === language)
        ?? voices.find(item => item.language.toLowerCase().startsWith(`${language}-`));
    } catch {
      return 'unavailable';
    }
    if (!voice) return 'unavailable';

    return new Promise(resolve => {
      let settled = false;
      const finish = (result: Availability) => {
        if (settled) return;
        settled = true;
        resolve(result);
      };
      try {
        this.speech.speak(content, {
          language: voice.language,
          voice: voice.identifier,
          rate: 0.93,
          onDone: () => finish('available'),
          onStopped: () => finish('unavailable'),
          onError: () => finish('unavailable'),
        });
      } catch {
        finish('unavailable');
      }
    });
  }

  async stop(): Promise<void> {
    await this.speech.stop();
  }
}

export type DictationState = 'idle' | 'listening' | 'error' | 'unavailable';
export type DictationSession = { stop: () => void; cancel?: () => void };

export type RecognitionResult = {
  results: ArrayLike<ArrayLike<{ transcript?: string }>>;
};

export type RecognitionError = { error?: string };

export interface BrowserSpeechRecognizer {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: RecognitionResult) => void) | null;
  onerror: ((event: RecognitionError) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort?(): void;
}

export type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognizer;

type RecognitionScope = {
  SpeechRecognition?: BrowserSpeechRecognitionConstructor;
  webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
};

export type DictationCallbacks = {
  onTranscript: (transcript: string) => void;
  onState: (state: DictationState, message?: string) => void;
};

export function getSpeechRecognitionConstructor(
  scope: RecognitionScope = globalThis as RecognitionScope,
): BrowserSpeechRecognitionConstructor | null {
  return scope.SpeechRecognition ?? scope.webkitSpeechRecognition ?? null;
}

export function isBanglaDictationAvailable(scope: RecognitionScope = globalThis as RecognitionScope): boolean {
  return getSpeechRecognitionConstructor(scope) !== null;
}

export function startBanglaDictation(
  callbacks: DictationCallbacks,
  scope: RecognitionScope = globalThis as RecognitionScope,
): DictationSession | null {
  const Constructor = getSpeechRecognitionConstructor(scope);
  if (!Constructor) {
    callbacks.onState('unavailable', 'Voice input is not supported here. Type your question or use keyboard dictation.');
    return null;
  }

  const recognizer = new Constructor();
  let listening = false;
  recognizer.lang = 'bn-BD';
  recognizer.continuous = false;
  recognizer.interimResults = false;
  recognizer.maxAlternatives = 1;
  recognizer.onresult = event => {
    const transcript = event.results[0]?.[0]?.transcript?.trim();
    if (transcript) callbacks.onTranscript(transcript);
  };
  recognizer.onerror = event => {
    listening = false;
    const denied = event.error === 'not-allowed' || event.error === 'service-not-allowed';
    callbacks.onState(
      denied ? 'unavailable' : 'error',
      denied
        ? 'Microphone permission was denied. You can still type your question.'
        : event.error === 'no-speech'
          ? 'No speech was detected. Try again or type your question.'
          : 'Voice input stopped. You can continue by typing.',
    );
  };
  recognizer.onend = () => {
    if (listening) callbacks.onState('idle');
    listening = false;
  };

  try {
    listening = true;
    callbacks.onState('listening');
    recognizer.start();
    if (!listening) return null;
  } catch (error) {
    listening = false;
    callbacks.onState('error', error instanceof Error ? error.message : 'Could not start voice input.');
    return null;
  }

  return {
    stop: () => {
      if (!listening) return;
      listening = false;
      try {
        recognizer.stop();
      } finally {
        callbacks.onState('idle');
      }
    },
    cancel: () => {
      if (!listening) return;
      listening = false;
      try {
        if (recognizer.abort) recognizer.abort();
        else recognizer.stop();
      } finally {
        callbacks.onState('idle');
      }
    },
  };
}

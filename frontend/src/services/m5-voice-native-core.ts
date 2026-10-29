export type NativeDictationCallbacks = {
  onTranscript: (transcript: string) => void;
  onState: (state: 'idle' | 'listening' | 'error' | 'unavailable', message?: string) => void;
};

type NativeResultEvent = { results?: ArrayLike<{ transcript?: string }> };
type NativeErrorEvent = { error?: string };
type NativeSubscription = { remove: () => void };

export type NativeSpeechRecognitionPort = {
  isRecognitionAvailable: () => boolean;
  supportsOnDeviceRecognition: () => boolean;
  getSupportedLocales?: (options: { androidRecognitionServicePackage?: string }) => Promise<{ installedLocales?: string[] }>;
  requestMicrophonePermissionsAsync: () => Promise<{ granted: boolean }>;
  requestPermissionsAsync: () => Promise<{ granted: boolean }>;
  addListener: (
    event: 'result' | 'error' | 'end',
    listener: (value: unknown) => void,
  ) => NativeSubscription;
  start: (options: {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    maxAlternatives: number;
    requiresOnDeviceRecognition: boolean;
  }) => void;
  stop: () => void;
  abort: () => void;
};

export type NativeDictationSession = { stop: () => void; cancel: () => void };

export function nativeRecognitionAvailable(module: NativeSpeechRecognitionPort): boolean {
  try {
    return module.isRecognitionAvailable();
  } catch {
    return false;
  }
}

function errorMessage(error: string | undefined): { state: 'error' | 'unavailable' | 'idle'; message: string } {
  if (error === 'not-allowed' || error === 'service-not-allowed') {
    return { state: 'unavailable', message: 'Microphone permission or Bengali speech recognition is unavailable. You can type your question.' };
  }
  if (error === 'language-not-supported') {
    return { state: 'unavailable', message: 'Bengali speech recognition is not available on this device. You can type your question.' };
  }
  if (error === 'no-speech' || error === 'speech-timeout') {
    return { state: 'error', message: 'No speech was detected. Try again or type your question.' };
  }
  if (error === 'interrupted' || error === 'aborted') {
    return { state: 'idle', message: '' };
  }
  return { state: 'error', message: 'Voice input stopped. You can continue by typing.' };
}

export function startNativeBanglaDictation(
  module: NativeSpeechRecognitionPort,
  callbacks: NativeDictationCallbacks,
): NativeDictationSession | null {
  if (!nativeRecognitionAvailable(module)) {
    callbacks.onState('unavailable', 'Voice input is not supported here. Type your question or use keyboard dictation.');
    return null;
  }

  let cancelled = false;
  let started = false;
  let listening = false;
  let subscriptions: NativeSubscription[] = [];
  const removeListeners = () => {
    subscriptions.forEach(subscription => subscription.remove());
    subscriptions = [];
  };

  void (async () => {
    try {
      let installedBanglaLocale = false;
      if (module.supportsOnDeviceRecognition() && module.getSupportedLocales) {
        const locales = await module.getSupportedLocales({}).catch(() => ({ installedLocales: [] }));
        installedBanglaLocale = (locales.installedLocales ?? []).some(locale =>
          ['bn-bd', 'bn-in'].includes(locale.toLowerCase()),
        );
      }
      const onDevice = module.supportsOnDeviceRecognition() && installedBanglaLocale;
      const permission = onDevice
        ? await module.requestMicrophonePermissionsAsync()
        : await module.requestPermissionsAsync();
      if (cancelled) return;
      if (!permission.granted) {
        callbacks.onState('unavailable', 'Microphone permission was denied. You can still type your question.');
        return;
      }

      subscriptions = [
        module.addListener('result', value => {
          const event = value as NativeResultEvent;
          const transcript = event.results?.[0]?.transcript?.trim();
          if (transcript && !cancelled) callbacks.onTranscript(transcript);
        }),
        module.addListener('error', value => {
          const event = value as NativeErrorEvent;
          if (cancelled) return;
          listening = false;
          const result = errorMessage(event.error);
          callbacks.onState(result.state, result.message);
          removeListeners();
        }),
        module.addListener('end', () => {
          if (cancelled) return;
          const hadBeenListening = listening;
          listening = false;
          removeListeners();
          if (hadBeenListening) callbacks.onState('idle');
        }),
      ];
      if (cancelled) {
        removeListeners();
        return;
      }
      module.start({
        lang: 'bn-BD',
        continuous: false,
        interimResults: false,
        maxAlternatives: 1,
        requiresOnDeviceRecognition: onDevice,
      });
      started = true;
      listening = true;
      callbacks.onState('listening');
    } catch {
      if (!cancelled) callbacks.onState('error', 'Could not start voice input. You can continue by typing.');
      removeListeners();
    }
  })();

  return {
    stop: () => {
      if (cancelled) return;
      if (!started) {
        cancelled = true;
        removeListeners();
        callbacks.onState('idle');
        return;
      }
      try {
        module.stop();
      } catch {
        cancelled = true;
        removeListeners();
        callbacks.onState('error', 'Voice input stopped. You can continue by typing.');
      }
    },
    cancel: () => {
      if (cancelled) return;
      cancelled = true;
      const shouldAbort = started && listening;
      listening = false;
      if (shouldAbort) {
        try { module.abort(); } catch { /* Native teardown is best effort. */ }
      }
      removeListeners();
      callbacks.onState('idle');
    },
  };
}

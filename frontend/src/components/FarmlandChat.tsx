import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  AppState,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AssistantIcon, AssistantIconName } from './assistant-icons';
import { BrandPlantIcon } from './icons';
import { DashboardIcon } from './dashboard-icons';
import { useAppContext } from '../context/AppProvider';
import type { ChatMessage } from '../data/demo';
import { getTaskScheduleState } from '../utils/task-dates';
import { ActionConfirmationCard } from '../modules/m5/ActionConfirmationCard';
import { actionConfirmationKeyId } from '../modules/m5/action-summary';
import type { ProposedAction } from '../modules/shared/contracts.generated';
import { ApiClientError } from '../services/api-client';
import { confirmAction, listPendingActions, recordConsent } from '../services/m5-actions';
import { m5Offline } from '../services/m5-offline';
import { isRetryableQueuedFailure } from '../services/m5-offline-core';
import type { CachedConversation, QueuedChatMessage } from '../services/m5-offline-core';
import { m5Speech } from '../services/m5-speech';
import { isBanglaDictationAvailable, startBanglaDictation, type DictationState } from '../services/m5-voice';

const PAPER = '#fffdf7';
const INK = '#0a392f';
const GREEN = '#145f3b';
const MUTED = '#687589';
const SERIF = 'Georgia';
const SANS = 'Arial';

function createClientRequestId(): string {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === 'function') return cryptoApi.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, character => {
    const random = Math.floor(Math.random() * 16);
    return (character === 'x' ? random : (random & 0x3) | 0x8).toString(16);
  });
}

function actionIsExpired(expiresAt: string): boolean {
  const expiration = Date.parse(expiresAt);
  return !Number.isFinite(expiration) || expiration <= Date.now();
}

function shouldRetryQueuedFailure(error: unknown): boolean {
  if (!(error instanceof ApiClientError)) return false;
  return isRetryableQueuedFailure(error.status, error.message);
}

function stopDictationSession(session: { stop: () => void; cancel?: () => void } | null): void {
  if (session?.cancel) session.cancel();
  else session?.stop();
}

const QUICK_ACTIONS: { title: string; icon: AssistantIconName; section: string; tone?: 'gold' }[] = [
  { title: 'Today’s tasks', icon: 'tasks', section: 'tasks' },
  { title: 'Disease help', icon: 'leaf', section: 'crop-health' },
  { title: 'Harvest guidance', icon: 'grain', section: 'season-plan', tone: 'gold' },
];

const BOTTOM_TABS = [
  { title: 'Home', icon: 'home' as const, section: null },
  { title: 'Tasks', icon: 'tasks' as const, section: 'tasks' },
  { title: 'Chat', icon: 'chat' as const, section: 'chat' },
  { title: 'Scan', icon: 'scan' as const, section: 'crop-health' },
  { title: 'Profile', icon: 'profile' as const, section: null },
];

export function FarmlandChat() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAppContext();
  const previousAccountId = useRef<string | null>(null);
  const farmId = Array.isArray(id) ? id[0] : id;
  const scopeKey = user?.id && farmId ? JSON.stringify([user.id, farmId]) : 'anonymous';

  useEffect(() => {
    const previous = previousAccountId.current;
    if (user?.id) {
      if (previous && previous !== user.id) void m5Offline.clearAccount(previous).catch(() => undefined);
      previousAccountId.current = user.id;
      void m5Offline.clearOtherAccounts(user.id).catch(() => undefined);
      return;
    }
    if (previous) {
      previousAccountId.current = null;
      void m5Offline.clearAccount(previous).catch(() => undefined);
    }
  }, [user?.id]);

  return <FarmlandChatScoped key={scopeKey} />;
}

function FarmlandChatScoped() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 380;
  const {
    user,
    farmlands,
    conversations,
    activeConversationIds,
    createConversation,
    addChatMessage,
    refreshFarmland,
    logout,
  } = useAppContext();
  const accountId = user?.id;
  const farm = farmlands.find(item => item.id === farmId);
  const offlineScopeKey = accountId && farmId ? JSON.stringify([accountId, farmId]) : null;
  const activeConversationId = farmId ? activeConversationIds[farmId] : undefined;
  const conversation = farmId && activeConversationId
    ? conversations[farmId]?.find(item => item.id === activeConversationId)
    : undefined;
  const messages = useMemo(() => conversation?.messages ?? [], [conversation?.messages]);
  const [cachedConversation, setCachedConversation] = useState<CachedConversation | null>(null);
  const [cachedConversationScope, setCachedConversationScope] = useState<string | null>(null);
  const [queuedMessages, setQueuedMessages] = useState<QueuedChatMessage[]>([]);
  const [queuedMessagesScope, setQueuedMessagesScope] = useState<string | null>(null);
  const [offlinePrompt, setOfflinePrompt] = useState<QueuedChatMessage | null>(null);
  const [offlineNotice, setOfflineNotice] = useState('');
  const [offlineNoticeScope, setOfflineNoticeScope] = useState<string | null>(null);
  const [offlineConsentAccountId, setOfflineConsentAccountId] = useState<string | null>(null);
  const [pendingActions, setPendingActions] = useState<ProposedAction[]>([]);
  const [pendingActionsScope, setPendingActionsScope] = useState<string | null>(null);
  const [actionMessages, setActionMessages] = useState<Record<string, string>>({});
  const [confirmingActionId, setConfirmingActionId] = useState<string | null>(null);
  const [dictationState, setDictationState] = useState<DictationState>('idle');
  const [voiceMessage, setVoiceMessage] = useState('');
  const [voiceConsentPromptForAccount, setVoiceConsentPromptForAccount] = useState<string | null>(null);
  const [voiceConsentAccountId, setVoiceConsentAccountId] = useState<string | null>(null);
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [text, setText] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const [clearOfflinePromptOpen, setClearOfflinePromptOpen] = useState(false);
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const listRef = useRef<ScrollView>(null);
  const pendingRequest = useRef<{ message: string; id: string } | null>(null);
  const conversationForPendingRequest = useRef<string | null>(null);
  const activeDictation = useRef<{ stop: () => void; cancel?: () => void } | null>(null);
  const confirmingKeys = useRef<Record<string, string>>({});
  const queueSyncing = useRef(false);
  const previousVoiceAccountId = useRef<string | null>(null);
  const voiceConsentPrompt = voiceConsentPromptForAccount === user?.id;
  const voiceConsentGranted = voiceConsentAccountId === user?.id;
  const offlineConsentGranted = offlineConsentAccountId === accountId;
  const scopedCachedConversation = cachedConversationScope === offlineScopeKey ? cachedConversation : null;
  const scopedQueuedMessages = queuedMessagesScope === offlineScopeKey ? queuedMessages : [];
  const scopedPendingActions = pendingActionsScope === offlineScopeKey ? pendingActions : [];
  const visibleOfflinePrompt = offlinePrompt && offlinePrompt.accountId === accountId && offlinePrompt.farmId === farmId
    ? offlinePrompt
    : null;
  const visibleOfflineNotice = offlineNoticeScope === offlineScopeKey ? offlineNotice : '';
  const showOfflineNotice = useCallback((message: string) => {
    setOfflineNotice(message);
    setOfflineNoticeScope(offlineScopeKey);
  }, [offlineScopeKey]);

  const refreshOfflineState = useCallback(async () => {
    if (!farmId || !accountId) return;
    try {
      const [queue, consent] = await Promise.all([
        m5Offline.queuedMessages(accountId, farmId),
        m5Offline.offlineConsent(accountId),
      ]);
      setQueuedMessages(queue);
      setQueuedMessagesScope(offlineScopeKey);
      setOfflineConsentAccountId(consent?.decision === 'granted' ? accountId : null);
      if (consent?.decision === 'granted') showOfflineNotice('Offline conversation storage is enabled on this device for up to 30 days.');
    } catch {
      showOfflineNotice('Offline storage is unavailable on this device.');
    }
  }, [accountId, farmId, offlineScopeKey, showOfflineNotice]);

  const refreshActions = useCallback(async () => {
    if (!farmId) return;
    try {
      setPendingActions(await listPendingActions(farmId));
      setPendingActionsScope(offlineScopeKey);
    } catch (error) {
      if (!(error instanceof ApiClientError && error.status === 503)) {
        setActionMessages(current => ({ ...current, list: 'Could not refresh pending farm changes.' }));
      }
    }
  }, [farmId, offlineScopeKey]);

  useEffect(() => {
    if (messages.length + scopedQueuedMessages.length > 0) listRef.current?.scrollToEnd({ animated: true });
  }, [messages.length, scopedQueuedMessages.length]);

  useEffect(() => {
    let active = true;
    if (!user?.id || !farmId) return () => { active = false; };
    void Promise.all([
      m5Offline.queuedMessages(user.id, farmId),
      m5Offline.offlineConsent(user.id),
    ]).then(([queue, consent]) => {
      if (!active) return;
      setQueuedMessages(queue);
      setQueuedMessagesScope(offlineScopeKey);
      setOfflineConsentAccountId(consent?.decision === 'granted' ? user.id : null);
      if (consent?.decision === 'granted') {
        showOfflineNotice('Offline conversation storage is enabled on this device for up to 30 days.');
      }
    }).catch(() => {
      if (active) showOfflineNotice('Offline storage is unavailable on this device.');
    });
    if (!conversation?.id) {
      void (async () => {
        const consent = await m5Offline.offlineConsent(user.id);
        if (!consent) {
          if (active) {
            setCachedConversation(null);
            setCachedConversationScope(offlineScopeKey);
          }
          return;
        }
        const latest = await m5Offline.latestConversation(user.id, farmId);
        if (active) {
          setCachedConversation(latest);
          setCachedConversationScope(offlineScopeKey);
        }
      })().catch(() => undefined);
    }
    return () => { active = false; };
  }, [user?.id, farmId, offlineScopeKey, conversation?.id, messages.length, showOfflineNotice]);

  useEffect(() => {
    if (!user?.id || !farmId || !conversation?.id || messages.length === 0) return;
    let active = true;
    void (async () => {
      const consent = await m5Offline.offlineConsent(user.id);
      if (!consent || consent.decision !== 'granted') return;
      await m5Offline.saveConversation(user.id, farmId, {
        id: conversation.id,
        title: conversation.title,
        messages: messages.map(message => ({
          id: message.id,
          text: message.text,
          sender: message.sender,
          timestamp: message.timestamp,
        })),
        updatedAt: conversation.updatedAt,
      });
    })().catch(() => {
      if (active) showOfflineNotice('This conversation could not be saved for offline viewing.');
    });
    return () => { active = false; };
  }, [user?.id, farmId, conversation?.id, conversation?.title, conversation?.updatedAt, messages, showOfflineNotice]);

  useEffect(() => {
    if (!farmId || !user?.id || !offlineScopeKey) return;
    let active = true;
    void listPendingActions(farmId).then(actions => {
      if (!active) return;
      setPendingActions(actions);
      setPendingActionsScope(offlineScopeKey);
    }).catch(error => {
      if (!(error instanceof ApiClientError && error.status === 503)) {
        setActionMessages(current => ({ ...current, list: 'Could not refresh pending farm changes.' }));
      }
    });
    return () => { active = false; };
  }, [farmId, user?.id, offlineScopeKey]);

  useEffect(() => () => {
    stopDictationSession(activeDictation.current);
    void m5Speech.stop().catch(() => undefined);
  }, []);

  useEffect(() => {
    const previousAccountId = previousVoiceAccountId.current;
    previousVoiceAccountId.current = user?.id ?? null;
    if (previousAccountId && previousAccountId !== user?.id) {
      stopDictationSession(activeDictation.current);
      activeDictation.current = null;
      void m5Speech.stop().catch(() => undefined);
      setSpeakingMessageId(null);
    }
  }, [user?.id]);

  useEffect(() => {
    const stopVoice = () => {
      stopDictationSession(activeDictation.current);
      activeDictation.current = null;
      setDictationState('idle');
      void m5Speech.stop().catch(() => undefined);
      setSpeakingMessageId(null);
    };
    const subscription = AppState.addEventListener('change', state => {
      if (state !== 'active') stopVoice();
    });
    const onVisibility = () => {
      if (document.visibilityState !== 'visible') stopVoice();
    };
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVisibility);
    return () => {
      subscription.remove();
      if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  useEffect(() => {
    if (!user?.id || !farmId || !offlineScopeKey) return;
    let active = true;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let syncQueue: () => Promise<void> = async () => undefined;
    const scheduleRetry = (queue: QueuedChatMessage[]) => {
      if (retryTimer) clearTimeout(retryTimer);
      retryTimer = null;
      if (!active || (typeof navigator !== 'undefined' && navigator.onLine === false)) return;
      const nextAttemptAt = queue[0]?.nextAttemptAt;
      if (!nextAttemptAt) return;
      const delay = Date.parse(nextAttemptAt) - Date.now();
      if (delay <= 0 || !Number.isFinite(delay)) return;
      retryTimer = setTimeout(() => {
        retryTimer = null;
        void syncQueue();
      }, delay);
    };
    syncQueue = async () => {
      if (!active) return;
      if (queueSyncing.current || (typeof navigator !== 'undefined' && navigator.onLine === false)) return;
      queueSyncing.current = true;
      let queue: QueuedChatMessage[] = [];
      try {
        const [consent, pending] = await Promise.all([
          m5Offline.offlineConsent(user.id),
          m5Offline.queuedMessages(user.id, farmId),
        ]);
        queue = pending;
        if (!consent || queue.length === 0) return;
        if (queue[0].deliveryState === 'needs_attention') {
          if (active) showOfflineNotice('A saved message needs attention. Remove it before sending later saved messages.');
          return;
        }
        if (queue[0].nextAttemptAt && Date.parse(queue[0].nextAttemptAt) > Date.now()) {
          scheduleRetry(queue);
          return;
        }
        if (!consent.synchronized) {
          await recordConsent({
            contract_version: '1.0.0',
            purpose: 'offline_storage',
            decision: 'granted',
            policy_version: consent.policyVersion,
            channel: 'explicit_tap',
            captured_at: consent.capturedAt,
          }, `offline-storage:${user.id}:${consent.capturedAt}`);
          await m5Offline.markConsentSynchronized(user.id);
        }

        let currentConversationId = activeConversationIds[farmId] ?? null;
        let sentCount = 0;
        for (const item of queue) {
          if (item.deliveryState === 'needs_attention') {
            if (active) showOfflineNotice('A saved message needs attention. Remove it before sending later saved messages.');
            break;
          }
          if (item.nextAttemptAt && Date.parse(item.nextAttemptAt) > Date.now()) break;
          let targetConversationId = item.conversationId ?? currentConversationId;
          if (!targetConversationId) targetConversationId = await createConversation(farmId);
          if (!item.conversationId) {
            await m5Offline.attachConversation(user.id, farmId, item.clientRequestId, targetConversationId);
          }
          try {
            await addChatMessage(farmId, targetConversationId, item.text, item.clientRequestId);
            await m5Offline.acknowledgeMessage(user.id, farmId, item.clientRequestId);
            currentConversationId = targetConversationId;
            sentCount += 1;
          } catch (error) {
            const failureNeedsAttention = !shouldRetryQueuedFailure(error);
            if (failureNeedsAttention) {
              await m5Offline.markNeedsAttention(user.id, farmId, item.clientRequestId, 'backend_rejected');
            } else {
              await m5Offline.recordRetry(user.id, farmId, item.clientRequestId);
            }
            queue = await m5Offline.queuedMessages(user.id, farmId);
            scheduleRetry(queue);
            if (active) {
              await refreshOfflineState();
              if (failureNeedsAttention || queue[0]?.deliveryState === 'needs_attention') {
                showOfflineNotice('A saved message could not be accepted. Remove it or clear this farm’s saved chat to continue.');
              }
            }
            return;
          }
        }
        if (active) {
          await refreshOfflineState();
          if (sentCount) showOfflineNotice(`${sentCount} saved message${sentCount === 1 ? '' : 's'} sent.`);
        }
        queue = await m5Offline.queuedMessages(user.id, farmId);
        scheduleRetry(queue);
      } catch (error) {
        if (queue.length > 0) {
          const first = queue[0];
          if (!shouldRetryQueuedFailure(error)) {
            await m5Offline.markNeedsAttention(user.id, farmId, first.clientRequestId, 'backend_rejected').catch(() => undefined);
          } else {
            await m5Offline.recordRetry(user.id, farmId, first.clientRequestId).catch(() => undefined);
          }
          queue = await m5Offline.queuedMessages(user.id, farmId).catch(() => queue);
          scheduleRetry(queue);
        }
        if (active) {
          await refreshOfflineState();
          if (queue[0]?.deliveryState === 'needs_attention') {
            showOfflineNotice('A saved message could not be accepted. Remove it or clear this farm’s saved chat to continue.');
          }
        }
      } finally {
        queueSyncing.current = false;
      }
    };

    void syncQueue();
    const onOnline = () => { void syncQueue(); };
    if (typeof window !== 'undefined') window.addEventListener('online', onOnline);
    const subscription = AppState.addEventListener('change', state => {
      if (state === 'active') void syncQueue();
    });
    return () => {
      active = false;
      if (retryTimer) clearTimeout(retryTimer);
      if (typeof window !== 'undefined') window.removeEventListener('online', onOnline);
      subscription.remove();
    };
  }, [user?.id, farmId, offlineScopeKey, scopedQueuedMessages.length, activeConversationIds, createConversation, addChatMessage, refreshOfflineState, showOfflineNotice]);

  const openSection = (section: string) => {
    if (!farmId) return;
    router.push(`/farmlands/${farmId}/${section}` as Href);
  };

  const send = async () => {
    const message = text.trim();
    if (!message || !farmId || sending) return;
    setSending(true);
    setChatError('');
    if (!pendingRequest.current || pendingRequest.current.message !== message) {
      pendingRequest.current = { message, id: createClientRequestId() };
      conversationForPendingRequest.current = conversation?.id ?? scopedCachedConversation?.id ?? null;
    }
    try {
      const conversationId = conversationForPendingRequest.current ?? await createConversation(farmId);
      conversationForPendingRequest.current = conversationId;
      await addChatMessage(farmId, conversationId, message, pendingRequest.current.id);
      setText('');
      pendingRequest.current = null;
      conversationForPendingRequest.current = null;
      showOfflineNotice('');
    } catch (error) {
      const request = pendingRequest.current;
      if (request && user?.id && error instanceof ApiClientError && error.status === undefined && error.message.includes('Could not connect to the backend')) {
        setOfflinePrompt({
          accountId: user.id,
          farmId,
          conversationId: conversationForPendingRequest.current,
          clientRequestId: request.id,
          text: request.message,
          createdAt: new Date().toISOString(),
        });
      } else {
        setChatError(error instanceof Error ? error.message : 'Message could not be sent. Please try again.');
      }
    } finally {
      setSending(false);
    }
  };

  const saveMessageForOffline = async () => {
    if (!offlinePrompt || !user?.id || offlinePrompt.accountId !== user.id || offlinePrompt.farmId !== farmId) return;
    try {
      let consent = await m5Offline.offlineConsent(user.id);
      if (!consent) {
        await m5Offline.grantOfflineConsent(user.id, '2026-10-v1');
        consent = await m5Offline.offlineConsent(user.id);
      }
      if (!consent) throw new Error('Offline consent could not be saved on this device.');
      await m5Offline.enqueueMessage(offlinePrompt);
      await m5Offline.recordRetry(user.id, farmId, offlinePrompt.clientRequestId);
      setText(value => value.trim() === offlinePrompt.text ? '' : value);
      if (pendingRequest.current?.id === offlinePrompt.clientRequestId) {
        pendingRequest.current = null;
        conversationForPendingRequest.current = null;
      }
      setOfflinePrompt(null);
      setOfflineConsentAccountId(user.id);
      showOfflineNotice('Message saved on this device. It will send when the connection returns.');
      await refreshOfflineState();
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'The message could not be saved offline.');
    }
  };

  const clearSavedFarmChat = async () => {
    if (!accountId || !farmId || !offlineScopeKey) return;
    try {
      await m5Offline.clearFarm(accountId, farmId);
      setCachedConversation(null);
      setCachedConversationScope(offlineScopeKey);
      setQueuedMessages([]);
      setQueuedMessagesScope(offlineScopeKey);
      setClearOfflinePromptOpen(false);
      showOfflineNotice('Saved conversation and queued messages for this farm were cleared from this device.');
    } catch {
      showOfflineNotice('Saved farm chat could not be cleared from this device.');
    }
  };

  const removeQueuedMessage = async (clientRequestId: string) => {
    if (!accountId || !farmId) return;
    try {
      await m5Offline.removeQueuedMessage(accountId, farmId, clientRequestId);
      await refreshOfflineState();
    } catch {
      showOfflineNotice('This saved message could not be removed from this device.');
    }
  };

  const decideAction = async (action: ProposedAction, decision: 'confirm' | 'reject') => {
    if (!farmId || action.farmland_id !== farmId || action.status !== 'awaiting_confirmation') return;
    if (decision === 'confirm' && actionIsExpired(action.expires_at)) {
      setActionMessages(current => ({ ...current, [action.action_id]: 'This proposal has expired. Refresh the farm changes before confirming.' }));
      await refreshActions();
      return;
    }
    setConfirmingActionId(action.action_id);
    setActionMessages(current => ({ ...current, [action.action_id]: '' }));
    const keyId = actionConfirmationKeyId(action.action_id, action.version, decision);
    const key = confirmingKeys.current[keyId] ?? `m5-action:${action.action_id}:${action.version}:${createClientRequestId()}`;
    confirmingKeys.current[keyId] = key;
    try {
      const receipt = await confirmAction(farmId, action, decision, key);
      delete confirmingKeys.current[keyId];
      if (receipt.status === 'applied') {
        setActionMessages(current => ({ ...current, [action.action_id]: 'Changes saved to this farm.' }));
        await refreshFarmland(farmId);
      } else if (receipt.status === 'rejected') {
        setActionMessages(current => ({ ...current, [action.action_id]: 'This change was declined.' }));
      } else {
        const code = typeof receipt.result?.code === 'string' ? receipt.result.code : '';
        const detail = code === 'action_expired'
          ? 'This proposal expired before it could be saved.'
          : 'The farm changed since this proposal was prepared. Review the updated proposal before confirming.';
        setActionMessages(current => ({ ...current, [action.action_id]: detail }));
      }
      await refreshActions();
    } catch (error) {
      const detail = error instanceof ApiClientError && error.status === 409
        ? 'The farm or action version changed. Refresh and review the latest proposal.'
        : error instanceof Error ? error.message : 'This farm change could not be saved.';
      setActionMessages(current => ({ ...current, [action.action_id]: detail }));
      await refreshActions();
    } finally {
      setConfirmingActionId(null);
    }
  };

  const beginDictation = () => {
    if (!isBanglaDictationAvailable()) {
      setDictationState('unavailable');
      setVoiceMessage('Voice input is not supported here. Type your question or use keyboard dictation.');
      return;
    }
    activeDictation.current = startBanglaDictation({
      onTranscript: transcript => setText(current => `${current.trim()}${current.trim() ? ' ' : ''}${transcript}`),
      onState: (state, message) => {
        setDictationState(state);
        setVoiceMessage(message ?? '');
        if (state !== 'listening') activeDictation.current = null;
      },
    });
  };

  const toggleDictation = () => {
    setVoiceMessage('');
    if (dictationState === 'listening') {
      activeDictation.current?.stop();
      activeDictation.current = null;
      return;
    }
    if (!isBanglaDictationAvailable()) {
      setDictationState('unavailable');
      setVoiceMessage('Voice input is not supported here. Type your question or use keyboard dictation.');
      return;
    }
    if (!voiceConsentGranted) {
      setVoiceConsentPromptForAccount(user?.id ?? null);
      return;
    }
    beginDictation();
  };

  const grantVoiceConsentAndStart = async () => {
    if (!user?.id) {
      setVoiceConsentPromptForAccount(null);
      setVoiceMessage('Sign in again before using voice input. You can type your question now.');
      return;
    }
    try {
      const capturedAt = new Date().toISOString();
      await recordConsent({
        contract_version: '1.0.0',
        purpose: 'speech_audio_transcription',
        decision: 'granted',
        policy_version: '2026-10-v1',
        channel: 'explicit_tap',
        captured_at: capturedAt,
      }, `speech-consent:${user.id}:${createClientRequestId()}`);
      setVoiceConsentAccountId(user.id);
      setVoiceConsentPromptForAccount(null);
      beginDictation();
    } catch {
      setVoiceConsentPromptForAccount(null);
      setVoiceMessage('Voice consent could not be saved. You can continue by typing.');
    }
  };

  const speakReply = async (message: ChatMessage) => {
    if (speakingMessageId === message.id) {
      await m5Speech.stop().catch(() => undefined);
      setSpeakingMessageId(null);
      return;
    }
    await m5Speech.stop().catch(() => undefined);
    setSpeakingMessageId(message.id);
    setVoiceMessage('');
    const language = /[\u0980-\u09ff]/.test(message.text) ? 'bn' : 'en';
    const result = await m5Speech.speak(message.text, language).catch(() => 'unavailable' as const);
    setSpeakingMessageId(null);
    if (result !== 'available') {
      setVoiceMessage(language === 'bn'
        ? 'এই ডিভাইসে বাংলা কণ্ঠস্বর নেই। লিখিত উত্তরটি পড়ে নিতে পারেন।'
        : 'Text-to-speech is unavailable on this device.');
    }
  };

  const onTabPress = (title: string, section: string | null) => {
    if (title === 'Profile') {
      setProfileOpen(true);
    } else if (section === null) {
      router.push('/farmlands' as Href);
    } else if (section !== 'chat') {
      openSection(section);
    }
  };

  if (!farm) {
    return (
      <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
        <View style={styles.notFound}>
          <Text style={styles.notFoundText}>Farm not found.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const todayCount = farm.tasks.filter(task => {
    const state = getTaskScheduleState(task, new Date());
    return state === 'due' || state === 'overdue' || state === 'unscheduled';
  }).length;
  const historyMessages: ChatMessage[] = messages.length
    ? messages
    : conversation?.id ? [] : scopedCachedConversation?.messages.map(message => ({
      id: message.id,
      text: message.text,
      sender: message.sender,
      timestamp: message.timestamp,
    })) ?? [];
  const hasCachedHistory = !conversation?.id && messages.length === 0 && historyMessages.length > 0;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.page}>
        <View style={styles.header}>
          <View style={styles.brand}>
            <BrandPlantIcon size={36} />
            <View>
              <Text style={styles.brandName}>FieldShift BD</Text>
              <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
            </View>
          </View>
          <View style={styles.headerActions}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="View notifications"
              onPress={() => openSection('alerts')}
              style={styles.bellButton}
            >
              <DashboardIcon name="bell" size={27} color={GREEN} />
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Open profile"
              onPress={() => setProfileOpen(true)}
              style={styles.avatarButton}
            >
              <Image source={require('../../assets/images/landing-farmer.png')} style={styles.avatar} />
            </Pressable>
          </View>
        </View>

        <View style={styles.intro}>
          <Text style={[styles.title, compact && styles.titleCompact]}>Assistant</Text>
          <Text numberOfLines={1} style={[styles.subtitle, compact && styles.subtitleCompact]}>
            Personalized advice using your crop, stage, weather and tasks.
          </Text>
        </View>

        <View style={[styles.contextCards, compact && styles.contextCardsCompact]}>
          <ContextCard icon="grass" label="Crop" value={farm.crop} onPress={() => openSection('season-plan')} compact={compact} />
          <ContextCard icon="sprout" label="Stage" value={farm.growthStage} onPress={() => openSection('season-plan')} compact={compact} />
          <ContextCard icon="list" label="Today" value={`${todayCount} tasks`} onPress={() => openSection('tasks')} compact={compact} />
        </View>

        <ScrollView
          ref={listRef}
          style={styles.messageScroll}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() => {
            if (historyMessages.length + scopedQueuedMessages.length > 0) listRef.current?.scrollToEnd({ animated: false });
          }}
        >
          {actionMessages.list ? <Text accessibilityRole="alert" style={styles.chatError}>{actionMessages.list}</Text> : null}
          {scopedPendingActions.map(action => (
            <ActionConfirmationCard
              key={action.action_id}
              action={action}
              farmName={farm.name}
              busy={confirmingActionId === action.action_id}
              message={actionMessages[action.action_id]}
              onDecision={decision => void decideAction(action, decision)}
            />
          ))}
          {hasCachedHistory ? <Text style={styles.cachedNotice}>Showing this farm’s saved conversation. It may be out of date.</Text> : null}
          {historyMessages.length || scopedQueuedMessages.length ? <>
            {historyMessages.map(message => (
              <MessageBubble
                key={message.id}
                message={message}
                compact={compact}
                speaking={speakingMessageId === message.id}
                onSpeak={() => void speakReply(message)}
              />
            ))}
            {scopedQueuedMessages.map(item => (
              <MessageBubble
                key={`queued:${item.clientRequestId}`}
                message={{ id: `queued:${item.clientRequestId}`, sender: 'farmer', text: item.text, timestamp: 'Saved offline' }}
                compact={compact}
                delivery={item.deliveryState === 'needs_attention' ? 'needs_attention' : 'queued'}
                onRemove={() => void removeQueuedMessage(item.clientRequestId)}
              />
            ))}
          </> : (
            <View style={styles.emptyConversation}>
              <View style={styles.emptyConversationIcon}><BrandPlantIcon size={26} /></View>
              <Text style={styles.emptyConversationTitle}>Ask about {farm.crop.toLowerCase()}</Text>
              <Text style={styles.emptyConversationText}>Your assistant can use this farm’s saved crop, tasks, and field records when you send a message.</Text>
            </View>
          )}
        </ScrollView>

        {chatError ? <Text accessibilityRole="alert" style={styles.chatError}>{chatError}</Text> : null}
        {visibleOfflineNotice ? <Text accessibilityLiveRegion="polite" style={styles.offlineNotice}>{visibleOfflineNotice}</Text> : null}
        {offlineConsentGranted ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Clear saved chat for this farm on this device"
            onPress={() => setClearOfflinePromptOpen(true)}
            style={styles.clearOfflineButton}
          >
            <Text style={styles.clearOfflineText}>Clear saved chat for this farm</Text>
          </Pressable>
        ) : null}
        {voiceMessage ? <Text accessibilityLiveRegion="polite" style={styles.voiceNotice}>{voiceMessage}</Text> : null}

        <View style={[styles.quickActions, compact && styles.quickActionsCompact]}>
          {QUICK_ACTIONS.map(action => (
            <Pressable
              key={action.title}
              accessibilityRole="button"
              accessibilityLabel={action.title}
              onPress={() => openSection(action.section)}
              style={[styles.quickCard, action.tone === 'gold' && styles.quickCardGold, compact && styles.quickCardCompact]}
            >
              <View style={[styles.quickIcon, action.tone === 'gold' && styles.quickIconGold, compact && styles.quickIconCompact]}>
              <AssistantIcon name={action.icon} size={compact ? 15 : 17} color={action.tone === 'gold' ? '#b47a10' : GREEN} />
              </View>
              <Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.68} style={[styles.quickTitle, compact && styles.quickTitleCompact]}>
                {action.title}
              </Text>
              <AssistantIcon name="chevron" size={compact ? 10 : 11} color="#42516a" />
            </Pressable>
          ))}
        </View>

        <View style={[styles.composer, compact && styles.composerCompact]}>
          <View style={[styles.sparkleCircle, compact && styles.sparkleCircleCompact]}>
            <AssistantIcon name="sparkle" size={22} color={GREEN} />
          </View>
          <TextInput
            accessibilityLabel="Ask anything about your farm"
            style={styles.messageInput}
            placeholder="Ask anything about your farm..."
            placeholderTextColor={MUTED}
            value={text}
            onChangeText={setText}
            multiline
            maxLength={4000}
            textAlignVertical="center"
            autoCorrect
            autoCapitalize="sentences"
            returnKeyType="default"
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={dictationState === 'listening' ? 'Stop Bangla voice input' : 'Start Bangla voice input'}
            accessibilityState={{ selected: dictationState === 'listening' }}
            onPress={toggleDictation}
            style={[styles.microphoneButton, dictationState === 'listening' && styles.microphoneButtonActive]}
          >
            <AssistantIcon name="microphone" size={24} color={dictationState === 'listening' ? GREEN : '#445267'} />
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Send message"
            disabled={!text.trim() || sending}
            onPress={() => void send()}
            style={({ pressed }) => [
              styles.sendButton,
              compact && styles.sendButtonCompact,
              (!text.trim() || sending) && styles.sendButtonDisabled,
              pressed && styles.sendButtonPressed,
            ]}
          >
            <AssistantIcon name="send" size={23} color="#fffdf7" />
          </Pressable>
        </View>

        <View style={[styles.tabBar, compact && styles.tabBarCompact]}>
          {BOTTOM_TABS.map(tab => {
            const active = tab.title === 'Chat';
            return (
              <Pressable
                key={tab.title}
                accessibilityRole="button"
                accessibilityLabel={tab.title}
                accessibilityState={{ selected: active }}
                onPress={() => onTabPress(tab.title, tab.section)}
                style={styles.tabButton}
              >
                <View style={[styles.tabActive, active && styles.tabActiveSelected]}>
                  <DashboardIcon name={tab.icon} size={22} color={active ? GREEN : '#758092'} />
                  <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.title}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Modal visible={profileOpen} transparent animationType="fade" onRequestClose={() => setProfileOpen(false)}>
        <View style={styles.modalLayer}>
          <Pressable accessibilityLabel="Close profile menu" onPress={() => setProfileOpen(false)} style={styles.modalBackdrop} />
          <View style={styles.profileCard}>
            <Text style={styles.profileTitle}>{user?.name ?? 'Farmer'}</Text>
            <Text style={styles.profilePhone}>{user?.phone ?? ''}</Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                router.push(`/farmlands/${farmId}/resources` as Href);
              }}
              style={styles.profileAction}
            >
              <Text style={styles.profileActionText}>Farm profile & resources</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                router.push('/farmlands/profile-setup' as Href);
              }}
              style={styles.profileAction}
            >
              <Text style={styles.profileActionText}>Map your farm</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                router.push('/farmlands/manage' as Href);
              }}
              style={styles.profileAction}
            >
              <Text style={styles.profileActionText}>My farmlands</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={async () => {
                setProfileOpen(false);
                await logout();
                router.replace('/auth/login' as Href);
              }}
              style={[styles.profileAction, styles.logoutAction]}
            >
              <Text style={styles.profileActionText}>Log out</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={visibleOfflinePrompt !== null} transparent animationType="fade" onRequestClose={() => setOfflinePrompt(null)}>
        <View style={styles.offlineModalLayer}>
          <Pressable accessibilityLabel="Close offline message prompt" onPress={() => setOfflinePrompt(null)} style={styles.modalBackdrop} />
          <View style={styles.offlinePromptCard}>
            <Text style={styles.profileTitle}>Save this message offline?</Text>
            <Text style={styles.offlinePromptText}>
              This saves the full chat history for this farm and queued messages on this device for up to 30 days. Up to 50 messages can wait per farm; they send with the same retry ID when the connection returns. Clear this farm’s saved chat any time. No audio is stored.
            </Text>
            <Pressable accessibilityRole="button" onPress={() => void saveMessageForOffline()} style={styles.offlineSaveButton}>
              <Text style={styles.offlineSaveText}>Save on this device</Text>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setOfflinePrompt(null)} style={styles.offlineCancelButton}>
              <Text style={styles.profileActionText}>Keep editing</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={clearOfflinePromptOpen} transparent animationType="fade" onRequestClose={() => setClearOfflinePromptOpen(false)}>
        <View style={styles.offlineModalLayer}>
          <Pressable accessibilityLabel="Close clear saved chat prompt" onPress={() => setClearOfflinePromptOpen(false)} style={styles.modalBackdrop} />
          <View style={styles.offlinePromptCard}>
            <Text style={styles.profileTitle}>Clear saved chat for this farm?</Text>
            <Text style={styles.offlinePromptText}>
              This removes saved conversation history and queued messages for {farm?.name ?? 'this farm'} from this device. Other farms are not affected. Offline storage stays enabled for future messages.
            </Text>
            <Pressable accessibilityRole="button" onPress={() => void clearSavedFarmChat()} style={styles.offlineSaveButton}>
              <Text style={styles.offlineSaveText}>Clear saved chat</Text>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setClearOfflinePromptOpen(false)} style={styles.offlineCancelButton}>
              <Text style={styles.profileActionText}>Keep saved chat</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={voiceConsentPrompt} transparent animationType="fade" onRequestClose={() => setVoiceConsentPromptForAccount(null)}>
        <View style={styles.offlineModalLayer}>
          <Pressable accessibilityLabel="Close voice consent prompt" onPress={() => setVoiceConsentPromptForAccount(null)} style={styles.modalBackdrop} />
          <View style={styles.offlinePromptCard}>
            <Text style={styles.profileTitle}>Allow Bengali voice input?</Text>
            <Text style={styles.offlinePromptText}>
              Your browser or phone’s speech service may process microphone audio to return text. FieldShift adds only that text to this composer; it is sent only after you tap Send. FieldShift never saves audio.
            </Text>
            <Pressable accessibilityRole="button" onPress={() => void grantVoiceConsentAndStart()} style={styles.offlineSaveButton}>
              <Text style={styles.offlineSaveText}>Allow and start microphone</Text>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setVoiceConsentPromptForAccount(null)} style={styles.offlineCancelButton}>
              <Text style={styles.profileActionText}>Continue typing</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function ContextCard({
  icon,
  label,
  value,
  onPress,
  compact,
}: {
  icon: AssistantIconName;
  label: string;
  value: string;
  onPress: () => void;
  compact: boolean;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.contextCard, compact && styles.contextCardCompact]}>
      <View style={[styles.contextIcon, compact && styles.contextIconCompact]}>
        <AssistantIcon name={icon} size={compact ? 20 : 23} color={GREEN} />
      </View>
      <View style={styles.contextCopy}>
        <Text numberOfLines={1} style={[styles.contextLabel, compact && styles.contextLabelCompact]}>{label}</Text>
        <Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.84} style={[styles.contextValue, compact && styles.contextValueCompact]}>{value}</Text>
      </View>
      <AssistantIcon name="chevron" size={compact ? 14 : 16} color="#3d4c60" />
    </Pressable>
  );
}

function MessageBubble({
  message,
  compact,
  delivery,
  speaking = false,
  onSpeak,
  onRemove,
}: {
  message: ChatMessage;
  compact: boolean;
  delivery?: 'queued' | 'needs_attention';
  speaking?: boolean;
  onSpeak?: () => void;
  onRemove?: () => void;
}) {
  const farmer = message.sender === 'farmer';

  if (farmer) {
    return (
      <View style={[styles.messageRow, styles.farmerRow]}>
        <View style={[styles.farmerBubble, compact && styles.farmerBubbleCompact]}>
          <Text style={[styles.farmerText, compact && styles.farmerTextCompact]}>{message.text}</Text>
          <View style={styles.farmerMeta}>
            <Text style={styles.timestamp}>{message.timestamp}</Text>
            {delivery === 'needs_attention' ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Remove unsent saved message"
                onPress={onRemove}
                style={styles.attentionButton}
              >
                <Text style={styles.attentionLabel}>Needs attention · Remove</Text>
              </Pressable>
            ) : delivery === 'queued' ? (
              <Text style={styles.queuedLabel}>Queued</Text>
            ) : (
              <AssistantIcon name="checks" size={17} color={GREEN} />
            )}
          </View>
        </View>
        <Image source={require('../../assets/images/landing-farmer.png')} style={[styles.messageAvatar, compact && styles.messageAvatarCompact]} />
      </View>
    );
  }

  return (
    <View style={styles.messageRow}>
      <View style={[styles.assistantAvatar, compact && styles.assistantAvatarCompact]}>
        <BrandPlantIcon size={28} />
      </View>
      <View style={styles.assistantMessageWrap}>
        <View style={[styles.assistantBubble, compact && styles.assistantBubbleCompact]}>
          <Text style={[styles.assistantText, compact && styles.assistantTextCompact]}>{message.text}</Text>
        </View>
        <View style={styles.assistantFooter}>
          <Text style={styles.assistantTimestamp}>{message.timestamp}</Text>
          {onSpeak ? (
            <Pressable accessibilityRole="button" accessibilityLabel={speaking ? 'Stop reading reply' : 'Read reply aloud'} onPress={onSpeak} style={styles.listenButton}>
              <AssistantIcon name="volume" size={15} color={GREEN} />
              <Text style={styles.listenText}>{speaking ? 'Stop' : 'Listen'}</Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  page: { flex: 1, minHeight: 0, overflow: 'hidden', width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  header: { minHeight: 49, marginTop: 5, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  brandName: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 18, lineHeight: 21, letterSpacing: -0.4 },
  brandTagline: { color: MUTED, fontFamily: SANS, fontSize: 11.5, lineHeight: 15 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bellButton: { width: 31, height: 38, alignItems: 'center', justifyContent: 'center' },
  avatarButton: { width: 39, height: 39, borderRadius: 22, padding: 2, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e9e6d8' },
  avatar: { width: '100%', height: '100%', borderRadius: 20 },
  intro: { marginTop: 8, marginBottom: 1, paddingHorizontal: 21 },
  title: { color: '#073c32', fontFamily: SERIF, fontSize: 37, fontWeight: '700', lineHeight: 43, letterSpacing: -1.1 },
  titleCompact: { fontSize: 34, lineHeight: 39 },
  subtitle: { color: MUTED, fontFamily: SANS, fontSize: 12.1, lineHeight: 16, letterSpacing: -0.16 },
  subtitleCompact: { fontSize: 11.2, lineHeight: 15 },
  contextCards: { marginHorizontal: 16, marginTop: 10, marginBottom: 8, flexDirection: 'row', gap: 6 },
  contextCardsCompact: { marginHorizontal: 13, gap: 5, marginTop: 8, marginBottom: 7 },
  contextCard: { flex: 1, minWidth: 0, height: 54, flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 3, borderRadius: 15, borderWidth: 1, borderColor: '#f0ecdf', backgroundColor: '#fffefa', boxShadow: '0px 3px 10px rgba(30, 54, 37, 0.06)', elevation: 1 },
  contextCardCompact: { height: 50, gap: 2, paddingHorizontal: 2, borderRadius: 13 },
  contextIcon: { width: 26, height: 30, borderRadius: 11, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  contextIconCompact: { width: 23, height: 26, borderRadius: 9 },
  contextCopy: { flex: 1, minWidth: 0 },
  contextLabel: { color: MUTED, fontFamily: SANS, fontSize: 9.8, lineHeight: 12 },
  contextLabelCompact: { fontSize: 9, lineHeight: 11 },
  contextValue: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 10, lineHeight: 13, letterSpacing: -0.22 },
  contextValueCompact: { fontSize: 9, lineHeight: 12 },
  messageScroll: { flex: 1, minHeight: 0 },
  messageContent: { paddingHorizontal: 19, paddingTop: 3, paddingBottom: 8, gap: 7 },
  emptyConversation: { flex: 1, minHeight: 170, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 26, gap: 8 },
  emptyConversationIcon: { width: 50, height: 50, borderRadius: 26, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  emptyConversationTitle: { color: INK, fontFamily: SERIF, fontSize: 17, fontWeight: '700', textAlign: 'center' },
  emptyConversationText: { maxWidth: 300, color: MUTED, fontFamily: SANS, fontSize: 12.5, lineHeight: 18, textAlign: 'center' },
  chatError: { marginHorizontal: 18, marginBottom: 5, color: '#a1372d', fontFamily: SANS, fontSize: 12, lineHeight: 16, textAlign: 'center' },
  offlineNotice: { marginHorizontal: 18, marginBottom: 4, color: GREEN, fontFamily: SANS, fontSize: 11, lineHeight: 15, textAlign: 'center' },
  clearOfflineButton: { minHeight: 44, marginHorizontal: 18, marginBottom: 2, alignItems: 'center', justifyContent: 'center' },
  clearOfflineText: { color: '#486655', fontFamily: SANS, fontSize: 11, lineHeight: 15, textDecorationLine: 'underline' },
  voiceNotice: { marginHorizontal: 18, marginBottom: 4, color: '#5b6570', fontFamily: SANS, fontSize: 11, lineHeight: 15, textAlign: 'center' },
  cachedNotice: { color: '#718092', fontFamily: SANS, fontSize: 11, lineHeight: 15, textAlign: 'center', paddingHorizontal: 16, paddingVertical: 4 },
  queuedLabel: { color: '#9a6c18', fontFamily: SANS, fontSize: 9.5, lineHeight: 13 },
  attentionButton: { minHeight: 44, paddingHorizontal: 4, justifyContent: 'center' },
  attentionLabel: { color: '#a1372d', fontFamily: SANS, fontSize: 10, lineHeight: 14, textDecorationLine: 'underline' },
  messageRow: { width: '100%', flexDirection: 'row', alignItems: 'flex-start', gap: 7 },
  farmerRow: { alignItems: 'flex-start', justifyContent: 'flex-end' },
  farmerBubble: { maxWidth: '79%', paddingHorizontal: 13, paddingTop: 8, paddingBottom: 6, borderRadius: 20, backgroundColor: '#eaf2e4', boxShadow: '0px 2px 8px rgba(40, 57, 39, 0.06)', elevation: 1 },
  farmerBubbleCompact: { maxWidth: '77%', paddingHorizontal: 10, paddingTop: 7, paddingBottom: 5, borderRadius: 18 },
  farmerText: { color: INK, fontFamily: SERIF, fontSize: 15.5, lineHeight: 20, letterSpacing: -0.23 },
  farmerTextCompact: { fontSize: 14, lineHeight: 18 },
  farmerMeta: { marginTop: 2, flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: 4 },
  timestamp: { color: '#63798a', fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  messageAvatar: { width: 31, height: 31, borderRadius: 17, marginTop: 1 },
  messageAvatarCompact: { width: 28, height: 28 },
  assistantAvatar: { width: 34, height: 34, marginTop: 1, borderRadius: 20, backgroundColor: '#edf3e8', borderWidth: 1, borderColor: '#fff', alignItems: 'center', justifyContent: 'center', boxShadow: '0px 2px 8px rgba(40, 57, 39, 0.08)', elevation: 1 },
  assistantAvatarCompact: { width: 30, height: 30 },
  assistantMessageWrap: { flex: 1, minWidth: 0, alignItems: 'flex-start' },
  assistantBubble: { width: '100%', maxWidth: 355, paddingHorizontal: 13, paddingVertical: 9, borderRadius: 18, borderWidth: 1, borderColor: '#f3efe6', backgroundColor: '#fffefa', boxShadow: '0px 3px 10px rgba(30, 54, 37, 0.06)', elevation: 1 },
  assistantBubbleCompact: { paddingHorizontal: 11, paddingVertical: 8, borderRadius: 16 },
  assistantText: { color: '#111e3a', fontFamily: SERIF, fontSize: 15.5, lineHeight: 20.5, letterSpacing: -0.2 },
  assistantTextCompact: { fontSize: 14.3, lineHeight: 18.2 },
  assistantTimestamp: { color: '#718092', fontFamily: SANS, fontSize: 10.5, lineHeight: 14, marginLeft: 13, marginTop: 2 },
  assistantFooter: { flexDirection: 'row', alignItems: 'center', gap: 12, marginLeft: 13, marginTop: 2 },
  listenButton: { minWidth: 48, minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3, paddingHorizontal: 5 },
  listenText: { color: GREEN, fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  quickActions: { marginHorizontal: 16, marginTop: 3, marginBottom: 7, flexDirection: 'row', gap: 6 },
  quickActionsCompact: { marginHorizontal: 13, marginBottom: 6, gap: 4 },
  quickCard: { flex: 1, minWidth: 0, height: 41, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 1, paddingHorizontal: 1, borderRadius: 15, borderWidth: 1, borderColor: '#f0ecdf', backgroundColor: '#fffefa', boxShadow: '0px 2px 7px rgba(30, 54, 37, 0.06)', elevation: 1 },
  quickCardCompact: { height: 38, paddingHorizontal: 1, gap: 1, borderRadius: 13 },
  quickCardGold: { backgroundColor: '#fffaf0', borderColor: '#eee4cc' },
  quickIcon: { width: 17, height: 26, borderRadius: 9, flexShrink: 0, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  quickIconCompact: { width: 15, height: 23, borderRadius: 8 },
  quickIconGold: { backgroundColor: '#fff0d1' },
  quickTitle: { flex: 1, minWidth: 0, color: INK, fontFamily: SERIF, fontSize: 8.7, lineHeight: 12, letterSpacing: -0.2 },
  quickTitleCompact: { fontSize: 8, lineHeight: 11 },
  composer: { minHeight: 54, marginHorizontal: 14, paddingHorizontal: 7, paddingVertical: 5, flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 30, borderWidth: 1, borderColor: '#f1ede2', backgroundColor: '#fffefa', boxShadow: '0px 3px 10px rgba(30, 54, 37, 0.08)', elevation: 2 },
  composerCompact: { minHeight: 49, marginHorizontal: 12, paddingHorizontal: 5, gap: 4 },
  sparkleCircle: { width: 39, height: 39, borderRadius: 22, flexShrink: 0, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  sparkleCircleCompact: { width: 34, height: 34 },
  messageInput: { flex: 1, minWidth: 0, minHeight: 38, maxHeight: 76, paddingHorizontal: 2, paddingVertical: 6, color: INK, fontFamily: SERIF, fontSize: 14.5, lineHeight: 18, outlineStyle: 'none' as never },
  microphoneButton: { width: 44, height: 44, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  microphoneButtonActive: { backgroundColor: '#edf3e8', borderRadius: 18 },
  sendButton: { width: 42, height: 42, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 24, backgroundColor: GREEN },
  sendButtonCompact: { width: 38, height: 38 },
  sendButtonDisabled: { opacity: 0.96 },
  sendButtonPressed: { opacity: 0.72 },
  tabBar: { minHeight: 62, marginTop: 5, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,254,250,0.98)', borderTopWidth: 1, borderTopColor: '#f5f0e5' },
  tabBarCompact: { minHeight: 57, paddingHorizontal: 7 },
  tabButton: { flex: 1, alignItems: 'stretch', justifyContent: 'center' },
  tabActive: { height: 53, borderRadius: 17, alignItems: 'center', justifyContent: 'center', gap: 0 },
  tabActiveSelected: { backgroundColor: '#edf3e8' },
  tabLabel: { color: '#687589', fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  tabLabelActive: { color: INK, fontWeight: '600' },
  notFound: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  notFoundText: { color: MUTED, fontFamily: SANS, fontSize: 15 },
  modalLayer: { flex: 1, alignItems: 'flex-end', paddingTop: 52, paddingHorizontal: 16 },
  modalBackdrop: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(11, 28, 22, 0.22)' },
  profileCard: { width: 220, padding: 16, borderRadius: 16, backgroundColor: PAPER, boxShadow: '0px 5px 16px rgba(0, 0, 0, 0.18)', elevation: 8 },
  profileTitle: { color: INK, fontFamily: SERIF, fontSize: 17, fontWeight: '700' },
  profilePhone: { color: MUTED, fontFamily: SANS, fontSize: 12, marginTop: 3 },
  profileAction: { marginTop: 12, minHeight: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#dce6d8' },
  profileActionText: { color: GREEN, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  offlineModalLayer: { flex: 1, justifyContent: 'center', paddingHorizontal: 20 },
  offlinePromptCard: { padding: 18, borderRadius: 18, backgroundColor: PAPER, boxShadow: '0px 5px 16px rgba(0, 0, 0, 0.18)', elevation: 8 },
  offlinePromptText: { marginTop: 8, color: MUTED, fontFamily: SANS, fontSize: 13, lineHeight: 19 },
  offlineSaveButton: { marginTop: 16, minHeight: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: GREEN },
  offlineSaveText: { color: PAPER, fontFamily: SANS, fontSize: 14, fontWeight: '700' },
  offlineCancelButton: { marginTop: 9, minHeight: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#dce6d8' },
  logoutAction: { backgroundColor: '#eaf1e7' },
});

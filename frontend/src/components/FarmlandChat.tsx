import { useEffect, useRef, useState } from 'react';
import {
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
    logout,
  } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const activeConversationId = farmId ? activeConversationIds[farmId] : undefined;
  const conversation = farmId && activeConversationId
    ? conversations[farmId]?.find(item => item.id === activeConversationId)
    : undefined;
  const messages = conversation?.messages ?? [];
  const [text, setText] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const listRef = useRef<ScrollView>(null);
  const pendingRequest = useRef<{ message: string; id: string } | null>(null);

  useEffect(() => {
    if (messages.length > 0) listRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

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
    }
    try {
      const conversationId = conversation?.id ?? await createConversation(farmId);
      await addChatMessage(farmId, conversationId, message, pendingRequest.current.id);
      setText('');
      pendingRequest.current = null;
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Message could not be sent. Please try again.');
    } finally {
      setSending(false);
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
            if (messages.length > 0) listRef.current?.scrollToEnd({ animated: false });
          }}
        >
          {messages.length ? messages.map(message => (
            <MessageBubble key={message.id} message={message} compact={compact} />
          )) : (
            <View style={styles.emptyConversation}>
              <View style={styles.emptyConversationIcon}><BrandPlantIcon size={26} /></View>
              <Text style={styles.emptyConversationTitle}>Ask about {farm.crop.toLowerCase()}</Text>
              <Text style={styles.emptyConversationText}>Your assistant can use this farm’s saved crop, tasks, and field records when you send a message.</Text>
            </View>
          )}
        </ScrollView>

        {chatError ? <Text accessibilityRole="alert" style={styles.chatError}>{chatError}</Text> : null}

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
          <View style={styles.microphoneButton}>
            <AssistantIcon name="microphone" size={24} color="#445267" />
          </View>
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
              onPress={() => {
                setProfileOpen(false);
                logout();
                router.replace('/auth/login' as Href);
              }}
              style={[styles.profileAction, styles.logoutAction]}
            >
              <Text style={styles.profileActionText}>Log out</Text>
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

function MessageBubble({ message, compact }: { message: ChatMessage; compact: boolean }) {
  const farmer = message.sender === 'farmer';

  if (farmer) {
    return (
      <View style={[styles.messageRow, styles.farmerRow]}>
        <View style={[styles.farmerBubble, compact && styles.farmerBubbleCompact]}>
          <Text style={[styles.farmerText, compact && styles.farmerTextCompact]}>{message.text}</Text>
          <View style={styles.farmerMeta}>
            <Text style={styles.timestamp}>{message.timestamp}</Text>
            <AssistantIcon name="checks" size={17} color={GREEN} />
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
        <Text style={styles.assistantTimestamp}>{message.timestamp}</Text>
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
  microphoneButton: { width: 28, height: 35, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
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
  logoutAction: { backgroundColor: '#eaf1e7' },
});

import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../context/AppProvider';
import {
  ChatMessageItem,
  createConversation,
  listConversations,
  getConversation,
  sendMessage,
} from '../services/m5-chat';
import { BORDER_RADIUS, COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

export function FarmlandChat() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [text, setText] = useState('');
  const listRef = useRef<FlatList<ChatMessageItem>>(null);

  useEffect(() => {
    if (!farmId) return;
    let mounted = true;
    setLoading(true);

    listConversations(farmId)
      .then(async list => {
        if (!mounted) return;
        if (list.length > 0) {
          const conv = await getConversation(farmId, list[0].id);
          if (mounted && conv) {
            setConversationId(conv.id);
            setMessages(conv.messages);
          }
        } else {
          const newConv = await createConversation(farmId, `Chat for ${farm?.name || 'Farm'}`);
          if (mounted && newConv) {
            setConversationId(newConv.id);
            setMessages([]);
          }
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [farmId]);

  useEffect(() => {
    listRef.current?.scrollToEnd({ animated: true });
  }, [messages.length, sending]);

  const send = async () => {
    const trimmed = text.trim();
    if (!trimmed || !farmId || !conversationId || sending) return;

    setText('');
    setSending(true);

    // Optimistically add user message
    const tempMsg: ChatMessageItem = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      sender_type: 'farmer',
      message: trimmed,
      message_type: 'text',
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempMsg]);

    const res = await sendMessage(farmId, conversationId, trimmed);
    if (res) {
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempMsg.id),
        res.farmer_message,
        res.assistant_message,
      ]);
    }
    setSending(false);
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

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={[
            styles.messageList,
            messages.length === 0 && styles.emptyMessageList,
          ]}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          ListEmptyComponent={
            <View style={styles.welcome}>
              <Text style={styles.welcomeTitle}>How can I help with {farm.name}?</Text>
              <Text style={styles.welcomeText}>
                Ask anything about your {farm.crop.toLowerCase()} crop, irrigation timing, fertilizer application, upcoming tasks, or recent weather alerts.
              </Text>
            </View>
          }
          renderItem={({ item }) => {
            const isUser = item.sender_type === 'farmer';
            return (
              <View
                style={[
                  styles.messageRow,
                  isUser ? styles.messageRowUser : styles.messageRowAssistant,
                ]}
              >
                <View
                  style={[
                    styles.messageBubble,
                    isUser ? styles.userBubble : styles.assistantBubble,
                  ]}
                >
                  <Text style={isUser ? styles.userMessageText : styles.assistantMessageText}>
                    {item.message}
                  </Text>
                  <Text style={styles.timestamp}>
                    {new Date(item.created_at).toLocaleTimeString([], {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>
              </View>
            );
          }}
          ListFooterComponent={
            sending ? (
              <View style={[styles.messageRow, styles.messageRowAssistant]}>
                <View style={[styles.messageBubble, styles.assistantBubble]}>
                  <ActivityIndicator size="small" color={COLORS.primary} />
                </View>
              </View>
            ) : null
          }
        />
      )}

      <View style={styles.composerArea}>
        <View style={styles.composer}>
          <TextInput
            accessibilityLabel="Message"
            style={styles.messageInput}
            placeholder={`Message AI Farm Manager for ${farm.name}`}
            placeholderTextColor={COLORS.textSecondary}
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
            accessibilityLabel="Send message"
            disabled={!text.trim() || sending}
            onPress={send}
            style={({ pressed }) => [
              styles.sendButton,
              (!text.trim() || sending) && styles.sendButtonDisabled,
              pressed && styles.sendButtonPressed,
            ]}
          >
            <Text style={styles.sendButtonText}>↑</Text>
          </Pressable>
        </View>
        <Text style={styles.disclaimer}>FieldShift AI Assistant · Grounded in farm state and agronomic knowledge</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.surface,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  messageList: {
    flexGrow: 1,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  emptyMessageList: {
    justifyContent: 'center',
  },
  welcome: {
    alignSelf: 'center',
    width: '100%',
    maxWidth: 560,
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
  },
  welcomeTitle: {
    ...TYPOGRAPHY.h2,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  welcomeText: {
    ...TYPOGRAPHY.bodySecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  messageRow: {
    width: '100%',
    maxWidth: 760,
    alignSelf: 'center',
    marginBottom: SPACING.md,
  },
  messageRowUser: {
    alignItems: 'flex-end',
  },
  messageRowAssistant: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '85%',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.lg,
  },
  userBubble: {
    backgroundColor: '#edf1ed',
    borderBottomRightRadius: SPACING.xs,
  },
  assistantBubble: {
    backgroundColor: '#f4f6f4',
    borderWidth: 1,
    borderColor: '#e0e6e0',
    borderBottomLeftRadius: SPACING.xs,
  },
  userMessageText: {
    ...TYPOGRAPHY.body,
    lineHeight: 22,
    color: COLORS.text,
  },
  assistantMessageText: {
    ...TYPOGRAPHY.body,
    lineHeight: 22,
    color: '#1a331a',
  },
  timestamp: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
    textAlign: 'right',
    color: COLORS.textSecondary,
  },
  composerArea: {
    width: '100%',
    maxWidth: 800,
    alignSelf: 'center',
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.sm,
    paddingBottom: SPACING.xs,
  },
  composer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: SPACING.md,
    paddingRight: SPACING.xs,
    paddingVertical: SPACING.xs,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.xl,
    backgroundColor: COLORS.surface,
  },
  messageInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 128,
    paddingTop: SPACING.sm,
    paddingBottom: SPACING.sm,
    paddingRight: SPACING.sm,
    ...TYPOGRAPHY.body,
    color: COLORS.text,
  },
  sendButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: BORDER_RADIUS.round,
    backgroundColor: COLORS.primary,
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.border,
  },
  sendButtonPressed: {
    opacity: 0.75,
  },
  sendButtonText: {
    color: COLORS.surface,
    fontSize: 24,
    lineHeight: 28,
    fontWeight: '600',
  },
  disclaimer: {
    ...TYPOGRAPHY.caption,
    textAlign: 'center',
    paddingTop: SPACING.xs,
  },
  notFound: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  notFoundText: {
    ...TYPOGRAPHY.bodySecondary,
  },
});
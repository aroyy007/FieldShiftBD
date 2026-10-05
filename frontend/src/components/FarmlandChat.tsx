import { useEffect, useRef, useState } from 'react';
import {
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
import { ChatMessage } from '../data/demo';
import { BORDER_RADIUS, COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

export function FarmlandChat() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands, conversations, activeConversationIds, createConversation, addChatMessage } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const activeConversationId = farmId ? activeConversationIds[farmId] : undefined;
  const conversation = farmId && activeConversationId
    ? conversations[farmId]?.find(item => item.id === activeConversationId)
    : undefined;
  const messages = conversation?.messages ?? [];
  const [text, setText] = useState('');
  const listRef = useRef<FlatList<ChatMessage>>(null);

  useEffect(() => {
    listRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

  const send = () => {
    const message = text.trim();
    if (!message || !farmId) return;

    const conversationId = conversation?.id ?? createConversation(farmId);
    addChatMessage(farmId, conversationId, message);
    setText('');
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
              Start a conversation about your {farm.crop.toLowerCase()} farm. Messages are saved in this demo session; assistant replies will be available when the backend is connected.
            </Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.messageRow}>
            <View style={styles.userMessage}>
              <Text style={styles.messageText}>{item.text}</Text>
              <Text style={styles.timestamp}>{item.timestamp}</Text>
            </View>
          </View>
        )}
      />

      <View style={styles.composerArea}>
        <View style={styles.composer}>
          <TextInput
            accessibilityLabel="Message"
            style={styles.messageInput}
            placeholder={`Message ${farm.name}`}
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
            disabled={!text.trim()}
            onPress={send}
            style={({ pressed }) => [
              styles.sendButton,
              !text.trim() && styles.sendButtonDisabled,
              pressed && styles.sendButtonPressed,
            ]}
          >
            <Text style={styles.sendButtonText}>↑</Text>
          </Pressable>
        </View>
        <Text style={styles.disclaimer}>FieldShift demo chat · Replies are not generated yet</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.surface,
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
    alignItems: 'flex-end',
    marginBottom: SPACING.md,
  },
  userMessage: {
    maxWidth: '92%',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.xl,
    backgroundColor: '#edf1ed',
  },
  messageText: {
    ...TYPOGRAPHY.body,
    lineHeight: 24,
  },
  timestamp: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
    textAlign: 'right',
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

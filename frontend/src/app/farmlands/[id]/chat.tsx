import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Button, Input } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY, BORDER_RADIUS } from '../../../theme/theme';

export default function Chat() {
  const { id } = useLocalSearchParams();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);
  const [messages, setMessages] = useState(farm?.chat || []);
  const [text, setText] = useState('');

  const send = () => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { id: Math.random().toString(), text, sender: 'farmer' as const, timestamp: 'Now' }]);
    setText('');
    setTimeout(() => {
      setMessages(prev => [...prev, { id: Math.random().toString(), text: 'I am analyzing your request...', sender: 'assistant' as const, timestamp: 'Now' }]);
    }, 1000);
  };

  if (!farm) return null;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <FlatList
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.sender === 'farmer' ? styles.bubbleFarmer : styles.bubbleAssistant]}>
              <Text style={[styles.messageText, item.sender === 'farmer' && { color: COLORS.surface }]}>{item.text}</Text>
              <Text style={[styles.time, item.sender === 'farmer' && { color: '#e0e0e0' }]}>{item.timestamp}</Text>
            </View>
          )}
        />
        <View style={styles.inputArea}>
          <Input style={styles.input} placeholder="Type a message..." value={text} onChangeText={setText} />
          <Button title="Send" onPress={send} style={styles.sendBtn} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flex: 1 },
  list: { padding: SPACING.md },
  bubble: { maxWidth: '80%', padding: SPACING.md, borderRadius: BORDER_RADIUS.lg, marginBottom: SPACING.sm },
  bubbleFarmer: { backgroundColor: COLORS.primary, alignSelf: 'flex-end', borderBottomRightRadius: 0 },
  bubbleAssistant: { backgroundColor: COLORS.surface, alignSelf: 'flex-start', borderBottomLeftRadius: 0 },
  messageText: { ...TYPOGRAPHY.body },
  time: { ...TYPOGRAPHY.caption, alignSelf: 'flex-end', marginTop: SPACING.xs },
  inputArea: { flexDirection: 'row', padding: SPACING.md, backgroundColor: COLORS.surface, borderTopWidth: 1, borderColor: COLORS.border },
  input: { flex: 1, marginBottom: 0, marginRight: SPACING.sm },
  sendBtn: { paddingHorizontal: SPACING.lg },
});
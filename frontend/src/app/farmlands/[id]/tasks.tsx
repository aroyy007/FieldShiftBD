import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function Tasks() {
  const { id } = useLocalSearchParams();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);
  const [tasks, setTasks] = useState(farm?.tasks || []);

  if (!farm) return null;

  const toggleTask = (taskId: string) => {
    setTasks(tasks.map(t => t.id === taskId ? { ...t, completed: !t.completed } : t));
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <FlatList
        data={tasks}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.empty}>No tasks scheduled.</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => toggleTask(item.id)}>
            <Card style={item.completed ? styles.completedCard : undefined}>
              <View style={styles.row}>
                <Text style={[styles.taskTitle, item.completed && styles.completedText]}>{item.title}</Text>
                <View style={[styles.checkbox, item.completed && styles.checked]} />
              </View>
              <Text style={styles.date}>Scheduled: {item.date}</Text>
            </Card>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  completedCard: { opacity: 0.7 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  taskTitle: { ...TYPOGRAPHY.h3, flex: 1 },
  completedText: { textDecorationLine: 'line-through', color: COLORS.textSecondary },
  checkbox: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: COLORS.primary },
  checked: { backgroundColor: COLORS.primary },
  date: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs, color: COLORS.textSecondary },
  empty: { textAlign: 'center', marginTop: SPACING.xl, ...TYPOGRAPHY.bodySecondary },
});
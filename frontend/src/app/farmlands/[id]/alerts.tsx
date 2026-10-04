import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function Alerts() {
  const { id } = useLocalSearchParams();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);

  if (!farm) return null;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <FlatList
        data={farm.alerts}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.empty}>No alerts for this farm.</Text>}
        renderItem={({ item }) => (
          <Card style={[styles.card, item.severity === 'high' ? styles.high : styles.medium]}>
            <Text style={styles.title}>{item.title}</Text>
            <View style={styles.row}>
              <Text style={styles.severity}>Severity: {item.severity.toUpperCase()}</Text>
              <Text style={styles.date}>{item.date}</Text>
            </View>
          </Card>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { borderLeftWidth: 4 },
  high: { borderLeftColor: COLORS.error },
  medium: { borderLeftColor: COLORS.warning },
  title: { ...TYPOGRAPHY.h3, marginBottom: SPACING.sm },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  severity: { ...TYPOGRAPHY.caption, fontWeight: 'bold' },
  date: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  empty: { textAlign: 'center', marginTop: SPACING.xl, ...TYPOGRAPHY.bodySecondary },
});
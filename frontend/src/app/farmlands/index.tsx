import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAppContext } from '../../context/AppProvider';
import { Button, Card } from '../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';
import { Farmland } from '../../data/demo';

export default function AllFarmlands() {
  const { user, farmlands, logout } = useAppContext();
  const router = useRouter();

  if (!user) return null;

  const renderFarmland = ({ item }: { item: Farmland }) => (
    <TouchableOpacity onPress={() => router.push(`/farmlands/${item.id}` as any)}>
      <Card>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <Text style={styles.cardDetail}>Crop: {item.crop}</Text>
        <Text style={styles.cardDetail}>Acreage: {item.acreage} acres</Text>
        <Text style={styles.cardDetail}>Stage: {item.growthStage}</Text>
        <View style={styles.cardFooter}>
        <Text style={styles.footerText}>{item.tasks.filter(t => t.status === 'pending').length} pending tasks</Text>
          <Text style={styles.footerText}>{item.alerts.length} alerts</Text>
        </View>
      </Card>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello,</Text>
          <Text style={styles.userName}>{user.name}</Text>
        </View>
        <Button title="Logout" variant="outline" onPress={() => { logout(); router.replace('/auth/login' as any); }} />
      </View>
      <FlatList
        data={farmlands}
        keyExtractor={(item) => item.id}
        renderItem={renderFarmland}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.emptyText}>No farmlands added yet.</Text>}
      />
      <View style={styles.addButtonWrapper}>
        <Button title="Add New Farmland" onPress={() => router.push('/farmlands/add' as any)} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: SPACING.md, backgroundColor: COLORS.surface, marginBottom: SPACING.sm,
  },
  greeting: { ...TYPOGRAPHY.bodySecondary },
  userName: { ...TYPOGRAPHY.h2, color: COLORS.primary },
  list: { padding: SPACING.md },
  cardTitle: { ...TYPOGRAPHY.h3, marginBottom: SPACING.xs },
  cardDetail: { ...TYPOGRAPHY.body, marginBottom: SPACING.xs },
  cardFooter: {
    flexDirection: 'row', justifyContent: 'space-between',
    marginTop: SPACING.sm, paddingTop: SPACING.sm,
    borderTopWidth: 1, borderColor: COLORS.border,
  },
  footerText: { ...TYPOGRAPHY.caption, fontWeight: 'bold', color: COLORS.warning },
  emptyText: { textAlign: 'center', marginTop: SPACING.xl, ...TYPOGRAPHY.bodySecondary },
  addButtonWrapper: { padding: SPACING.md },
});

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Href, Stack, useLocalSearchParams, usePathname, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FarmlandSidebar } from '../../../components/FarmlandSidebar';
import { useAppContext } from '../../../context/AppProvider';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function FarmlandDetailLayout() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const pathname = usePathname();
  const { width } = useWindowDimensions();
  const isWide = width >= 820;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const {
    farmlands,
    conversations,
    activeConversationIds,
    createConversation,
    selectConversation,
  } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const farmConversations = farmId ? conversations[farmId] ?? [] : [];
  const activeConversationId = farmId ? activeConversationIds[farmId] : undefined;
  const activeSection = pathname.endsWith('/alerts')
    ? 'alerts'
    : pathname.endsWith('/tasks')
      ? 'tasks'
      : pathname.endsWith('/check-ins')
        ? 'check-ins'
        : pathname.endsWith('/problems')
          ? 'problems'
          : pathname.endsWith('/season-plan')
            ? 'season-plan'
            : pathname.endsWith('/crop-health')
              ? 'crop-health'
              : pathname.endsWith('/crop-advisor')
                ? 'crop-advisor'
                : farmId && pathname === `/farmlands/${farmId}`
                  ? 'overview'
                  : 'chat';

  const openSection = (section: 'overview' | 'chat' | 'alerts' | 'tasks' | 'check-ins' | 'problems' | 'season-plan' | 'crop-health' | 'crop-advisor') => {
    if (!farmId) return;
    setDrawerOpen(false);
    const path = section === 'overview' ? `/farmlands/${farmId}` : `/farmlands/${farmId}/${section}`;
    router.replace(path as Href);
  };

  const openNewChat = () => {
    if (!farmId) return;
    createConversation(farmId);
    openSection('chat');
  };

  const openConversation = (conversationId: string) => {
    if (!farmId) return;
    selectConversation(farmId, conversationId);
    openSection('chat');
  };

  const sidebar = farm ? (
    <FarmlandSidebar
      farm={farm}
      conversations={farmConversations}
      activeConversationId={activeConversationId}
      activeSection={activeSection}
      onNewChat={openNewChat}
      onSelectSection={openSection}
      onSelectConversation={openConversation}
      onBackToFarmlands={() => {
        setDrawerOpen(false);
        router.replace('/farmlands' as Href);
      }}
    />
  ) : null;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.row}>
        {isWide && sidebar}
        <View style={styles.main}>
          <View style={styles.header}>
            {!isWide && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Open farmland menu"
                onPress={() => setDrawerOpen(true)}
                style={styles.menuButton}
              >
                <Text style={styles.menuText}>☰</Text>
              </Pressable>
            )}
            <View style={styles.headerText}>
              <Text numberOfLines={1} style={styles.headerTitle}>
                {farm?.name ?? 'Farmland'}
              </Text>
              <Text numberOfLines={1} style={styles.headerSubtitle}>
                {farm ? `${farm.crop} · ${farm.acreage} acres` : ''}
              </Text>
            </View>
          </View>
          <Stack screenOptions={{ headerShown: false }} />
        </View>
        {!isWide && drawerOpen && sidebar && (
          <View style={styles.drawerLayer}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Close farmland menu"
              onPress={() => setDrawerOpen(false)}
              style={styles.drawerBackdrop}
            />
            <View style={styles.drawer}>{sidebar}</View>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.surface,
  },
  row: {
    flex: 1,
    flexDirection: 'row',
  },
  main: {
    flex: 1,
    minWidth: 0,
  },
  header: {
    minHeight: 58,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  menuButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.sm,
    borderRadius: 21,
  },
  menuText: {
    color: COLORS.text,
    fontSize: 20,
  },
  headerText: {
    flex: 1,
    minWidth: 0,
  },
  headerTitle: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  headerSubtitle: {
    ...TYPOGRAPHY.caption,
    marginTop: 2,
  },
  drawerLayer: {
    ...StyleSheet.absoluteFill,
    zIndex: 5,
    flexDirection: 'row',
  },
  drawerBackdrop: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
  },
  drawer: {
    width: 280,
    height: '100%',
  },
});

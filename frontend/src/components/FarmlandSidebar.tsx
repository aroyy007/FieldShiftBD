import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { ChatThread, Farmland } from '../data/demo';
import { BORDER_RADIUS, COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

type Section = 'chat' | 'alerts' | 'tasks' | 'season-plan' | 'crop-health';

type FarmlandSidebarProps = {
  farm: Farmland;
  conversations: ChatThread[];
  activeConversationId?: string;
  activeSection: Section;
  onNewChat: () => void;
  onSelectSection: (section: Section) => void;
  onSelectConversation: (conversationId: string) => void;
  onBackToFarmlands: () => void;
};

const SECTIONS: { id: Exclude<Section, 'chat'>; title: string }[] = [
  { id: 'alerts', title: 'Alerts' },
  { id: 'tasks', title: 'Daily Tasks' },
  { id: 'season-plan', title: 'Season Plan' },
  { id: 'crop-health', title: 'Crop Health' },
];

export function FarmlandSidebar({
  farm,
  conversations,
  activeConversationId,
  activeSection,
  onNewChat,
  onSelectSection,
  onSelectConversation,
  onBackToFarmlands,
}: FarmlandSidebarProps) {
  return (
    <View style={styles.sidebar}>
      <TouchableOpacity
        accessibilityRole="button"
        onPress={onBackToFarmlands}
        style={styles.backButton}
      >
        <Text style={styles.backText}>‹  All farmlands</Text>
      </TouchableOpacity>

      <View style={styles.farmHeading}>
        <Text style={styles.brand}>FieldShift</Text>
        <Text style={styles.farmName} numberOfLines={1}>{farm.name}</Text>
        <Text style={styles.farmDetails} numberOfLines={1}>{farm.crop} · {farm.acreage} acres</Text>
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        onPress={onNewChat}
        style={styles.newChatButton}
      >
        <Text style={styles.newChatText}>＋  New Chat</Text>
      </TouchableOpacity>

      <View style={styles.sectionList}>
        {SECTIONS.map(section => (
          <TouchableOpacity
            key={section.id}
            accessibilityRole="button"
            accessibilityState={{ selected: activeSection === section.id }}
            onPress={() => onSelectSection(section.id)}
            style={[styles.navItem, activeSection === section.id && styles.navItemActive]}
          >
            <Text style={[styles.navText, activeSection === section.id && styles.navTextActive]}>
              {section.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.historyHeading}>Chat history</Text>
      <ScrollView
        style={styles.history}
        contentContainerStyle={styles.historyContent}
        keyboardShouldPersistTaps="handled"
      >
        {conversations.length === 0 ? (
          <Text style={styles.emptyHistory}>Your conversations will appear here.</Text>
        ) : (
          conversations.map(conversation => (
            <TouchableOpacity
              key={conversation.id}
              accessibilityRole="button"
              accessibilityState={{ selected: activeConversationId === conversation.id }}
              onPress={() => onSelectConversation(conversation.id)}
              style={[
                styles.historyItem,
                activeConversationId === conversation.id && styles.navItemActive,
              ]}
            >
              <Text
                numberOfLines={2}
                style={[
                  styles.navText,
                  activeConversationId === conversation.id && styles.navTextActive,
                ]}
              >
                {conversation.title}
              </Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  sidebar: {
    width: 280,
    flex: 1,
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.md,
    paddingBottom: SPACING.lg,
    backgroundColor: '#edf1ed',
    borderRightWidth: 1,
    borderRightColor: COLORS.border,
  },
  backButton: {
    minHeight: 44,
    justifyContent: 'center',
    marginBottom: SPACING.md,
  },
  backText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
  },
  farmHeading: {
    marginBottom: SPACING.lg,
  },
  brand: {
    ...TYPOGRAPHY.h3,
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  farmName: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  farmDetails: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
  },
  newChatButton: {
    minHeight: 48,
    justifyContent: 'center',
    paddingHorizontal: SPACING.md,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    backgroundColor: COLORS.surface,
  },
  newChatText: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    color: COLORS.text,
  },
  sectionList: {
    gap: SPACING.xs,
  },
  navItem: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  navItemActive: {
    backgroundColor: '#dce7dd',
  },
  navText: {
    ...TYPOGRAPHY.body,
    fontSize: 15,
    color: COLORS.text,
  },
  navTextActive: {
    color: COLORS.primaryDark,
    fontWeight: '600',
  },
  historyHeading: {
    ...TYPOGRAPHY.caption,
    fontWeight: '600',
    marginTop: SPACING.lg,
    marginBottom: SPACING.xs,
    paddingHorizontal: SPACING.md,
    textTransform: 'uppercase',
  },
  history: {
    flex: 1,
  },
  historyContent: {
    gap: SPACING.xs,
  },
  historyItem: {
    minHeight: 42,
    justifyContent: 'center',
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  emptyHistory: {
    ...TYPOGRAPHY.caption,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
});

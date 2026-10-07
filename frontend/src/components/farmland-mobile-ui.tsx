import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Href, useRouter } from 'expo-router';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { DashboardIcon, DashboardIconName } from './dashboard-icons';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';

export type FarmHeaderAction = 'filters' | 'plus' | 'save';

export function FarmPageHeader({
  title,
  subtitle,
  actionLabel,
  actionIcon,
  onAction,
  subtitleLines = 1,
  backHref = '/farmlands',
}: {
  title: string;
  subtitle: string;
  actionLabel: string;
  actionIcon: FarmHeaderAction;
  onAction: () => void;
  subtitleLines?: 1 | 2;
  backHref?: Href;
}) {
  const router = useRouter();

  return (
    <View style={[styles.header, subtitleLines === 2 && styles.headerTall]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Go back"
        onPress={() => router.canGoBack() ? router.back() : router.replace(backHref)}
        style={styles.headerButton}
      >
        <FarmChromeIcon name="back" size={22} color={INK} />
      </Pressable>
      <View style={styles.headerCopy}>
        <Text numberOfLines={1} style={styles.headerTitle}>{title}</Text>
        <Text numberOfLines={subtitleLines} style={styles.headerSubtitle}>{subtitle}</Text>
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={actionLabel}
        onPress={onAction}
        style={[styles.headerButton, styles.actionButton]}
      >
        <FarmChromeIcon name={actionIcon} size={22} color={GREEN} />
      </Pressable>
    </View>
  );
}

export function FarmBottomNavigation({
  active = 'Home',
  farmId,
  compact = false,
}: {
  active?: 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile';
  farmId?: string;
  compact?: boolean;
}) {
  const router = useRouter();
  const items: { label: 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile'; icon: DashboardIconName; href: Href }[] = [
    { label: 'Home', icon: 'home', href: '/farmlands' },
    { label: 'Tasks', icon: 'tasks', href: (farmId ? `/farmlands/${farmId}/tasks` : '/farmlands') as Href },
    { label: 'Chat', icon: 'chat', href: (farmId ? `/farmlands/${farmId}/chat` : '/farmlands') as Href },
    { label: 'Scan', icon: 'scan', href: (farmId ? `/farmlands/${farmId}/crop-health` : '/farmlands') as Href },
    { label: 'Profile', icon: 'profile', href: '/farmlands/profile-setup' },
  ];

  return (
    <View style={[styles.bottomNav, compact && styles.bottomNavCompact]}>
      {items.map(item => {
        const selected = item.label === active;
        return (
          <Pressable
            key={item.label}
            accessibilityRole="button"
            accessibilityLabel={item.label}
            accessibilityState={{ selected }}
            onPress={() => router.push(item.href)}
            style={[styles.navButton, compact && styles.navButtonCompact]}
          >
            <View style={[styles.navIconWrap, selected && styles.navIconSelected]}>
              <DashboardIcon name={item.icon} size={selected ? 22 : 23} color={selected ? GREEN : MUTED} />
            </View>
            <Text style={[styles.navLabel, selected && styles.navLabelSelected]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function FarmChromeIcon({ name, size = 22, color = GREEN }: { name: FarmHeaderAction | 'back' | 'search' | 'close' | 'chevron'; size?: number; color?: string }) {
  const stroke = { fill: 'none', stroke: color, strokeWidth: 1.9, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'back' ? <Path d="m15 18-6-6 6-6" {...stroke} strokeWidth="2.2" /> : null}
      {name === 'filters' ? <>
        <Path d="M4 6h16M4 12h16M4 18h16" {...stroke} />
        <Circle cx="9" cy="6" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
        <Circle cx="15" cy="12" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
        <Circle cx="8" cy="18" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
      </> : null}
      {name === 'plus' ? <Path d="M12 5v14M5 12h14" {...stroke} strokeWidth="2.3" /> : null}
      {name === 'save' ? <>
        <Rect x="4" y="3.5" width="16" height="17" rx="2.5" fill={color} stroke={color} strokeWidth="1.4" />
        <Path d="m8 12 2.8 2.8L17 8.5" fill="none" stroke={PAPER} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === 'search' ? <>
        <Circle cx="10.5" cy="10.5" r="6.5" {...stroke} strokeWidth="2.2" />
        <Path d="m15.5 15.5 5 5" {...stroke} strokeWidth="2.2" />
      </> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'close' ? <Path d="m6 6 12 12M18 6 6 18" {...stroke} strokeWidth="2.2" /> : null}
    </Svg>
  );
}

const styles = StyleSheet.create({
  header: {
    minHeight: 64,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: PAPER,
    borderBottomWidth: 1,
    borderBottomColor: '#ebe9df',
  },
  headerTall: { minHeight: 80, paddingVertical: 8 },
  headerButton: {
    width: 40,
    height: 40,
    flexShrink: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 22,
    backgroundColor: '#f1f0e8',
  },
  actionButton: { backgroundColor: '#eaf2e6' },
  headerCopy: { flex: 1, minWidth: 0, alignItems: 'center', paddingHorizontal: 4 },
  headerTitle: { color: '#101820', fontFamily: 'Georgia', fontSize: 20, lineHeight: 25, fontWeight: '700' },
  headerSubtitle: { color: MUTED, fontSize: 11, lineHeight: 14, marginTop: 1, textAlign: 'center' },
  bottomNav: {
    minHeight: 63,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 5,
    paddingTop: 5,
    borderTopWidth: 1,
    borderTopColor: '#ebe9df',
    backgroundColor: PAPER,
  },
  bottomNavCompact: {
    minHeight: 52,
    paddingTop: 2,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    boxShadow: '0px -2px 8px rgba(30, 54, 37, 0.06)',
  },
  navButton: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2, minHeight: 56 },
  navButtonCompact: { minHeight: 46, gap: 1 },
  navIconWrap: { width: 34, height: 31, alignItems: 'center', justifyContent: 'center' },
  navIconSelected: { width: 34, height: 31, borderRadius: 8, backgroundColor: '#edf3e8' },
  navLabel: { color: MUTED, fontSize: 11, lineHeight: 14 },
  navLabelSelected: { color: GREEN, fontWeight: '700' },
});

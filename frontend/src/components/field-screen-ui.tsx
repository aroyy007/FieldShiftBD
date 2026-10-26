import React from 'react';
import { Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Href, useRouter } from 'expo-router';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';

export type FieldIconName =
  | 'back' | 'history' | 'filters' | 'leaf' | 'sprout' | 'droplet' | 'weeds'
  | 'note' | 'location' | 'rice' | 'camera' | 'trash' | 'chevron' | 'check'
  | 'home' | 'tasks' | 'chat' | 'scan' | 'profile' | 'cloudRain' | 'warning'
  | 'clock' | 'link' | 'calendar' | 'list' | 'plus' | 'close' | 'checkCircle' | 'save';

export function FieldIcon({ name, size = 20, color = GREEN }: { name: FieldIconName; size?: number; color?: string }) {
  const stroke = { fill: 'none', stroke: color, strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'back' ? <Path d="m15 18-6-6 6-6" {...stroke} strokeWidth={2.2} /> : null}
      {name === 'history' ? <>
        <Rect x="4" y="5" width="16" height="16" rx="2.5" {...stroke} />
        <Path d="M8 3v4M16 3v4M4 9h16M12 12v3l2 1" {...stroke} />
        <Circle cx="12" cy="15" r="4" {...stroke} />
      </> : null}
      {name === 'filters' ? <>
        <Path d="M4 6h16M4 12h16M4 18h16" {...stroke} />
        <Circle cx="9" cy="6" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
        <Circle cx="15" cy="12" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
        <Circle cx="8" cy="18" r="2" fill={PAPER} stroke={color} strokeWidth="1.8" />
      </> : null}
      {name === 'leaf' ? <>
        <Path d="M19.5 4.5C10 4.5 5 8 5 14a5 5 0 0 0 5 5c6 0 9.5-5 9.5-14.5Z" fill={color} stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
        <Path d="M4 21c3-5 6.5-8 11-11" fill="none" stroke={PAPER} strokeWidth="1.3" strokeLinecap="round" />
      </> : null}
      {name === 'sprout' ? <>
        <Path d="M12 21v-9M12 14c-4-.2-6-2.1-6.4-5.8 3.8.2 6 2.1 6.4 5.8ZM12 11c.4-4 2.8-6.3 6.4-6.8-.3 4-2.4 6.4-6.4 6.8ZM7 21h10" {...stroke} />
      </> : null}
      {name === 'droplet' ? <Path d="M12 3S5.5 11 5.5 15.4a6.5 6.5 0 0 0 13 0C18.5 11 12 3 12 3Z" {...stroke} fill={color} stroke={color} strokeWidth="1.4" /> : null}
      {name === 'weeds' ? <>
        <Path d="M12 21V7M12 15c-3.7-1.3-5.3-3.8-5-7.2 3.3 1.3 4.9 3.5 5 7.2ZM12 12c.3-3.6 2.2-5.9 5.5-7.1.4 3.5-1.4 5.9-5.5 7.1ZM7.5 21c-1.7-1.3-2.3-3.2-2-5.5 2.3 1 3.6 2.5 3.8 4.9M16.5 21c1.7-1.3 2.3-3.2 2-5.5-2.3 1-3.6 2.5-3.8 4.9" {...stroke} />
      </> : null}
      {name === 'note' ? <>
        <Path d="M6 3h9l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" {...stroke} />
        <Path d="M14 3v5h5M8 12h8M8 16h8" {...stroke} />
      </> : null}
      {name === 'location' ? <>
        <Path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" fill={color} stroke={color} strokeWidth="1.3" />
        <Circle cx="12" cy="10" r="2.2" fill={PAPER} stroke={PAPER} strokeWidth="1" />
      </> : null}
      {name === 'rice' ? <>
        <Path d="M5 21c0-5 1.3-10.5 4-16M12 21c-.1-6.5.2-12 1-18M19 21c0-5-1.2-10.5-4-16" {...stroke} strokeWidth="2.2" />
      </> : null}
      {name === 'camera' ? <>
        <Path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" {...stroke} />
        <Circle cx="12" cy="13" r="3.3" {...stroke} />
      </> : null}
      {name === 'trash' ? <>
        <Path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" {...stroke} />
      </> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'check' ? <Path d="m5 12 4.5 4.5L19 7" {...stroke} strokeWidth="2.4" /> : null}
      {name === 'home' ? <Path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1Z" {...stroke} strokeWidth="1.8" /> : null}
      {name === 'tasks' ? <>
        <Rect x="4" y="4" width="16" height="17" rx="2.5" {...stroke} />
        <Path d="m7.5 12 3 3 6-6" {...stroke} />
      </> : null}
      {name === 'chat' ? <>
        <Path d="M5 5h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-8l-6 3v-5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" {...stroke} />
        <Circle cx="8.5" cy="11.5" r=".7" fill={color} /><Circle cx="12" cy="11.5" r=".7" fill={color} /><Circle cx="15.5" cy="11.5" r=".7" fill={color} />
      </> : null}
      {name === 'scan' ? <Path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'profile' ? <>
        <Circle cx="12" cy="7.5" r="4" {...stroke} />
        <Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" {...stroke} />
      </> : null}
      {name === 'cloudRain' ? <>
        <Path d="M6 15.5h12a4 4 0 0 0 .2-8 6.4 6.4 0 0 0-12.1 1.3A3.6 3.6 0 0 0 6 15.5Z" {...stroke} />
        <Path d="m8 18-1 2M13 18l-1 2M18 18l-1 2" {...stroke} />
      </> : null}
      {name === 'warning' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="M12 7v6M12 17h.01" {...stroke} strokeWidth="2.3" />
      </> : null}
      {name === 'clock' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="M12 7v5l3.5 2" {...stroke} />
      </> : null}
      {name === 'link' ? <Path d="M10 13.5 8.5 15a3.5 3.5 0 0 1-5-5l3-3a3.5 3.5 0 0 1 5 0M14 10.5l1.5-1.5a3.5 3.5 0 0 1 5 5l-3 3a3.5 3.5 0 0 1-5 0M9 15l6-6" {...stroke} /> : null}
      {name === 'calendar' ? <>
        <Rect x="3.5" y="5" width="17" height="16" rx="2.5" {...stroke} />
        <Path d="M7.5 3v4M16.5 3v4M4 9h16M8 13h2M14 13h2M8 17h2" {...stroke} />
      </> : null}
      {name === 'list' ? <>
        <Path d="M9 6h11M9 12h11M9 18h11" {...stroke} />
        <Circle cx="4.5" cy="6" r=".7" fill={color} /><Circle cx="4.5" cy="12" r=".7" fill={color} /><Circle cx="4.5" cy="18" r=".7" fill={color} />
      </> : null}
      {name === 'plus' ? <Path d="M12 5v14M5 12h14" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'close' ? <Path d="m6 6 12 12M18 6 6 18" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'checkCircle' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="m7.5 12 3 3 6-6" {...stroke} strokeWidth="2.1" />
      </> : null}
      {name === 'save' ? <>
        <Path d="M4 3h13l4 4v14H3V3Z" {...stroke} />
        <Path d="M7 3v6h10V3M7 21v-7h10v7" {...stroke} />
      </> : null}
    </Svg>
  );
}

export function FieldScreenHeader({
  title,
  subtitle,
  actionLabel,
  actionIcon,
  onAction,
  backHref = '/farmlands',
}: {
  title: string;
  subtitle: string;
  actionLabel: string;
  actionIcon: FieldIconName;
  onAction: () => void;
  backHref?: Href;
}) {
  const router = useRouter();
  const { width } = useWindowDimensions();
  return (
    <View style={[styles.header, Platform.OS === 'web' && styles.headerWeb]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Go back"
        onPress={() => router.canGoBack() ? router.back() : router.replace(backHref)}
        style={styles.headerButton}
      >
        <FieldIcon name="back" size={24} color={INK} />
      </Pressable>
      <View style={styles.headerCopy}>
        <Text numberOfLines={1} style={styles.headerTitle}>{title}</Text>
        <Text numberOfLines={width < 375 ? 2 : 1} style={[styles.headerSubtitle, width < 320 ? styles.headerSubtitleNarrow : width < 375 && styles.headerSubtitleCompact]}>{subtitle}</Text>
      </View>
      <Pressable accessibilityRole="button" accessibilityLabel={actionLabel} onPress={onAction} style={[styles.headerButton, styles.headerAction]}>
        <FieldIcon name={actionIcon} size={22} color={GREEN} />
      </Pressable>
    </View>
  );
}

export function FieldBottomNav({ active, farmId }: { active: 'Tasks' | 'Scan'; farmId: string }) {
  const router = useRouter();
  const items: { label: 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile'; icon: FieldIconName; href: Href }[] = [
    { label: 'Home', icon: 'home', href: '/farmlands' },
    { label: 'Tasks', icon: 'tasks', href: `/farmlands/${farmId}/tasks` as Href },
    { label: 'Chat', icon: 'chat', href: `/farmlands/${farmId}/chat` as Href },
    { label: 'Scan', icon: 'scan', href: `/farmlands/${farmId}/crop-health` as Href },
    { label: 'Profile', icon: 'profile', href: '/farmlands/profile-setup' },
  ];

  return (
    <View style={styles.bottomNav}>
      {items.map(item => {
        const selected = item.label === active;
        return (
          <Pressable
            key={item.label}
            accessibilityRole="button"
            accessibilityLabel={item.label}
            accessibilityState={{ selected }}
            onPress={() => router.push(item.href)}
            style={styles.navButton}
          >
            <View style={[styles.navIconWrap, selected && active === 'Tasks' && styles.navIconSelected]}>
              <FieldIcon name={item.icon} size={selected ? 21 : 23} color={selected ? (active === 'Tasks' ? '#fffdf7' : GREEN) : MUTED} />
            </View>
            <Text style={[styles.navLabel, selected && styles.navLabelSelected]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    height: 64,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    backgroundColor: PAPER,
    borderBottomWidth: 1,
    borderBottomColor: '#ebe9df',
  },
  headerWeb: { height: 64, paddingTop: 2 },
  headerButton: {
    width: 42,
    height: 42,
    flexShrink: 0,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f1f0e8',
  },
  headerAction: { backgroundColor: '#eaf2e6' },
  headerCopy: { flex: 1, minWidth: 0, alignItems: 'center', paddingHorizontal: 4 },
  headerTitle: { color: '#101820', fontFamily: 'Georgia', fontSize: 20, lineHeight: 25, fontWeight: '700' },
  headerSubtitle: { color: MUTED, fontSize: 12, lineHeight: 16, marginTop: 1 },
  headerSubtitleCompact: { fontSize: 10, lineHeight: 13 },
  headerSubtitleNarrow: { fontSize: 9, lineHeight: 12 },
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
  navButton: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2, minHeight: 56 },
  navIconWrap: { width: 34, height: 31, alignItems: 'center', justifyContent: 'center' },
  navIconSelected: { width: 32, height: 31, borderRadius: 7, backgroundColor: GREEN },
  navLabel: { color: MUTED, fontSize: 11, lineHeight: 14 },
  navLabelSelected: { color: GREEN, fontWeight: '700' },
});

import { useEffect, useState } from 'react';
import {
  Image,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Href, useRouter } from 'expo-router';
import { useAppContext } from '../context/AppProvider';
import { ArrowRightIcon, BrandPlantIcon, FeatureIcon } from '../components/icons';
import type { FeatureIconName } from '../components/icons';

const PAPER = '#fffdf7';
const GREEN = '#07583f';
const INK = '#0a392f';
const MUTED = '#65717b';
const PALE_GREEN = '#f1f5e9';
const SERIF_FONT = Platform.select({ web: 'Georgia', default: 'serif' }) ?? 'serif';
const SANS_FONT = Platform.select({ web: 'Arial', default: 'sans-serif' }) ?? 'sans-serif';

type Language = 'en' | 'bn';

const COPY = {
  en: {
    tagline: 'AI Farmer Assistant',
    title: 'Your farm,\nguided every day',
    description: 'Get personalized crop advice, daily tasks, weather updates and detect crop problems with a simple leaf scan.',
    features: ['Crop\nadvice', 'Daily\ntasks', 'Weather\nupdates', 'Leaf\nscanning'],
    getStarted: 'Get started',
    signIn: 'I already have an account',
  },
  bn: {
    tagline: 'AI কৃষি সহকারী',
    title: 'আপনার খামার,\nপ্রতিদিনের সঙ্গী',
    description: 'ফসলের পরামর্শ, প্রতিদিনের কাজ, আবহাওয়ার খবর এবং পাতার ছবি থেকে রোগ শনাক্ত করুন সহজেই।',
    features: ['ফসলের\nপরামর্শ', 'দৈনিক\nকাজ', 'আবহাওয়ার\nখবর', 'পাতা\nস্ক্যান'],
    getStarted: 'শুরু করুন',
    signIn: 'আমার অ্যাকাউন্ট আছে',
  },
} as const;

const FEATURES: FeatureIconName[] = ['crop', 'tasks', 'weather', 'scan'];

export default function Index() {
  const { user } = useAppContext();
  const router = useRouter();
  const { width, height } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [language, setLanguage] = useState<Language>('en');
  const copy = COPY[language];
  const pageScale = Math.min(width / 393, 1);
  const availableHeight = Math.max(
    height - (Platform.OS === 'web' ? 0 : insets.top + insets.bottom),
    1,
  );
  const compactPageStyle = pageScale < 1 ? {
    width: width / pageScale,
    maxWidth: width / pageScale,
    height: availableHeight / pageScale,
    flexGrow: 0,
    flexShrink: 0,
    alignSelf: 'flex-start' as const,
    marginLeft: -(width / pageScale - width) / 2,
    marginTop: -(availableHeight / pageScale - availableHeight) / 2,
    transform: [{ scale: pageScale }],
  } : undefined;

  useEffect(() => {
    if (user) router.replace('/farmlands' as Href);
  }, [router, user]);

  const screenContent = (
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={false}
        scrollEnabled={pageScale === 1}
      >
        <View style={[styles.page, compactPageStyle]}>
          <View style={styles.mainContent}>
            <View style={styles.introGroup}>
              <View style={styles.header}>
                <View style={styles.brand}>
                  <BrandPlantIcon />
                  <View style={styles.brandCopy}>
                    <Text style={styles.brandName}>FieldShift BD</Text>
                    <Text style={styles.brandTagline}>{copy.tagline}</Text>
                  </View>
                </View>

                <View style={styles.languageSwitch} accessibilityRole="radiogroup" accessibilityLabel="Language">
                  <Pressable
                    accessibilityRole="radio"
                    accessibilityState={{ checked: language === 'en' }}
                    onPress={() => setLanguage('en')}
                    style={[styles.languageOption, styles.languageEnglish, language === 'en' && styles.languageSelected]}
                  >
                    <Text style={[styles.languageText, language === 'en' && styles.languageTextSelected]}>English</Text>
                  </Pressable>
                  <View style={styles.languageDivider} />
                  <Pressable
                    accessibilityRole="radio"
                    accessibilityState={{ checked: language === 'bn' }}
                    onPress={() => setLanguage('bn')}
                    style={[styles.languageOption, styles.languageBangla, language === 'bn' && styles.languageSelected]}
                  >
                    <Text style={[styles.languageText, language === 'bn' && styles.languageTextSelected]}>বাংলা</Text>
                  </Pressable>
                </View>
              </View>

              <View style={styles.heroCopy}>
                <Text style={styles.heroTitle}>{copy.title}</Text>
                <Text style={styles.heroDescription}>{copy.description}</Text>
              </View>
            </View>

            <View style={styles.photoFrame}>
              <Image source={require('../../assets/images/landing-farmer.png')} style={styles.photo} resizeMode="cover" />
            </View>

            <View style={styles.featureRow}>
              {FEATURES.map((kind, index) => (
                <View key={kind} style={styles.featureCard}>
                  <View style={styles.featureIcon}>
                    <FeatureIcon kind={kind} />
                  </View>
                  <Text style={styles.featureLabel}>{copy.features[index]}</Text>
                </View>
              ))}
            </View>

            <View style={styles.actions}>
              <Pressable
                accessibilityRole="button"
                onPress={() => router.push('/auth/signup' as Href)}
                style={({ pressed }) => [styles.primaryButton, pressed && styles.buttonPressed]}
              >
                <Text style={styles.primaryButtonText}>{copy.getStarted}</Text>
                <View style={styles.arrowBubble}>
                  <ArrowRightIcon />
                </View>
              </Pressable>

              <Pressable
                accessibilityRole="button"
                onPress={() => router.push('/auth/login' as Href)}
                style={({ pressed }) => [styles.signInButton, pressed && styles.buttonPressed]}
              >
                <Text style={styles.signInButtonText}>{copy.signIn}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </ScrollView>
  );

  return Platform.OS === 'web'
    ? <View style={styles.safeArea}>{screenContent}</View>
    : <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>{screenContent}</SafeAreaView>;
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: PAPER,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    alignItems: 'center',
  },
  page: {
    width: '100%',
    maxWidth: 480,
    flexGrow: 1,
    flexShrink: 0,
    paddingHorizontal: 16,
  },
  mainContent: {
    flexGrow: 1,
    flexShrink: 0,
    justifyContent: 'space-between',
    paddingTop: 10,
    paddingBottom: 14,
  },
  introGroup: {
    flexShrink: 0,
  },
  header: {
    minHeight: 42,
    marginHorizontal: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    transform: [{ translateY: 6 }],
  },
  brand: {
    flexShrink: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brandCopy: {
    flexShrink: 1,
  },
  brandName: {
    color: INK,
    fontFamily: SERIF_FONT,
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 23,
    letterSpacing: -0.55,
  },
  brandTagline: {
    color: MUTED,
    fontFamily: SANS_FONT,
    fontSize: 12.5,
    lineHeight: 16,
  },
  languageSwitch: {
    height: 38,
    padding: 3,
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#eeecdf',
    backgroundColor: '#fffef9',
    boxShadow: '0px 2px 8px rgba(38, 56, 46, 0.1)',
    elevation: 2,
  },
  languageOption: {
    height: 31,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 19,
  },
  languageEnglish: {
    width: 65,
  },
  languageBangla: {
    width: 51,
  },
  languageSelected: {
    backgroundColor: '#eaf1e1',
  },
  languageText: {
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 14,
    lineHeight: 20,
  },
  languageTextSelected: {
    fontWeight: '500',
  },
  languageDivider: {
    width: 1,
    height: 22,
    backgroundColor: '#e7e8dc',
  },
  heroCopy: {
    marginTop: 23,
    marginHorizontal: 8,
    transform: [{ translateY: 6 }],
  },
  heroTitle: {
    color: '#073c32',
    fontFamily: SERIF_FONT,
    fontSize: 40,
    fontWeight: '700',
    lineHeight: 41,
    letterSpacing: -1.35,
  },
  heroDescription: {
    marginTop: 8,
    color: MUTED,
    fontFamily: SANS_FONT,
    fontSize: 17.5,
    fontWeight: '400',
    lineHeight: 22,
    letterSpacing: -0.15,
  },
  photoFrame: {
    width: '100%',
    aspectRatio: 864 / 513,
    overflow: 'hidden',
    borderRadius: 22,
    backgroundColor: '#e8ecda',
  },
  photo: {
    width: '100%',
    height: '100%',
  },
  featureRow: {
    flexDirection: 'row',
    gap: 9,
  },
  featureCard: {
    flex: 1,
    minWidth: 0,
    height: 88,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 19,
    backgroundColor: PALE_GREEN,
  },
  featureIcon: {
    width: 38,
    height: 36,
    marginBottom: 5,
  },
  featureLabel: {
    color: '#102e2e',
    fontFamily: SANS_FONT,
    fontSize: 15.5,
    fontWeight: '400',
    lineHeight: 18,
    textAlign: 'center',
  },
  actions: {
    gap: 8,
  },
  primaryButton: {
    height: 47,
    borderRadius: 25,
    backgroundColor: GREEN,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  primaryButtonText: {
    color: '#fffdf7',
    fontFamily: SERIF_FONT,
    fontSize: 23,
    fontWeight: '700',
    lineHeight: 29,
  },
  arrowBubble: {
    position: 'absolute',
    right: 6,
    top: 4,
    width: 39,
    height: 39,
    borderRadius: 20,
    backgroundColor: '#fffef9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  signInButton: {
    height: 39,
    borderWidth: 1.5,
    borderColor: GREEN,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  signInButtonText: {
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 16,
    lineHeight: 21,
    textAlign: 'center',
  },
  buttonPressed: {
    opacity: 0.86,
  },
});

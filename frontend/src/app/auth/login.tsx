import React, { useState } from 'react';
import {
  Image,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useRouter } from 'expo-router';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';
import {
  ArrowRightIcon,
  BackChevronIcon,
  BrandPlantIcon,
  ChevronDownIcon,
  LockOutlineIcon,
  MobilePhoneIcon,
} from '../../components/icons';
import { useAppContext } from '../../context/AppProvider';
import { normalizeBangladeshPhone } from '../../services/farm-data';

const PAPER = '#fffdf7';
const GREEN = '#07583f';
const INK = '#0a392f';
const MUTED = '#65717b';
const PALE_GREEN = '#eef4e6';
const SERIF_FONT = Platform.select({ web: 'Georgia', default: 'serif' }) ?? 'serif';
const SANS_FONT = Platform.select({ web: 'Arial', default: 'sans-serif' }) ?? 'sans-serif';
const FOOTER_IMAGE = require('../../../assets/images/verification-rice-field.png');

export default function Login() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { width, height } = useWindowDimensions();
  const router = useRouter();
  const { login, loadError } = useAppContext();
  const compact = width < 380 || height < 660;
  const tiny = width < 330 || height < 580;
  const pageHorizontal = width < 330 ? 18 : width < 370 ? 22 : 25;
  const footerHeight = Math.max(112, Math.min(176, Math.min(width / 2.72, height * 0.2)));

  const normalizedPhone = normalizeBangladeshPhone(phone);

  const handleLogin = async () => {
    if (normalizedPhone.length < 12 || normalizedPhone.length > 16 || password.length < 12) {
      setMessage(password.length < 12 ? 'Password must be at least 12 characters.' : 'Enter a valid Bangladesh phone number.');
      return;
    }
    setIsSubmitting(true);
    try {
      await login(normalizedPhone, password);
      setMessage('');
      router.replace('/farmlands' as Href);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not sign in. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const page = (
    <View style={styles.root}>
      <Image
        accessibilityElementsHidden
        accessible={false}
        resizeMode="cover"
        source={FOOTER_IMAGE}
        style={[styles.footerImage, { height: footerHeight }]}
      />
      <Svg
        aria-hidden
        height={footerHeight}
        pointerEvents="none"
        style={styles.footerFade}
        viewBox="0 0 100 100"
        width="100%"
        preserveAspectRatio="none"
      >
        <Defs>
          <LinearGradient id="login-footer-fade" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0%" stopColor={PAPER} stopOpacity="1" />
            <Stop offset="14%" stopColor={PAPER} stopOpacity="0.92" />
            <Stop offset="43%" stopColor={PAPER} stopOpacity="0.48" />
            <Stop offset="58%" stopColor={PAPER} stopOpacity="0.1" />
            <Stop offset="70%" stopColor={PAPER} stopOpacity="0" />
          </LinearGradient>
        </Defs>
        <Rect width="100" height="100" fill="url(#login-footer-fade)" />
      </Svg>

      <ScrollView
        bounces={false}
        contentContainerStyle={styles.scrollContent}
        keyboardDismissMode="on-drag"
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        style={styles.foregroundScroll}
      >
        <View
          style={[
            styles.page,
            { paddingHorizontal: pageHorizontal },
            compact && styles.compactPage,
            tiny && styles.tinyPage,
          ]}
        >
          <View style={[styles.header, compact && styles.compactHeader, tiny && styles.tinyHeader]}>
            <Pressable
              accessibilityLabel="Go back"
              accessibilityRole="button"
              hitSlop={8}
              onPress={() => router.back()}
              style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
            >
              <BackChevronIcon size={24} />
            </Pressable>
            <View style={[styles.brand, compact && styles.compactBrand]} accessibilityLabel="FieldShift BD, AI Farmer Assistant">
              <BrandPlantIcon size={compact ? 42 : 46} />
              <View>
                <Text style={styles.brandName}>FieldShift BD</Text>
                <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
              </View>
            </View>
          </View>

          <View style={[styles.intro, compact && styles.compactIntro, tiny && styles.tinyIntro]}>
            <Text
              accessibilityRole="header"
              style={[
                styles.title,
                { fontSize: tiny ? 34 : compact ? 41 : 42, lineHeight: tiny ? 40 : compact ? 49 : 50 },
              ]}
            >
              Welcome back
            </Text>
            <Text style={[styles.subtitle, compact && styles.compactSubtitle, tiny && styles.tinySubtitle]}>
              Sign in to continue managing your farm with personalized advice.
            </Text>
          </View>

          <View style={[styles.fields, compact && styles.compactFields, tiny && styles.tinyFields]}>
            <View style={[styles.fieldCard, compact && styles.compactFieldCard, tiny && styles.tinyFieldCard]}>
              <View style={[styles.fieldIcon, compact && styles.compactFieldIcon, tiny && styles.tinyFieldIcon]}>
                <MobilePhoneIcon size={compact ? 22 : 24} />
              </View>
              <View style={styles.fieldContent}>
                <Text style={[styles.fieldLabel, compact && styles.compactFieldLabel]}>Phone number</Text>
                <View style={[styles.inputShell, compact && styles.compactInputShell]}>
                  <View
                    accessibilityLabel="Country code plus 880"
                    style={[styles.countryCode, compact && styles.compactCountryCode]}
                  >
                    <Text style={[styles.countryCodeText, compact && styles.compactInputText]}>+880</Text>
                    <ChevronDownIcon size={17} />
                  </View>
                  <View style={styles.inputDivider} />
                  <TextInput
                    accessibilityLabel="Phone number"
                    autoCapitalize="none"
                    autoComplete="tel-national"
                    autoCorrect={false}
                    keyboardType="phone-pad"
                    maxLength={18}
                    onChangeText={(value) => { setPhone(value); setMessage(''); }}
                    onSubmitEditing={() => void handleLogin()}
                    placeholder="01XXX-XXXXXX"
                    placeholderTextColor="#87919c"
                    returnKeyType="next"
                    style={[styles.input, compact && styles.compactInput, tiny && styles.tinyInput]}
                    value={phone}
                  />
                </View>
              </View>
            </View>
            <View style={[styles.fieldCard, compact && styles.compactFieldCard, tiny && styles.tinyFieldCard]}>
              <View style={[styles.fieldIcon, compact && styles.compactFieldIcon, tiny && styles.tinyFieldIcon]}>
                <LockOutlineIcon size={22} />
              </View>
              <View style={styles.fieldContent}>
                <Text style={[styles.fieldLabel, compact && styles.compactFieldLabel]}>Password</Text>
                <View style={[styles.inputShell, compact && styles.compactInputShell]}>
                  <TextInput
                    accessibilityLabel="Password"
                    autoCapitalize="none"
                    autoComplete="current-password"
                    autoCorrect={false}
                    onChangeText={(value) => { setPassword(value); setMessage(''); }}
                    onSubmitEditing={() => void handleLogin()}
                    placeholder="Enter your password"
                    placeholderTextColor="#87919c"
                    returnKeyType="go"
                    secureTextEntry
                    style={[styles.input, compact && styles.compactInput]}
                    value={password}
                  />
                </View>
              </View>
            </View>
          </View>

          {message || loadError ? <Text accessibilityRole="alert" style={styles.message}>{message || loadError}</Text> : null}

          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: isSubmitting }}
            disabled={isSubmitting}
            onPress={() => void handleLogin()}
            style={({ pressed }) => [styles.primaryButton, compact && styles.compactPrimaryButton, tiny && styles.tinyPrimaryButton, pressed && styles.pressed, isSubmitting && styles.submittingButton]}
          >
            <Svg aria-hidden height="100%" preserveAspectRatio="none" style={styles.primaryGradient} viewBox="0 0 400 60" width="100%">
              <Defs>
                <LinearGradient id="login-button-gradient" x1="0" y1="0" x2="1" y2="0">
                  <Stop offset="0%" stopColor="#226b4b" />
                  <Stop offset="100%" stopColor="#074a35" />
                </LinearGradient>
              </Defs>
              <Rect width="400" height="60" rx="30" fill="url(#login-button-gradient)" />
            </Svg>
            <Text style={styles.primaryButtonText}>{isSubmitting ? 'Signing in…' : 'Sign in'}</Text>
            <View style={[styles.arrowBubble, compact && styles.compactArrowBubble]}>
              <ArrowRightIcon size={23} color={INK} />
            </View>
          </Pressable>

          <View style={[styles.accountRow, compact && styles.compactAccountRow]}>
            <Text style={[styles.accountText, compact && styles.compactAccountText]}>
              Don’t have an account?{' '}
              <Text
                accessibilityRole="link"
                onPress={() => router.push('/auth/signup' as Href)}
                style={styles.accountLink}
              >
                Create account
              </Text>
            </Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );

  return Platform.OS === 'web'
    ? <View style={styles.safeArea}>{page}</View>
    : <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>{page}</SafeAreaView>;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: PAPER },
  root: { flex: 1, position: 'relative', backgroundColor: PAPER },
  footerImage: { position: 'absolute', left: 0, right: 0, bottom: 0, width: '100%' },
  footerFade: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  foregroundScroll: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 },
  scrollContent: { width: '100%', flexGrow: 1, alignItems: 'center' },
  page: { width: '100%', maxWidth: 440, paddingTop: 28, paddingBottom: 10 },
  compactPage: { paddingTop: 26 },
  tinyPage: { paddingTop: 12, paddingBottom: 18 },
  header: { height: 58, alignItems: 'center', justifyContent: 'center', position: 'relative' },
  compactHeader: { height: 52 },
  tinyHeader: { height: 48 },
  backButton: {
    position: 'absolute', left: 0, top: 9, width: 40, height: 40, borderRadius: 22,
    borderWidth: 1, borderColor: '#e9e9dd', backgroundColor: '#fbfbf4',
    alignItems: 'center', justifyContent: 'center',
    ...Platform.select({
      web: { boxShadow: '0px 2px 8px rgba(38, 56, 46, 0.08)' },
      default: { shadowColor: '#26382e', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 2 },
    }),
  },
  brand: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  compactBrand: { transform: [{ translateX: 8 }] },
  brandName: { color: INK, fontFamily: SERIF_FONT, fontSize: 20, fontWeight: '700', lineHeight: 24, letterSpacing: -0.55 },
  brandTagline: { color: MUTED, fontFamily: SANS_FONT, fontSize: 12.5, lineHeight: 16 },
  intro: { marginTop: 13, marginBottom: 0, paddingHorizontal: 4 },
  compactIntro: { marginTop: 15, paddingHorizontal: 2 },
  tinyIntro: { marginTop: 16 },
  title: { color: '#073c32', fontFamily: SERIF_FONT, fontWeight: '700', letterSpacing: -1.15 },
  subtitle: { maxWidth: 350, marginTop: 5, color: MUTED, fontFamily: SANS_FONT, fontSize: 17.5, lineHeight: 22, letterSpacing: -0.2 },
  compactSubtitle: { marginTop: 4, fontSize: 16.5, lineHeight: 22 },
  tinySubtitle: { fontSize: 15.5, lineHeight: 21 },
  fields: { marginTop: 15, gap: 10 },
  compactFields: { marginTop: 13, gap: 7 },
  tinyFields: { marginTop: 8, gap: 7 },
  fieldCard: {
    minHeight: 74, paddingHorizontal: 9, paddingVertical: 6, flexDirection: 'row', alignItems: 'center', gap: 11,
    borderWidth: 1, borderColor: '#e9e7df', borderRadius: 18, backgroundColor: 'rgba(255,254,250,0.94)',
    ...Platform.select({
      web: { boxShadow: '0px 2px 8px rgba(110, 115, 89, 0.08)' },
      default: { shadowColor: '#6e7359', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.045, shadowRadius: 8, elevation: 1 },
    }),
  },
  compactFieldCard: { minHeight: 70, paddingHorizontal: 8, gap: 9, borderRadius: 17 },
  tinyFieldCard: { minHeight: 66, paddingVertical: 5 },
  fieldIcon: { width: 43, height: 43, flexShrink: 0, borderRadius: 24, backgroundColor: PALE_GREEN, alignItems: 'center', justifyContent: 'center' },
  compactFieldIcon: { width: 40, height: 40 },
  tinyFieldIcon: { width: 37, height: 37 },
  fieldContent: { flex: 1, minWidth: 0 },
  fieldLabel: { marginBottom: 3, color: INK, fontFamily: SERIF_FONT, fontSize: 16.5, fontWeight: '700', lineHeight: 19, letterSpacing: -0.24 },
  compactFieldLabel: { fontSize: 15.5, lineHeight: 18 },
  inputShell: { height: 38, flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: '#dedfdd', borderRadius: 12, backgroundColor: 'rgba(255,254,250,0.74)', overflow: 'hidden' },
  compactInputShell: { height: 36, borderRadius: 11 },
  countryCode: { width: 82, height: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  compactCountryCode: { width: 72, gap: 5 },
  countryCodeText: { color: INK, fontFamily: SANS_FONT, fontSize: 16.5, fontWeight: '500' },
  compactInputText: { fontSize: 15 },
  inputDivider: { width: 1, height: '72%', backgroundColor: '#e3e4e1' },
  input: { flex: 1, minWidth: 0, height: '100%', paddingHorizontal: 12, paddingVertical: 0, color: INK, fontFamily: SANS_FONT, fontSize: 16.5, lineHeight: 21 },
  compactInput: { paddingHorizontal: 9, fontSize: 15.5 },
  tinyInput: { paddingHorizontal: 6, fontSize: 14 },
  passwordInput: { paddingRight: 2 },
  passwordToggle: { width: 47, height: '100%', alignItems: 'center', justifyContent: 'center' },
  compactPasswordToggle: { width: 40 },
  forgotButton: { minHeight: 24, marginTop: 8, alignSelf: 'flex-end', justifyContent: 'center' },
  compactForgotButton: { marginTop: 4, minHeight: 22 },
  forgotText: { color: '#07583f', fontFamily: SERIF_FONT, fontSize: 15.5, fontWeight: '700', lineHeight: 22 },
  compactForgotText: { fontSize: 14.5, lineHeight: 21 },
  message: { marginTop: 1, marginBottom: 4, color: '#a1372d', fontFamily: SANS_FONT, fontSize: 12.5, lineHeight: 17 },
  submittingButton: { opacity: 0.72 },
  primaryButton: { height: 50, marginTop: 10, borderRadius: 29, backgroundColor: GREEN, alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' },
  compactPrimaryButton: { height: 48, marginTop: 9 },
  tinyPrimaryButton: { height: 44, marginTop: 7 },
  primaryGradient: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 },
  primaryButtonText: { color: PAPER, fontFamily: SERIF_FONT, fontSize: 22, fontWeight: '700', lineHeight: 28 },
  arrowBubble: { position: 'absolute', right: 6, top: 4, width: 42, height: 42, borderRadius: 22, backgroundColor: '#fffef9', alignItems: 'center', justifyContent: 'center' },
  compactArrowBubble: { width: 40, height: 40, top: 4 },
  dividerRow: { height: 18, marginTop: 12, flexDirection: 'row', alignItems: 'center', gap: 14 },
  compactDividerRow: { height: 16, marginTop: 9 },
  tinyDividerRow: { height: 14, marginTop: 8 },
  dividerLine: { height: 1, flex: 1, backgroundColor: '#c9cbc4' },
  dividerText: { color: '#68727b', fontFamily: SANS_FONT, fontSize: 15.5, lineHeight: 20 },
  codeButton: { height: 46, marginTop: 8, borderWidth: 1.4, borderColor: GREEN, borderRadius: 28, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 14, backgroundColor: 'rgba(255,253,247,0.55)' },
  compactCodeButton: { height: 44, marginTop: 3, gap: 11 },
  tinyCodeButton: { height: 42, marginTop: 6, gap: 8 },
  codeButtonText: { color: INK, fontFamily: SERIF_FONT, fontSize: 18, fontWeight: '700', lineHeight: 24, letterSpacing: -0.35 },
  compactCodeButtonText: { fontSize: 16, lineHeight: 22, letterSpacing: -0.25 },
  tinyCodeButtonText: { fontSize: 14, lineHeight: 18, letterSpacing: -0.15 },
  accountRow: { marginTop: 12, alignItems: 'center' },
  compactAccountRow: { marginTop: 8 },
  accountText: { color: '#576778', fontFamily: SERIF_FONT, fontSize: 15.5, lineHeight: 23, textAlign: 'center' },
  compactAccountText: { fontSize: 14, lineHeight: 21 },
  accountLink: { color: '#076044', fontWeight: '700' },
  pressed: { opacity: 0.82 },
});

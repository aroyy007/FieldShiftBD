import React, { useEffect, useMemo, useState } from 'react';
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
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';
import {
  ArrowRightIcon,
  BackChevronIcon,
  BrandPlantIcon,
  PhoneCallIcon,
  ShieldLeafIcon,
} from '../../components/icons';
import { useAppContext } from '../../context/AppProvider';

const PAPER = '#fffdf7';
const GREEN = '#07583f';
const INK = '#0a392f';
const MUTED = '#65717b';
const PALE_GREEN = '#eef4e6';
const SERIF_FONT = Platform.select({ web: 'Georgia', default: 'serif' }) ?? 'serif';
const SANS_FONT = Platform.select({ web: 'Arial', default: 'sans-serif' }) ?? 'sans-serif';
const FOOTER_IMAGE = require('../../../assets/images/verification-rice-field.png');

export default function VerifyPhone() {
  const [code, setCode] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(52);
  const [deliveryMethod, setDeliveryMethod] = useState<'sms' | 'call'>('sms');
  const [error, setError] = useState('');
  const { height, width } = useWindowDimensions();
  const router = useRouter();
  const { user } = useAppContext();
  const { phone: phoneParam } = useLocalSearchParams<{ phone?: string }>();
  const compact = width < 360 || height < 680;
  const tiny = width < 340 || height < 590;
  const titleSize = tiny ? 27 : width < 340 ? 30 : width < 380 ? 35 : 39;
  const footerHeight = Math.max(110, Math.min(180, Math.min(width / 2.72, height * 0.22)));
  const scrollBottom = compact ? 0 : Math.max(0, footerHeight - 20);
  const digits = useMemo(() => Array.from({ length: 6 }, (_, index) => code[index] ?? ''), [code]);
  const phonePrefix = (user?.phone || phoneParam)?.replace(/\D/g, '').replace(/^880/, '').slice(0, 2) || '01';

  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const timer = setTimeout(() => setSecondsLeft((current) => Math.max(0, current - 1)), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  const handleContinue = () => {
    if (code.length !== 6) {
      setError('Please enter the 6-digit code.');
      return;
    }
    setError('');
    router.replace('/farmlands' as Href);
  };

  const handleResend = () => {
    if (secondsLeft > 0) return;
    setSecondsLeft(52);
    setError('');
  };

  const page = (
    <View style={styles.root}>
      <Image
        accessibilityElementsHidden
        accessible={false}
        resizeMode="cover"
        source={FOOTER_IMAGE}
        style={[styles.footerImage, { height: footerHeight + 44 }]}
      />
      <Svg
        aria-hidden
        height={footerHeight + 44}
        pointerEvents="none"
        style={styles.footerFade}
        viewBox="0 0 100 100"
        width="100%"
        preserveAspectRatio="none"
      >
        <Defs>
          <LinearGradient id="verification-footer-fade" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0%" stopColor={PAPER} stopOpacity="1" />
            <Stop offset="28%" stopColor={PAPER} stopOpacity="0.8" />
            <Stop offset="60%" stopColor={PAPER} stopOpacity="0" />
          </LinearGradient>
        </Defs>
        <Rect width="100" height="100" fill="url(#verification-footer-fade)" />
      </Svg>

      <ScrollView
        bounces={false}
        contentContainerStyle={styles.scrollContent}
        keyboardDismissMode="on-drag"
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        style={[styles.foregroundScroll, { bottom: scrollBottom }]}
      >
        <View style={[styles.page, { paddingHorizontal: width < 340 ? 18 : 22 }, compact && styles.compactPage, tiny && styles.tinyPage]}>
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
            <View style={styles.brand} accessibilityLabel="FieldShift BD, AI Farmer Assistant">
              <BrandPlantIcon size={48} />
              <View>
                <Text style={styles.brandName}>FieldShift BD</Text>
                <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
              </View>
            </View>
          </View>

          <View style={[styles.intro, compact && styles.compactIntro, tiny && styles.tinyIntro]}>
            <Text
              accessibilityRole="header"
              style={[styles.title, { fontSize: titleSize, lineHeight: titleSize * 1.13 }]}
            >
              Verify your phone
            </Text>
            <Text style={[styles.subtitle, compact && styles.compactSubtitle, tiny && styles.tinySubtitle]}>
              We have sent a 6-digit code to
            </Text>
            <View style={[styles.phoneLine, compact && styles.compactPhoneLine, tiny && styles.tinyPhoneLine]}>
              <Text numberOfLines={1} style={[styles.phoneNumber, width < 350 && styles.compactPhoneNumber, tiny && styles.tinyPhoneNumber]}>
                {`+880 ${phonePrefix}XXX-XXXXXX`}
              </Text>
              <Pressable
                accessibilityRole="button"
                onPress={() => router.back()}
                style={({ pressed }) => [styles.editButton, pressed && styles.pressed]}
              >
                <Text style={styles.editText}>Edit</Text>
              </Pressable>
            </View>
          </View>

          <View style={[styles.otpRow, compact && styles.compactOtpRow, tiny && styles.tinyOtpRow]}>
            {digits.map((digit, index) => {
              const active = index === Math.min(code.length, 5);
              return (
                <View
                  key={index}
                  accessibilityElementsHidden
                  style={[
                    styles.otpCell,
                    compact && styles.compactOtpCell,
                    tiny && styles.tinyOtpCell,
                    active && styles.otpCellActive,
                  ]}
                >
                  {digit ? <Text style={styles.otpDigit}>{digit}</Text> : null}
                  {active && !digit ? <View style={styles.otpCaret} /> : null}
                </View>
              );
            })}
            <TextInput
              accessibilityLabel="6-digit verification code"
              accessibilityHint="Enter the six-digit code sent to your phone"
              autoCapitalize="none"
              autoComplete="one-time-code"
              autoCorrect={false}
              caretHidden
              keyboardType="number-pad"
              maxLength={6}
              onChangeText={(value) => {
                setCode(value.replace(/\D/g, '').slice(0, 6));
                setError('');
              }}
              onSubmitEditing={handleContinue}
              selectionColor="transparent"
              style={styles.otpInput}
              textContentType="oneTimeCode"
              underlineColorAndroid="transparent"
              value={code}
            />
          </View>

          <View style={[styles.resendRow, compact && styles.compactResendRow, tiny && styles.tinyResendRow]}>
            <Text style={[styles.resendPrompt, compact && styles.compactResendText, tiny && styles.tinyResendText]}>
              Didn’t receive the code?
            </Text>
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ disabled: secondsLeft > 0 }}
              disabled={secondsLeft > 0}
              onPress={handleResend}
              style={({ pressed }) => [styles.resendButton, pressed && styles.pressed]}
            >
              <Text style={[styles.resendText, compact && styles.compactResendText, tiny && styles.tinyResendText]}>
                {secondsLeft > 0 ? `Resend in 00:${String(secondsLeft).padStart(2, '0')}` : 'Resend code'}
              </Text>
            </Pressable>
          </View>

          {error ? <Text accessibilityRole="alert" style={styles.errorText}>{error}</Text> : null}

          <Pressable
            accessibilityRole="button"
            onPress={handleContinue}
            style={({ pressed }) => [styles.primaryButton, compact && styles.compactPrimaryButton, tiny && styles.tinyPrimaryButton, pressed && styles.pressed]}
          >
            <Svg aria-hidden height="100%" preserveAspectRatio="none" style={styles.primaryGradient} viewBox="0 0 400 60" width="100%">
              <Defs>
                <LinearGradient id="verification-button-gradient" x1="0" y1="0" x2="1" y2="0">
                  <Stop offset="0%" stopColor="#287752" />
                  <Stop offset="100%" stopColor="#064a34" />
                </LinearGradient>
              </Defs>
              <Rect width="400" height="60" rx="30" fill="url(#verification-button-gradient)" />
            </Svg>
            <Text style={styles.primaryButtonText}>Continue</Text>
            <View style={styles.arrowBubble}><ArrowRightIcon size={23} color={GREEN} /></View>
          </Pressable>

          <View style={[styles.dividerRow, compact && styles.compactDividerRow, tiny && styles.tinyDividerRow]}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          <Pressable
            accessibilityHint="Switch between text and voice verification"
            accessibilityRole="button"
            onPress={() => setDeliveryMethod((method) => method === 'sms' ? 'call' : 'sms')}
            style={({ pressed }) => [styles.callButton, compact && styles.compactCallButton, tiny && styles.tinyCallButton, pressed && styles.pressed]}
          >
            <PhoneCallIcon size={26} />
            <Text style={styles.callButtonText}>{deliveryMethod === 'sms' ? 'Call me instead' : 'Text me instead'}</Text>
          </Pressable>

          <View style={[styles.securitySpacer, height > 720 && styles.expandedSecuritySpacer]} />

          <View style={[styles.securityNote, compact && styles.compactSecurityNote, tiny && styles.tinySecurityNote]}>
            <ShieldLeafIcon size={42} />
            <Text style={[styles.securityText, compact && styles.compactSecurityText, tiny && styles.tinySecurityText]}>
              This code helps us keep your account safe and secure.
            </Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );

  return Platform.OS === 'web'
    ? <View style={[styles.safeArea, { width, height }]}>{page}</View>
    : <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>{page}</SafeAreaView>;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: PAPER },
  root: { flex: 1, position: 'relative', backgroundColor: PAPER },
  footerImage: { position: 'absolute', left: 0, right: 0, bottom: -44, width: '100%' },
  footerFade: { position: 'absolute', left: 0, right: 0, bottom: -44 },
  foregroundScroll: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 },
  scrollContent: { flexGrow: 1, alignItems: 'center' },
  page: {
    width: '100%',
    maxWidth: 440,
    flexGrow: 1,
    paddingTop: 18,
    paddingBottom: 0,
  },
  compactPage: { paddingTop: 10 },
  tinyPage: { paddingTop: 7 },
  header: { height: 54, alignItems: 'center', justifyContent: 'center', position: 'relative' },
  compactHeader: { height: 50 },
  tinyHeader: { height: 44 },
  backButton: {
    position: 'absolute',
    left: 0,
    top: 7,
    width: 40,
    height: 40,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#e9e9dd',
    backgroundColor: '#fbfbf4',
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      web: { boxShadow: '0px 2px 8px rgba(38, 56, 46, 0.08)' },
      default: { shadowColor: '#26382e', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 2 },
    }),
  },
  brand: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  brandName: { color: INK, fontFamily: SERIF_FONT, fontSize: 21, fontWeight: '700', lineHeight: 25, letterSpacing: -0.55 },
  brandTagline: { color: MUTED, fontFamily: SANS_FONT, fontSize: 13, lineHeight: 17 },
  intro: { marginTop: 18, alignItems: 'center' },
  compactIntro: { marginTop: 12 },
  tinyIntro: { marginTop: 7 },
  title: { color: '#073c32', fontFamily: SERIF_FONT, fontWeight: '700', lineHeight: 1.13, letterSpacing: -1.05, textAlign: 'center' },
  subtitle: { marginTop: 5, color: MUTED, fontFamily: SANS_FONT, fontSize: 17.5, fontWeight: '400', lineHeight: 23, letterSpacing: -0.12, textAlign: 'center' },
  compactSubtitle: { marginTop: 3, fontSize: 15.5, lineHeight: 21 },
  tinySubtitle: { marginTop: 2, fontSize: 14, lineHeight: 18 },
  phoneLine: { marginTop: 9, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 14 },
  compactPhoneLine: { marginTop: 6, gap: 9 },
  tinyPhoneLine: { marginTop: 4, gap: 7 },
  phoneNumber: { flexShrink: 0, color: '#0a2925', fontFamily: SERIF_FONT, fontSize: 21.5, fontWeight: '700', lineHeight: 28, letterSpacing: -0.35 },
  compactPhoneNumber: { fontSize: 20, lineHeight: 26, letterSpacing: -0.4 },
  tinyPhoneNumber: { fontSize: 18, lineHeight: 22, letterSpacing: -0.45 },
  editButton: { minHeight: 40, justifyContent: 'center', paddingHorizontal: 2 },
  editText: { color: GREEN, fontFamily: SANS_FONT, fontSize: 17, fontWeight: '700', lineHeight: 22, textDecorationLine: 'underline' },
  otpRow: { height: 60, marginTop: 14, marginHorizontal: 6, flexDirection: 'row', gap: 8, position: 'relative' },
  compactOtpRow: { height: 55, marginTop: 16, gap: 7 },
  tinyOtpRow: { height: 49, marginTop: 12, gap: 6, marginHorizontal: 2 },
  otpCell: { flex: 1, minWidth: 0, alignItems: 'center', justifyContent: 'center', borderWidth: 1.2, borderColor: '#c8c9c6', borderRadius: 13, backgroundColor: 'rgba(255,253,247,0.72)' },
  compactOtpCell: { borderRadius: 12 },
  tinyOtpCell: { borderRadius: 10 },
  otpCellActive: { borderColor: GREEN, borderWidth: 2 },
  otpDigit: { color: INK, fontFamily: SANS_FONT, fontSize: 24, fontWeight: '500', lineHeight: 30 },
  otpCaret: { width: 2, height: 24, borderRadius: 1, backgroundColor: INK },
  otpInput: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, width: '100%', height: '100%', opacity: 0.02, color: 'transparent', backgroundColor: 'transparent', fontSize: 22, borderWidth: 0, padding: 0, textAlign: 'center' },
  resendRow: { minHeight: 24, marginTop: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 11 },
  compactResendRow: { minHeight: 22, marginTop: 12, gap: 8 },
  tinyResendRow: { minHeight: 20, marginTop: 8, gap: 4, flexWrap: 'nowrap' },
  resendPrompt: { color: MUTED, fontFamily: SANS_FONT, fontSize: 16.5, lineHeight: 23, letterSpacing: -0.28 },
  resendButton: { minHeight: 36, justifyContent: 'center' },
  resendText: { color: GREEN, fontFamily: SANS_FONT, fontSize: 16.5, fontWeight: '700', lineHeight: 23, letterSpacing: -0.25 },
  compactResendText: { fontSize: 14.5, lineHeight: 20, letterSpacing: -0.2 },
  tinyResendText: { fontSize: 12.5, lineHeight: 18, letterSpacing: -0.3 },
  errorText: { marginTop: 2, color: '#b3261e', fontFamily: SANS_FONT, fontSize: 12.5, lineHeight: 17, textAlign: 'center' },
  primaryButton: { height: 50, marginTop: 15, borderRadius: 29, backgroundColor: GREEN, alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' },
  compactPrimaryButton: { height: 48, marginTop: 17 },
  tinyPrimaryButton: { height: 44, marginTop: 12 },
  primaryGradient: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 },
  primaryButtonText: { color: PAPER, fontFamily: SERIF_FONT, fontSize: 22, fontWeight: '700', lineHeight: 28 },
  arrowBubble: { position: 'absolute', right: 6, top: 4, width: 42, height: 42, borderRadius: 22, backgroundColor: '#fffef9', alignItems: 'center', justifyContent: 'center' },
  dividerRow: { height: 18, marginTop: 14, flexDirection: 'row', alignItems: 'center', gap: 14 },
  compactDividerRow: { height: 16, marginTop: 11 },
  tinyDividerRow: { height: 14, marginTop: 8 },
  dividerLine: { height: 1, flex: 1, backgroundColor: '#c9cbc4' },
  dividerText: { color: '#68727b', fontFamily: SANS_FONT, fontSize: 15.5, lineHeight: 20 },
  callButton: { height: 48, marginTop: 12, borderWidth: 1.4, borderColor: GREEN, borderRadius: 28, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, backgroundColor: 'rgba(255,253,247,0.55)' },
  compactCallButton: { height: 44, marginTop: 10 },
  tinyCallButton: { height: 42, marginTop: 8 },
  callButtonText: { color: INK, fontFamily: SERIF_FONT, fontSize: 20, fontWeight: '700', lineHeight: 26, letterSpacing: -0.35 },
  securitySpacer: { height: 0 },
  expandedSecuritySpacer: { flexGrow: 1, minHeight: 12 },
  securityNote: { minHeight: 70, marginTop: 12, paddingHorizontal: 15, paddingVertical: 9, flexDirection: 'row', alignItems: 'center', gap: 13, borderRadius: 20, backgroundColor: PALE_GREEN },
  compactSecurityNote: { minHeight: 60, marginTop: 10, paddingHorizontal: 12, paddingVertical: 7, gap: 10, borderRadius: 18 },
  tinySecurityNote: { minHeight: 56, marginTop: 8, paddingHorizontal: 10, paddingVertical: 6, gap: 8, borderRadius: 16 },
  securityText: { flex: 1, color: INK, fontFamily: SANS_FONT, fontSize: 17, lineHeight: 24, letterSpacing: -0.18 },
  compactSecurityText: { fontSize: 15.5, lineHeight: 21 },
  tinySecurityText: { fontSize: 14, lineHeight: 19 },
  pressed: { opacity: 0.82 },
});

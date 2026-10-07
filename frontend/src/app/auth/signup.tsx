import React, { useState } from 'react';
import {
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
import {
  ArrowRightIcon,
  BackChevronIcon,
  BrandPlantIcon,
  CheckIcon,
  ChevronDownIcon,
  MobilePhoneIcon,
  PersonOutlineIcon,
  ShieldLeafIcon,
} from '../../components/icons';
import { useAppContext } from '../../context/AppProvider';
import { normalizeBangladeshPhone } from '../../services/farm-data';

const PAPER = '#fffdf7';
const GREEN = '#07583f';
const INK = '#0a392f';
const MUTED = '#65717b';
const PALE_GREEN = '#f0f5e9';
const SERIF_FONT = Platform.select({ web: 'Georgia', default: 'serif' }) ?? 'serif';
const SANS_FONT = Platform.select({ web: 'Arial', default: 'sans-serif' }) ?? 'sans-serif';

export default function Signup() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { width } = useWindowDimensions();
  const router = useRouter();
  const { register } = useAppContext();

  const handleSignup = async () => {
    const normalizedName = name.trim();
    const normalizedPhone = normalizeBangladeshPhone(phone);

    if (!normalizedName || normalizedPhone.length < 12 || normalizedPhone.length > 16) {
      setError('Enter your name and a valid Bangladesh phone number.');
      return;
    }
    if (!agreed) {
      setError('Please agree to the Terms of Service and Privacy Policy.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register(normalizedName, normalizedPhone);
      setError('');
      router.replace('/farmlands' as Href);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'We could not create your account. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const page = (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="on-drag"
      showsVerticalScrollIndicator={false}
      bounces={false}
    >
      <View style={[styles.page, width < 340 && styles.narrowPage]}>
        <View style={styles.header}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Go back"
            hitSlop={8}
            onPress={() => router.back()}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
          >
            <BackChevronIcon />
          </Pressable>

          <View
            style={[styles.brand, width < 340 && styles.compactBrand]}
            accessibilityLabel="FieldShift BD, AI Farmer Assistant"
          >
            <BrandPlantIcon size={45} />
            <View>
              <Text style={styles.brandName}>FieldShift BD</Text>
              <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
            </View>
          </View>
        </View>

        <View style={styles.intro}>
          <Text
            accessibilityRole="header"
            style={[styles.title, { fontSize: width < 310 ? 27 : width < 370 ? 30 : 32 }]}
          >
            Create your account
          </Text>
          <Text style={styles.subtitle}>
            Join thousands of farmers getting personalized advice for better harvests.
          </Text>
        </View>

        <View style={styles.fields}>
          <View style={styles.fieldCard}>
            <View style={[styles.fieldIcon, width < 340 && styles.compactFieldIcon]}><MobilePhoneIcon size={23} /></View>
            <View style={styles.fieldContent}>
              <Text style={styles.fieldLabel}>Phone number</Text>
              <View style={styles.inputShell}>
                <View style={[styles.countryCode, width < 340 && styles.compactCountryCode]} accessibilityLabel="Country code plus 880">
                  <Text style={styles.countryCodeText}>+880</Text>
                  <ChevronDownIcon size={17} />
                </View>
                <View style={styles.inputDivider} />
                <TextInput
                  accessibilityLabel="Phone number"
                  autoComplete="tel-national"
                  autoCorrect={false}
                  keyboardType="phone-pad"
                  maxLength={15}
                  onChangeText={(value) => { setPhone(value); setError(''); }}
                  placeholder="01XXX-XXXXXX"
                  placeholderTextColor="#87919c"
                  returnKeyType="next"
                  style={[styles.input, width < 340 && styles.compactInput]}
                  value={phone}
                />
              </View>
            </View>
          </View>

          <View style={styles.fieldCard}>
            <View style={[styles.fieldIcon, width < 340 && styles.compactFieldIcon]}><PersonOutlineIcon size={24} /></View>
            <View style={styles.fieldContent}>
              <Text style={styles.fieldLabel}>Your name</Text>
              <View style={styles.inputShell}>
                <TextInput
                  accessibilityLabel="Your name"
                  autoCapitalize="words"
                  autoComplete="name"
                  autoCorrect={false}
                  onChangeText={(value) => { setName(value); setError(''); }}
                  placeholder="Enter your full name"
                  placeholderTextColor="#87919c"
                  returnKeyType="next"
                  style={[styles.input, width < 340 && styles.compactInput]}
                  value={name}
                />
              </View>
            </View>
          </View>

        </View>

        <View style={styles.securityNote}>
          <ShieldLeafIcon size={43} />
          <Text style={styles.securityText}>
            The current account API registers with your name and phone number. Password and OTP verification are not configured yet.
          </Text>
        </View>

        <Pressable
          aria-checked={agreed}
          accessibilityRole="checkbox"
          accessibilityState={{ checked: agreed }}
          onPress={() => { setAgreed((checked) => !checked); setError(''); }}
          style={({ pressed }) => [styles.termsRow, pressed && styles.pressed]}
        >
          <View style={[styles.checkbox, agreed && styles.checkboxChecked]}>
            {agreed ? <CheckIcon size={18} /> : null}
          </View>
          <Text style={styles.termsText}>
            I agree to the <Text style={styles.termsLink}>Terms of Service</Text> and{'\n'}
            <Text style={styles.termsLink}>Privacy Policy</Text>.
          </Text>
        </Pressable>

        {error ? <Text accessibilityRole="alert" style={styles.errorText}>{error}</Text> : null}

        <Pressable
          accessibilityRole="button"
          disabled={isSubmitting}
          accessibilityState={{ disabled: isSubmitting }}
          onPress={() => void handleSignup()}
          style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed, isSubmitting && styles.submittingButton]}
        >
          <Text style={styles.primaryButtonText}>{isSubmitting ? 'Creating account…' : 'Create account'}</Text>
          <View style={styles.arrowBubble}><ArrowRightIcon size={21} /></View>
        </Pressable>

        <View style={styles.dividerRow}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>or</Text>
          <View style={styles.dividerLine} />
        </View>

        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/auth/login' as Href)}
          style={({ pressed }) => [styles.loginButton, pressed && styles.pressed]}
        >
          <Text style={styles.loginButtonText}>I already have an account</Text>
        </Pressable>
      </View>
    </ScrollView>
  );

  return Platform.OS === 'web'
    ? <View style={styles.safeArea}>{page}</View>
    : <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>{page}</SafeAreaView>;
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: PAPER,
  },
  scrollContent: {
    flexGrow: 1,
    alignItems: 'center',
  },
  page: {
    width: '100%',
    maxWidth: 440,
    paddingHorizontal: 22,
    paddingTop: 20,
    paddingBottom: 2,
  },
  narrowPage: {
    paddingHorizontal: 18,
  },
  header: {
    height: 59,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    left: 0,
    top: 12,
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
      default: {
        shadowColor: '#26382e',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 8,
        elevation: 2,
      },
    }),
  },
  brand: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  compactBrand: {
    transform: [{ translateX: 10 }],
  },
  brandName: {
    color: INK,
    fontFamily: SERIF_FONT,
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
    letterSpacing: -0.55,
  },
  brandTagline: {
    color: MUTED,
    fontFamily: SANS_FONT,
    fontSize: 12.5,
    lineHeight: 16,
  },
  intro: {
    marginTop: 19,
    marginBottom: 6,
    alignItems: 'center',
  },
  title: {
    color: '#073c32',
    fontFamily: SERIF_FONT,
    fontWeight: '700',
    lineHeight: 40,
    letterSpacing: -1.1,
    textAlign: 'center',
  },
  subtitle: {
    maxWidth: 350,
    marginTop: 3,
    color: MUTED,
    fontFamily: SANS_FONT,
    fontSize: 16.5,
    fontWeight: '400',
    lineHeight: 22,
    letterSpacing: -0.12,
    textAlign: 'center',
  },
  fields: {
    gap: 5,
  },
  fieldCard: {
    minHeight: 72,
    paddingHorizontal: 9,
    paddingVertical: 5,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderWidth: 1,
    borderColor: '#f0eee5',
    borderRadius: 18,
    backgroundColor: '#fffefa',
    ...Platform.select({
      web: { boxShadow: '0px 2px 8px rgba(110, 115, 89, 0.08)' },
      default: {
        shadowColor: '#6e7359',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.045,
        shadowRadius: 8,
        elevation: 1,
      },
    }),
  },
  fieldIcon: {
    width: 44,
    height: 44,
    flexShrink: 0,
    borderRadius: 24,
    backgroundColor: PALE_GREEN,
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactFieldIcon: {
    width: 40,
    height: 40,
  },
  fieldContent: {
    flex: 1,
    minWidth: 0,
  },
  fieldLabel: {
    marginBottom: 3,
    color: INK,
    fontFamily: SERIF_FONT,
    fontSize: 16.5,
    fontWeight: '700',
    lineHeight: 19,
    letterSpacing: -0.24,
  },
  inputShell: {
    height: 38,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#dedfdd',
    borderRadius: 12,
    backgroundColor: '#fffefa',
    overflow: 'hidden',
  },
  countryCode: {
    width: 77,
    height: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  compactCountryCode: {
    width: 65,
    gap: 5,
  },
  countryCodeText: {
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 16,
    fontWeight: '500',
  },
  inputDivider: {
    width: 1,
    height: '72%',
    backgroundColor: '#e3e4e1',
  },
  input: {
    flex: 1,
    minWidth: 0,
    height: '100%',
    paddingHorizontal: 12,
    paddingVertical: 0,
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 16,
    lineHeight: 20,
  },
  compactInput: {
    paddingHorizontal: 8,
    fontSize: 14.5,
  },
  passwordInput: {
    paddingRight: 2,
  },
  passwordToggle: {
    width: 42,
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  securityNote: {
    minHeight: 64,
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderRadius: 19,
    backgroundColor: '#eef4e6',
  },
  securityText: {
    flex: 1,
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 13,
    lineHeight: 17,
    letterSpacing: -0.08,
  },
  termsRow: {
    minHeight: 39,
    marginTop: 11,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  checkbox: {
    width: 26,
    height: 26,
    marginTop: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#9aa69b',
    borderRadius: 6,
    backgroundColor: '#fffefa',
  },
  checkboxChecked: {
    borderColor: GREEN,
    backgroundColor: GREEN,
  },
  termsText: {
    flex: 1,
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 14.5,
    lineHeight: 20,
  },
  termsLink: {
    color: '#147047',
    textDecorationLine: 'underline',
  },
  errorText: {
    marginBottom: 7,
    color: '#b3261e',
    fontFamily: SANS_FONT,
    fontSize: 12.5,
    lineHeight: 17,
  },
  primaryButton: {
    height: 40,
    marginTop: 0,
    borderRadius: 25,
    backgroundColor: GREEN,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  submittingButton: { opacity: 0.72 },
  primaryButtonText: {
    color: PAPER,
    fontFamily: SERIF_FONT,
    fontSize: 19,
    fontWeight: '700',
    lineHeight: 24,
  },
  arrowBubble: {
    position: 'absolute',
    right: 5,
    top: 3,
    width: 34,
    height: 34,
    borderRadius: 20,
    backgroundColor: '#fffef9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dividerRow: {
    height: 12,
    marginTop: 5,
    marginBottom: 2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dividerLine: {
    height: 1,
    flex: 1,
    backgroundColor: '#c9cbc4',
  },
  dividerText: {
    color: '#8a939b',
    fontFamily: SANS_FONT,
    fontSize: 14,
    lineHeight: 18,
  },
  loginButton: {
    height: 34,
    borderWidth: 1.5,
    borderColor: GREEN,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  loginButtonText: {
    color: INK,
    fontFamily: SANS_FONT,
    fontSize: 15.5,
    lineHeight: 19,
    textAlign: 'center',
  },
  pressed: {
    opacity: 0.82,
  },
});

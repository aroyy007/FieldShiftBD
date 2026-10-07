import { useEffect, useState } from 'react';
import {
  Href,
  useRouter,
} from 'expo-router';
import {
  Image,
  ImageBackground,
  Modal,
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
import Svg, { Defs, LinearGradient, Stop, Path } from 'react-native-svg';
import { BrandPlantIcon } from '../../components/icons';
import { DashboardIcon, DashboardIconName } from '../../components/dashboard-icons';
import { FarmProfileIcon, FarmProfileIconName } from '../../components/farm-profile-icons';
import { useAppContext } from '../../context/AppProvider';
import { apiRequest } from '../../services/api-client';

const PAPER = '#fffdf7';
const INK = '#083a33';
const GREEN = '#17643b';
const MUTED = '#687587';
const SERIF = 'Georgia';
const SANS = 'Arial';

type FarmProfileValues = {
  location: string;
  size: string;
  soil: string;
  irrigation: string;
  water: string;
  experience: string;
  budget: string;
};
type Tab = { title: string; icon: DashboardIconName; route?: string };

const TABS: Tab[] = [
  { title: 'Home', icon: 'home' },
  { title: 'Tasks', icon: 'tasks', route: 'tasks' },
  { title: 'Chat', icon: 'chat', route: 'chat' },
  { title: 'Scan', icon: 'scan', route: 'crop-health' },
  { title: 'Profile', icon: 'profile' },
];

const INITIAL_VALUES: FarmProfileValues = {
  location: 'Not set',
  size: 'Not set',
  soil: 'Not set',
  irrigation: 'Not set',
  water: 'Not set',
  experience: 'Not set',
  budget: 'Not set',
};

const PROFILE_FIELDS: { key: keyof FarmProfileValues; label: string }[] = [
  { key: 'location', label: 'Location' },
  { key: 'size', label: 'Farm size' },
  { key: 'soil', label: 'Soil type' },
  { key: 'irrigation', label: 'Irrigation' },
  { key: 'water', label: 'Water source' },
  { key: 'experience', label: 'Experience' },
  { key: 'budget', label: 'Budget (BDT)' },
];

export default function FarmProfileSetup() {
  const router = useRouter();
  const { user, profile, farmlands, logout, updateFarmland, updateFarmerProfile } = useAppContext();
  const { width } = useWindowDimensions();
  const compact = width < 380;
  const farm = farmlands[0];
  const farmlandId = farm?.id;
  const ScreenContainer = Platform.OS === 'web' ? View : SafeAreaView;
  const [profileDraft, setProfileDraft] = useState(INITIAL_VALUES);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [onboardingStatus, setOnboardingStatus] = useState<{ farmId: string; percent: number } | null>(null);
  const profileValues: FarmProfileValues = farm ? {
    location: farm.location ?? 'Location not set',
    size: `${farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres`,
    soil: farm.soilType ?? 'Not set',
    irrigation: farm.irrigationAvailable == null ? 'Not set' : farm.irrigationAvailable ? 'Available' : 'Not available',
    water: farm.waterSource ?? 'Not set',
    experience: profile?.farming_experience_years == null ? 'Not set' : `${profile.farming_experience_years} years`,
    budget: farm.budgetAmount == null ? 'Not set' : String(farm.budgetAmount),
  } : {
    ...INITIAL_VALUES,
    experience: profile?.farming_experience_years == null ? 'Not set' : `${profile.farming_experience_years} years`,
  };
  const onboardingPercent = onboardingStatus?.farmId === farm?.id ? onboardingStatus.percent : 0;
  const [savingAnswers, setSavingAnswers] = useState(false);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    if (!user) router.replace('/auth/login' as Href);
  }, [router, user]);

  useEffect(() => {
    if (!farmlandId) return;
    let active = true;
    apiRequest<{ percent_complete: number }>(`/farmlands/${encodeURIComponent(farmlandId)}/onboarding-status`)
      .then(status => { if (active) setOnboardingStatus({ farmId: farmlandId, percent: status.percent_complete }); })
      .catch(() => { if (active) setOnboardingStatus({ farmId: farmlandId, percent: 0 }); });
    return () => { active = false; };
  }, [farmlandId]);

  const openFarmSection = (section: string) => {
    if (!farm) {
      router.push('/farmlands/add' as Href);
      return;
    }
    router.push(`/farmlands/${farm.id}/${section}` as Href);
  };

  const onTabPress = (tab: Tab) => {
    if (tab.title === 'Profile') {
      setMenuOpen(true);
    } else if (tab.route) {
      openFarmSection(tab.route);
    } else {
      router.push('/farmlands' as Href);
    }
  };

  const continueToFarmDetails = () => {
    if (farm) openFarmSection('crop-advisor');
    else router.push('/farmlands/add' as Href);
  };

  const openEditAnswers = () => {
    setProfileDraft(profileValues);
    setProfileModalOpen(true);
  };

  const saveProfileAnswers = async () => {
    setSaveError('');
    const experience = profileDraft.experience.match(/[\d.]+/)?.[0];
    const patch: Record<string, unknown> = {};
    if (profileDraft.experience.trim() !== 'Not set') {
      const parsedExperience = Number(experience);
      if (!Number.isFinite(parsedExperience) || parsedExperience < 0) {
        setSaveError('Enter farming experience as a non-negative number of years.');
        return;
      }
      patch.farming_experience_years = parsedExperience;
    } else {
      patch.farming_experience_years = null;
    }
    if (!farm) {
      if (Object.keys(patch).length === 0) return;
      setSavingAnswers(true);
      try {
        await updateFarmerProfile(patch);
        setProfileModalOpen(false);
      } catch (error) {
        setSaveError(error instanceof Error ? error.message : 'Could not save profile answers.');
      } finally {
        setSavingAnswers(false);
      }
      return;
    }
    const parsedAcres = Number(profileDraft.size.match(/[\d.]+/)?.[0]);
    if (!Number.isFinite(parsedAcres) || parsedAcres <= 0) {
      setSaveError('Enter a farm size greater than zero acres.');
      return;
    }
    const parsedBudget = profileDraft.budget.trim() === 'Not set' ? null : Number(profileDraft.budget.match(/[\d.]+/)?.[0]);
    if (parsedBudget !== null && (!Number.isFinite(parsedBudget) || parsedBudget < 0)) {
      setSaveError('Enter a valid farm budget in BDT.');
      return;
    }
    const locationParts = profileDraft.location.split(',').map(part => part.trim()).filter(Boolean);
    const farmlandPatch: Record<string, unknown> = {
      land_area_sqm: parsedAcres * 4046.8564224,
      land_area_display_unit: 'acre',
      district: locationParts[0] || null,
      division: locationParts[1] || null,
      soil_type: profileDraft.soil === 'Not set' ? null : profileDraft.soil.trim(),
      irrigation_available: profileDraft.irrigation === 'Not set' ? null : profileDraft.irrigation !== 'Not available',
      water_source: profileDraft.water === 'Not set' ? null : profileDraft.water.trim(),
      budget_amount: parsedBudget,
      budget_currency: 'BDT',
    };
    setSavingAnswers(true);
    try {
      await updateFarmerProfile(patch);
      await updateFarmland(farm.id, farmlandPatch);
      setProfileModalOpen(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Could not save profile answers.');
    } finally {
      setSavingAnswers(false);
    }
  };

  if (!user) return null;

  return (
    <ScreenContainer style={styles.safe}>
      <View style={styles.page}>
        <View style={styles.header}>
          <View style={styles.brand}>
            <BrandPlantIcon size={39} />
            <View>
              <Text style={styles.brandName}>FieldShift BD</Text>
              <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
            </View>
          </View>
          <View style={styles.headerActions}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="View notifications"
              onPress={() => openFarmSection('alerts')}
              style={styles.bellButton}
            >
              <DashboardIcon name="bell" size={26} color={GREEN} />
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Open profile menu"
              onPress={() => setMenuOpen(true)}
              style={styles.avatarButton}
            >
              <Image source={require('../../../assets/images/landing-farmer.png')} style={styles.avatar} />
            </Pressable>
          </View>
        </View>

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.intro}>
            <Text style={[styles.title, compact && styles.titleCompact]}>Let’s map your farm</Text>
            <Text style={styles.subtitle}>
              Answer a few guided questions so your advice stays specific to your land, crop and resources.
            </Text>
          </View>

          <View style={styles.progressCard}>
            <ImageBackground
              source={require('../../../assets/images/verification-rice-field.png')}
              style={styles.progressImage}
              imageStyle={styles.progressImageAsset}
            >
              <Svg width="100%" height="100%" viewBox="0 0 360 100" preserveAspectRatio="none" style={styles.progressFade}>
                <Defs>
                  <LinearGradient id="farmProfileFade" x1="0" y1="0" x2="1" y2="0">
                    <Stop offset="0%" stopColor={PAPER} stopOpacity="1" />
                    <Stop offset="50%" stopColor={PAPER} stopOpacity="0.94" />
                    <Stop offset="75%" stopColor={PAPER} stopOpacity="0.42" />
                    <Stop offset="100%" stopColor={PAPER} stopOpacity="0.03" />
                  </LinearGradient>
                </Defs>
                <Path d="M0 0h360v100H0z" fill="url(#farmProfileFade)" />
              </Svg>
              <View style={styles.progressContent}>
                <View style={styles.progressHeading}>
                  <View style={styles.progressIconCircle}>
                    <FarmProfileIcon name="clipboard" size={24} />
                  </View>
                  <View style={styles.progressCopy}>
                    <Text style={styles.progressTitle}>Your farm profile</Text>
                    <Text style={styles.progressSubtitle}>{farm ? `${onboardingPercent}% complete for ${farm.name}` : 'Add your first farmland to begin.'}</Text>
                  </View>
                </View>
                <Text style={styles.progressPercent}>{onboardingPercent}%</Text>
                <View style={styles.progressTrack}>
                  <View style={[styles.progressFill, { width: `${onboardingPercent}%` }]} />
                </View>
              </View>
            </ImageBackground>
          </View>

          <View style={styles.summaryCard}>
            <View style={styles.summaryHeader}>
              <View style={styles.summaryHeading}>
                <FarmProfileIcon name="chart" size={22} />
                  <Text numberOfLines={1} style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>What we know so far</Text>
              </View>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Edit previous answers"
                onPress={openEditAnswers}
                style={styles.editLink}
              >
                <Text style={[styles.editLinkText, compact && styles.editLinkTextCompact]}>You can edit these anytime</Text>
                <DashboardIcon name="chevron" size={16} color="#50647a" />
              </Pressable>
            </View>
            <View style={[styles.summaryRow, compact && styles.summaryRowCompact]}>
              <InfoCard icon="location" label="Location" value={profileValues.location} />
              <InfoCard icon="field" label="Farm size" value={profileValues.size} />
              <InfoCard icon="soil" label="Soil type" value={profileValues.soil} />
            </View>
            <View style={[styles.summaryRow, compact && styles.summaryRowCompact]}>
              <InfoCard icon="drop" label="Irrigation" value={profileValues.irrigation} />
              <InfoCard icon="water" label="Water source" value={profileValues.water} />
              <InfoCard icon="person" label="Experience" value={profileValues.experience} />
            </View>
            <View style={styles.summaryRow}>
              <InfoCard icon="coins" label="Budget" value={profileValues.budget} wide />
            </View>
          </View>

          <View style={styles.cropSection}>
            <View style={styles.cropSectionHeading}>
              <View style={styles.cropSectionIcon}><FarmProfileIcon name="leaf" size={24} /></View>
              <View style={styles.cropHeadingCopy}>
                <Text style={[styles.cropHeading, compact && styles.cropHeadingCompact]}>
                  Current crop and season
                </Text>
                <Text style={styles.cropSubtitle}>{farm?.activeSeasonId ? 'This information comes from your saved season.' : 'Use Crop Advisor to choose a crop and create a season plan.'}</Text>
              </View>
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel={farm?.activeSeasonId ? 'Open crop advisor to change season' : 'Open crop advisor'} onPress={continueToFarmDetails} style={[styles.cropCard, styles.cropCardSelected]}>
              <View style={styles.cropImageWrap}><View style={[styles.cropImage, styles.cropImagePlaceholder]}><FarmProfileIcon name="leaf" size={30} color={GREEN} /></View></View>
              <View style={styles.cropCopy}>
                <Text numberOfLines={1} style={[styles.cropName, compact && styles.cropNameCompact]}>{farm?.crop ?? 'No farmland yet'}</Text>
                <Text numberOfLines={2} style={[styles.cropDescription, compact && styles.cropDescriptionCompact]}>{farm ? farm.growthStage : 'Create a farmland profile before starting a crop season.'}</Text>
              </View>
              <DashboardIcon name="chevron" size={19} color={GREEN} />
            </Pressable>
          </View>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={farm ? 'Open Crop Advisor' : 'Add farmland'}
            onPress={continueToFarmDetails}
            style={styles.continueButton}
          >
            <Text style={styles.continueText}>{farm ? 'Open Crop Advisor' : 'Add farmland'}</Text>
            <View style={styles.continueArrow}>
              <DashboardIcon name="chevron" size={19} color={GREEN} />
            </View>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Edit previous answers"
            onPress={openEditAnswers}
            style={styles.editButton}
          >
            <FarmProfileIcon name="edit" size={21} />
            <Text style={styles.editButtonText}>Edit previous answers</Text>
          </Pressable>
        </ScrollView>

        <View style={styles.tabBar}>
          {TABS.map((tab) => {
            const active = tab.title === 'Home';
            return (
              <Pressable
                key={tab.title}
                accessibilityRole="button"
                accessibilityLabel={tab.title}
                accessibilityState={{ selected: active }}
                onPress={() => onTabPress(tab)}
                style={styles.tabButton}
              >
                <View style={[styles.tabActive, active && styles.tabActiveSelected]}>
                  <DashboardIcon name={tab.icon} size={22} color={active ? GREEN : '#758293'} />
                  <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.title}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Modal
        visible={profileModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setProfileModalOpen(false)}
      >
        <View style={styles.modalRoot}>
          <Pressable style={styles.modalScrim} onPress={() => setProfileModalOpen(false)} />
          <View style={styles.editModal}>
            <Text style={styles.modalTitle}>Edit previous answers</Text>
            <Text style={styles.modalSubtitle}>Update the details we use to personalize your advice.</Text>
            <ScrollView style={styles.editFields} keyboardShouldPersistTaps="handled">
              {PROFILE_FIELDS.map((field) => (
                <View key={field.key} style={styles.editField}>
                  <Text style={styles.editFieldLabel}>{field.label}</Text>
                  <TextInput
                    accessibilityLabel={field.label}
                    value={profileDraft[field.key]}
                    onChangeText={(value) => setProfileDraft(current => ({ ...current, [field.key]: value }))}
                    style={styles.editFieldInput}
                    returnKeyType="done"
                  />
                </View>
              ))}
            </ScrollView>
            {saveError ? <Text accessibilityRole="alert" style={styles.saveError}>{saveError}</Text> : null}
            <View style={styles.modalActions}>
              <Pressable accessibilityRole="button" onPress={() => setProfileModalOpen(false)} style={styles.modalCancel}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </Pressable>
              <Pressable accessibilityRole="button" disabled={savingAnswers} onPress={() => void saveProfileAnswers()} style={[styles.modalSave, savingAnswers && styles.modalSaveDisabled]}>
                <Text style={styles.modalSaveText}>{savingAnswers ? 'Saving…' : 'Save answers'}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <Modal
        visible={menuOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setMenuOpen(false)}
      >
        <View style={styles.modalRoot}>
          <Pressable style={styles.modalScrim} onPress={() => setMenuOpen(false)} />
          <View style={styles.profileMenu}>
            <Text style={styles.profileMenuName}>{user.name}</Text>
            <Text style={styles.profileMenuPhone}>{user.phone}</Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setMenuOpen(false);
                router.push('/farmlands/manage' as Href);
              }}
              style={styles.menuAction}
            >
              <Text style={styles.menuActionText}>My farmlands</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setMenuOpen(false);
                logout();
                router.replace('/auth/login' as Href);
              }}
              style={styles.menuAction}
            >
              <Text style={styles.logoutText}>Log out</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </ScreenContainer>
  );
}

function InfoCard({ icon, label, value, wide = false }: {
  icon: FarmProfileIconName;
  label: string;
  value: string;
  wide?: boolean;
}) {
  return (
    <View style={[styles.infoCard, wide && styles.infoCardWide]}>
      <View style={styles.infoIconCircle}><FarmProfileIcon name={icon} size={22} /></View>
      <View style={styles.infoCopy}>
        <Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.82} style={styles.infoLabel}>{label}</Text>
        <Text numberOfLines={2} style={styles.infoValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  page: { flex: 1, minHeight: 0, overflow: 'hidden', width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  header: { minHeight: 49, marginTop: 3, paddingHorizontal: 19, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  brandName: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 18, lineHeight: 22, letterSpacing: -0.35 },
  brandTagline: { color: MUTED, fontFamily: SANS, fontSize: 12.5, lineHeight: 16 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 13 },
  bellButton: { width: 37, height: 42, alignItems: 'center', justifyContent: 'center' },
  avatarButton: { width: 42, height: 42, borderRadius: 22, padding: 2, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e9e6d8' },
  avatar: { width: '100%', height: '100%', borderRadius: 20 },
  scroll: { flex: 1, minHeight: 0 },
  scrollContent: { paddingHorizontal: 17, paddingTop: 9, paddingBottom: 8, gap: 8 },
  intro: { paddingHorizontal: 4, marginBottom: 1 },
  title: { color: INK, fontFamily: SERIF, fontSize: 29, fontWeight: '700', lineHeight: 35, letterSpacing: -0.8 },
  titleCompact: { fontSize: 27, lineHeight: 33 },
  subtitle: { color: MUTED, fontFamily: SANS, fontSize: 15, lineHeight: 19, letterSpacing: -0.12 },
  progressCard: { minHeight: 98, overflow: 'hidden', borderRadius: 18, borderWidth: 1, borderColor: '#fff', backgroundColor: '#fffefa', boxShadow: '0px 3px 12px rgba(30,54,37,0.07)', elevation: 2 },
  progressImage: { flex: 1, minHeight: 98, justifyContent: 'center' },
  progressImageAsset: { resizeMode: 'cover', opacity: 0.94 },
  progressFade: { ...StyleSheet.absoluteFill },
  progressContent: { paddingHorizontal: 11, paddingVertical: 8 },
  progressHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  progressIconCircle: { width: 39, height: 39, borderRadius: 22, backgroundColor: 'rgba(237,244,228,0.94)', alignItems: 'center', justifyContent: 'center' },
  progressCopy: { minWidth: 0, flexShrink: 1 },
  progressTitle: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 19, lineHeight: 23, letterSpacing: -0.45 },
  progressSubtitle: { color: MUTED, fontFamily: SANS, fontSize: 13.5, lineHeight: 18 },
  progressPercent: { color: '#095d43', fontFamily: SERIF, fontWeight: '700', fontSize: 28, lineHeight: 32, marginTop: 1, marginLeft: 5 },
  progressTrack: { height: 9, marginHorizontal: 1, borderRadius: 8, backgroundColor: 'rgba(159,174,149,0.37)', overflow: 'hidden' },
  progressFill: { width: '72%', height: '100%', borderRadius: 8, backgroundColor: '#176b3d' },
  summaryCard: { paddingHorizontal: 7, paddingTop: 7, paddingBottom: 7, gap: 4, borderRadius: 17, borderWidth: 1, borderColor: '#fff', backgroundColor: 'rgba(255,254,250,0.94)', boxShadow: '0px 3px 12px rgba(30,54,37,0.06)', elevation: 2 },
  summaryHeader: { minHeight: 25, paddingHorizontal: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginBottom: 1 },
  summaryHeading: { flexDirection: 'row', alignItems: 'center', gap: 7, flexShrink: 1 },
  sectionTitle: { color: INK, fontFamily: SERIF, fontSize: 15.5, lineHeight: 20, fontWeight: '700', letterSpacing: -0.55 },
  sectionTitleCompact: { fontSize: 14.5, lineHeight: 18 },
  editLink: { minHeight: 30, flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: 1, flexShrink: 0, paddingLeft: 1 },
  editLinkText: { color: MUTED, fontFamily: SANS, fontSize: 9, lineHeight: 13 },
  editLinkTextCompact: { fontSize: 8.5 },
  summaryRow: { flexDirection: 'row', gap: 5, minHeight: 41 },
  summaryRowCompact: { minHeight: 43 },
  infoCard: { flex: 1, minWidth: 0, minHeight: 41, paddingHorizontal: 4, paddingVertical: 4, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 13, borderWidth: 1, borderColor: '#f1eee5', backgroundColor: 'rgba(255,254,250,0.94)' },
  infoCardWide: { flex: 1 },
  infoIconCircle: { width: 29, height: 29, flexShrink: 0, borderRadius: 16, backgroundColor: '#eef4e6', alignItems: 'center', justifyContent: 'center' },
  infoCopy: { flex: 1, minWidth: 0 },
  infoLabel: { color: '#162c32', fontFamily: SANS, fontSize: 10.8, lineHeight: 13, fontWeight: '500' },
  infoValue: { color: MUTED, fontFamily: SANS, fontSize: 10.4, lineHeight: 12.5 },
  cropSection: { paddingHorizontal: 8, paddingTop: 8, paddingBottom: 7, gap: 6, borderRadius: 17, borderWidth: 1, borderColor: '#fff', backgroundColor: 'rgba(255,254,250,0.96)', boxShadow: '0px 3px 12px rgba(30,54,37,0.06)', elevation: 2 },
  cropSectionHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: 7 },
  cropSectionIcon: { width: 25, alignItems: 'center', paddingTop: 2 },
  cropHeadingCopy: { flex: 1, minWidth: 0 },
  cropHeading: { color: INK, fontFamily: SERIF, fontSize: 17, lineHeight: 20, fontWeight: '700', letterSpacing: -0.4 },
  cropHeadingCompact: { fontSize: 15.5, lineHeight: 18 },
  cropSubtitle: { color: MUTED, fontFamily: SANS, fontSize: 12.2, lineHeight: 16, marginTop: 2 },
  cropOptions: { flexDirection: 'row', gap: 6 },
  cropCard: { flex: 1, minWidth: 0, overflow: 'hidden', borderRadius: 14, borderWidth: 1, borderColor: '#f1eee5', backgroundColor: '#fffefa' },
  cropCardSelected: { borderWidth: 2, borderColor: '#17643b' },
  cropImageWrap: { overflow: 'hidden', borderTopLeftRadius: 12, borderTopRightRadius: 12 },
  cropImage: { width: '100%', aspectRatio: 1.62, justifyContent: 'flex-start', alignItems: 'flex-end' },
  cropImagePlaceholder: { alignItems: 'center', justifyContent: 'center', backgroundColor: '#e9f2e5' },
  cropImageAsset: { resizeMode: 'cover' },
  selectedMark: { width: 24, height: 24, marginTop: 4, marginRight: 4, borderRadius: 13, borderWidth: 1.4, borderColor: '#fff', backgroundColor: GREEN, alignItems: 'center', justifyContent: 'center' },
  cropCopy: { minHeight: 43, paddingHorizontal: 6, paddingTop: 4, paddingBottom: 5 },
  cropName: { color: INK, fontFamily: SERIF, fontSize: 14.4, lineHeight: 18, fontWeight: '700', letterSpacing: -0.3 },
  cropNameCompact: { fontSize: 13.1, lineHeight: 16 },
  cropDescription: { color: MUTED, fontFamily: SANS, fontSize: 10.7, lineHeight: 13 },
  cropDescriptionCompact: { fontSize: 9.8, lineHeight: 12 },
  continueButton: { minHeight: 46, marginHorizontal: 6, paddingLeft: 15, paddingRight: 4, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderRadius: 27, backgroundColor: '#145b3a', boxShadow: '0px 3px 8px rgba(12,72,46,0.14)', elevation: 2 },
  continueText: { flex: 1, color: PAPER, fontFamily: SERIF, fontSize: 19, fontWeight: '700', lineHeight: 25, textAlign: 'center', marginLeft: 30 },
  continueArrow: { width: 36, height: 36, borderRadius: 19, alignItems: 'center', justifyContent: 'center', backgroundColor: PAPER },
  editButton: { minHeight: 42, marginHorizontal: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 23, borderWidth: 1.2, borderColor: '#17643b', backgroundColor: 'rgba(255,253,247,0.9)' },
  editButtonText: { color: INK, fontFamily: SANS, fontSize: 15, lineHeight: 20, fontWeight: '500' },
  tabBar: { minHeight: 56, marginHorizontal: 8, marginBottom: 2, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,254,250,0.97)', borderRadius: 18, borderWidth: 1, borderColor: '#fff', boxShadow: '0px -2px 12px rgba(48,55,44,0.08)', elevation: 4 },
  tabButton: { flex: 1, minWidth: 0, alignItems: 'stretch', justifyContent: 'center' },
  tabActive: { minHeight: 46, borderRadius: 14, alignItems: 'center', justifyContent: 'center', gap: 0 },
  tabActiveSelected: { backgroundColor: '#edf3e8' },
  tabLabel: { color: '#53637b', fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  tabLabelActive: { color: INK, fontWeight: '600' },
  modalRoot: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 22 },
  modalScrim: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(11,28,22,0.34)' },
  editModal: { width: '100%', maxWidth: 430, maxHeight: '88%', padding: 18, borderRadius: 20, backgroundColor: PAPER, boxShadow: '0px 8px 28px rgba(0,0,0,0.2)', elevation: 10 },
  modalTitle: { color: INK, fontFamily: SERIF, fontSize: 22, fontWeight: '700', lineHeight: 28 },
  modalSubtitle: { color: MUTED, fontFamily: SANS, fontSize: 14, lineHeight: 20, marginTop: 3, marginBottom: 10 },
  editFields: { flexGrow: 0 },
  editField: { marginBottom: 9 },
  editFieldLabel: { color: INK, fontFamily: SANS, fontSize: 13, fontWeight: '600', marginBottom: 4 },
  editFieldInput: { minHeight: 42, paddingHorizontal: 11, borderRadius: 11, borderWidth: 1, borderColor: '#dfe5d8', color: INK, backgroundColor: '#fffefa', fontFamily: SANS, fontSize: 14 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 9, marginTop: 9 },
  modalCancel: { minHeight: 42, minWidth: 84, alignItems: 'center', justifyContent: 'center', borderRadius: 22, borderWidth: 1, borderColor: '#cbd4c8' },
  modalCancelText: { color: INK, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  modalSave: { minHeight: 42, minWidth: 120, alignItems: 'center', justifyContent: 'center', borderRadius: 22, backgroundColor: GREEN },
  modalSaveDisabled: { opacity: 0.6 },
  modalSaveText: { color: '#fff', fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  saveError: { color: '#b42318', fontFamily: SANS, fontSize: 12, lineHeight: 16, marginTop: 8 },
  profileMenu: { position: 'absolute', top: 62, right: 18, width: 220, padding: 15, borderRadius: 16, backgroundColor: PAPER, boxShadow: '0px 5px 16px rgba(0,0,0,0.18)', elevation: 8 },
  profileMenuName: { color: INK, fontFamily: SERIF, fontSize: 16, fontWeight: '700' },
  profileMenuPhone: { color: MUTED, fontFamily: SANS, fontSize: 12, marginTop: 2, marginBottom: 10 },
  menuAction: { minHeight: 42, justifyContent: 'center', borderTopWidth: 1, borderColor: '#eeeadd' },
  menuActionText: { color: GREEN, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  logoutText: { color: '#b54537', fontFamily: SANS, fontSize: 14, fontWeight: '600' },
});

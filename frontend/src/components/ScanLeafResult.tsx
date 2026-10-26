import { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import type { ImageSourcePropType } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { DiseaseAnalysis, DiseaseResult } from '../utils/disease-api';
import { ScanResultIcon } from './scan-result-icons';
import type { ScanResultIconName } from './scan-result-icons';

const PAPER = '#fbf9f2';
const CARD = '#fffefa';
const INK = '#103832';
const GREEN = '#245d40';
const MUTED = '#596a7d';
const SERIF = 'Georgia';
const SANS = 'Arial';

type TabName = 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile';
type Action = { title: string; detail: string; icon: ScanResultIconName };

type Props = {
  analysis: DiseaseAnalysis;
  photoUri?: string;
  previewPhoto?: boolean;
  retrying: boolean;
  retryError?: string | null;
  onBack: () => void;
  onRetake: () => void;
  onFarmLog: () => void;
  onTabPress: (tab: TabName) => void;
};

type CaptureProps = {
  hasBackendFarmId: boolean;
  photoUri?: string;
  photoName?: string;
  photoSize?: number;
  loading: boolean;
  error?: string;
  history: DiseaseResult[];
  historyLoading: boolean;
  historyMessage?: string;
  retryingId: string | null;
  retryError?: { resultId: string; message: string } | null;
  onBack: () => void;
  onChoosePhoto: () => void;
  onTakePhoto: () => void;
  onAnalyze: () => void;
  onRetry: (resultId: string) => void;
  onTabPress: (tab: TabName) => void;
};

const BROWN_SPOT_ACTIONS: Action[] = [
  { title: 'Inspect nearby plants', detail: 'Check surrounding leaves for similar spotting.', icon: 'sprout' },
  { title: 'Manage watering carefully', detail: 'Avoid unnecessary standing moisture.', icon: 'drop' },
  { title: 'Seek local treatment guidance', detail: 'Use approved fungicide advice or contact an extension officer.', icon: 'document' },
];

const SAFE_ACTIONS: Action[] = [
  { title: 'Inspect nearby plants', detail: 'Check other leaves for similar signs.', icon: 'sprout' },
  { title: 'Avoid excess moisture', detail: 'Keep the affected area well drained.', icon: 'drop' },
  { title: 'Ask an extension officer', detail: 'Confirm treatment locally before applying it.', icon: 'document' },
];

const TABS: { title: TabName; icon: ScanResultIconName }[] = [
  { title: 'Home', icon: 'home' },
  { title: 'Tasks', icon: 'tasks' },
  { title: 'Chat', icon: 'chat' },
  { title: 'Scan', icon: 'focus' },
  { title: 'Profile', icon: 'profile' },
];

function ScanLeafHeader({ compact, phone, onBack }: { compact: boolean; phone: boolean; onBack: () => void }) {
  return (
    <View style={[styles.header, phone && styles.headerPhone]}>
      <Pressable accessibilityRole="button" accessibilityLabel="Back to farm" onPress={onBack} style={styles.backButton} hitSlop={8}>
        <ScanResultIcon name="back" size={21} color={INK} />
      </Pressable>
      <View style={styles.headerCopy}>
        <Text style={[styles.pageTitle, compact && styles.pageTitleCompact]}>Scan Leaf</Text>
        <Text style={[styles.pageSubtitle, compact && styles.pageSubtitleCompact]}>
          Detect likely crop problems from a plant photo.
        </Text>
      </View>
    </View>
  );
}

function ScanLeafTabs({ onTabPress }: { onTabPress: (tab: TabName) => void }) {
  return (
    <View style={styles.tabBar}>
      {TABS.map(tab => {
        const active = tab.title === 'Scan';
        return (
          <Pressable
            key={tab.title}
            accessibilityRole="button"
            accessibilityLabel={tab.title}
            accessibilityState={{ selected: active }}
            onPress={() => onTabPress(tab.title)}
            style={styles.tabButton}
          >
            <View style={[styles.tabContent, active && styles.tabContentActive]}>
              <ScanResultIcon name={tab.icon} size={21} color={active ? GREEN : '#778291'} />
              <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.title}</Text>
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

export default function ScanLeafResult({
  analysis,
  photoUri,
  previewPhoto = false,
  retrying,
  retryError,
  onBack,
  onRetake,
  onFarmLog,
  onTabPress,
}: Props) {
  const { width, height } = useWindowDimensions();
  const phone = width < 600;
  const compact = width < 400 || height < 760;
  const veryCompact = width < 370 || height < 690;
  const narrowPhone = width < 340;
  const [selectedAction, setSelectedAction] = useState<Action | null>(null);
  const result = analysis.disease_result;
  const confidence = result.confidence === null
    ? null
    : Math.round(Math.max(0, Math.min(1, result.confidence)) * 100);
  const issueName = result.possible_issue?.trim() || 'Crop issue';
  const isPossibleIssue = analysis.outcome === 'possible_disease';
  const isRecorded = analysis.problem_sync === 'created' || analysis.problem_sync === 'reused';
  const photoSource: ImageSourcePropType | undefined = photoUri
    ? { uri: photoUri }
    : previewPhoto
      ? require('../../assets/images/scan-leaf-preview.jpg')
      : undefined;
  const actions = isKnownBrownSpot(issueName)
    ? BROWN_SPOT_ACTIONS
    : result.recommended_actions.length > 0
      ? result.recommended_actions.slice(0, 3).map((title, index) => ({
        title,
        detail: SAFE_ACTIONS[index]?.detail ?? 'Ask a local extension officer for guidance.',
        icon: SAFE_ACTIONS[index]?.icon ?? 'document',
      }))
      : SAFE_ACTIONS;
  const symptoms = getSymptomsSummary(analysis);
  const mainPhotoWidth = Math.min(width, 480) - 38;
  const photoHeight = mainPhotoWidth / 2.55;
  const farmLogTitle = isRecorded
    ? 'Add to farm log'
    : analysis.problem_sync === 'failed'
      ? retrying ? 'Saving to farm log…' : 'Retry farm log'
      : 'View farm log';

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.page}>
        <ScanLeafHeader compact={compact} phone={phone} onBack={onBack} />

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[
            styles.content,
            { minHeight: Math.max(0, height - (phone ? 50 : 72) - 52) },
            compact && styles.contentCompact,
            veryCompact && styles.contentVeryCompact,
          ]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.photoFrame, { height: photoHeight }]}>
            {photoSource ? (
              <Image
                source={photoSource}
                style={styles.photo}
                resizeMode="cover"
                accessibilityLabel="Leaf photo analyzed for crop problems"
              />
            ) : (
              <View style={styles.photoPlaceholder}>
                <ScanResultIcon name="focus" size={34} color={GREEN} />
                <Text style={styles.photoPlaceholderText}>Analyzed leaf photo</Text>
              </View>
            )}
            <View style={styles.photoFocus}>
              <ScanResultIcon name="focus" size={25} color={GREEN} />
            </View>
          </View>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Open farm problems for ${issueName}`}
            onPress={onFarmLog}
            style={[styles.issueCard, compact && styles.issueCardCompact]}
          >
            <View style={styles.issueCopy}>
              <View style={styles.issueEyebrow}>
                <ScanResultIcon
                  name={isPossibleIssue ? 'warning' : 'leaf'}
                  size={19}
                  color={isPossibleIssue ? '#b56009' : GREEN}
                />
                <Text style={[styles.issueLabel, !isPossibleIssue && styles.issueLabelGreen]}>
                  {isPossibleIssue ? 'Possible issue' : analysis.outcome === 'healthy' ? 'Healthy leaf' : 'Uncertain result'}
                </Text>
              </View>
              <Text numberOfLines={1} adjustsFontSizeToFit style={[styles.issueTitle, compact && styles.issueTitleCompact]}>
                {analysis.outcome === 'healthy' ? 'No issue found' : analysis.outcome === 'uncertain' ? 'Needs another look' : issueName}
              </Text>
              <Text numberOfLines={2} style={styles.issueDescription}>
                {issueDescription(analysis, issueName)}
              </Text>
            </View>
            <View style={styles.arrowCircle}>
              <ScanResultIcon name="chevron" size={17} color="#314a60" />
            </View>
          </Pressable>

          <View style={[styles.confidenceCard, compact && styles.confidenceCardCompact]}>
            <View style={[styles.metricColumn, narrowPhone && styles.metricColumnNarrow]}>
              <View style={styles.metricHeading}>
                <View style={styles.metricIconCircle}>
                  <ScanResultIcon name="signal" size={19} color={GREEN} />
                </View>
                <View style={styles.metricText}>
                  <Text style={styles.metricLabel}>Confidence</Text>
                  <Text style={styles.metricValue}>{capitalize(analysis.confidence_level)}</Text>
                </View>
              </View>
              <View style={styles.confidenceTrackRow}>
                <View style={styles.confidenceTrack}>
                  <View style={[styles.confidenceFill, { width: `${confidence ?? 0}%` }]} />
                </View>
                <Text style={styles.confidenceNumber}>{confidence === null ? '—' : `${confidence}%`}</Text>
              </View>
            </View>
            <View style={styles.verticalRule} />
            <View style={[styles.metricColumn, narrowPhone && styles.symptomsColumnNarrow]}>
              <View style={styles.metricHeading}>
                <View style={styles.metricIconCircle}>
                  <ScanResultIcon name="leaf" size={21} color={GREEN} />
                </View>
                <View style={styles.metricText}>
                    <Text numberOfLines={1} style={[styles.metricLabel, narrowPhone && styles.metricLabelNarrow]}>Observed symptoms</Text>
                  <Text style={styles.symptomsText}>{symptoms}</Text>
                </View>
              </View>
            </View>
          </View>

          <View style={[styles.actionsCard, compact && styles.actionsCardCompact]}>
            <View style={styles.actionsHeading}>
              <ScanResultIcon name="list" size={21} color={INK} />
              <Text style={[styles.actionsTitle, compact && styles.actionsTitleCompact]}>Recommended actions</Text>
            </View>
            <View style={styles.actionRows}>
              {actions.map((action, index) => (
                <Pressable
                  key={`${action.title}-${index}`}
                  accessibilityRole="button"
                  accessibilityLabel={`${action.title}. ${action.detail}`}
                  onPress={() => setSelectedAction(action)}
                  style={[styles.actionRow, compact && styles.actionRowCompact, index === actions.length - 1 && styles.actionRowLast]}
                >
                  <View style={styles.actionNumber}><Text style={styles.actionNumberText}>{index + 1}</Text></View>
                  <View style={styles.actionIcon}><ScanResultIcon name={action.icon} size={24} color={GREEN} /></View>
                  <View style={styles.actionCopy}>
                    <Text numberOfLines={narrowPhone ? 2 : 1} style={[styles.actionTitle, narrowPhone && styles.actionTitleNarrow]}>{action.title}</Text>
                    <Text numberOfLines={2} style={styles.actionDetail}>{action.detail}</Text>
                  </View>
                  <View style={styles.arrowCircleSmall}>
                    <ScanResultIcon name="chevron" size={15} color="#314a60" />
                  </View>
                </Pressable>
              ))}
            </View>
          </View>

          <View style={[styles.statusCard, isRecorded ? styles.statusRecorded : styles.statusPending]}>
            <View style={[styles.statusIconCircle, isRecorded ? styles.statusIconRecorded : styles.statusIconPending]}>
              <ScanResultIcon name={isRecorded ? 'check' : 'warning'} size={22} color={isRecorded ? '#fffefa' : '#a85d08'} />
            </View>
            <View style={styles.statusCopy}>
              <Text style={[styles.statusTitle, !isRecorded && styles.statusTitlePending]}>
                {isRecorded ? 'Recorded in your farm log' : analysis.problem_sync === 'failed' ? 'Farm log sync needs attention' : 'No farm problem was recorded'}
              </Text>
                  <Text numberOfLines={1} style={styles.statusDetail}>
                {analysis.problem_sync === 'created'
                  ? 'This issue has been saved as an open farm problem for follow-up.'
                  : analysis.problem_sync === 'reused'
                    ? 'A matching open farm problem is already saved for follow-up.'
                    : analysis.problem_sync === 'failed'
                      ? 'The analysis is saved. Try again to finish recording the farm problem.'
                      : 'Healthy or uncertain results are kept in your analysis history without opening a farm problem.'}
              </Text>
            </View>
          </View>

          {retryError ? <Text accessibilityRole="alert" style={styles.retryError}>{retryError}</Text> : null}

          <View style={[styles.noticeCard, compact && styles.noticeCardCompact]}>
            <View style={styles.noticeIconCircle}>
              <ScanResultIcon name="warning" size={22} color="#b66a08" />
            </View>
            <View style={styles.noticeCopy}>
              <Text style={styles.noticeTitle}>AI estimate — confirm if symptoms worsen.</Text>
              <Text style={styles.noticeText}>
                {analysis.disclaimer || 'This result is based on the image and may require local expert verification.'}
              </Text>
            </View>
          </View>

          <View style={styles.bottomSpacer} />

          <View style={styles.buttonRow}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Retake crop photo"
              onPress={onRetake}
              style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
            >
              <ScanResultIcon name="camera" size={21} color={INK} />
              <Text numberOfLines={1} style={styles.secondaryButtonText}>Retake photo</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={farmLogTitle}
              accessibilityState={{ disabled: retrying }}
              disabled={retrying}
              onPress={onFarmLog}
              style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed, retrying && styles.disabledButton]}
            >
              <ScanResultIcon name="add-document" size={21} color={CARD} />
              <Text numberOfLines={1} style={styles.primaryButtonText}>{farmLogTitle}</Text>
            </Pressable>
          </View>
        </ScrollView>

        <ScanLeafTabs onTabPress={onTabPress} />
      </View>

      <Modal
        visible={selectedAction !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setSelectedAction(null)}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => setSelectedAction(null)}>
          <View style={styles.actionModal}>
            <View style={styles.modalIconCircle}>
              <ScanResultIcon name={selectedAction?.icon ?? 'leaf'} size={24} color={GREEN} />
            </View>
            <Text style={styles.modalTitle}>{selectedAction?.title}</Text>
            <Text style={styles.modalDescription}>{selectedAction?.detail}</Text>
            <Pressable accessibilityRole="button" onPress={() => setSelectedAction(null)} style={styles.modalButton}>
              <Text style={styles.modalButtonText}>Done</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

export function ScanLeafCapture({
  hasBackendFarmId,
  photoUri,
  photoName,
  photoSize,
  loading,
  error,
  history,
  historyLoading,
  historyMessage,
  retryingId,
  retryError,
  onBack,
  onChoosePhoto,
  onTakePhoto,
  onAnalyze,
  onRetry,
  onTabPress,
}: CaptureProps) {
  const { width, height } = useWindowDimensions();
  const phone = width < 600;
  const compact = width < 400 || height < 760;
  const photoHeight = (Math.min(width, 480) - 38) / 2.55;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.page}>
        <ScanLeafHeader compact={compact} phone={phone} onBack={onBack} />
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[
            styles.content,
            { minHeight: Math.max(0, height - (phone ? 50 : 72) - 52) },
            compact && styles.contentCompact,
          ]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.photoFrame, styles.capturePhotoFrame, { height: photoHeight }]}>
            {photoUri ? (
              <Image source={{ uri: photoUri }} style={styles.photo} resizeMode="cover" accessibilityLabel="Selected crop photo" />
            ) : (
              <View style={styles.photoPlaceholder}>
                <ScanResultIcon name="focus" size={31} color={GREEN} />
                <Text style={styles.photoPlaceholderTitle}>Choose a clear leaf photo</Text>
                <Text style={styles.photoPlaceholderText}>Keep the affected area in frame.</Text>
              </View>
            )}
            {photoUri ? (
              <View style={styles.photoFocus}>
                <ScanResultIcon name="focus" size={25} color={GREEN} />
              </View>
            ) : null}
          </View>

          <View style={styles.captureCard}>
            <Text style={styles.captureHeading}>{photoUri ? 'Photo ready to check' : 'Start with one plant photo'}</Text>
            <Text style={styles.captureBody}>
              Use daylight and focus on one affected leaf. The active crop and growth stage come from your farm season.
            </Text>
            <View style={styles.captureActions}>
              <Pressable
                accessibilityRole="button"
                disabled={loading || retryingId !== null}
                onPress={onChoosePhoto}
                style={({ pressed }) => [styles.captureActionButton, pressed && styles.pressed, (loading || retryingId !== null) && styles.disabledButton]}
              >
                <ScanResultIcon name="document" size={19} color={GREEN} />
                <Text style={styles.captureActionText}>Choose photo</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                disabled={loading || retryingId !== null}
                onPress={onTakePhoto}
                style={({ pressed }) => [styles.captureActionButton, pressed && styles.pressed, (loading || retryingId !== null) && styles.disabledButton]}
              >
                <ScanResultIcon name="camera" size={19} color={GREEN} />
                <Text style={styles.captureActionText}>Take photo</Text>
              </Pressable>
            </View>
            {photoUri ? (
              <View style={styles.selectedPhoto}>
                <View style={styles.selectedPhotoCopy}>
                  <Text numberOfLines={1} style={styles.selectedPhotoName}>{photoName || 'Crop photo'}</Text>
                  <Text style={styles.selectedPhotoMeta}>
                    {photoSize ? `${Math.ceil(photoSize / 1024)} KB · ` : ''}JPEG, PNG, or WebP · up to 10 MB
                  </Text>
                </View>
                <Pressable
                  accessibilityRole="button"
                  disabled={loading || !hasBackendFarmId || retryingId !== null}
                  accessibilityState={{ disabled: loading || !hasBackendFarmId || retryingId !== null }}
                  onPress={onAnalyze}
                  style={({ pressed }) => [styles.analyzeButton, pressed && styles.pressed, (!hasBackendFarmId || loading || retryingId !== null) && styles.disabledButton]}
                >
                  {loading ? <ActivityIndicator color={CARD} size="small" /> : <ScanResultIcon name="focus" size={18} color={CARD} />}
                  <Text style={styles.analyzeText}>{loading ? 'Analyzing…' : 'Analyze photo'}</Text>
                </Pressable>
              </View>
            ) : (
              <Text style={styles.captureMeta}>JPEG, PNG, or WebP · up to 10 MB</Text>
            )}
            {!hasBackendFarmId ? (
              <View style={styles.connectionNote}>
                <ScanResultIcon name="warning" size={17} color="#ae640b" />
                <Text style={styles.connectionText}>Connect a saved farm to send this photo for analysis.</Text>
              </View>
            ) : null}
            {error ? <Text accessibilityRole="alert" style={styles.captureError}>{error}</Text> : null}
          </View>

          <View style={styles.guidanceCard}>
            <View style={styles.guidanceHeading}>
              <ScanResultIcon name="leaf" size={18} color={GREEN} />
              <Text style={styles.captureHeading}>Photo guidance</Text>
            </View>
            <Text style={styles.guidanceBody}>Take the photo in daylight and keep nearby plants out of focus. The model offers an estimate; a local expert can confirm treatment.</Text>
            <Text style={styles.privacyNote}>If Gemini verification is enabled, the photo is also sent to Google Gemini for a separate visual check.</Text>
          </View>

          <View style={styles.historyHeading}>
            <Text style={styles.captureHeading}>Previous analyses</Text>
            {historyLoading ? <ActivityIndicator color={GREEN} size="small" /> : null}
          </View>
          {historyMessage ? <Text accessibilityRole="alert" style={styles.historyMessage}>{historyMessage}</Text> : null}
          {!historyLoading && history.length === 0 ? (
            <View style={styles.historyCard}><Text style={styles.captureBody}>Saved disease checks will appear here.</Text></View>
          ) : history.map(item => (
            <View key={item.id} style={styles.historyCard}>
              <View style={styles.historyTop}>
                <Text numberOfLines={1} style={styles.historyTitle}>{item.possible_issue || 'Disease check'}</Text>
                <Text style={styles.historyOutcome}>{resultOutcome(item)}</Text>
              </View>
              <Text style={styles.historyDate}>
                {item.crop_name || 'Crop'} · {new Date(item.created_at).toLocaleString()}
              </Text>
              {item.model_details.problem_sync === 'created' || item.model_details.problem_sync === 'reused' ? (
                <Text style={styles.historyRecorded}>Linked to a farm problem.</Text>
              ) : null}
              {item.model_details.problem_sync === 'failed' ? (
                <View style={styles.historyRetry}>
                  {retryError?.resultId === item.id ? <Text accessibilityRole="alert" style={styles.captureError}>{retryError.message}</Text> : null}
                  <Pressable
                    accessibilityRole="button"
                    disabled={retryingId !== null}
                    onPress={() => onRetry(item.id)}
                    style={({ pressed }) => [styles.retryButton, pressed && styles.pressed, retryingId !== null && styles.disabledButton]}
                  >
                    <Text style={styles.retryButtonText}>{retryingId === item.id ? 'Retrying…' : 'Retry farm log sync'}</Text>
                  </Pressable>
                </View>
              ) : null}
            </View>
          ))}
          <View style={styles.bottomSpacer} />
        </ScrollView>
        <ScanLeafTabs onTabPress={onTabPress} />
      </View>
    </SafeAreaView>
  );
}

function isKnownBrownSpot(issueName: string) {
  return issueName.toLowerCase().includes('brown spot');
}

function getSymptomsSummary(analysis: DiseaseAnalysis) {
  const symptoms = analysis.disease_result.symptoms;
  if (symptoms.length > 0) return symptoms.join(', ');
  if (isKnownBrownSpot(analysis.disease_result.possible_issue ?? '')) {
    return 'Small oval brown lesions with yellowish margins.';
  }
  if (analysis.verification.visible_signs) return analysis.verification.visible_signs;
  return 'Review the leaf closely for changes in color, shape, or texture.';
}

function issueDescription(analysis: DiseaseAnalysis, issueName: string) {
  if (analysis.outcome === 'healthy') return `The photo looks healthy for ${analysis.crop_name}.`;
  if (analysis.outcome === 'uncertain') return 'The photo needs a clearer view or local review.';
  if (isKnownBrownSpot(issueName)) return `A likely fungal disease affecting ${analysis.crop_name.toLowerCase()} leaves.`;
  return analysis.message || `The photo may show a crop problem affecting ${analysis.crop_name.toLowerCase()}.`;
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function resultOutcome(result: DiseaseResult) {
  const outcome = result.model_details.outcome;
  return typeof outcome === 'string' ? outcome.replace(/_/g, ' ') : 'saved';
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  page: { flex: 1, minHeight: 0, width: '100%', maxWidth: 480, alignSelf: 'center', overflow: 'hidden', backgroundColor: PAPER },
  header: { height: 72, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 18 },
  headerPhone: { height: 50 },
  backButton: { position: 'absolute', left: 19, top: 10, zIndex: 1, width: 30, height: 30, borderRadius: 18, backgroundColor: '#edf0e5', alignItems: 'center', justifyContent: 'center' },
  headerCopy: { position: 'absolute', left: 57, right: 18, top: 0, alignItems: 'center', pointerEvents: 'none' },
  pageTitle: { color: INK, fontFamily: SERIF, fontSize: 22, lineHeight: 27, fontWeight: '700', letterSpacing: -0.45, textAlign: 'center' },
  pageTitleCompact: { fontSize: 21, lineHeight: 25 },
  pageSubtitle: { color: MUTED, fontFamily: SANS, fontSize: 11.5, lineHeight: 16, textAlign: 'center' },
  pageSubtitleCompact: { fontSize: 10.8, lineHeight: 15 },
  scroll: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: 19, paddingTop: 6, paddingBottom: 10, gap: 6 },
  contentCompact: { paddingTop: 4, gap: 3 },
  contentVeryCompact: { paddingHorizontal: 16, gap: 2 },
  photoFrame: { width: '100%', overflow: 'hidden', borderRadius: 15, borderWidth: 1, borderColor: '#fff', backgroundColor: '#e5ebd9', boxShadow: '0px 3px 12px rgba(35, 53, 33, 0.1)', elevation: 2 },
  photo: { width: '100%', height: '100%' },
  photoPlaceholder: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 8 },
  photoPlaceholderText: { color: GREEN, fontFamily: SANS, fontSize: 12 },
  photoPlaceholderTitle: { color: INK, fontFamily: SERIF, fontSize: 15, lineHeight: 19, fontWeight: '700' },
  photoFocus: { position: 'absolute', right: 7, bottom: 7, width: 39, height: 39, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,254,250,0.96)' },
  capturePhotoFrame: { borderStyle: 'dashed', borderWidth: 1.5, borderColor: '#d5decb', boxShadow: 'none', elevation: 0 },
  captureCard: { padding: 12, borderRadius: 16, borderWidth: 1, borderColor: '#fff', backgroundColor: CARD, boxShadow: '0px 3px 12px rgba(35, 53, 33, 0.075)', elevation: 2 },
  captureHeading: { color: INK, fontFamily: SERIF, fontSize: 15, lineHeight: 19, fontWeight: '700' },
  captureBody: { marginTop: 4, color: MUTED, fontFamily: SANS, fontSize: 11, lineHeight: 15 },
  captureActions: { flexDirection: 'row', gap: 8, marginTop: 11 },
  captureActionButton: { minHeight: 44, flex: 1, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 13, borderWidth: 1, borderColor: '#cbd9cb', backgroundColor: '#fbfcf7' },
  captureActionText: { color: GREEN, fontFamily: SANS, fontSize: 12, lineHeight: 16, fontWeight: '600' },
  captureMeta: { marginTop: 9, color: MUTED, fontFamily: SANS, fontSize: 10, lineHeight: 13, textAlign: 'center' },
  selectedPhoto: { marginTop: 10, paddingTop: 9, flexDirection: 'row', alignItems: 'center', gap: 8, borderTopWidth: 1, borderTopColor: '#eee9de' },
  selectedPhotoCopy: { flex: 1, minWidth: 0 },
  selectedPhotoName: { color: INK, fontFamily: SERIF, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  selectedPhotoMeta: { color: MUTED, fontFamily: SANS, fontSize: 9, lineHeight: 12 },
  analyzeButton: { minHeight: 42, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, borderRadius: 12, backgroundColor: GREEN },
  analyzeText: { color: CARD, fontFamily: SANS, fontSize: 11.5, lineHeight: 15, fontWeight: '600' },
  connectionNote: { marginTop: 10, paddingTop: 8, flexDirection: 'row', alignItems: 'center', gap: 7, borderTopWidth: 1, borderTopColor: '#eee9de' },
  connectionText: { flex: 1, color: '#9a5b12', fontFamily: SANS, fontSize: 10, lineHeight: 14 },
  captureError: { marginTop: 8, color: '#a53327', fontFamily: SANS, fontSize: 11, lineHeight: 15 },
  guidanceCard: { padding: 12, borderRadius: 16, borderWidth: 1, borderColor: '#fff', backgroundColor: '#f2f5ed' },
  guidanceHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  guidanceBody: { marginTop: 5, color: MUTED, fontFamily: SANS, fontSize: 11, lineHeight: 15 },
  privacyNote: { marginTop: 6, color: '#7b8490', fontFamily: SANS, fontSize: 9.5, lineHeight: 13 },
  historyHeading: { marginTop: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  historyMessage: { color: '#a53327', fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  historyCard: { padding: 10, borderRadius: 14, borderWidth: 1, borderColor: '#f0ede5', backgroundColor: CARD },
  historyTop: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  historyTitle: { flex: 1, color: INK, fontFamily: SERIF, fontSize: 12, lineHeight: 15, fontWeight: '700' },
  historyOutcome: { color: MUTED, fontFamily: SANS, fontSize: 9, lineHeight: 12, textTransform: 'capitalize' },
  historyDate: { marginTop: 3, color: MUTED, fontFamily: SANS, fontSize: 9.5, lineHeight: 13 },
  historyRecorded: { marginTop: 4, color: GREEN, fontFamily: SANS, fontSize: 9.5, lineHeight: 13 },
  historyRetry: { marginTop: 6, gap: 4 },
  retryButton: { minHeight: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 11, borderWidth: 1, borderColor: GREEN, backgroundColor: PAPER },
  retryButtonText: { color: GREEN, fontFamily: SANS, fontSize: 11, lineHeight: 14, fontWeight: '600' },
  issueCard: { minHeight: 63, paddingHorizontal: 13, paddingVertical: 4, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 17, borderWidth: 1, borderColor: '#fff', backgroundColor: CARD, boxShadow: '0px 3px 12px rgba(35, 53, 33, 0.075)', elevation: 2 },
  issueCardCompact: { minHeight: 61, paddingVertical: 4 },
  issueCopy: { flex: 1, minWidth: 0 },
  issueEyebrow: { height: 17, flexDirection: 'row', alignItems: 'center', gap: 8 },
  issueLabel: { color: '#a75208', fontFamily: SERIF, fontSize: 11.5, lineHeight: 15, fontWeight: '700' },
  issueLabelGreen: { color: GREEN },
  issueTitle: { color: '#102f35', fontFamily: SERIF, fontSize: 24, lineHeight: 27, fontWeight: '700', letterSpacing: -0.45 },
  issueTitleCompact: { fontSize: 21.5, lineHeight: 24 },
  issueDescription: { color: MUTED, fontFamily: SANS, fontSize: 10.4, lineHeight: 13 },
  arrowCircle: { width: 28, height: 28, borderRadius: 15, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#f1eee7', backgroundColor: CARD, boxShadow: '0px 1px 4px rgba(0,0,0,0.06)' },
  confidenceCard: { minHeight: 63, padding: 6, flexDirection: 'row', alignItems: 'stretch', borderRadius: 17, borderWidth: 1, borderColor: '#fff', backgroundColor: CARD, boxShadow: '0px 3px 12px rgba(35, 53, 33, 0.075)', elevation: 2 },
  confidenceCardCompact: { minHeight: 60, padding: 5 },
  metricColumn: { flex: 1, minWidth: 0, justifyContent: 'center' },
  metricColumnNarrow: { flex: 0.9 },
  symptomsColumnNarrow: { flex: 1.1 },
  metricHeading: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  metricIconCircle: { width: 30, height: 30, flexShrink: 0, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: '#edf2e8' },
  metricText: { flex: 1, minWidth: 0 },
  metricLabel: { color: INK, fontFamily: SERIF, fontSize: 10.4, lineHeight: 13, fontWeight: '700' },
  metricLabelNarrow: { fontSize: 9.5 },
  metricValue: { color: INK, fontFamily: SERIF, fontSize: 14.5, lineHeight: 18, fontWeight: '700' },
  confidenceTrackRow: { marginTop: 6, paddingLeft: 3, paddingRight: 2, flexDirection: 'row', alignItems: 'center', gap: 7 },
  confidenceTrack: { height: 7, flex: 1, overflow: 'hidden', borderRadius: 5, backgroundColor: '#d9ddd2' },
  confidenceFill: { height: '100%', borderRadius: 5, backgroundColor: '#2f6647' },
  confidenceNumber: { width: 26, color: INK, fontFamily: SANS, fontSize: 10.5, lineHeight: 14, textAlign: 'right' },
  verticalRule: { width: 1, marginHorizontal: 6, backgroundColor: '#e6e1d5' },
  symptomsText: { marginTop: 2, color: MUTED, fontFamily: SANS, fontSize: 9.8, lineHeight: 12 },
  actionsCard: { paddingHorizontal: 7, paddingTop: 5, paddingBottom: 5, borderRadius: 17, borderWidth: 1, borderColor: '#fff', backgroundColor: CARD, boxShadow: '0px 3px 12px rgba(35, 53, 33, 0.075)', elevation: 2 },
  actionsCardCompact: { paddingTop: 5, paddingBottom: 5 },
  actionsHeading: { minHeight: 20, paddingHorizontal: 3, marginBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 8 },
  actionsTitle: { color: INK, fontFamily: SERIF, fontSize: 16, lineHeight: 21, fontWeight: '700', letterSpacing: -0.25 },
  actionsTitleCompact: { fontSize: 15, lineHeight: 19 },
  actionRows: { gap: 3 },
  actionRow: { minHeight: 35, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 7, borderRadius: 13, borderWidth: 1, borderColor: '#f2efe7', backgroundColor: CARD, boxShadow: '0px 2px 8px rgba(35, 53, 33, 0.045)' },
  actionRowCompact: { minHeight: 32 },
  actionRowLast: { minHeight: 36 },
  actionNumber: { width: 26, height: 26, flexShrink: 0, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#edf2e8' },
  actionNumberText: { color: INK, fontFamily: SERIF, fontSize: 13, lineHeight: 17, fontWeight: '700' },
  actionIcon: { width: 37, height: 34, alignItems: 'center', justifyContent: 'center' },
  actionCopy: { flex: 1, minWidth: 0 },
  actionTitle: { color: '#142e3b', fontFamily: SERIF, fontSize: 11.2, lineHeight: 14.5, fontWeight: '700' },
  actionTitleNarrow: { fontSize: 9.6, lineHeight: 12.5 },
  actionDetail: { color: MUTED, fontFamily: SANS, fontSize: 9.8, lineHeight: 12.5 },
  arrowCircleSmall: { width: 24, height: 24, flexShrink: 0, borderRadius: 13, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#f1eee7', backgroundColor: CARD },
  statusCard: { minHeight: 35, paddingHorizontal: 8, paddingVertical: 3, flexDirection: 'row', alignItems: 'center', gap: 7, borderRadius: 15, borderWidth: 1, borderColor: '#fff' },
  statusRecorded: { backgroundColor: '#eef3e8' },
  statusPending: { backgroundColor: '#fff4df' },
  statusIconCircle: { width: 27, height: 27, flexShrink: 0, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  statusIconRecorded: { backgroundColor: '#356646' },
  statusIconPending: { backgroundColor: '#ffedc9' },
  statusCopy: { flex: 1, minWidth: 0 },
  statusTitle: { color: INK, fontFamily: SERIF, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  statusTitlePending: { color: '#a75208' },
  statusDetail: { color: '#536a6b', fontFamily: SANS, fontSize: 8.8, lineHeight: 11.2 },
  retryError: { color: '#a53327', fontFamily: SANS, fontSize: 11, lineHeight: 15, paddingHorizontal: 3 },
  noticeCard: { minHeight: 42, paddingHorizontal: 8, paddingVertical: 4, flexDirection: 'row', alignItems: 'center', gap: 7, borderRadius: 16, borderWidth: 1, borderColor: '#fff', backgroundColor: '#fff4dc' },
  noticeCardCompact: { minHeight: 42 },
  noticeIconCircle: { width: 27, height: 27, flexShrink: 0, borderRadius: 17, alignItems: 'center', justifyContent: 'center', backgroundColor: '#ffedc9' },
  noticeCopy: { flex: 1, minWidth: 0 },
  noticeTitle: { color: '#a75209', fontFamily: SERIF, fontSize: 10.8, lineHeight: 13, fontWeight: '700' },
  noticeText: { color: '#62717e', fontFamily: SANS, fontSize: 9.4, lineHeight: 11.8 },
  bottomSpacer: { flexGrow: 1, minHeight: 0 },
  buttonRow: { flexDirection: 'row', gap: 6, marginTop: 1 },
  secondaryButton: { flex: 1, minWidth: 0, minHeight: 44, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, borderRadius: 13, borderWidth: 1, borderColor: '#1e654f', backgroundColor: PAPER },
  secondaryButtonText: { color: INK, fontFamily: SERIF, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  primaryButton: { flex: 1, minWidth: 0, minHeight: 44, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 13, backgroundColor: '#20543b', boxShadow: '0px 2px 5px rgba(31, 69, 45, 0.16)', elevation: 2 },
  primaryButtonText: { color: CARD, fontFamily: SERIF, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  pressed: { opacity: 0.82 },
  disabledButton: { opacity: 0.55 },
  tabBar: { minHeight: 52, marginHorizontal: -1, paddingHorizontal: 8, paddingTop: 3, paddingBottom: 2, flexDirection: 'row', alignItems: 'center', borderTopLeftRadius: 25, borderTopRightRadius: 25, borderWidth: 1, borderBottomWidth: 0, borderColor: '#f1eee7', backgroundColor: 'rgba(255,254,250,0.98)', boxShadow: '0px -2px 10px rgba(48,55,44,0.065)', elevation: 4 },
  tabButton: { flex: 1, minWidth: 0, alignItems: 'stretch', justifyContent: 'center' },
  tabContent: { height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', gap: 0 },
  tabContentActive: { backgroundColor: '#edf3e8' },
  tabLabel: { color: '#53637b', fontFamily: SANS, fontSize: 9.5, lineHeight: 12 },
  tabLabelActive: { color: INK, fontWeight: '600' },
  modalBackdrop: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, backgroundColor: 'rgba(11,28,22,0.28)' },
  actionModal: { width: '100%', maxWidth: 330, padding: 22, alignItems: 'center', borderRadius: 20, backgroundColor: CARD, boxShadow: '0px 6px 20px rgba(0,0,0,0.18)', elevation: 8 },
  modalIconCircle: { width: 48, height: 48, borderRadius: 25, alignItems: 'center', justifyContent: 'center', backgroundColor: '#edf2e8' },
  modalTitle: { marginTop: 12, color: INK, fontFamily: SERIF, fontSize: 19, lineHeight: 24, fontWeight: '700', textAlign: 'center' },
  modalDescription: { marginTop: 6, color: MUTED, fontFamily: SANS, fontSize: 14, lineHeight: 20, textAlign: 'center' },
  modalButton: { minWidth: 100, minHeight: 42, marginTop: 18, paddingHorizontal: 20, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: GREEN },
  modalButtonText: { color: CARD, fontFamily: SANS, fontSize: 14, lineHeight: 18, fontWeight: '600' },
});

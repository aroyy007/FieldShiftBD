import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';

import { Button, Card } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import {
  analyzeDiseaseImage,
  DiseaseAnalysis,
  DiseaseResult,
  getDiseaseResults,
  retryDiseaseProblemSync,
} from '../../../utils/disease-api';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const MAX_IMAGE_BYTES = 10 * 1024 * 1024;

function outcomeTitle(outcome: DiseaseAnalysis['outcome']) {
  if (outcome === 'healthy') return 'Healthy class detected';
  if (outcome === 'possible_disease') return 'Possible crop issue';
  return 'Could not confirm';
}

function outcomeColor(outcome: DiseaseAnalysis['outcome']) {
  if (outcome === 'healthy') return COLORS.success;
  if (outcome === 'possible_disease') return COLORS.warning;
  return COLORS.textSecondary;
}

function outcomeFromResult(result: DiseaseResult): string {
  const outcome = result.model_details.outcome;
  return typeof outcome === 'string' ? outcome.replace('_', ' ') : 'saved analysis';
}

function verificationSummary(status: DiseaseAnalysis['verification']['status']): string {
  switch (status) {
    case 'not_configured':
      return 'Gemini is not configured; this check used the local classifier only.';
    case 'verified_healthy':
      return 'Gemini and the local classifier agree that the photo appears healthy.';
    case 'verified_issue':
      return 'Gemini independently agrees that the photo may show a crop problem.';
    case 'gemini_only_issue':
      return 'Gemini saw possible signs, but the local classifier did not confirm them.';
    case 'disagreement':
      return 'The models disagree. The result is uncertain and no farm problem was recorded.';
    case 'uncertain':
      return 'Gemini could not confirm the active crop or a clear finding.';
    case 'unavailable':
      return 'Gemini could not verify this photo. No farm problem was recorded.';
  }
}

export default function CropHealth() {
  const params = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  return <CropHealthScreen key={farmId || 'missing'} farmId={farmId} />;
}

function CropHealthScreen({ farmId }: { farmId: string | undefined }) {
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const hasBackendFarmId = Boolean(farmId && UUID_PATTERN.test(farmId));

  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [analysis, setAnalysis] = useState<DiseaseAnalysis | null>(null);
  const [history, setHistory] = useState<DiseaseResult[]>([]);
  const [historyMessage, setHistoryMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [problemRetryingId, setProblemRetryingId] = useState<string | null>(null);
  const [problemRetryError, setProblemRetryError] = useState<{ resultId: string; message: string } | null>(null);
  const [historyLoadedFor, setHistoryLoadedFor] = useState<string | null>(null);
  const historyLoading = hasBackendFarmId && historyLoadedFor !== farmId;
  const problemRetrying = Boolean(
    analysis && problemRetryingId === analysis.disease_result.id,
  );

  useEffect(() => {
    if (!farmId || !hasBackendFarmId) return;

    let mounted = true;
    getDiseaseResults(farmId)
      .then(results => {
        if (mounted) {
          setHistory(results);
          setHistoryMessage('');
          setHistoryLoadedFor(farmId);
        }
      })
      .catch(requestError => {
        if (mounted) {
          setHistoryMessage(requestError instanceof Error ? requestError.message : 'Could not load disease history.');
          setHistoryLoadedFor(farmId);
        }
      });

    return () => { mounted = false; };
  }, [farmId, hasBackendFarmId]);

  const handlePickerError = (pickerError: unknown) => {
    setError(pickerError instanceof Error ? pickerError.message : 'Could not open the photo picker.');
  };

  const choosePhoto = async () => {
    setError('');
    setProblemRetryError(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.9,
      });
      if (!result.canceled && result.assets.length > 0) {
        setPhoto(result.assets[0]);
        setAnalysis(null);
      }
    } catch (pickerError) {
      handlePickerError(pickerError);
    }
  };

  const takePhoto = async () => {
    setError('');
    setProblemRetryError(null);
    try {
      if (Platform.OS !== 'web') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          setError('Allow camera access to take a crop photo.');
          return;
        }
      }
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.9,
      });
      if (!result.canceled && result.assets.length > 0) {
        setPhoto(result.assets[0]);
        setAnalysis(null);
      }
    } catch (pickerError) {
      handlePickerError(pickerError);
    }
  };

  const analyzePhoto = async () => {
    if (!photo || !farmId || !hasBackendFarmId) return;
    if (photo.fileSize && photo.fileSize > MAX_IMAGE_BYTES) {
      setError('Choose a photo smaller than 10 MB.');
      return;
    }

    setLoading(true);
    setError('');
    setProblemRetryError(null);
    try {
      const result = await analyzeDiseaseImage(farmId, photo);
      setAnalysis(result);
      setHistory(current => [
        result.disease_result,
        ...current.filter(item => item.id !== result.disease_result.id),
      ].slice(0, 20));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Disease analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const retryProblemSync = async (diseaseResultId: string) => {
    if (!farmId) return;
    setProblemRetryingId(diseaseResultId);
    setProblemRetryError(null);
    try {
      const result = await retryDiseaseProblemSync(farmId, diseaseResultId);
      setAnalysis(current => current?.disease_result.id === diseaseResultId ? {
        ...current,
        disease_result: result.disease_result,
        farm_problem: result.farm_problem,
        problem_sync: result.problem_sync,
      } : current);
      setHistory(current => [
        result.disease_result,
        ...current.filter(item => item.id !== result.disease_result.id),
      ].slice(0, 20));
    } catch (requestError) {
      setProblemRetryError({
        resultId: diseaseResultId,
        message: requestError instanceof Error ? requestError.message : 'Could not retry the farm problem write.',
      });
    } finally {
      setProblemRetryingId(null);
    }
  };

  if (!farm || !farmId) {
    return (
      <SafeAreaView style={styles.safe}>
        <Text style={styles.empty}>Farm not found.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>MODULE 6 · CROP HEALTH</Text>
          <Text style={styles.title}>Check a crop photo</Text>
          <Text style={styles.subtitle}>
            Take or choose one clear photo of an affected leaf. The active crop and growth stage come from the farm state.
          </Text>
        </View>

        {!hasBackendFarmId ? (
          <Card style={styles.integrationCard}>
            <Text style={styles.cardTitle}>Farm account connection needed</Text>
            <Text style={styles.body}>
              This screen is showing local demo data. Module 6 needs the UUID farmland and verified farmer sign-in from Module 1 before it can send a photo to the backend.
            </Text>
          </Card>
        ) : null}

        <Card>
          <Text style={styles.cardTitle}>Photo guidance</Text>
          <Text style={styles.body}>
            Use daylight, focus on one affected leaf, and keep the full affected area in frame. The server checks file type, size, and dimensions; it does not have a separate blur or leaf-quality model.
          </Text>
          <Text style={styles.privacyNote}>
            The photo is uploaded to FieldShift. If Gemini verification is enabled on the server, the photo is also sent to Google Gemini for a separate visual check.
          </Text>
          <View style={styles.buttonRow}>
            <Button title="Choose photo" variant="outline" onPress={choosePhoto} disabled={loading || problemRetryingId !== null} style={styles.actionButton} />
            <Button title="Take photo" variant="outline" onPress={takePhoto} disabled={loading || problemRetryingId !== null} style={styles.actionButton} />
          </View>
          {photo ? (
            <View style={styles.previewWrap}>
              <Image source={{ uri: photo.uri }} style={styles.preview} resizeMode="cover" accessibilityLabel="Selected crop photo" />
              <Text style={styles.photoMeta}>
                {photo.fileName || 'Crop photo'}{photo.fileSize ? ' · ' + Math.ceil(photo.fileSize / 1024) + ' KB' : ''}
              </Text>
              <Button
                title={loading ? 'Analyzing photo…' : 'Analyze photo'}
                onPress={analyzePhoto}
                disabled={loading || problemRetrying || !hasBackendFarmId}
                style={[styles.analyzeButton, (loading || problemRetrying || !hasBackendFarmId) && styles.disabledButton]}
              />
              {loading ? <ActivityIndicator color={COLORS.primary} style={styles.spinner} /> : null}
            </View>
          ) : (
            <View style={styles.emptyPhoto}>
              <Text style={styles.emptyPhotoTitle}>No photo selected</Text>
              <Text style={styles.body}>JPEG, PNG, or WebP · up to 10 MB</Text>
            </View>
          )}
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        </Card>

        {analysis ? (
          <Card style={analysis.outcome === 'possible_disease' ? styles.resultWarning : styles.resultCard}>
            <Text style={styles.eyebrow}>ANALYSIS RESULT</Text>
            <Text style={[styles.resultTitle, { color: outcomeColor(analysis.outcome) }]}>
              {outcomeTitle(analysis.outcome)}
            </Text>
            <Text style={styles.issue}>
              {analysis.outcome === 'healthy'
                ? 'The model matched a healthy class for ' + analysis.crop_name + '.'
                : analysis.outcome === 'possible_disease'
                  ? 'Classifier suggestion: ' + analysis.disease_result.possible_issue
                  : 'No disease category could be confirmed.'}
            </Text>
            <Text style={styles.meta}>
              {analysis.crop_name}
              {analysis.growth_stage_name ? ' · ' + analysis.growth_stage_name : ''}
              {' · Model score '}
              {analysis.disease_result.confidence === null
                ? 'unavailable'
                : Math.round(analysis.disease_result.confidence * 100) + '%'}
              {' · ' + analysis.confidence_level}
            </Text>
            <Text style={styles.meta}>
              {analysis.verification.status === 'not_configured'
                ? 'The classifier score is not a field-validated probability. Gemini verification is not configured.'
                : analysis.verification.status === 'unavailable'
                  ? 'The classifier score is not a field-validated probability. Gemini verification was unavailable.'
                  : 'The classifier score is not a field-validated probability. Gemini checks broad visible signs; it does not confirm the disease name.'}
            </Text>
            <Text style={styles.body}>{analysis.message}</Text>
            <View style={styles.detailBlock}>
              <Text style={styles.detailTitle}>Model cross-check</Text>
              <Text style={styles.body}>{verificationSummary(analysis.verification.status)}</Text>
              {analysis.verification.visible_signs ? (
                <Text style={styles.meta}>Gemini noted: {analysis.verification.visible_signs}</Text>
              ) : null}
            </View>
            <View style={styles.detailBlock}>
              <Text style={styles.detailTitle}>Observed symptoms</Text>
              <Text style={styles.body}>
                {analysis.disease_result.symptoms.length > 0
                  ? analysis.disease_result.symptoms.join(', ')
                  : 'The selected classifier does not mark or explain individual leaf symptoms.'}
              </Text>
            </View>
            <View style={styles.detailBlock}>
              <Text style={styles.detailTitle}>Recommended next actions</Text>
              {analysis.disease_result.recommended_actions.map((action, index) => (
                <Text key={index} style={styles.actionText}>• {action}</Text>
              ))}
            </View>
            {analysis.problem_sync === 'created' ? (
              <Text style={styles.problemRecorded}>Recorded in Farm Problems as an open issue.</Text>
            ) : analysis.problem_sync === 'reused' ? (
              <Text style={styles.problemRecorded}>A matching open or monitored farm problem already exists.</Text>
            ) : analysis.problem_sync === 'failed' ? (
              <View style={styles.retryBlock}>
                <Text accessibilityRole="alert" style={styles.error}>The analysis is saved, but the farm problem was not recorded.</Text>
                {problemRetryError?.resultId === analysis.disease_result.id ? (
                  <Text accessibilityRole="alert" style={styles.error}>{problemRetryError.message}</Text>
                ) : null}
                <Button
                  title={problemRetrying ? 'Retrying…' : 'Retry recording'}
                  onPress={() => retryProblemSync(analysis.disease_result.id)}
                  disabled={problemRetryingId !== null}
                  style={styles.analyzeButton}
                />
              </View>
            ) : (
              <Text style={styles.meta}>No new farm problem was created for this result.</Text>
            )}
            <Text style={styles.disclaimer}>{analysis.disclaimer}</Text>
          </Card>
        ) : null}

        <View style={styles.historyHeader}>
          <Text style={styles.cardTitle}>Previous analyses</Text>
          {historyLoading ? <ActivityIndicator color={COLORS.primary} /> : null}
        </View>
        {historyMessage ? <Text style={styles.historyMessage}>{historyMessage}</Text> : null}
        {!historyLoading && history.length === 0 ? (
          <Card><Text style={styles.body}>Saved disease checks will appear here.</Text></Card>
        ) : history.map(item => (
          <Card key={item.id} style={styles.historyCard}>
            <View style={styles.historyTop}>
              <Text style={styles.historyTitle}>{item.possible_issue || 'Disease check'}</Text>
              <Text style={styles.historyOutcome}>{outcomeFromResult(item)}</Text>
            </View>
            <Text style={styles.meta}>
              {item.crop_name || 'Crop'} · {new Date(item.created_at).toLocaleString()}
            </Text>
            {item.model_details.problem_sync === 'created' || item.model_details.problem_sync === 'reused' ? (
              <Text style={styles.problemRecorded}>Previously linked to a farm problem.</Text>
            ) : null}
            {item.model_details.problem_sync === 'failed' && analysis?.disease_result.id !== item.id ? (
              <View style={styles.retryBlock}>
                {problemRetryError?.resultId === item.id ? (
                  <Text accessibilityRole="alert" style={styles.error}>{problemRetryError.message}</Text>
                ) : null}
                <Button
                  title={problemRetryingId === item.id ? 'Retrying…' : 'Retry recording'}
                  onPress={() => retryProblemSync(item.id)}
                  disabled={problemRetryingId !== null}
                  style={styles.analyzeButton}
                />
              </View>
            ) : null}
          </Card>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, width: '100%', maxWidth: 920, alignSelf: 'center', padding: SPACING.md },
  heading: { marginBottom: SPACING.md },
  eyebrow: { ...TYPOGRAPHY.caption, fontWeight: '700', letterSpacing: 1.1, color: COLORS.primary },
  title: { ...TYPOGRAPHY.h1, marginTop: SPACING.xs },
  subtitle: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs, lineHeight: 23 },
  integrationCard: { borderLeftWidth: 4, borderLeftColor: COLORS.warning },
  cardTitle: { ...TYPOGRAPHY.h3, marginBottom: SPACING.xs },
  body: { ...TYPOGRAPHY.bodySecondary, lineHeight: 23 },
  privacyNote: { ...TYPOGRAPHY.caption, marginTop: SPACING.sm, lineHeight: 18, color: COLORS.textSecondary },
  buttonRow: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.sm, marginTop: SPACING.md },
  actionButton: { flexGrow: 1, minWidth: 145 },
  previewWrap: { marginTop: SPACING.md },
  preview: { width: '100%', maxHeight: 340, aspectRatio: 4 / 3, borderRadius: 12, backgroundColor: '#e9f0e8' },
  photoMeta: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs },
  analyzeButton: { marginTop: SPACING.md },
  disabledButton: { opacity: 0.5 },
  spinner: { marginTop: SPACING.sm },
  emptyPhoto: { alignItems: 'center', padding: SPACING.xl, marginTop: SPACING.md, borderWidth: 1, borderStyle: 'dashed', borderColor: COLORS.border, borderRadius: 12 },
  emptyPhotoTitle: { ...TYPOGRAPHY.h3, marginBottom: SPACING.xs },
  error: { ...TYPOGRAPHY.body, color: COLORS.error, marginTop: SPACING.md },
  resultWarning: { borderLeftWidth: 4, borderLeftColor: COLORS.warning },
  resultCard: { borderLeftWidth: 4, borderLeftColor: COLORS.primary },
  resultTitle: { ...TYPOGRAPHY.h2, marginTop: SPACING.xs },
  issue: { ...TYPOGRAPHY.h3, marginTop: SPACING.md },
  meta: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs, lineHeight: 18 },
  detailBlock: { marginTop: SPACING.md },
  detailTitle: { ...TYPOGRAPHY.body, fontWeight: '700', marginBottom: SPACING.xs },
  actionText: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs, lineHeight: 22 },
  problemRecorded: { ...TYPOGRAPHY.body, color: COLORS.success, fontWeight: '600', marginTop: SPACING.md },
  retryBlock: { marginTop: SPACING.sm },
  disclaimer: { ...TYPOGRAPHY.caption, marginTop: SPACING.md, lineHeight: 18 },
  historyHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: SPACING.lg, marginBottom: SPACING.sm },
  historyMessage: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, marginBottom: SPACING.sm },
  historyCard: { marginBottom: SPACING.sm },
  historyTop: { flexDirection: 'row', justifyContent: 'space-between', gap: SPACING.sm },
  historyTitle: { ...TYPOGRAPHY.h3, flex: 1 },
  historyOutcome: { ...TYPOGRAPHY.caption, textTransform: 'capitalize', color: COLORS.textSecondary },
  empty: { ...TYPOGRAPHY.body, textAlign: 'center', padding: SPACING.lg },
});

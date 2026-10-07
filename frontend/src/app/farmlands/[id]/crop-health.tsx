import React, { useEffect, useState } from 'react';
import {
  Platform,
  Text,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, router, useLocalSearchParams } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';

import ScanLeafResult, { ScanLeafCapture } from '../../../components/ScanLeafResult';
import { useAppContext } from '../../../context/AppProvider';
import { analyzeDiseaseImage, getDiseaseResults, retryDiseaseProblemSync } from '../../../utils/disease-api';
import type {
  DiseaseAnalysis,
  DiseaseResult,
  FarmProblem,
} from '../../../utils/disease-api';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const PREVIEW_DISCLAIMER = 'This result is based on the image and may require local expert verification.';

function createPreviewAnalysis(farmId: string): DiseaseAnalysis {
  const createdAt = new Date().toISOString();
  const diseaseResult: DiseaseResult = {
    id: 'scan-leaf-preview-result',
    farmland_id: farmId,
    season_id: null,
    crop_id: null,
    crop_name: 'Rice',
    possible_issue: 'Brown spot',
    confidence: 0.6,
    symptoms: ['Small oval brown lesions with yellowish margins.'],
    recommended_actions: [],
    model_details: { outcome: 'possible_disease', problem_sync: 'created' },
    created_at: createdAt,
  };
  const farmProblem: FarmProblem = {
    id: 'scan-leaf-preview-problem',
    farmland_id: farmId,
    season_id: null,
    source: 'disease_detection',
    category: 'crop_disease',
    description: 'Possible Brown spot in Rice.',
    severity: 'moderate',
    status: 'open',
    created_at: createdAt,
    resolved_at: null,
  };

  return {
    disease_result: diseaseResult,
    outcome: 'possible_disease',
    verification: {
      status: 'not_configured',
      finding: null,
      crop_match: null,
      visible_signs: null,
      model: null,
    },
    confidence_level: 'moderate',
    crop_name: 'Rice',
    growth_stage_name: 'Vegetative',
    farm_problem: farmProblem,
    problem_sync: 'created',
    message: 'The photo may show signs of Brown spot.',
    disclaimer: PREVIEW_DISCLAIMER,
  };
}

export default function CropHealth() {
  const params = useLocalSearchParams<{ id: string; preview?: string }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const previewParam = Array.isArray(params.preview) ? params.preview[0] : params.preview;
  const previewMode = typeof __DEV__ !== 'undefined' && __DEV__ && previewParam === '1';
  return <CropHealthScreen key={`${farmId || 'missing'}-${previewMode ? 'preview' : 'live'}`} farmId={farmId} previewMode={previewMode} />;
}

function CropHealthScreen({ farmId, previewMode: previewRequested }: { farmId: string | undefined; previewMode: boolean }) {
  const { farmlands, refreshFarmland } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const hasBackendFarmId = Boolean(farmId && UUID_PATTERN.test(farmId));

  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [previewMode, setPreviewMode] = useState(previewRequested);
  const [analysis, setAnalysis] = useState<DiseaseAnalysis | null>(() =>
    previewRequested && farmId ? createPreviewAnalysis(farmId) : null,
  );
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
        setPreviewMode(false);
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
        setPreviewMode(false);
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
      if (result.farm_problem) {
        await refreshFarmland(farmId).catch(() => undefined);
      }
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
      if (result.farm_problem) {
        await refreshFarmland(farmId).catch(() => undefined);
      }
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

  const navigateTab = (tab: 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile') => {
    const routes: Record<typeof tab, Href> = {
      Home: '/farmlands',
      Tasks: `/farmlands/${farmId}/tasks` as Href,
      Chat: `/farmlands/${farmId}/chat` as Href,
      Scan: `/farmlands/${farmId}/crop-health` as Href,
      Profile: '/farmlands/profile-setup',
    };
    router.push(routes[tab]);
  };

  if (!farm || !farmId) {
    return (
      <SafeAreaView style={{ flex: 1, justifyContent: 'center', backgroundColor: '#fbf9f2' }}>
        <Text style={{ padding: 24, color: '#103832', fontSize: 16, textAlign: 'center' }}>Farm not found.</Text>
      </SafeAreaView>
    );
  }

  if (analysis) {
    return (
      <ScanLeafResult
        analysis={analysis}
        photoUri={photo?.uri}
        previewPhoto={previewMode}
        retrying={problemRetrying}
        retryError={problemRetryError?.resultId === analysis.disease_result.id ? problemRetryError.message : null}
        onBack={() => router.replace(`/farmlands/${farmId}` as Href)}
        onRetake={() => void takePhoto()}
        onFarmLog={() => {
          if (analysis.problem_sync === 'failed') {
            void retryProblemSync(analysis.disease_result.id);
            return;
          }
          router.push(`/farmlands/${farmId}/problems` as Href);
        }}
        onTabPress={navigateTab}
      />
    );
  }

  return (
    <ScanLeafCapture
      hasBackendFarmId={hasBackendFarmId}
      photoUri={photo?.uri}
      photoName={photo?.fileName ?? undefined}
      photoSize={photo?.fileSize ?? undefined}
      loading={loading}
      error={error}
      history={history}
      historyLoading={historyLoading}
      historyMessage={historyMessage}
      retryingId={problemRetryingId}
      retryError={problemRetryError}
      onBack={() => router.replace(`/farmlands/${farmId}` as Href)}
      onChoosePhoto={() => void choosePhoto()}
      onTakePhoto={() => void takePhoto()}
      onAnalyze={() => void analyzePhoto()}
      onRetry={diseaseResultId => void retryProblemSync(diseaseResultId)}
      onTabPress={navigateTab}
    />
  );
}

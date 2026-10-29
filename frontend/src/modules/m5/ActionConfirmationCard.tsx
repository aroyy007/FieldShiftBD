import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ProposedAction } from '../shared/contracts.generated';
import { isActionReviewable, summarizeTaskChange } from './action-summary';

type Props = {
  action: ProposedAction;
  farmName: string;
  busy: boolean;
  message?: string;
  onDecision: (decision: 'confirm' | 'reject') => void;
};

export function ActionConfirmationCard({ action, farmName, busy, message, onDecision }: Props) {
  const expiresAt = new Date(action.expires_at);
  const expiryIsValid = Number.isFinite(expiresAt.getTime());
  const [currentTime, setCurrentTime] = useState(0);
  const reviewable = isActionReviewable(action);

  useEffect(() => {
    const updateCurrentTime = () => setCurrentTime(Date.now());
    const initialUpdate = setTimeout(updateCurrentTime, 0);
    const timer = setInterval(updateCurrentTime, 15_000);
    return () => {
      clearTimeout(initialUpdate);
      clearInterval(timer);
    };
  }, [action.expires_at]);

  const expired = !expiryIsValid || (currentTime > 0 && expiresAt.getTime() <= currentTime);

  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>REVIEW FARM CHANGE</Text>
      <Text style={styles.title}>For {farmName}</Text>
      <Text style={styles.subtitle}>Review the task and every before-and-after value before saving:</Text>
      {action.task_diff.operations.map(change => (
        <View key={change.reference} style={styles.changeRow}>
          <Text style={styles.bullet}>•</Text>
          <Text style={styles.changeText}>{summarizeTaskChange(action, change)}</Text>
        </View>
      ))}
      {!reviewable ? (
        <Text accessibilityRole="alert" style={styles.reviewWarning}>
          This proposal is missing the current task details needed for a safe review. Refresh and request a new proposal before confirming.
        </Text>
      ) : null}
      <Text style={styles.expiry}>
        {expiryIsValid ? `Expires ${expiresAt.toLocaleString()}` : 'Expiry could not be verified; refresh before continuing.'}
        {action.required_consent_purposes?.length ? ' · Required consent must be active.' : ''}
      </Text>
      {message ? <Text accessibilityRole="alert" style={styles.message}>{message}</Text> : null}
      <View style={styles.actions}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Reject this farm change"
          disabled={busy}
          onPress={() => onDecision('reject')}
          style={[styles.rejectButton, busy && styles.disabled]}
        >
          <Text style={styles.rejectText}>Decline</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Confirm changes for ${farmName}`}
          disabled={busy || expired || !reviewable}
          onPress={() => onDecision('confirm')}
          style={[styles.confirmButton, (busy || expired || !reviewable) && styles.disabled]}
        >
          <Text style={styles.confirmText}>{busy ? 'Saving…' : expired ? 'Expired' : 'Confirm changes'}</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { marginHorizontal: 14, marginBottom: 8, padding: 14, borderRadius: 16, backgroundColor: '#fffaf0', borderWidth: 1, borderColor: '#e8d8b5' },
  eyebrow: { color: '#8a641a', fontFamily: 'Arial', fontSize: 10, fontWeight: '700', letterSpacing: 0.8 },
  title: { marginTop: 3, color: '#0a392f', fontFamily: 'Georgia', fontSize: 16, fontWeight: '700' },
  subtitle: { marginTop: 4, color: '#52635c', fontFamily: 'Arial', fontSize: 12, lineHeight: 17 },
  changeRow: { flexDirection: 'row', alignItems: 'flex-start', marginTop: 7, gap: 7 },
  bullet: { color: '#8a641a', fontSize: 16, lineHeight: 19 },
  changeText: { flex: 1, color: '#18372d', fontFamily: 'Georgia', fontSize: 13, lineHeight: 18 },
  expiry: { marginTop: 9, color: '#687589', fontFamily: 'Arial', fontSize: 10.5, lineHeight: 15 },
  message: { marginTop: 7, color: '#9b352e', fontFamily: 'Arial', fontSize: 12, lineHeight: 17 },
  reviewWarning: { marginTop: 8, color: '#9b352e', fontFamily: 'Arial', fontSize: 12, lineHeight: 17 },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginTop: 11 },
  rejectButton: { minHeight: 44, paddingHorizontal: 13, justifyContent: 'center', borderRadius: 11, borderWidth: 1, borderColor: '#d9d3c2' },
  rejectText: { color: '#42516a', fontFamily: 'Arial', fontSize: 12, fontWeight: '600' },
  confirmButton: { minHeight: 44, paddingHorizontal: 14, justifyContent: 'center', borderRadius: 11, backgroundColor: '#145f3b' },
  confirmText: { color: '#fffdf7', fontFamily: 'Arial', fontSize: 12, fontWeight: '700' },
  disabled: { opacity: 0.5 },
});

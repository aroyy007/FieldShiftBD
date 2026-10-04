import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Button, Input } from '../../components/ui';
import { useAppContext } from '../../context/AppProvider';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';

export default function Signup() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const router = useRouter();
  const { login } = useAppContext();

  const handleSignup = () => {
    if (!name || !phone || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }
    login(phone, password);
    router.replace('/farmlands' as any);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Join FieldShift</Text>
        <Text style={styles.subtitle}>Create your farmer account</Text>
        <Input label="Full Name" placeholder="e.g. John Doe" value={name} onChangeText={setName} />
        <Input label="Phone Number" placeholder="e.g. 01700000000" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <Input label="Password" placeholder="Create password" value={password} onChangeText={setPassword} secureTextEntry />
        <Input label="Confirm Password" placeholder="Confirm password" value={confirmPassword} onChangeText={setConfirmPassword} secureTextEntry />
        <Button title="Sign Up" onPress={handleSignup} style={styles.button} />
        <Button title="Back to Login" variant="secondary" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, padding: SPACING.lg, justifyContent: 'center' },
  title: { ...TYPOGRAPHY.h1, color: COLORS.primary, textAlign: 'center', marginBottom: SPACING.sm },
  subtitle: { ...TYPOGRAPHY.bodySecondary, textAlign: 'center', marginBottom: SPACING.xl },
  button: { marginBottom: SPACING.md },
});
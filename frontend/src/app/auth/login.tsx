import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Button, Input } from '../../components/ui';
import { useAppContext } from '../../context/AppProvider';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';
import { DEMO_CREDENTIALS } from '../../data/demo';

export default function Login() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();
  const { login } = useAppContext();

  const handleLogin = () => {
    if (!phone || !password) {
      Alert.alert('Error', 'Please enter phone and password');
      return;
    }
    const success = login(phone, password);
    if (success) {
      router.replace('/farmlands' as any);
    } else {
      Alert.alert('Error', 'Invalid credentials');
    }
  };

  const handleDemoLogin = () => {
    setPhone(DEMO_CREDENTIALS.phone);
    setPassword(DEMO_CREDENTIALS.password);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>FieldShift</Text>
        <Text style={styles.subtitle}>Welcome back to your farm</Text>
        <Input label="Phone Number" placeholder="e.g. 01700000000" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <Input label="Password" placeholder="Enter password" value={password} onChangeText={setPassword} secureTextEntry />
        <Button title="Login" onPress={handleLogin} style={styles.button} />
        <Button title="Use Demo Account" variant="outline" onPress={handleDemoLogin} style={styles.button} />
        <Button title="Create an account" variant="secondary" onPress={() => router.push('/auth/signup' as any)} />
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
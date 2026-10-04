import { Stack } from 'expo-router';
import { COLORS } from '../../../theme/theme';

export default function FarmlandDetailLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.surface },
        headerTintColor: COLORS.primary,
        headerTitleStyle: { fontWeight: 'bold' },
        headerBackTitleVisible: false,
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Farm Dashboard' }} />
      <Stack.Screen name="chat" options={{ title: 'Assistant Chat' }} />
      <Stack.Screen name="alerts" options={{ title: 'Farm Alerts' }} />
      <Stack.Screen name="tasks" options={{ title: 'Daily Tasks' }} />
      <Stack.Screen name="season-plan" options={{ title: 'Season Plan' }} />
      <Stack.Screen name="crop-health" options={{ title: 'Crop Health' }} />
    </Stack>
  );
}

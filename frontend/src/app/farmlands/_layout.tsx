import { Stack } from 'expo-router';
import { COLORS } from '../../theme/theme';

export default function FarmlandsLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.primary },
        headerTintColor: COLORS.surface,
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'All Farmlands', headerLeft: () => null }} />
      <Stack.Screen name="add" options={{ title: 'Add Farmland', presentation: 'modal' }} />
      <Stack.Screen name="[id]" options={{ headerShown: false }} />
    </Stack>
  );
}

import { Stack } from "expo-router";
import { AppProvider } from "../context/AppProvider";

export default function RootLayout() {
  return (
    <AppProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </AppProvider>
  );
}

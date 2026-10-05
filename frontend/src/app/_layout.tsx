import { Stack } from "expo-router";
import { KeyboardAvoidingView, Platform, StyleSheet } from "react-native";
import { AppProvider } from "../context/AppProvider";

export default function RootLayout() {
  return (
    <AppProvider>
      <KeyboardAvoidingView
        style={styles.keyboardArea}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <Stack screenOptions={{ headerShown: false }} />
      </KeyboardAvoidingView>
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  keyboardArea: {
    flex: 1,
  },
});

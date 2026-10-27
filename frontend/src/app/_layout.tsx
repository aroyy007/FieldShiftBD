import { Stack } from "expo-router";
import { useFonts } from "expo-font";
import { StatusBar } from "expo-status-bar";
import { KeyboardAvoidingView, Platform, StyleSheet } from "react-native";
import { AppProvider } from "../context/AppProvider";

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    MinaRegular: require("../../assets/fonts/Mina-Regular.ttf"),
    MinaBold: require("../../assets/fonts/Mina-Bold.ttf"),
  });

  if (!fontsLoaded) return null;

  return (
    <AppProvider>
      <StatusBar hidden />
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

import { Redirect } from 'expo-router';

// Sign-in lands on the complete farm list. The selected farm opens its own chat.
export default function FarmlandsIndex() {
  return <Redirect href="/farmlands/manage" />;
}

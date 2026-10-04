import { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useRouter, Href } from 'expo-router';
import { useAppContext } from '../context/AppProvider';

export default function Index() {
  const { user } = useAppContext();
  const router = useRouter();
  
  useEffect(() => {
    // Wait a tiny bit for the navigation tree to fully mount before pushing a route
    const timeout = setTimeout(() => {
      if (user) {
        router.replace("/farmlands" as Href);
      } else {
        router.replace("/auth/login" as Href);
      }
    }, 10);
    return () => clearTimeout(timeout);
  }, [user]);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f7f5' }}>
      <ActivityIndicator size="large" color="#2e7d32" />
    </View>
  );
}

import React, { createContext, useContext, useState } from 'react';
import { DEMO_CREDENTIALS, DEMO_FARMLANDS, Farmland } from '../data/demo';

type AppContextType = {
  user: { name: string; phone: string } | null;
  login: (phone: string, pass: string) => boolean;
  logout: () => void;
  farmlands: Farmland[];
  addFarmland: (farm: Farmland) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ name: string; phone: string } | null>(null);
  const [farmlands, setFarmlands] = useState<Farmland[]>(DEMO_FARMLANDS);

  const login = (phone: string, pass: string) => {
    if (phone === DEMO_CREDENTIALS.phone && pass === DEMO_CREDENTIALS.password) {
      setUser({ name: 'Demo Farmer', phone });
      return true;
    }
    // Allow any signup through if they type something else, just for demo purposes
    if (phone && pass && phone !== DEMO_CREDENTIALS.phone) {
      setUser({ name: 'New Farmer', phone });
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
  };

  const addFarmland = (farm: Farmland) => {
    setFarmlands([...farmlands, farm]);
  };

  return (
    <AppContext.Provider value={{ user, login, logout, farmlands, addFarmland }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppContext must be used within AppProvider');
  return context;
}

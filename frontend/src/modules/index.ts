import { challengeNamespaces } from './shared/i18n';

export const challengeModules = {
  m1: { id: 'M1', name: challengeNamespaces.m1 },
  m2: { id: 'M2', name: challengeNamespaces.m2 },
  m3: { id: 'M3', name: challengeNamespaces.m3 },
  m4: { id: 'M4', name: challengeNamespaces.m4 },
  m5: { id: 'M5', name: challengeNamespaces.m5 },
  m6: { id: 'M6', name: challengeNamespaces.m6 },
} as const;

export type ChallengeModuleId = keyof typeof challengeModules;

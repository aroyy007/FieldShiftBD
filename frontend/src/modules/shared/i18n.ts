export const challengeNamespaces = {
  m1: { en: 'Farm profile', bn: 'খামারের প্রোফাইল' },
  m2: { en: 'Crop advisor', bn: 'ফসল পরামর্শ' },
  m3: { en: 'Farm operations', bn: 'খামার পরিচালনা' },
  m4: { en: 'Climate intelligence', bn: 'জলবায়ু তথ্য' },
  m5: { en: 'Farm assistant', bn: 'খামার সহকারী' },
  m6: { en: 'Crop health', bn: 'ফসলের স্বাস্থ্য' },
} as const;

export type ChallengeNamespace = keyof typeof challengeNamespaces;
export type ChallengeLanguage = 'en' | 'bn';

export function getChallengeNamespaceLabel(namespace: ChallengeNamespace, language: ChallengeLanguage): string {
  return challengeNamespaces[namespace][language];
}

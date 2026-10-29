/** Reserved mount points: modules add views only through these shared routes. */
export const challengeNavigationMounts = {
  farmlandList: '/farmlands',
  farmlandDetail: '/farmlands/[id]',
  cropAdvisor: '/farmlands/[id]/crop-advisor',
  seasonPlan: '/farmlands/[id]/season-plan',
  tasks: '/farmlands/[id]/tasks',
  alerts: '/farmlands/[id]/alerts',
  chat: '/farmlands/[id]/chat',
  cropHealth: '/farmlands/[id]/crop-health',
} as const;

export type ChallengeNavigationMount = keyof typeof challengeNavigationMounts;

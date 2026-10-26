import Svg, { Circle, Line, Path, Rect } from 'react-native-svg';

export type AssistantIconName =
  | 'grass'
  | 'sprout'
  | 'list'
  | 'chevron'
  | 'checks'
  | 'sparkle'
  | 'microphone'
  | 'send'
  | 'tasks'
  | 'leaf'
  | 'grain'
  | 'bulb'
  | 'rain';

export function AssistantIcon({
  name,
  size = 22,
  color = '#145f3b',
}: {
  name: AssistantIconName;
  size?: number;
  color?: string;
}) {
  const outline = {
    fill: 'none',
    stroke: color,
    strokeWidth: 1.9,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'grass' ? <>
        <Path d="M12 21V8M12 19c-4.6-2.5-6.8-6.3-6.5-11.4C9.8 9.3 12 13 12 19ZM12 17c.2-5.4 2.7-9.2 7-11.6.5 5.4-1.9 9.4-7 11.6ZM8.5 21c-2.1-2-2.9-4.3-2.5-7 2.4 1.4 3.4 3.6 3.5 6.7M15.7 21c2.2-2 3-4.3 2.6-7-2.5 1.4-3.4 3.6-3.5 6.7" fill={color} stroke={color} strokeWidth=".7" strokeLinejoin="round" />
      </> : null}
      {name === 'sprout' ? <>
        <Path d="M12 21V9" {...outline} />
        <Path d="M11.8 12.8C6.5 12.7 4 9.7 4 5c5 .3 7.6 2.6 7.8 7.8ZM12.1 10.1C12.5 5.6 15.3 3.1 20 3c-.2 4.8-2.7 7.4-7.9 7.1Z" fill={color} stroke={color} strokeWidth=".8" strokeLinejoin="round" />
      </> : null}
      {name === 'list' || name === 'tasks' ? <>
        <Rect x="4.5" y="4" width="15" height="16" rx="2" {...outline} />
        <Path d="M8 8h8M8 12h2m2 0h4M8 16h2m2 0h4" {...outline} />
        <Circle cx="8" cy="12" r=".5" fill={color} />
        <Circle cx="8" cy="16" r=".5" fill={color} />
      </> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...outline} strokeWidth="2.2" /> : null}
      {name === 'checks' ? <>
        <Path d="m3 12 3 3 5.5-6M10 14l2 2 8-9" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === 'sparkle' ? <>
        <Path d="M12 2.5 14.2 9.8 21.5 12l-7.3 2.2L12 21.5l-2.2-7.3L2.5 12l7.3-2.2L12 2.5Z" fill={color} />
        <Path d="m19 2 .7 2.3L22 5l-2.3.7L19 8l-.7-2.3L16 5l2.3-.7L19 2Z" fill={color} />
      </> : null}
      {name === 'microphone' ? <>
        <Rect x="9" y="3" width="6" height="12" rx="3" {...outline} strokeWidth="2" />
        <Path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3m-3 0h6" {...outline} strokeWidth="2" />
      </> : null}
      {name === 'send' ? <Path d="m3 4 18 8-18 8 3.2-7.1L15 12l-8.8-.9L3 4Z" fill={color} stroke={color} strokeWidth="1" strokeLinejoin="round" /> : null}
      {name === 'leaf' ? <>
        <Path d="M5 19c.3-8.4 4.8-13.6 14-14-1 8.7-5.5 13.2-14 14Z" fill={color} />
        <Path d="M5 19c3.2-4.4 6.8-7.6 12-11" fill="none" stroke="#fffdf7" strokeWidth="1.2" strokeLinecap="round" />
      </> : null}
      {name === 'grain' ? <>
        <Path d="M12 21V5m0 8c-3.6-.3-5.2-2.3-5-5.8 3.3.7 5 2.5 5 5.8Zm0-3c3.6-.3 5.2-2.3 5-5.8-3.3.7-5 2.5-5 5.8Zm0 8c-3.4-.2-4.8-2-4.8-5 3.1.6 4.7 2.2 4.8 5Zm0-2.5c3.4-.2 4.8-2 4.8-5-3.1.6-4.7 2.2-4.8 5Z" fill={color} stroke={color} strokeWidth=".7" strokeLinejoin="round" />
      </> : null}
      {name === 'bulb' ? <>
        <Path d="M9 16c-.4-1.5-2.2-2.6-2.2-5.2a5.2 5.2 0 0 1 10.4 0c0 2.6-1.8 3.7-2.2 5.2M9 18h6m-5 2h4m-2-19v1.5M4.5 4.5l1.2 1.2M2 11h1.8m14.5-5.3 1.2-1.2M20.2 11H22" {...outline} />
      </> : null}
      {name === 'rain' ? <>
        <Path d="M5.5 14.5h12a4 4 0 0 0 .2-8 6.2 6.2 0 0 0-11.8 1.2 3.5 3.5 0 0 0-.4 6.8Z" fill={color} stroke={color} strokeWidth="1.1" />
        <Line x1="8" y1="17" x2="7" y2="20" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <Line x1="13" y1="17" x2="12" y2="20" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <Line x1="18" y1="17" x2="17" y2="20" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
      </> : null}
    </Svg>
  );
}

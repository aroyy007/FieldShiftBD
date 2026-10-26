import Svg, { Circle, Path, Rect } from 'react-native-svg';

export type FarmProfileIconName =
  | 'clipboard'
  | 'chart'
  | 'location'
  | 'field'
  | 'soil'
  | 'drop'
  | 'water'
  | 'person'
  | 'coins'
  | 'leaf'
  | 'edit'
  | 'check';

type Props = { name: FarmProfileIconName; size?: number; color?: string };

export function FarmProfileIcon({ name, size = 22, color = '#17653c' }: Props) {
  const line = {
    fill: 'none',
    stroke: color,
    strokeWidth: 1.9,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'clipboard' ? <>
        <Rect x="5" y="4.5" width="14" height="17" rx="2" {...line} />
        <Path d="M9 4.5v-1h6v1M8.5 10h7M8.5 14h7M8.5 18h4" {...line} />
      </> : null}
      {name === 'chart' ? <>
        <Path d="M4 20h17M6 16v-4M11 16V8M16 16V5M21 16V3" {...line} strokeWidth="2.4" />
      </> : null}
      {name === 'location' ? <>
        <Path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" {...line} />
        <Circle cx="12" cy="10" r="2.2" {...line} />
      </> : null}
      {name === 'field' ? <>
        <Path d="M4 8h16M5 12h14M6 16h12M8 20h8" {...line} strokeWidth="2.1" />
        <Path d="m8 5 2-2 2 2M14 5l2-2 2 2" {...line} />
      </> : null}
      {name === 'soil' ? <>
        <Path d="M3 19c.7-4.6 3.5-7 9-7s8.3 2.4 9 7H3Z" {...line} />
        <Path d="M7 12.2 9.4 9l2.2 2.4L14 7l2.2 4.5 2-2.1" {...line} />
        <Circle cx="7" cy="16" r=".7" fill={color} />
        <Circle cx="12" cy="15" r=".7" fill={color} />
        <Circle cx="17" cy="17" r=".7" fill={color} />
      </> : null}
      {name === 'drop' ? <Path d="M12 2.8S5.5 10.2 5.5 14.5a6.5 6.5 0 0 0 13 0C18.5 10.2 12 2.8 12 2.8Z" {...line} /> : null}
      {name === 'water' ? <>
        <Path d="M3 8c2.3 0 2.3 2 4.5 2S9.8 8 12 8s2.3 2 4.5 2S18.8 8 21 8M3 13c2.3 0 2.3 2 4.5 2S9.8 13 12 13s2.3 2 4.5 2 2.3-2 4.5-2M3 18c2.3 0 2.3 2 4.5 2S9.8 18 12 18s2.3 2 4.5 2 2.3-2 4.5-2" {...line} strokeWidth="2.2" />
      </> : null}
      {name === 'person' ? <>
        <Circle cx="12" cy="7" r="4" {...line} />
        <Path d="M4.5 21v-2a7.5 7.5 0 0 1 15 0v2Z" {...line} />
      </> : null}
      {name === 'coins' ? <>
        <Path d="M5 8c0-1.1 2.2-2 5-2s5 .9 5 2-2.2 2-5 2-5-.9-5-2Z" {...line} />
        <Path d="M5 8v3c0 1.1 2.2 2 5 2 1 0 1.9-.1 2.7-.4M5 11v3c0 1.1 2.2 2 5 2M5 14v3c0 1.1 2.2 2 5 2 .8 0 1.5-.1 2.2-.2" {...line} />
        <Path d="M13 12c0-1.1 1.8-2 4-2s4 .9 4 2-1.8 2-4 2-4-.9-4-2ZM13 12v5c0 1.1 1.8 2 4 2s4-.9 4-2v-5M13 14.5c0 1.1 1.8 2 4 2s4-.9 4-2" {...line} />
      </> : null}
      {name === 'leaf' ? <>
        <Path d="M4 19c.2-8.1 5.1-13.6 16-15-.4 9.4-5.2 15.4-14.2 15.4M5 19c4.2-4.2 8.1-7.5 13.7-11" {...line} />
      </> : null}
      {name === 'edit' ? <>
        <Path d="m4 16.5-.8 4.3 4.3-.8L19 8.5 15.5 5 4 16.5Z" {...line} />
        <Path d="m13.8 6.7 3.5 3.5" {...line} />
      </> : null}
      {name === 'check' ? <Path d="m5 12.5 4.2 4.2L19.5 6.8" {...line} strokeWidth="2.6" /> : null}
    </Svg>
  );
}

import Svg, { Circle, Path, Rect } from 'react-native-svg';

export type ScanResultIconName =
  | 'back'
  | 'focus'
  | 'home'
  | 'tasks'
  | 'chat'
  | 'profile'
  | 'chevron'
  | 'warning'
  | 'signal'
  | 'leaf'
  | 'list'
  | 'sprout'
  | 'drop'
  | 'document'
  | 'check'
  | 'camera'
  | 'add-document';

type Props = { name: ScanResultIconName; size?: number; color?: string };

export function ScanResultIcon({ name, size = 20, color = '#155d3c' }: Props) {
  const stroke = {
    fill: 'none',
    stroke: color,
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'back' ? <Path d="m15 18-6-6 6-6" {...stroke} strokeWidth={2.2} /> : null}
      {name === 'focus' ? <>
        <Path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3" {...stroke} strokeWidth={2.1} />
        <Circle cx="12" cy="12" r="3.5" {...stroke} strokeWidth={2} />
        <Circle cx="12" cy="12" r=".8" fill={color} />
      </> : null}
      {name === 'home' ? (
        <Path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1Z" fill={color} stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
      ) : null}
      {name === 'tasks' ? <>
        <Path d="M8 4.5H6a2 2 0 0 0-2 2V20a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6.5a2 2 0 0 0-2-2h-2" {...stroke} />
        <Rect x="8" y="2.5" width="8" height="4.5" rx="1.5" {...stroke} />
        <Path d="M8 11h8M8 15h8M8 19h5" {...stroke} />
      </> : null}
      {name === 'chat' ? <>
        <Path d="M5 4h14a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-7l-6 3v-5a3 3 0 0 1-4-3V7a3 3 0 0 1 3-3Z" {...stroke} />
        <Circle cx="8" cy="11.5" r=".8" fill={color} /><Circle cx="12" cy="11.5" r=".8" fill={color} /><Circle cx="16" cy="11.5" r=".8" fill={color} />
      </> : null}
      {name === 'profile' ? <>
        <Circle cx="12" cy="7.5" r="4" {...stroke} />
        <Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" {...stroke} />
      </> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...stroke} strokeWidth={2.2} /> : null}
      {name === 'warning' ? <>
        <Path d="M10.3 4.3 2.7 18a1.7 1.7 0 0 0 1.5 2.5h15.6a1.7 1.7 0 0 0 1.5-2.5L13.7 4.3a2 2 0 0 0-3.4 0Z" {...stroke} />
        <Path d="M12 9v5M12 17.4v.1" {...stroke} strokeWidth={2.2} />
      </> : null}
      {name === 'signal' ? <>
        <Rect x="4" y="14" width="3.5" height="6" rx="1.4" fill={color} />
        <Rect x="10.2" y="9.5" width="3.5" height="10.5" rx="1.4" fill={color} />
        <Rect x="16.4" y="4" width="3.5" height="16" rx="1.4" fill={color} />
      </> : null}
      {name === 'leaf' ? <>
        <Path d="M11.5 21v-8.5M11.5 15.7C6.3 15.1 4.2 11.9 4 7c4.9.2 7.4 2.8 7.5 8.7ZM12.5 12.4C13 6.8 16.3 3.7 21 3c-.4 5.7-3.2 8.8-8.5 9.4Z" fill={color} stroke={color} strokeWidth={1.1} strokeLinejoin="round" />
        <Path d="M7.5 21c-1.1-2.1-1.1-4.1 0-6.1 2.1 1.1 3.1 2.8 3.1 5.1M16.4 21c1.2-2.1 1.2-4.1.1-6.1-2.1 1.1-3.1 2.8-3.1 5.1" fill={color} stroke={color} strokeWidth={1.1} strokeLinejoin="round" />
      </> : null}
      {name === 'list' ? <>
        {[5, 12, 19].map(y => <Circle key={y} cx="4" cy={y} r="1.7" fill={color} />)}
        <Path d="M9 5h12M9 12h12M9 19h12" {...stroke} strokeWidth={2.1} />
      </> : null}
      {name === 'sprout' ? <>
        <Path d="M12 21v-8.5M12 16c-4.9 0-7.4-2.8-7.5-7.4 4.8.1 7.2 2.5 7.5 7.4ZM12 12.5C12.4 7 15.7 4 20.5 3.4c-.3 5.5-3 8.6-8.5 9.1Z" fill={color} stroke={color} strokeWidth={1.1} strokeLinejoin="round" />
      </> : null}
      {name === 'drop' ? <>
        <Path d="M12 2.8S5 11 5 15.1a7 7 0 0 0 14 0C19 11 12 2.8 12 2.8Z" {...stroke} />
        <Path d="M9 15.5a3.2 3.2 0 0 0 3.2 3.2" {...stroke} />
      </> : null}
      {name === 'document' || name === 'add-document' ? <>
        <Path d="M6 2.8h8l5 5V21H6a2 2 0 0 1-2-2V4.8a2 2 0 0 1 2-2Z" {...stroke} />
        <Path d="M14 3v5h5M8 12h7M8 15.5h7" {...stroke} />
        {name === 'add-document' ? <Path d="M17.5 17v5m-2.5-2.5h5" {...stroke} strokeWidth={2.1} /> : <Path d="M8 19h4" {...stroke} />}
      </> : null}
      {name === 'check' ? <Path d="m5 12.5 4.5 4.5L19 7" {...stroke} strokeWidth={2.5} /> : null}
      {name === 'camera' ? <>
        <Path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" {...stroke} />
        <Circle cx="12" cy="13" r="3.4" {...stroke} />
      </> : null}
    </Svg>
  );
}

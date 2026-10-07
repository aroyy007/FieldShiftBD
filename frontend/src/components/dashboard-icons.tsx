import Svg, { Circle, Path, Rect } from 'react-native-svg';

export type DashboardIconName =
  | 'bell' | 'location' | 'acreage' | 'tasks' | 'fertilizer' | 'weeds'
  | 'camera' | 'rain' | 'bulb' | 'assistant' | 'scan' | 'calendar'
  | 'home' | 'chat' | 'profile' | 'chevron' | 'warning' | 'grid';

type Props = { name: DashboardIconName; size?: number; color?: string };

export function DashboardIcon({ name, size = 20, color = '#155d3b' }: Props) {
  const common = { fill: 'none', stroke: color, strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'bell' ? <>
        <Path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z" {...common} />
        <Path d="M10 21h4" {...common} />
        <Circle cx="20" cy="4" r="2.5" fill="#d79514" stroke="#fffdf7" strokeWidth="1" />
      </> : null}
      {name === 'location' ? <>
        <Path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" {...common} />
        <Circle cx="12" cy="10" r="2.2" {...common} />
      </> : null}
      {name === 'acreage' ? <>
        <Path d="M4 9.5h16v11H4zM8 9.5V6a4 4 0 0 1 8 0v3.5M8 14h8M8 17h5" {...common} />
      </> : null}
      {name === 'tasks' ? <>
        <Rect x="3.5" y="4" width="17" height="17" rx="3" fill={color} stroke={color} />
        <Path d="m7.5 12 2.5 2.5 6-6M8 7.5h8" fill="none" stroke="#fffdf7" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === 'fertilizer' ? <>
        <Path d="M12 20v-9M12 14c-4.7-.1-7-2.5-7.3-6.6 4.3.3 6.8 2.3 7.3 6.6ZM12 11c.5-4.4 3.1-6.8 7.3-7.3-.3 4.4-2.6 6.9-7.3 7.3Z" fill={color} stroke={color} strokeWidth="1.2" strokeLinejoin="round" />
        <Path d="M7 20h10" {...common} />
      </> : null}
      {name === 'weeds' ? <>
        <Path d="M12 21V8M12 16C8 14 6.8 11.2 7.4 7c3.4 1.8 4.9 4.3 4.6 9ZM12 13c.2-4.2 2.1-6.8 5.8-8.5.6 4.1-.8 7-5.8 8.5ZM8 21c-2.1-1.6-2.8-3.7-2.4-6.3 2.7 1.1 4.1 2.9 4.4 5.5M16 21c2.1-1.6 2.8-3.7 2.4-6.3-2.7 1.1-4.1 2.9-4.4 5.5" fill={color} stroke={color} strokeWidth="1.1" strokeLinejoin="round" />
      </> : null}
      {name === 'camera' ? <>
        <Path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" {...common} />
        <Circle cx="12" cy="13" r="3.4" {...common} />
      </> : null}
      {name === 'rain' ? <>
        <Path d="M6 15.5h12a4 4 0 0 0 .2-8 6.4 6.4 0 0 0-12.1 1.3A3.6 3.6 0 0 0 6 15.5Z" fill="#f4fcff" stroke="#f4fcff" strokeWidth="1.4" />
        <Path d="m8 18-1 2M13 18l-1 2M18 18l-1 2" fill="none" stroke="#d7eef0" strokeWidth="1.8" strokeLinecap="round" />
      </> : null}
      {name === 'bulb' ? <>
        <Path d="M9 16c-.3-1.4-2-2.3-2-5a5 5 0 0 1 10 0c0 2.7-1.7 3.6-2 5ZM9 18h6M10 21h4M12 1v2M4.2 4.2l1.5 1.5M1 11h2M19.8 4.2l-1.5 1.5M23 11h-2" {...common} />
      </> : null}
      {name === 'assistant' ? <>
        <Path d="M4 5.5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 3v-5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z" {...common} />
        <Circle cx="8" cy="12.5" r=".9" fill={color} /><Circle cx="12" cy="12.5" r=".9" fill={color} /><Circle cx="16" cy="12.5" r=".9" fill={color} />
      </> : null}
      {name === 'scan' ? <>
        <Path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3" {...common} />
        <Path d="M12 17c-3-.4-4.3-2.1-4.5-4.8 2.7.2 4.1 1.7 4.5 4.8ZM12.5 15.8c.4-3 2-4.7 4.8-5.2-.3 2.9-1.9 4.7-4.8 5.2Z" fill={color} stroke={color} strokeWidth=".8" />
      </> : null}
      {name === 'calendar' ? <>
        <Rect x="3.5" y="5" width="17" height="16" rx="2.5" {...common} />
        <Path d="M7.5 3v4M16.5 3v4M4 9h16" {...common} />
      </> : null}
      {name === 'home' ? <Path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1Z" fill={color} stroke={color} strokeWidth="1.5" strokeLinejoin="round" /> : null}
      {name === 'chat' ? <>
        <Path d="M4 5h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-9l-6 3v-5a2 2 0 0 1-3-2V7a2 2 0 0 1 2-2Z" {...common} />
        <Circle cx="8" cy="11.5" r=".8" fill={color} /><Circle cx="12" cy="11.5" r=".8" fill={color} /><Circle cx="16" cy="11.5" r=".8" fill={color} />
      </> : null}
      {name === 'profile' ? <>
        <Circle cx="12" cy="7.5" r="4" {...common} />
        <Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" {...common} />
      </> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...common} strokeWidth="2.2" /> : null}
      {name === 'warning' ? <>
        <Path d="M12 3 22 20H2L12 3Z" {...common} />
        <Path d="M12 9v5M12 17.5v.1" {...common} />
      </> : null}
      {name === 'grid' ? <>
        <Circle cx="7" cy="7" r="3" fill={color} /><Circle cx="17" cy="7" r="3" fill={color} />
        <Circle cx="7" cy="17" r="3" fill={color} /><Circle cx="17" cy="17" r="3" fill={color} />
      </> : null}
    </Svg>
  );
}

export function LeafSpotIllustration() {
  return (
    <Svg width="64" height="38" viewBox="0 0 64 38" aria-hidden>
      <Path d="M4 33C12 8 36 2 60 4 55 24 33 37 4 33Z" fill="#77a940" />
      <Path d="M7 33C23 25 39 15 57 6" fill="none" stroke="#d3df85" strokeWidth="2" />
      <Path d="m20 27 4-5m5-4 4-4m5 9 4-5m1-7 3-4" fill="none" stroke="#b5cf64" strokeWidth="1.3" />
      <EllipseSpots />
    </Svg>
  );
}

function EllipseSpots() {
  return <>
    <Circle cx="28" cy="24" r="2.4" fill="#694529" /><Circle cx="39" cy="16" r="2" fill="#7c4d2b" />
    <Circle cx="47" cy="20" r="1.8" fill="#583b2a" /><Circle cx="19" cy="29" r="1.5" fill="#906135" />
  </>;
}

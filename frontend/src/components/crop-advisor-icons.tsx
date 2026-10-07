import Svg, { Circle, Ellipse, Path, Rect } from 'react-native-svg';

export type CropAdvisorIconName =
  | 'back' | 'leaf' | 'location' | 'acreage' | 'sprout' | 'calendar' | 'drop'
  | 'field' | 'coins' | 'warning' | 'bug' | 'chart' | 'sowing' | 'vegetative'
  | 'reproductive' | 'maturity' | 'arrow' | 'chevron-up' | 'chevron-down'
  | 'home' | 'tasks' | 'chat' | 'scan' | 'profile' | 'grid';

type Props = { name: CropAdvisorIconName; size?: number; color?: string };

export function CropAdvisorIcon({ name, size = 22, color = '#185d3d' }: Props) {
  const line = {
    fill: 'none',
    stroke: color,
    strokeWidth: 1.9,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'back' ? <Path d="m15 5-7 7 7 7" {...line} strokeWidth="2.4" /> : null}
      {name === 'leaf' ? <>
        <Path d="M20.8 3.4C12.2 3.1 5.3 6.1 4.1 12.2c-.8 4.1 2.1 6.8 5.9 6.2 6.2-1 9.5-7.2 10.8-15Z" fill={color} />
        <Path d="M4.8 21c3.2-5.2 6.7-8.5 12.1-12.5" fill="none" stroke={color} strokeWidth="1.3" strokeLinecap="round" />
      </> : null}
      {name === 'location' ? <>
        <Path d="M19 10c0 5-7 11-7 11s-7-6-7-11a7 7 0 1 1 14 0Z" {...line} />
        <Circle cx="12" cy="10" r="2.2" {...line} />
      </> : null}
      {name === 'acreage' ? <>
        <Path d="M4 19h16M6 19V8h12v11M9 8V5h6v3M9 12h6M9 15.5h6" {...line} strokeWidth="2" />
        <Path d="M4 8h16M8 5h8" {...line} />
      </> : null}
      {name === 'sprout' || name === 'sowing' ? <>
        <Path d="M12 21v-9M12 14c-4.8-.1-7.2-2.7-7.4-7 4.5.3 7 2.4 7.4 7ZM12 11c.5-4.5 3.1-6.9 7.4-7.4-.3 4.5-2.7 7-7.4 7.4ZM7 21h10" fill={name === 'sowing' ? color : 'none'} stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === 'calendar' ? <>
        <Rect x="3.5" y="5" width="17" height="16" rx="2.5" {...line} strokeWidth="1.8" />
        <Path d="M7.5 3v4M16.5 3v4M4 9h16" {...line} strokeWidth="2" />
      </> : null}
      {name === 'drop' ? <>
        <Path d="M12 2.8S5.4 10 5.4 14.5a6.6 6.6 0 1 0 13.2 0C18.6 10 12 2.8 12 2.8Z" fill="none" stroke={color} strokeWidth="1.9" strokeLinejoin="round" />
        <Path d="M9.2 15.1c.1 1.7 1.2 2.8 2.8 3.1" {...line} strokeWidth="1.6" />
      </> : null}
      {name === 'field' ? <>
        <Path d="M3 19c4-5.2 8.6-8.4 18-10M4 21h17M5.5 16.7c3.9-4.2 7.8-6.8 15-8.9M8 20V15M12 20v-8M16 20v-9" {...line} strokeWidth="1.8" />
        <Path d="M5 13c2.1-2.2 4.1-3.6 6.2-4.8M9.6 10.5c2-2.4 4.4-4 7.4-5" {...line} strokeWidth="2.1" />
      </> : null}
      {name === 'coins' ? <>
        <Ellipse cx="10" cy="6" rx="6.5" ry="2.7" {...line} strokeWidth="1.8" />
        <Path d="M3.5 6v9c0 1.5 2.9 2.7 6.5 2.7 1.3 0 2.5-.2 3.5-.5M16.5 9.5c2.2.4 3.8 1.3 3.8 2.3v8c0 1.5-2.9 2.7-6.5 2.7s-6.5-1.2-6.5-2.7v-3M3.5 10.5c0 1.5 2.9 2.7 6.5 2.7 1.1 0 2.1-.1 3-.4M3.5 15c0 1.5 2.9 2.7 6.5 2.7" {...line} strokeWidth="1.8" />
        <Path d="M7 21h13" {...line} strokeWidth="1.8" />
      </> : null}
      {name === 'warning' ? <>
        <Path d="M12 3.2 22 20.5H2L12 3.2Z" fill="#f3a208" stroke="#f3a208" strokeLinejoin="round" />
        <Path d="M12 9v5M12 17.1v.1" fill="none" stroke="#fffdf6" strokeWidth="2" strokeLinecap="round" />
      </> : null}
      {name === 'bug' ? <>
        <Path d="M8 10.5h8v5.2a4 4 0 0 1-8 0v-5.2ZM9 9a3 3 0 0 1 6 0M12 10.5v10M5 12h3M16 12h3M5.8 17h2.5M15.7 17h2.5M7 7.5l2 2M17 7.5l-2 2M12 2v2" {...line} strokeWidth="1.7" />
      </> : null}
      {name === 'chart' ? <>
        <Rect x="3.5" y="12.5" width="4" height="8" rx="1.4" fill={color} />
        <Rect x="10" y="7.5" width="4" height="13" rx="1.4" fill={color} />
        <Rect x="16.5" y="3" width="4" height="17.5" rx="1.4" fill={color} />
      </> : null}
      {name === 'vegetative' ? <>
        <Path d="M12 21V7M12 17c-4.4-1.4-6.2-4.1-5.7-8 3.6 1.3 5.4 3.5 5.7 8ZM12.3 14c.5-4.1 2.6-6.6 6.1-8.1.5 4.1-1.5 7.1-6.1 8.1ZM6 21h12" {...line} strokeWidth="1.8" />
        <Path d="M9.3 21c-2-1.6-2.7-3.6-2.3-6.1 2.5 1.1 3.8 2.8 4.1 5.3M15 21c2-1.5 2.8-3.5 2.4-6-2.6 1.1-3.9 2.8-4.2 5.3" {...line} strokeWidth="1.6" />
      </> : null}
      {name === 'reproductive' ? <>
        <Path d="M12 21V10M12 11l-2-3M12 13l-3-2M12 15l-3-1M12 10l2-3M12 12l3-2M12 14l3-1M12 8l-1-3M14 7l2-3M9 8 7 5M15 10l3-1" {...line} strokeWidth="1.8" />
        <Ellipse cx="11" cy="4.2" rx="1.1" ry="2" fill={color} transform="rotate(-25 11 4.2)" />
        <Ellipse cx="16" cy="3.6" rx="1.1" ry="2" fill={color} transform="rotate(25 16 3.6)" />
        <Ellipse cx="6.8" cy="4.8" rx="1.1" ry="2" fill={color} transform="rotate(-40 6.8 4.8)" />
      </> : null}
      {name === 'maturity' ? <>
        <Path d="M12 21V4M12 8c-3.4-.4-5-2.3-5.1-5.3 3.2.2 5 1.7 5.1 5.3ZM12 12c3.4-.4 5-2.3 5.1-5.3-3.2.2-5 1.7-5.1 5.3ZM12 16c-3.2-.3-4.7-2.1-4.8-4.8 3 .2 4.7 1.6 4.8 4.8ZM12 19.5h5" fill={name === 'maturity' ? color : 'none'} stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </> : null}
      {name === 'arrow' ? <Path d="m8 5 7 7-7 7" {...line} strokeWidth="2.3" /> : null}
      {name === 'chevron-up' ? <Path d="m5 14 7-7 7 7" {...line} strokeWidth="2.1" /> : null}
      {name === 'chevron-down' ? <Path d="m5 10 7 7 7-7" {...line} strokeWidth="2.1" /> : null}
      {name === 'home' ? <Path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1Z" fill={color} stroke={color} strokeWidth="1.3" strokeLinejoin="round" /> : null}
      {name === 'tasks' ? <>
        <Rect x="5" y="4" width="14" height="18" rx="2" {...line} />
        <Path d="M9 4.5V3h6v1.5M8.5 10h7M8.5 14h7M8.5 18h4" {...line} strokeWidth="1.7" />
      </> : null}
      {name === 'chat' ? <>
        <Path d="M4 5h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-9l-6 3v-5a2 2 0 0 1-3-2V7a2 2 0 0 1 2-2Z" {...line} />
        <Circle cx="8" cy="11.5" r=".8" fill={color} /><Circle cx="12" cy="11.5" r=".8" fill={color} /><Circle cx="16" cy="11.5" r=".8" fill={color} />
      </> : null}
      {name === 'scan' ? <Path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3" {...line} strokeWidth="2" /> : null}
      {name === 'profile' ? <>
        <Circle cx="12" cy="7.5" r="4" {...line} />
        <Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" {...line} />
      </> : null}
      {name === 'grid' ? <>
        <Rect x="4" y="4" width="6" height="6" rx="1.5" {...line} />
        <Rect x="14" y="4" width="6" height="6" rx="1.5" {...line} />
        <Rect x="4" y="14" width="6" height="6" rx="1.5" {...line} />
        <Rect x="14" y="14" width="6" height="6" rx="1.5" {...line} />
      </> : null}
    </Svg>
  );
}

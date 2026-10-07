import Svg, { Circle, Line, Path, Rect } from 'react-native-svg';

const GREEN = '#07583f';
const INK = '#0a392f';

export type FeatureIconName = 'crop' | 'tasks' | 'weather' | 'scan';

type IconProps = {
  size?: number;
  color?: string;
};

export function BrandPlantIcon({ size = 38 }: Pick<IconProps, 'size'>) {
  return (
    <Svg width={size} height={size} viewBox="0 0 38 38" aria-hidden>
      <Path d="M18.5 35c.2-8.3-.5-15.2-3.2-22.2" fill="none" stroke="#176c3b" strokeWidth="2.4" strokeLinecap="round" />
      <Path d="M16.1 25.6C8.7 25.1 4.9 20.2 4.2 14.1c7.1 1.1 11.1 4.8 11.9 11.5Z" fill="#19703b" />
      <Path d="M16.9 18.4C17.7 10.1 23.2 5.1 31.5 4.2c-.7 8.2-5.1 13.4-14.6 14.2Z" fill="#19703b" />
      <Path d="M17.6 33.1c-6.1-.5-9.3-3.5-10.1-8.5 5.7.5 9 3.3 10.1 8.5Z" fill="#19703b" />
      <Path d="M18.7 27.1c1.3-6.1 5.6-9.7 12.3-10.5-1.1 6.1-5.2 9.9-12.3 10.5Z" fill="#19703b" />
      <Path d="M14.8 11.8c-4.2-4.7-3.5-8.4.1-11.1 4.4 4 4.3 7.8-.1 11.1Z" fill="#e29a12" />
    </Svg>
  );
}

export function FeatureIcon({ kind }: { kind: FeatureIconName }) {
  return (
    <Svg width={38} height={36} viewBox="0 0 40 40" aria-hidden>
      {kind === 'crop' ? (
        <>
          <Path d="M19.4 25.4C8.8 24.9 4 18.5 3.2 10.4c9.4 1.1 15.1 5.8 16.2 15Z" fill={GREEN} />
          <Path d="M20.4 23.4C21.2 10.2 28 3.2 38 2.5c-.8 11.8-6.9 19.5-17.6 20.9Z" fill={GREEN} />
          <Path d="M20 24v12" fill="none" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
        </>
      ) : null}
      {kind === 'tasks' ? (
        <>
          <Rect x="7" y="8" width="26" height="27" rx="4" fill="none" stroke={GREEN} strokeWidth="2.8" />
          <Line x1="13" y1="5" x2="13" y2="11" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
          <Line x1="27" y1="5" x2="27" y2="11" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
          <Line x1="8" y1="16" x2="32" y2="16" stroke={GREEN} strokeWidth="2.8" />
          <Line x1="13" y1="23" x2="18" y2="23" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
          <Line x1="23" y1="23" x2="27" y2="23" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
          <Line x1="13" y1="29" x2="18" y2="29" stroke={GREEN} strokeWidth="2.8" strokeLinecap="round" />
        </>
      ) : null}
      {kind === 'weather' ? (
        <>
          <Path d="M11 26.5a7.5 7.5 0 1 1 1.2-14.9A10 10 0 0 1 31.8 15a6 6 0 0 1-.8 11.5H11Z" fill={GREEN} />
          <Line x1="13" y1="30" x2="10.8" y2="35" stroke={GREEN} strokeWidth="3.2" strokeLinecap="round" />
          <Line x1="22" y1="30" x2="19.8" y2="35" stroke={GREEN} strokeWidth="3.2" strokeLinecap="round" />
          <Line x1="31" y1="30" x2="28.8" y2="35" stroke={GREEN} strokeWidth="3.2" strokeLinecap="round" />
        </>
      ) : null}
      {kind === 'scan' ? (
        <>
          <Path d="M13 4H8a4 4 0 0 0-4 4v5M27 4h5a4 4 0 0 1 4 4v5M4 27v5a4 4 0 0 0 4 4h5M36 27v5a4 4 0 0 1-4 4h-5" fill="none" stroke={GREEN} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <Circle cx="20" cy="20" r="5" fill="none" stroke={GREEN} strokeWidth="3" />
        </>
      ) : null}
    </Svg>
  );
}

export function ArrowRightIcon({ size = 20, color = INK }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="m9 5 7 7-7 7" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function MenuIcon({ size = 20, color = INK }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="M4 6h16M4 12h16M4 18h16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </Svg>
  );
}

export function BackChevronIcon({ size = 24, color = INK }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="m15 5-7 7 7 7" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function MobilePhoneIcon({ size = 23, color = GREEN }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Rect x="6.5" y="2.5" width="11" height="19" rx="2.2" fill="none" stroke={color} strokeWidth="2" />
      <Line x1="9.5" y1="5.5" x2="14.5" y2="5.5" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
      <Circle cx="12" cy="18.2" r=".9" fill={color} />
    </Svg>
  );
}

export function PhoneCallIcon({ size = 25, color = INK }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="M7.1 3.2 9.8 3a1.8 1.8 0 0 1 1.8 1.3l.8 3a1.8 1.8 0 0 1-.5 1.8l-1.6 1.4a14.3 14.3 0 0 0 5.2 5.2l1.4-1.6a1.8 1.8 0 0 1 1.8-.5l3 .8a1.8 1.8 0 0 1 1.3 1.8l-.2 2.7a2.2 2.2 0 0 1-2.4 2.1A18.9 18.9 0 0 1 2.9 5.6a2.2 2.2 0 0 1 2.1-2.4Z" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function PersonOutlineIcon({ size = 24, color = GREEN }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Circle cx="12" cy="7.3" r="4" fill="none" stroke={color} strokeWidth="2" />
      <Path d="M4.5 21v-2.1a7.5 7.5 0 0 1 15 0V21h-15Z" fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </Svg>
  );
}

export function LockOutlineIcon({ size = 24, color = GREEN }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Rect x="4.5" y="10" width="15" height="12" rx="2.2" fill="none" stroke={color} strokeWidth="2" />
      <Path d="M8 10V7a4 4 0 0 1 8 0v3" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <Circle cx="12" cy="15.5" r="1.1" fill={color} />
    </Svg>
  );
}

export function EyeIcon({ size = 23, color = '#65717b', visible = true }: IconProps & { visible?: boolean }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z" fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {visible ? <Circle cx="12" cy="12" r="2.6" fill="none" stroke={color} strokeWidth="2" /> : (
        <Path d="m4 4 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
      )}
    </Svg>
  );
}

export function ShieldLeafIcon({ size = 42 }: Pick<IconProps, 'size'>) {
  return (
    <Svg width={size} height={size} viewBox="0 0 44 48" aria-hidden>
      <Path d="M22 2 40 8v13c0 11.4-7 19.3-18 24C11 40.3 4 32.4 4 21V8l18-6Z" fill="#137446" />
      <Path d="M22 8v32c7.3-4.3 11.5-10.6 11.5-19V11L22 8Z" fill="#07583f" />
      <Path d="M21.4 32c-.2-8.4-4.3-13.1-11.9-13.8.8 7.2 4.4 11.7 11.9 13.8Z" fill="#fffdf7" />
      <Path d="M22.5 29.2c.7-7 4.8-11.2 12.1-12.1-.6 7-4.4 11.3-12.1 12.1Z" fill="#fffdf7" />
      <Path d="M22 40c.1-6.2.2-10.2.4-13.3" fill="none" stroke="#fffdf7" strokeWidth="1.5" strokeLinecap="round" />
    </Svg>
  );
}

export function CheckIcon({ size = 17, color = '#fffdf7' }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="m4.5 12.5 5 5L20 7" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function ChevronDownIcon({ size = 18, color = INK }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <Path d="m6 9 6 6 6-6" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

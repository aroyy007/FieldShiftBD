import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line, Rect, Text as SvgText } from 'react-native-svg';
import type { PlantingWindowEvidence } from '../services/m2-advisor';
import { COLORS, TYPOGRAPHY } from '../theme/theme';

type Props = {
  comparison: PlantingWindowEvidence['annual_comparison'];
  gdd?: PlantingWindowEvidence['gdd_summary'];
  language: 'bn' | 'en';
};

export default function ClimateEvidenceCharts({ comparison, gdd = null, language }: Props) {
  const bn = language === 'bn';
  const groups = comparison ? [comparison.baseline, comparison.recent] : [];
  const values = groups.flatMap(item => item.onset_day_offsets).filter(Number.isFinite);
  const minimum = values.length ? Math.min(...values) : 0;
  const maximum = values.length ? Math.max(...values) : 1;
  const low = minimum === maximum ? minimum - 1 : minimum;
  const high = minimum === maximum ? maximum + 1 : maximum;
  const x = (value: number) => 24 + ((value - low) / (high - low)) * 312;
  const periods = [comparison?.baseline_period ?? '2001–2012', comparison?.recent_period ?? '2013–2025'];
  const gddValues = gdd?.annual_values ?? [];
  const maximumGdd = Math.max(1, ...gddValues.map(item => item.total_degree_days ?? 0));

  return (
    <View style={styles.root}>
      <Text style={styles.heading}>{bn ? 'বৃষ্টির শুরুর দুই সময়কালের তুলনা' : 'Rainfall onset: compare the two periods'}</Text>
      {comparison && values.length > 0 ? <>
        <Text style={styles.helper}>{bn ? 'প্রতি বিন্দু একটি বছর। একই দিনে একাধিক বছর হলে বিন্দুগুলো ওপরের দিকে সাজানো হয়েছে।' : 'Each dot is one year. Years with the same onset day are stacked vertically.'}</Text>
        <Svg width="100%" height={250} viewBox="0 0 360 250" accessible={false}>
          {groups.map((group, index) => {
            const seen = new Map<number, number>();
            const y = index === 0 ? 102 : 207;
            const color = index === 0 ? '#245b95' : '#247341';
            return <ViewlessGroup key={periods[index]} label={periods[index]} y={y} color={color} points={group.onset_day_offsets.map((value, pointIndex) => {
              const stack = seen.get(value) ?? 0;
              seen.set(value, stack + 1);
              return <Circle key={pointIndex} cx={x(value)} cy={y - stack * 7} r={3} fill={color} />;
            })} />;
          })}
          <Line x1={24} x2={336} y1={230} y2={230} stroke={COLORS.border} />
          {[low, (low + high) / 2, high].map((value, index) => <SvgText key={index} x={x(value)} y={246} fontSize={11} textAnchor="middle" fill={COLORS.text}>{Number(value.toFixed(1))}</SvgText>)}
        </Svg>
        <Text style={styles.helper}>{bn ? 'অনুসন্ধানের নির্ধারিত শুরুর পর দিন; এটি সরাসরি রোপণের তারিখ নয়।' : 'Days after the declared search-window start; these are not transplanting dates.'}</Text>
        {groups.map((group, index) => <Text key={periods[index]} style={styles.helper}>{periods[index]} ({group.sample_size} {bn ? 'বছর' : 'years'}): {group.onset_day_offsets.join(', ') || '—'}</Text>)}
      </> : <Text style={styles.helper}>{bn ? 'তুলনার জন্য যথেষ্ট বৃষ্টির তথ্য নেই।' : 'There are not enough rainfall observations to plot.'}</Text>}
      <Text style={styles.heading}>{bn ? 'বছরভিত্তিক তাপ সঞ্চয় (GDD)' : 'Annual thermal accumulation (GDD)'}</Text>
      {gdd && gddValues.length > 0 ? <>
        <Svg width="100%" height={180} viewBox="0 0 360 180" accessible={false}>
          <Line x1={20} x2={340} y1={155} y2={155} stroke={COLORS.border} />
          {gddValues.map((item, index) => {
            const width = 320 / gddValues.length;
            const height = item.total_degree_days === null ? 0 : (item.total_degree_days / maximumGdd) * 130;
            return <Rect key={item.year} x={20 + index * width} y={item.total_degree_days === null ? 152 : 155 - height} width={Math.max(1, width - 2)} height={item.total_degree_days === null ? 3 : height} fill={item.total_degree_days === null ? '#929b95' : COLORS.primary} />;
          })}
          <SvgText x={20} y={174} fontSize={11} fill={COLORS.text}>{gddValues[0]?.year}</SvgText>
          <SvgText x={340} y={174} fontSize={11} textAnchor="end" fill={COLORS.text}>{gddValues[gddValues.length - 1]?.year}</SvgText>
          <SvgText x={340} y={14} fontSize={11} textAnchor="end" fill={COLORS.text}>{maximumGdd.toFixed(0)} °C·day</SvgText>
        </Svg>
        <Text style={styles.helper}>{bn ? 'সম্পূর্ণ বছরের হিসাব, °C·day; ধূসর চিহ্নে তথ্য অসম্পূর্ণ।' : 'Complete-year totals in °C·day; grey marks indicate incomplete observations.'}</Text>
        <Text style={styles.helper}>{gddValues.map(item => `${item.year}: ${item.total_degree_days ?? '—'}`).join(' · ')}</Text>
      </> : <Text style={styles.helper}>{bn ? 'এই জাতের পর্যালোচিত GDD পদ্ধতি পাওয়া গেলে চার্ট দেখাবে। কোনো মান অনুমান করা হয়নি।' : 'A chart will appear when a reviewed GDD method is available for this variety. No values have been assumed.'}</Text>}
    </View>
  );
}

function ViewlessGroup({ label, y, color, points }: { label: string; y: number; color: string; points: React.ReactNode[] }) {
  return <>
    <SvgText x={24} y={y - 88} fontSize={12} fill={color}>{label}</SvgText>
    <Line x1={24} x2={336} y1={y + 7} y2={y + 7} stroke={COLORS.border} />
    {points}
  </>;
}

const styles = StyleSheet.create({
  root: { gap: 8, paddingVertical: 8 },
  heading: { ...TYPOGRAPHY.body, fontWeight: '600', marginTop: 8 },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 20 },
});

import { useState } from 'react';
import { Linking, StyleSheet, Text, View } from 'react-native';
import { Button } from '../ui';
import type { CalendarStepEvidenceV2 } from '../../modules/shared/contracts-v2.generated';
import { calendarDrySpellText, calendarWeatherText } from '../../services/rotation-display';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';

type Props={evidence: CalendarStepEvidenceV2;language:'bn'|'en';stepNumber:number};
export default function CalendarStepDetails({evidence,language,stepNumber}:Props) {
  const [open,setOpen]=useState(false);
  const [linkError,setLinkError]=useState(false);
  const bn=language==='bn';
  const statuses={
    method_mismatch:bn?'চাষের পদ্ধতি মেলে না':'Establishment method differs',
    method_not_recorded:bn?'চাষের পদ্ধতি নিশ্চিত করুন':'Confirm establishment method',
    not_available:bn?'মিল থাকা ক্যালেন্ডার নেই':'No matching calendar',
    source_reference_available:bn?'প্রকাশিত ক্যালেন্ডার পাওয়া গেছে':'Published calendar reference',
  };
  return <View style={styles.stack}>
    <Button accessibilityRole="button" variant="outline" accessibilityState={{expanded:open}}
      title={`${bn?'ধাপ':'Step'} ${stepNumber} · ${statuses[evidence.status]}`} onPress={()=>setOpen(v=>!v)} />
    {open && <View style={styles.stack}>
      <Text style={styles.note}>{bn?evidence.limitation_bn:evidence.limitation_en}</Text>
      {evidence.references?.map(ref=><View key={ref.profile_id} style={styles.reference}>
        <Text style={styles.title}>{bn?ref.variety_name_bn:ref.variety_name}</Text>
        <Text style={styles.note}>{bn?'উৎসে চাষের পদ্ধতি':'Source establishment method'}: {ref.cultivation_method === 'transplanted' ? (bn?'চারা রোপণ':'Transplanted') : (bn?'অন্য পদ্ধতি; উৎস দেখুন': 'Other method; see source')}</Text>
        <Text style={styles.note}>{bn?'প্রকাশিত চাষ শুরুর সময়':'Published establishment window'}: {ref.establishment_window.start} – {ref.establishment_window.end}</Text>
        <Text style={styles.note}>{bn?'প্রকাশিত ফসল কাটার সময়':'Published harvest window'}: {ref.harvest_window.start} – {ref.harvest_window.end}</Text>
        {ref.weather && <>
          <Text style={styles.note}>{bn?'নির্বাচিত বছরের সময়সীমা':'Calendar scenario dates'}: {ref.weather.establishment_start} – {ref.weather.establishment_end} → {ref.weather.harvest_start} – {ref.weather.harvest_end}</Text>
          <Text style={styles.body}>{calendarWeatherText(ref.weather,language)}</Text>
          <Text style={styles.body}>{calendarDrySpellText(ref.weather,language)}</Text>
        </>}
        {!ref.weather && <Text style={styles.note}>{bn?'এই ক্যালেন্ডারের সঙ্গে আবহাওয়ার হিসাব প্রয়োগ করা হয়নি।':'Weather calculations have not been applied to this calendar.'}</Text>}
        <Text style={styles.note}>{bn?ref.scope_bn:ref.scope_en}</Text>
        <Text style={styles.note}>{bn?'উৎস যাচাই হয়েছে; কৃষিবিদের পর্যালোচনা বাকি।':'Source checked; agronomic review pending.'}</Text>
        <Button accessibilityRole="button" variant="outline" title={bn?'BRRI-র মূল তথ্য':'Open BRRI reference'} onPress={()=>{void Linking.openURL(ref.source_url).catch(()=>setLinkError(true));}} />
      </View>)}
      {linkError && <Text accessibilityRole="alert" style={styles.note}>{bn?'উৎস খোলা যায়নি।':'Could not open source.'}</Text>}
    </View>}
  </View>;
}
const styles=StyleSheet.create({stack:{gap:SPACING.sm},reference:{borderLeftWidth:2,borderLeftColor:COLORS.border,paddingLeft:SPACING.md,gap:SPACING.sm},title:{...TYPOGRAPHY.body,fontWeight:'600'},body:{...TYPOGRAPHY.body,lineHeight:25},note:{...TYPOGRAPHY.bodySecondary,fontSize:14,lineHeight:22}});

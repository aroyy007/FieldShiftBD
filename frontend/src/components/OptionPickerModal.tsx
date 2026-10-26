import { useMemo, useState } from 'react';
import { FlatList, Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

export type PickerOption = { value: string; label: string; detail?: string };

type Props = {
  visible: boolean;
  title: string;
  options: PickerOption[];
  selected?: string | null;
  allowClear?: boolean;
  onSelect: (value: string | null) => void;
  onClose: () => void;
};

const PAPER = '#fffdf7';
const INK = '#102b25';
const GREEN = '#07543a';

/** Searchable single-choice sheet used for reference data (locations, soil, varieties). */
export default function OptionPickerModal({ visible, title, options, selected, allowClear, onSelect, onClose }: Props) {
  const [query, setQuery] = useState('');
  const filtered = useMemo(() => {
    const key = query.trim().toLowerCase();
    if (!key) return options;
    return options.filter(option =>
      option.label.toLowerCase().includes(key) || option.detail?.toLowerCase().includes(key));
  }, [options, query]);

  const close = () => {
    setQuery('');
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={close}>
      <View style={styles.root}>
        <Pressable accessibilityLabel="Close picker" style={styles.scrim} onPress={close} />
        <View style={styles.sheet}>
          <Text style={styles.title}>{title}</Text>
          {options.length > 8 ? (
            <TextInput
              accessibilityLabel={`Search ${title}`}
              autoCorrect={false}
              placeholder="Search"
              placeholderTextColor="#82909a"
              value={query}
              onChangeText={setQuery}
              style={styles.search}
            />
          ) : null}
          <FlatList
            data={filtered}
            keyExtractor={item => item.value}
            keyboardShouldPersistTaps="handled"
            style={styles.list}
            ListEmptyComponent={<Text style={styles.empty}>No matching options.</Text>}
            renderItem={({ item }) => (
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ selected: item.value === selected }}
                onPress={() => { setQuery(''); onSelect(item.value); }}
                style={styles.row}
              >
                <View style={styles.rowCopy}>
                  <Text style={styles.rowLabel}>{item.label}</Text>
                  {item.detail ? <Text style={styles.rowDetail}>{item.detail}</Text> : null}
                </View>
                <View style={[styles.radio, item.value === selected && styles.radioSelected]} />
              </Pressable>
            )}
          />
          <View style={styles.actions}>
            {allowClear ? (
              <Pressable accessibilityRole="button" onPress={() => { setQuery(''); onSelect(null); }} style={styles.secondary}>
                <Text style={styles.secondaryText}>Clear</Text>
              </Pressable>
            ) : null}
            <Pressable accessibilityRole="button" onPress={close} style={styles.secondary}>
              <Text style={styles.secondaryText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: 'flex-end', paddingHorizontal: 12, paddingBottom: 18 },
  scrim: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: 'rgba(16, 24, 32, 0.38)' },
  sheet: { maxHeight: '80%', padding: 14, borderRadius: 18, backgroundColor: PAPER },
  title: { color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 24, fontWeight: '700', marginBottom: 8 },
  search: { minHeight: 42, paddingHorizontal: 12, marginBottom: 6, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 10, backgroundColor: '#f8f7f2', color: INK, fontSize: 15 },
  list: { flexGrow: 0 },
  empty: { paddingVertical: 14, color: '#52677a', fontSize: 14 },
  row: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, borderBottomWidth: 1, borderBottomColor: '#e5e2d8' },
  rowCopy: { flex: 1, minWidth: 0, paddingVertical: 6 },
  rowLabel: { color: INK, fontSize: 15 },
  rowDetail: { color: '#52677a', fontSize: 12, marginTop: 2 },
  radio: { width: 18, height: 18, borderRadius: 10, borderWidth: 1.5, borderColor: '#abb6ad' },
  radioSelected: { borderWidth: 6, borderColor: GREEN },
  actions: { flexDirection: 'row', gap: 8, marginTop: 8 },
  secondary: { flex: 1, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 9, backgroundColor: '#edf2e8' },
  secondaryText: { color: GREEN, fontSize: 14, fontWeight: '700' },
});

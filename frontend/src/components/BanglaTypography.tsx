import React, { forwardRef } from 'react';
import {
  StyleSheet,
  Text as NativeText,
  TextInput as NativeTextInput,
} from 'react-native';
import type { TextInputProps, TextProps } from 'react-native';

const BENGALI_SCRIPT = /[\u0980-\u09FF]/u;
const MINA_REGULAR = 'MinaRegular';
const MINA_BOLD = 'MinaBold';

function hasBangla(value: unknown): boolean {
  if (typeof value === 'string') return BENGALI_SCRIPT.test(value);
  if (Array.isArray(value)) return value.some(hasBangla);
  return false;
}

function includesBangla(...values: unknown[]): boolean {
  return values.some(hasBangla);
}

function minaFamily(style: TextProps['style']): string {
  const weight = StyleSheet.flatten(style)?.fontWeight;
  const numericWeight = typeof weight === 'number' ? weight : Number(weight);
  return weight === 'bold' || numericWeight >= 600 ? MINA_BOLD : MINA_REGULAR;
}

/** Use Mina only for text containing Bangla, preserving existing English typography. */
export const Text = forwardRef<React.ElementRef<typeof NativeText>, TextProps>(
  function BanglaAwareText({ children, style, ...props }, ref) {
    const fontFamily = includesBangla(children) ? minaFamily(style) : undefined;
    return (
      <NativeText
        {...props}
        ref={ref}
        style={fontFamily ? [style, { fontFamily }] : style}
      >
        {children}
      </NativeText>
    );
  },
);

Text.displayName = 'BanglaAwareText';

/** Keep Bangla placeholders and typed values in Mina as the input changes. */
export const TextInput = forwardRef<React.ElementRef<typeof NativeTextInput>, TextInputProps>(
  function BanglaAwareTextInput({ style, value, defaultValue, placeholder, ...props }, ref) {
    const fontFamily = includesBangla(value, defaultValue, placeholder)
      ? minaFamily(style as TextProps['style'])
      : undefined;
    return (
      <NativeTextInput
        {...props}
        ref={ref}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        style={fontFamily ? [style, { fontFamily }] : style}
      />
    );
  },
);

TextInput.displayName = 'BanglaAwareTextInput';

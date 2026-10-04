import React from 'react';
import { TouchableOpacity, Text, TextInput, View, StyleSheet, TouchableOpacityProps, TextInputProps } from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, TYPOGRAPHY, SHADOWS } from '../theme/theme';

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: 'primary' | 'secondary' | 'outline';
}

export const Button = ({ title, variant = 'primary', style, ...props }: ButtonProps) => {
  const getBgColor = () => {
    if (variant === 'primary') return COLORS.primary;
    if (variant === 'secondary') return COLORS.surface;
    return 'transparent';
  };

  const getTextColor = () => {
    if (variant === 'primary') return COLORS.surface;
    return COLORS.primary;
  };

  return (
    <TouchableOpacity
      style={[
        styles.button,
        { backgroundColor: getBgColor() },
        variant === 'outline' && styles.buttonOutline,
        style,
      ]}
      {...props}
    >
      <Text style={[styles.buttonText, { color: getTextColor() }]}>{title}</Text>
    </TouchableOpacity>
  );
};

interface InputProps extends TextInputProps {
  label?: string;
}

export const Input = ({ label, style, ...props }: InputProps) => {
  return (
    <View style={styles.inputContainer}>
      {label && <Text style={styles.inputLabel}>{label}</Text>}
      <TextInput
        style={[styles.input, style]}
        placeholderTextColor={COLORS.textSecondary}
        {...props}
      />
    </View>
  );
};

export const Card = ({ children, style }: { children: React.ReactNode; style?: any }) => {
  return <View style={[styles.card, style]}>{children}</View>;
};

const styles = StyleSheet.create({
  button: {
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonOutline: {
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  buttonText: {
    ...TYPOGRAPHY.h3,
  },
  inputContainer: {
    marginBottom: SPACING.md,
  },
  inputLabel: {
    ...TYPOGRAPHY.caption,
    marginBottom: SPACING.xs,
    color: COLORS.text,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    ...TYPOGRAPHY.body,
    backgroundColor: COLORS.surface,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.sm,
  },
});

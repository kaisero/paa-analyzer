import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider, theme as antdTheme } from 'antd';
import type { ThemeConfig } from 'antd';
import './styles/global.css';
import App from './App';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

/**
 * Accent — Prisma cyan.
 *
 * Two values, one hue (187.6°): the bright cyan reads at 8.8:1 on the dark
 * canvas but only 2.0:1 on white, and the accent is used as *text* (the
 * wordmark, the pacli prompt, the report heading), so light mode takes a
 * darker shade of the same colour at 4.9:1. Keep both in sync with the
 * `--accent*` custom properties in styles/global.css.
 */
const ACCENT = { dark: '#00c8e5', light: '#0E7C8C' } as const;
const ACCENT_RGB = { dark: '0,200,229', light: '14,124,140' } as const;

/** Accent at a given alpha, for the tints antd wants as literals. */
const tint = (mode: 'dark' | 'light', alpha: number) => `rgba(${ACCENT_RGB[mode]},${alpha})`;

const sharedToken = {
  borderRadius: 0,
  borderRadiusLG: 0,
  borderRadiusSM: 0,
  borderRadiusXS: 0,
  fontFamily: "'Inter', -apple-system, 'Segoe UI', sans-serif",
  fontFamilyCode: "'JetBrains Mono', 'SF Mono', Consolas, monospace",
  fontSize: 13,
  fontSizeSM: 11,
};

/** Component overrides that depend on the accent, so they differ per theme. */
const sharedComponents = (mode: 'dark' | 'light') => ({
  Tabs: {
    inkBarColor: ACCENT[mode],
    itemActiveColor: '#E8EEF4',
    itemHoverColor: '#E8EEF4',
    itemSelectedColor: '#E8EEF4',
    titleFontSize: 12,
    horizontalItemPadding: '14px 18px',
  },
  Input: {
    activeBorderColor: tint(mode, 0.6),
    hoverBorderColor: tint(mode, 0.4),
    activeShadow: `0 0 0 2px ${tint(mode, 0.2)}`,
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
  },
  Button: { fontWeight: 600, fontSize: 11 },
  Tag: { fontSizeSM: 10 },
  Card: { headerBg: '#1C2535', headerFontSize: 11, headerHeight: 36 },
  Select: {
    selectorBg: '#1C2535',
    optionSelectedBg: tint(mode, 0.12),
    activeBorderColor: tint(mode, 0.6),
  },
  DatePicker: {
    activeBorderColor: tint(mode, 0.6),
    hoverBorderColor: tint(mode, 0.4),
    activeShadow: `0 0 0 2px ${tint(mode, 0.2)}`,
  },
});

const lightComponents = sharedComponents('light');

const darkTokens: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    ...sharedToken,
    colorPrimary: ACCENT.dark,
    colorBgBase: '#0C0F14',
    colorBgContainer: '#131920',
    colorBgElevated: '#1C2535',
    colorBorder: '#283040',
    colorBorderSecondary: '#1E2632',
    colorText: '#E8EEF4',
    colorTextSecondary: '#8FA4BC',
    colorTextTertiary: '#5C6E84',
    colorTextQuaternary: '#5C6E84',
    colorError: '#F0564A',
    colorWarning: '#E8A33D',
    colorSuccess: '#3DBE7B',
    colorInfo: '#4D9FDC',
  },
  components: {
    ...sharedComponents('dark'),
    Layout: {
      headerBg: '#131920',
      bodyBg: '#0C0F14',
      siderBg: '#131920',
      headerHeight: 52,
      headerPadding: '0 0',
    },
    Menu: {
      darkItemBg: '#131920',
      darkSubMenuItemBg: '#131920',
      darkItemSelectedBg: tint('dark', 0.12),
      darkItemSelectedColor: '#E8EEF4',
      darkItemHoverBg: tint('dark', 0.06),
      darkItemHoverColor: '#E8EEF4',
      itemHeight: 30,
      itemMarginBlock: 0,
      itemMarginInline: 0,
      itemPaddingInline: 12,
      groupTitleFontSize: 10,
      groupTitleColor: '#5C6E84',
      activeBarBorderWidth: 3,
    },
    Table: {
      headerBg: '#1C2535',
      rowHoverBg: tint('dark', 0.06),
      borderColor: '#1E2632',
      headerColor: '#8FA4BC',
      headerSortActiveBg: '#1C2535',
      headerSortHoverBg: '#1C2535',
      fontSize: 12,
    },
  },
};

const lightTokens: ThemeConfig = {
  algorithm: antdTheme.defaultAlgorithm,
  token: {
    ...sharedToken,
    colorPrimary: ACCENT.light,
    colorBgBase: '#F0F4F8',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#E8EEF4',
    colorBorder: '#CBD5E1',
    colorBorderSecondary: '#DAE2EC',
    colorText: '#0F172A',
    colorTextSecondary: '#526071',
    colorTextTertiary: '#7C8A9C',
    colorTextQuaternary: '#7C8A9C',
    colorError: '#C4372C',
    colorWarning: '#A66E12',
    colorSuccess: '#1F8A55',
    colorInfo: '#1D6FAE',
  },
  components: {
    ...lightComponents,
    Tabs: {
      ...lightComponents.Tabs,
      itemActiveColor: '#0F172A',
      itemHoverColor: '#0F172A',
      itemSelectedColor: '#0F172A',
    },
    Card: { ...lightComponents.Card, headerBg: '#E8EEF4' },
    Select: { ...lightComponents.Select, selectorBg: '#FFFFFF' },
    Layout: {
      headerBg: '#FFFFFF',
      bodyBg: '#F0F4F8',
      siderBg: '#FFFFFF',
      headerHeight: 52,
      headerPadding: '0 0',
    },
    Menu: {
      itemBg: '#FFFFFF',
      subMenuItemBg: '#FFFFFF',
      itemSelectedBg: tint('light', 0.08),
      itemSelectedColor: '#0F172A',
      itemHoverBg: tint('light', 0.05),
      itemHoverColor: '#0F172A',
      itemHeight: 30,
      itemMarginBlock: 0,
      itemMarginInline: 0,
      itemPaddingInline: 12,
      groupTitleFontSize: 10,
      groupTitleColor: '#7C8A9C',
      activeBarBorderWidth: 3,
    },
    Table: {
      headerBg: '#E8EEF4',
      rowHoverBg: tint('light', 0.05),
      borderColor: '#DAE2EC',
      headerColor: '#526071',
      fontSize: 12,
    },
  },
};

function AppWithTheme() {
  const { isDark } = useTheme();
  return (
    <ConfigProvider theme={isDark ? darkTokens : lightTokens}>
      <App />
    </ConfigProvider>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AppWithTheme />
    </ThemeProvider>
  </StrictMode>,
);

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider, theme as antdTheme } from 'antd';
import type { ThemeConfig } from 'antd';
import './styles/global.css';
import App from './App';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

const sharedToken = {
  colorPrimary: '#FA582D',
  borderRadius: 0,
  borderRadiusLG: 0,
  borderRadiusSM: 0,
  borderRadiusXS: 0,
  fontFamily: "'Inter', -apple-system, 'Segoe UI', sans-serif",
  fontFamilyCode: "'JetBrains Mono', 'SF Mono', Consolas, monospace",
  fontSize: 13,
  fontSizeSM: 11,
};

const sharedComponents = {
  Tabs: {
    inkBarColor: '#FA582D',
    itemActiveColor: '#E8EEF4',
    itemHoverColor: '#E8EEF4',
    itemSelectedColor: '#E8EEF4',
    titleFontSize: 12,
    horizontalItemPadding: '14px 18px',
  },
  Input: {
    activeBorderColor: 'rgba(250,88,45,0.6)',
    hoverBorderColor: 'rgba(250,88,45,0.4)',
    activeShadow: '0 0 0 2px rgba(250,88,45,0.2)',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
  },
  Button: { fontWeight: 600, fontSize: 11 },
  Tag: { fontSizeSM: 10 },
  Card: { headerBg: '#1C2535', headerFontSize: 11, headerHeight: 36 },
  Select: {
    selectorBg: '#1C2535',
    optionSelectedBg: 'rgba(250,88,45,0.12)',
    activeBorderColor: 'rgba(250,88,45,0.6)',
  },
  DatePicker: {
    activeBorderColor: 'rgba(250,88,45,0.6)',
    hoverBorderColor: 'rgba(250,88,45,0.4)',
    activeShadow: '0 0 0 2px rgba(250,88,45,0.2)',
  },
};

const darkTokens: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    ...sharedToken,
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
    ...sharedComponents,
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
      darkItemSelectedBg: 'rgba(250,88,45,0.12)',
      darkItemSelectedColor: '#E8EEF4',
      darkItemHoverBg: 'rgba(250,88,45,0.06)',
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
      rowHoverBg: 'rgba(250,88,45,0.06)',
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
    ...sharedComponents,
    Tabs: {
      ...sharedComponents.Tabs,
      itemActiveColor: '#0F172A',
      itemHoverColor: '#0F172A',
      itemSelectedColor: '#0F172A',
    },
    Card: { ...sharedComponents.Card, headerBg: '#E8EEF4' },
    Select: { ...sharedComponents.Select, selectorBg: '#FFFFFF' },
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
      itemSelectedBg: 'rgba(250,88,45,0.08)',
      itemSelectedColor: '#0F172A',
      itemHoverBg: 'rgba(250,88,45,0.05)',
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
      rowHoverBg: 'rgba(250,88,45,0.05)',
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

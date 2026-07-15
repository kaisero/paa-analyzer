import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider, theme } from 'antd';
import './styles/global.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00c8e5',
          colorBgBase: '#0a0e14',
          colorBgContainer: '#111820',
          colorBgElevated: '#1a2332',
          colorBorder: '#1e2a3a',
          colorText: '#e6edf3',
          colorTextSecondary: '#8b949e',
          fontFamily: "'Inter', system-ui, sans-serif",
        },
        components: {
          Layout: { headerBg: '#111820', bodyBg: '#0a0e14', siderBg: '#111820' },
          Menu: { darkItemBg: '#111820', darkSubMenuItemBg: '#111820', darkItemSelectedBg: 'transparent', darkItemSelectedColor: '#00c8e5', darkItemHoverBg: '#1e2a3a', itemHeight: 28, itemMarginBlock: 0, itemMarginInline: 0, itemPaddingInline: 8, groupTitleFontSize: 10 },
          Table: { headerBg: '#111820', rowHoverBg: '#1e2a3a', borderColor: '#1e2a3a' },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>,
);

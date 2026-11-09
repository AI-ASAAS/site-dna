import './styles/app.css';
import './asaas-ui/styles/index.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Ambient, ToastProvider } from './asaas-ui';
import { LangProvider } from './lib/i18n';
import App from './App.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LangProvider>
      <ToastProvider>
        <Ambient />
        <App />
      </ToastProvider>
    </LangProvider>
  </StrictMode>,
);

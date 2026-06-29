import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

interface PreferencesContextValue {
  emailNotif: boolean;
  soundAlerts: boolean;
  setEmailNotif: (v: boolean) => void;
  setSoundAlerts: (v: boolean) => void;
}

const PreferencesContext = createContext<PreferencesContextValue>({
  emailNotif: true,
  soundAlerts: true,
  setEmailNotif: () => {},
  setSoundAlerts: () => {},
});

export const usePreferences = () => useContext(PreferencesContext);

export const PreferencesProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [emailNotif, setEmailNotifState] = useState(() => localStorage.getItem('emailNotif') !== 'false');
  const [soundAlerts, setSoundAlertsState] = useState(() => localStorage.getItem('soundAlerts') !== 'false');

  const setEmailNotif = useCallback((v: boolean) => {
    setEmailNotifState(v);
    localStorage.setItem('emailNotif', String(v));
  }, []);

  const setSoundAlerts = useCallback((v: boolean) => {
    setSoundAlertsState(v);
    localStorage.setItem('soundAlerts', String(v));
  }, []);

  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === 'emailNotif') setEmailNotifState(e.newValue !== 'false');
      if (e.key === 'soundAlerts') setSoundAlertsState(e.newValue !== 'false');
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, []);

  return (
    <PreferencesContext.Provider value={{ emailNotif, soundAlerts, setEmailNotif, setSoundAlerts }}>
      {children}
    </PreferencesContext.Provider>
  );
};

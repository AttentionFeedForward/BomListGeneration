import React, { useState, createContext, useContext } from 'react';
import './App.css';
import AppRouter, { PageType } from './components/Router/AppRouter';
import ParticleBackground from './components/Effects/ParticleBackground';
import Sidebar from './components/Navigation/Sidebar';
import { AppProvider } from './store';
import { ErrorBoundary } from './components/ErrorBoundary';
import { NotificationProvider } from './components/Notification';

// 导航上下文
interface NavigationContextType {
  currentPage: PageType;
  navigateTo: (page: PageType) => void;
}

const NavigationContext = createContext<NavigationContextType | null>(null);

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within NavigationProvider');
  }
  return context;
};

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');

  const navigateTo = (page: PageType) => {
    setCurrentPage(page);
  };

  return (
    <ErrorBoundary>
      <AppProvider>
        <NotificationProvider>
          <NavigationContext.Provider value={{ currentPage, navigateTo }}>
            <div className="App min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
              <ParticleBackground />
              <div className="relative z-10 flex">
                <ErrorBoundary>
                  <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
                </ErrorBoundary>
                <main className="flex-1 ml-64">
                  <ErrorBoundary>
                    <AppRouter currentPage={currentPage} />
                  </ErrorBoundary>
                </main>
              </div>
            </div>
          </NavigationContext.Provider>
        </NotificationProvider>
      </AppProvider>
    </ErrorBoundary>
  );
}

export default App;

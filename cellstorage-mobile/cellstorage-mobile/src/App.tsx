import React, { useState } from 'react';
import { ThemeProvider } from '@/components/theme-provider';
import MobileDashboard from '@/components/mobile-dashboard';
import MobileLocations from '@/components/mobile-locations';
import MobileCellLines from '@/components/mobile-cell-lines';
import './globals.css';

type Page = 'dashboard' | 'locations' | 'celllines';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <MobileDashboard onNavigate={setCurrentPage} />;
      case 'locations':
        return <MobileLocations onNavigate={setCurrentPage} />;
      case 'celllines':
        return <MobileCellLines onNavigate={setCurrentPage} />;
      default:
        return <MobileDashboard onNavigate={setCurrentPage} />;
    }
  };

  return (
    <ThemeProvider defaultTheme="light" storageKey="cellstorage-ui-theme">
      <div className="App">
        {renderPage()}
      </div>
    </ThemeProvider>
  );
}

export default App;
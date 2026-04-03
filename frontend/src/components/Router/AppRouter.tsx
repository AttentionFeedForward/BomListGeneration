import React from 'react';
import Dashboard from '../Dashboard/Dashboard';
import ContourProcessing from '../Pages/ContourProcessing';
import LayoutRecognition from '../Pages/LayoutRecognition';

import MaterialCalculation from '../Pages/MaterialCalculation';
import BOMGeneration from '../Pages/BOMGeneration';

export type PageType = 'dashboard' | 'contour-processing' | 'layout-recognition' | 'material-calculation' | 'bom-generation' | 'settings';

interface AppRouterProps {
  currentPage: PageType;
}

const AppRouter: React.FC<AppRouterProps> = ({ currentPage }) => {
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'contour-processing':
        return <ContourProcessing />;
      case 'layout-recognition':
        return <LayoutRecognition />;
      case 'material-calculation':
        return <MaterialCalculation />;
      case 'bom-generation':
        return <BOMGeneration />;
      case 'settings':
        return (
          <div className="p-6">
            <h1 className="text-3xl font-bold text-white mb-4">系统设置</h1>
            <div className="glass-effect rounded-xl p-6 border border-white/20">
              <p className="text-gray-400">系统设置功能正在开发中...</p>
            </div>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return <>{renderPage()}</>;
};

export default AppRouter;
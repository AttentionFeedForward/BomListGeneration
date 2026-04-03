import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, Calculator, FileText, Activity, Upload, Settings, Download, RefreshCw } from 'lucide-react';
import { Card, ProgressBar, PageTransition, AnimatedContainer, FloatingActionButton, ResponsiveGrid, ResponsiveContainer } from '../UI';
import { useResponsive, usePerformanceMonitor } from '../../hooks';
import QuickActions from './QuickActions';
import RecentActivity from './RecentActivity';
import ContourVisualization from '../Contour/ContourVisualization';
import { useActions, useApp } from '../../store';
import { useNotification } from '../Notification';
import { LoadingOverlay } from '../Loading';

interface StatsData {
  title: string;
  value: string;
  unit: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
}

const Dashboard: React.FC = () => {
  const { isMobile, isTablet, currentBreakpoint } = useResponsive();
  const { metrics: performanceMetrics } = usePerformanceMonitor();
  const { loading } = useApp();
  const { addNotification } = useActions();
  const [refreshing, setRefreshing] = useState(false);

  // 模拟数据（后续可以替换为真实API调用）
  const statsData: StatsData[] = [
    {
      title: '今日处理',
      value: '24',
      unit: '个项目',
      change: '+12%',
      trend: 'up',
      icon: <Activity className="w-6 h-6" />,
      color: 'neon-green'
    },
    {
      title: '模块识别',
      value: '156',
      unit: '个模块',
      change: '+8%',
      trend: 'up',
      icon: <Eye className="w-6 h-6" />,
      color: 'neon-cyan'
    },
    {
      title: '物料计算',
      value: '89',
      unit: '种物料',
      change: '-3%',
      trend: 'down',
      icon: <Calculator className="w-6 h-6" />,
      color: 'neon-blue'
    },
    {
      title: 'BOM生成',
      value: '94.2%',
      unit: '准确率',
      change: '+2.1%',
      trend: 'up',
      icon: <FileText className="w-6 h-6" />,
      color: 'neon-purple'
    }
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 2000));
      addNotification({
        id: Math.random().toString(36).substr(2, 9),
        type: 'success',
        title: '数据刷新成功',
        message: '仪表板数据已更新到最新状态',
        timestamp: new Date()
      });
    } catch (error) {
      addNotification({
        id: Math.random().toString(36).substr(2, 9),
        type: 'error',
        title: '刷新失败',
        message: '无法获取最新数据，请稍后重试',
        timestamp: new Date()
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleUpload = () => {
    addNotification({
      id: Math.random().toString(36).substr(2, 9),
      type: 'info',
      title: '上传功能',
      message: '文件上传功能即将开放',
      timestamp: new Date()
    });
  };

  const handleExport = () => {
    addNotification({
      id: Math.random().toString(36).substr(2, 9),
      type: 'success',
      title: '导出成功',
      message: 'BOM数据已导出到下载文件夹',
      timestamp: new Date()
    });
  };

  return (
    <PageTransition variant="slide">
      <ResponsiveContainer
        maxWidth={{ xs: '100%', sm: '100%', md: '100%', lg: 1200, xl: 1400, '2xl': 1600 }}
        padding={{ xs: 16, sm: 20, md: 24, lg: 32, xl: 40 }}
      >
        <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="text-3xl font-bold text-white mb-2">BOM系统控制台</h1>
        <p className="text-gray-400">实时监控模块平面数据处理和物料计算状态</p>
      </motion.div>

      {/* 统计卡片 */}
      <ResponsiveGrid
        columns={{ xs: 1, sm: 2, md: 2, lg: 4, xl: 4 }}
        gap={{ xs: 16, sm: 20, md: 24, lg: 24, xl: 24 }}
        minItemWidth={250}
        animate={true}
      >
        {statsData.map((stat, index) => (
          <Card
            key={stat.title}
            variant="neon"
            title={stat.title}
            subtitle={`${stat.value} ${stat.unit}`}
            className="h-full"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg bg-${stat.color.replace('neon-', '')}-500/20`}>
                  {stat.icon}
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.unit}</div>
                </div>
              </div>
              <div className={`text-${stat.trend === 'up' ? 'green' : 'red'}-400 text-sm font-medium`}>
                {stat.change}
              </div>
            </div>
          </Card>
        ))}
      </ResponsiveGrid>

      {/* 主要功能区域 */}
      <ResponsiveGrid
        columns={{ xs: 1, sm: 1, md: 2, lg: 3, xl: 3 }}
        gap={{ xs: 20, sm: 24, md: 24, lg: 24, xl: 24 }}
        minItemWidth={300}
        animate={true}
      >
        {/* 快速操作 */}
        <QuickActions />

        {/* 模块可视化 */}
        <ContourVisualization mode="3d" showGrid={true} showMeasurements={true} />

        {/* 最近活动 */}
        <RecentActivity />
      </ResponsiveGrid>

      {/* 实时数据监控 */}
      <motion.div
        className="glass-effect rounded-xl p-6 border border-white/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">实时处理状态</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-400">实时更新</span>
          </div>
        </div>
        
        <ResponsiveGrid
          columns={{ xs: 1, sm: 2, md: 3, lg: 3, xl: 3 }}
          gap={{ xs: 16, sm: 16, md: 16, lg: 16, xl: 16 }}
          minItemWidth={200}
          animate={true}
        >
          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-300">队列中</span>
              <span className="text-blue-400 font-bold">3</span>
            </div>
            <ProgressBar 
              value={30} 
              variant="default" 
              size="sm" 
              showPercentage={false}
            />
          </Card>
          
          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-300">处理中</span>
              <span className="text-cyan-400 font-bold">2</span>
            </div>
            <ProgressBar 
              value={65} 
              variant="neon" 
              size="sm" 
              showPercentage={false}
              animated={true}
            />
          </Card>
          
          <Card variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-300">已完成</span>
              <span className="text-green-400 font-bold">18</span>
            </div>
            <ProgressBar 
              value={90} 
              variant="gradient" 
              size="sm" 
              showPercentage={false}
            />
          </Card>
        </ResponsiveGrid>
      </motion.div>

      {/* 悬浮动作按钮 */}
      <FloatingActionButton
        actions={[
          {
            icon: <Upload />,
            label: "上传文件",
            onClick: handleUpload
          },
          {
            icon: <Download />,
            label: "导出BOM",
            onClick: handleExport
          },
          {
            icon: refreshing ? <RefreshCw className="animate-spin" /> : <RefreshCw />,
            label: "刷新数据",
            onClick: handleRefresh,
            disabled: refreshing
          },
          {
            icon: <Settings />,
            label: "设置",
            onClick: () => console.log("设置")
          }
        ]}
        position="bottom-right"
        size="md"
      />
        </div>
      </ResponsiveContainer>
    </PageTransition>
  );
};

export default Dashboard;
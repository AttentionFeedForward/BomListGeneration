import React from 'react';
import { motion } from 'framer-motion';
import { Clock, FileText, Upload, Download, Eye, Calculator, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { Card } from '../UI';

interface ActivityItem {
  id: string;
  type: 'upload' | 'contour' | 'material' | 'bom' | 'export';
  title: string;
  description: string;
  timestamp: number;
  status: 'success' | 'warning' | 'error' | 'processing';
  metadata?: {
    fileName?: string;
    fileSize?: number;
    processingTime?: number;
    accuracy?: number;
  };
}

const RecentActivity: React.FC = () => {
  // 模拟活动数据
  const activities: ActivityItem[] = [
    {
      id: '1',
      type: 'upload',
      title: '文件上传完成',
      description: '建筑图纸.dwg 已成功上传',
      timestamp: Date.now() - 300000, // 5分钟前
      status: 'success',
      metadata: { fileName: '建筑图纸.dwg', fileSize: 2048000 }
    },
    {
      id: '2',
      type: 'contour',
      title: '模块识别完成',
      description: '识别出 12 个模块平面',
      timestamp: Date.now() - 600000, // 10分钟前
      status: 'success',
      metadata: { processingTime: 45, accuracy: 94.2 }
    },
    {
      id: '3',
      type: 'material',
      title: '物料计算中',
      description: '正在计算石膏板用量',
      timestamp: Date.now() - 900000, // 15分钟前
      status: 'processing'
    },
    {
      id: '4',
      type: 'bom',
      title: 'BOM生成完成',
      description: '材料清单已生成，包含 45 种材料',
      timestamp: Date.now() - 1200000, // 20分钟前
      status: 'success'
    },
    {
      id: '5',
      type: 'export',
      title: '导出失败',
      description: '网络连接超时，请重试',
      timestamp: Date.now() - 1500000, // 25分钟前
      status: 'error'
    }
  ];

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'upload':
        return <FileText className="w-4 h-4" />;
      case 'contour':
        return <Eye className="w-4 h-4" />;
      case 'material':
        return <Calculator className="w-4 h-4" />;
      case 'bom':
        return <FileText className="w-4 h-4" />;
      case 'export':
        return <FileText className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getActivityGradient = (type: ActivityItem['type']) => {
    switch (type) {
      case 'upload':
        return 'from-blue-500 to-cyan-500';
      case 'contour':
        return 'from-cyan-500 to-teal-500';
      case 'material':
        return 'from-green-500 to-emerald-500';
      case 'bom':
        return 'from-purple-500 to-pink-500';
      case 'export':
        return 'from-red-500 to-orange-500';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getActivityColor = (status: ActivityItem['status']) => {
    switch (status) {
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      case 'processing':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: ActivityItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4" />;
      case 'error':
        return <XCircle className="w-4 h-4" />;
      case 'processing':
        return <Clock className="w-4 h-4 animate-spin" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  };

  return (
    <div className="glass-effect rounded-xl p-6 border border-white/20 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">最近活动</h3>
        <Clock className="w-5 h-5 text-gray-400" />
      </div>
      
      <div className="space-y-3 overflow-y-auto h-[calc(100%-4rem)] pb-2">
        {activities.map((activity, index) => (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className="flex items-start space-x-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group"
          >
            <div className={`p-2 rounded-lg bg-gradient-to-r ${getActivityGradient(activity.type)}`}>
              {getActivityIcon(activity.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-white truncate group-hover:text-neon-cyan transition-colors">
                  {activity.title}
                </h4>
                <div className="flex items-center space-x-2">
                  <div className={getActivityColor(activity.status)}>
                    {getStatusIcon(activity.status)}
                  </div>
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(activity.timestamp)}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {activity.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
  );
};

export default RecentActivity;
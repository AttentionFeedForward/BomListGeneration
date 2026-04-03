import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string;
  unit: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  unit,
  change,
  trend,
  icon,
  color
}) => {
  const colorClasses = {
    'neon-green': 'border-neon-green/30 text-neon-green',
    'neon-cyan': 'border-neon-cyan/30 text-neon-cyan',
    'neon-blue': 'border-neon-blue/30 text-neon-blue',
    'neon-purple': 'border-neon-purple/30 text-neon-purple',
    'neon-orange': 'border-neon-orange/30 text-neon-orange',
  };

  return (
    <motion.div
      className={`glass-effect rounded-xl p-6 border ${colorClasses[color as keyof typeof colorClasses] || 'border-white/20'} 
                  hover:shadow-lg transition-all duration-300 group cursor-pointer`}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-400 text-sm font-medium mb-1">{title}</p>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white">{value}</span>
            <span className="text-sm text-gray-400">{unit}</span>
          </div>
        </div>
        
        <div className={`p-3 rounded-lg bg-glass-blue border ${colorClasses[color as keyof typeof colorClasses] || 'border-white/20'} 
                        group-hover:scale-110 transition-transform duration-300`}>
          <div className={colorClasses[color as keyof typeof colorClasses] || 'text-white'}>
            {icon}
          </div>
        </div>
      </div>

      <div className="flex items-center mt-4 space-x-2">
        <div className={`flex items-center space-x-1 ${
          trend === 'up' ? 'text-neon-green' : 'text-neon-red'
        }`}>
          {trend === 'up' ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">{change}</span>
        </div>
        <span className="text-gray-400 text-sm">较昨日</span>
      </div>

      {/* 数据流线装饰 */}
      <div className="mt-4 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-30"></div>
    </motion.div>
  );
};

export default StatsCard;
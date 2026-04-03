import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Maximize2, RotateCw, ZoomIn, ZoomOut } from 'lucide-react';

const ContourPreview: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    canvas.width = 300;
    canvas.height = 200;

    // 绘制示例轮廓
    const drawContour = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // 设置样式
      ctx.strokeStyle = '#00F5FF';
      ctx.lineWidth = 2;
      ctx.shadowBlur = 10;
      ctx.shadowColor = '#00F5FF';

      // 绘制建筑轮廓
      ctx.beginPath();
      ctx.moveTo(50, 50);
      ctx.lineTo(250, 50);
      ctx.lineTo(250, 100);
      ctx.lineTo(200, 100);
      ctx.lineTo(200, 150);
      ctx.lineTo(100, 150);
      ctx.lineTo(100, 100);
      ctx.lineTo(50, 100);
      ctx.closePath();
      ctx.stroke();

      // 绘制关键点
      const points = [
        [50, 50], [250, 50], [250, 100], [200, 100],
        [200, 150], [100, 150], [100, 100], [50, 100]
      ];

      points.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#00F5FF';
        ctx.fill();
      });

      // 绘制尺寸标注
      ctx.strokeStyle = '#FF8C00';
      ctx.lineWidth = 1;
      ctx.font = '12px Inter';
      ctx.fillStyle = '#FF8C00';
      
      // 水平尺寸
      ctx.beginPath();
      ctx.moveTo(50, 30);
      ctx.lineTo(250, 30);
      ctx.stroke();
      ctx.fillText('200m', 140, 25);

      // 垂直尺寸
      ctx.beginPath();
      ctx.moveTo(270, 50);
      ctx.lineTo(270, 150);
      ctx.stroke();
      ctx.fillText('100m', 275, 105);
    };

    drawContour();
  }, []);

  return (
    <div className="glass-effect rounded-xl p-6 border border-white/20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">轮廓预览</h3>
        <div className="flex items-center space-x-2">
          <motion.button
            className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <ZoomIn className="w-4 h-4 text-gray-300" />
          </motion.button>
          <motion.button
            className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <ZoomOut className="w-4 h-4 text-gray-300" />
          </motion.button>
          <motion.button
            className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
            whileHover={{ scale: 1.1, rotate: 90 }}
            whileTap={{ scale: 0.95 }}
          >
            <RotateCw className="w-4 h-4 text-gray-300" />
          </motion.button>
          <motion.button
            className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Maximize2 className="w-4 h-4 text-gray-300" />
          </motion.button>
        </div>
      </div>

      {/* 3D预览区域 */}
      <div className="relative bg-space-dark rounded-lg border border-neon-cyan/30 overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full h-auto"
          style={{ background: 'transparent' }}
        />
        
        {/* 扫描线效果 */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-full h-0.5 bg-neon-cyan opacity-50 
                         animate-pulse"></div>
        </div>
      </div>

      {/* 轮廓信息 */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="p-3 rounded-lg bg-glass-blue border border-neon-blue/30">
          <div className="text-sm text-gray-400">面积</div>
          <div className="text-lg font-bold text-neon-blue">2,400 m²</div>
        </div>
        <div className="p-3 rounded-lg bg-glass-blue border border-neon-cyan/30">
          <div className="text-sm text-gray-400">周长</div>
          <div className="text-lg font-bold text-neon-cyan">220 m</div>
        </div>
      </div>

      {/* 处理状态 */}
      <div className="mt-4 p-3 rounded-lg bg-glass-blue border border-neon-green/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">识别完成</span>
          </div>
          <span className="text-sm text-neon-green font-medium">100%</span>
        </div>
        <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
          <motion.div 
            className="bg-neon-green h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 2, ease: "easeOut" }}
          ></motion.div>
        </div>
      </div>
    </div>
  );
};

export default ContourPreview;
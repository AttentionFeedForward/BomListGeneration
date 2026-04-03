import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Upload, 
  FileImage, 
  Scan, 
  CheckCircle, 
  AlertCircle,
  RotateCw,
  ArrowRight
} from 'lucide-react';

import ContourVisualization from '../Contour/ContourVisualization';
import bomService, { ModuleIdentificationResult, ContourProcessResult } from '../../services/bomService';
import { useNavigation } from '../../App';
import { useActions, useApp, useModuleData } from '../../store';

interface ProcessingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
}

const ContourProcessing: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [identificationResult, setIdentificationResult] = useState<ModuleIdentificationResult | null>(null);
  const [modelHeight, setModelHeight] = useState<number>(2950); // 默认2950mm高度
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const hasAutoClickedRef = useRef(false);
  
  // 获取导航和全局状态管理
  const { navigateTo } = useNavigation();
  const { setModuleData, clearUploadPrompt } = useActions();
  const moduleData = useModuleData();
  const app = useApp();

  // Initialize from store if available
  useEffect(() => {
    if (moduleData.identificationResult && !identificationResult) {
      setIdentificationResult(moduleData.identificationResult.identificationResult);
      if (moduleData.identificationResult.height) {
        setModelHeight(moduleData.identificationResult.height);
      }
      setCurrentStep(5);
    }
  }, []);

  // Sync to store when result changes
  useEffect(() => {
    if (identificationResult) {
      // Calculate derived data
      // Data sync logic handled in handleTransitionConfirm for final submission
      // But we can also sync intermediate state if needed. 
      // For now, we rely on the button to commit to store.
    }
  }, [identificationResult]);

  // 若从仪表盘点击“上传数据”，则自动弹出文件选择框（一次性）
  useEffect(() => {
    if (app.ui?.triggerUpload && !hasAutoClickedRef.current) {
      hasAutoClickedRef.current = true;
      // 触发文件选择（一次性）
      fileInputRef.current?.click();
      // 清理触发标记，确保只弹一次
      clearUploadPrompt();
    }
  }, [app.ui?.triggerUpload, clearUploadPrompt]);

  const processingSteps: ProcessingStep[] = [
    {
      id: 'upload',
      title: '图像上传',
      description: '上传建筑平面图或CAD文件',
      status: uploadedFile ? 'completed' : 'pending',
      progress: uploadedFile ? 100 : 0
    },
    {
      id: 'preprocessing',
      title: '图像预处理',
      description: '图像增强、噪声去除、边缘检测',
      status: 'pending',
      progress: 0
    },
    {
      id: 'contour-detection',
      title: '图像识别',
      description: 'AI算法识别模块轮廓边界、尺寸标注',
      status: 'pending',
      progress: 0
    },
    {
      id: 'dimension-matching',
      title: '尺寸匹配',
      description: '尺寸与轮廓匹配，计算真实值',
      status: 'pending',
      progress: 0
    },
    {
      id: 'validation',
      title: '结果验证',
      description: '精准检查、过滤异常值',
      status: 'pending',
      progress: 0
    }
  ];

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setError(null);
      setIdentificationResult(null);
      localStorage.removeItem('module_recognition_result'); // Clear saved data
      // 开始实际的模块识别处理
      setTimeout(() => {
        processModuleIdentification(file);
      }, 1000);
    }
  };

  const processModuleIdentification = async (file: File) => {
    try {
      setIsProcessing(true);
      setCurrentStep(1);

      // 步骤1: 图像预处理
      await new Promise(resolve => setTimeout(resolve, 1000));
      setCurrentStep(2);

      // 步骤2: 轮廓识别 - 调用后端API
      const response = await bomService.processContour({
        image: file,
        confidence_threshold: 0.5,
        debug: true
      });

      if (response.success) {
        setIdentificationResult(response.data);
        setCurrentStep(3);

        await new Promise(resolve => setTimeout(resolve, 1000));
        setCurrentStep(4);

        await new Promise(resolve => setTimeout(resolve, 1000));
        setCurrentStep(5);

        setIsProcessing(false);
      } else {
        throw new Error('模块识别失败');
      }
    } catch (err: any) {
      console.error('模块识别错误:', err);
      setError(err.message || '模块识别过程中发生错误');
      setIsProcessing(false);
      setCurrentStep(0);
    }
  };

  const handleTransitionConfirm = () => {
    if (identificationResult && identificationResult.contour_info) {
      // 从轮廓结果中获取面积和周长数据（原始单位：mm² 和 mm）
      const moduleAreaMm2 = identificationResult.contour_info.summary.total_area; // 模块面积 (mm²)
      const modulePerimeterMm = identificationResult.contour_info.summary.total_perimeter; // 模块周长 (mm)
      const moduleHeightMm = modelHeight; // 模块高度 (mm)
      const verticesCount = identificationResult.contour_info.contours
        ? identificationResult.contour_info.contours.reduce((sum, c) => sum + (c.geometry?.num_points || 0), 0)
        : 0;
      
      // 单位换算：mm² -> m²，mm -> m
      const moduleAreaM2 = parseFloat((moduleAreaMm2 / 1_000_000).toFixed(2)); // 转换为m²并保留2位小数
      const modulePerimeterM = modulePerimeterMm / 1000; // 转换为m
      const moduleHeightM = moduleHeightMm / 1000; // 转换为m
      const moduleVolumeM3 = parseFloat((moduleAreaM2 * moduleHeightM).toFixed(3));
      
      // 计算各个面积（单位：m²）
      const floorArea = moduleAreaM2; // 地面面积 = 模块面积
      const ceilingArea = moduleAreaM2; // 天花面积 = 模块面积  
      const wallArea = parseFloat((modulePerimeterM * moduleHeightM).toFixed(2)); // 墙体面积 = 周长(m) × 高度(m)，保留2位小数
      
      // 保存识别结果到全局状态
      setModuleData({
        identificationResult: identificationResult,
        height: moduleHeightMm, // 高度（mm）
        floor_area: floorArea, // 地面面积（m²）
        wall_area: wallArea, // 墙体面积（m²）
        ceiling_area: ceilingArea, // 天花板面积（m²）
        timestamp: new Date().toISOString(),
        processing_time: identificationResult.summary?.processing_time || 0,
        vertices_count: verticesCount,
        perimeter: modulePerimeterM, // m
        module_area: moduleAreaM2, // m²
        module_volume: moduleVolumeM3, // m³
      });
      
      // 跳转到材料计算页面
      navigateTo('material-calculation');
    }
  };

  const getStepIcon = (step: ProcessingStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-neon-green" />;
      case 'processing':
        return <RotateCw className="w-5 h-5 text-neon-blue animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-500" />;
    }
  };

  const getStepStatus = (index: number): ProcessingStep['status'] => {
    if (index === 0 && uploadedFile) return 'completed';
    if (index === currentStep && isProcessing) return 'processing';
    if (index < currentStep) return 'completed';
    return 'pending';
  };

  return (
    <div className="p-6 h-full flex flex-col overflow-hidden">
      {/* 页面标题 */}
      <h1 className="text-3xl font-bold text-white mb-6 flex items-center flex-shrink-0">
          <Scan className="mr-3" /> 模块识别
      </h1>

      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        {/* 左侧：上传和处理流程 */}
        <div className="lg:w-1/3 flex flex-col gap-6 h-full overflow-y-auto pr-2">
          {/* 文件上传区域 */}
          <motion.div
            className="glass-effect rounded-xl p-6 border border-white/20"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <h3 className="text-xl font-semibold text-white mb-4">文件上传</h3>
            
            <div className="relative">
              <input
                type="file"
                accept="image/*,.dwg,.dxf"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                ref={fileInputRef}
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center w-full h-32 
                         border-2 border-dashed border-neon-cyan/50 rounded-lg 
                         hover:border-neon-cyan transition-all duration-300 cursor-pointer
                         bg-glass-blue"
              >
                <Upload className="w-8 h-8 text-neon-cyan mb-2" />
                <span className="text-gray-300 text-sm text-center">
                  {uploadedFile ? uploadedFile.name : '点击上传图片或CAD文件'}
                </span>
                <span className="text-gray-500 text-xs mt-1">
                  支持 JPG, PNG, DWG, DXF 格式
                </span>
              </label>
            </div>

            {uploadedFile && (
              <motion.div
                className="mt-4 p-3 bg-glass-blue rounded-lg border border-neon-green/30"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex items-center space-x-3">
                  <FileImage className="w-5 h-5 text-neon-green" />
                  <div className="flex-1">
                    <div className="text-sm text-white font-medium">
                      {uploadedFile.name}
                    </div>
                    <div className="text-xs text-gray-400">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                  <CheckCircle className="w-5 h-5 text-neon-green" />
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div
                className="mt-4 p-3 bg-red-900/30 rounded-lg border border-red-500/30"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  <div className="flex-1">
                    <div className="text-sm text-red-400 font-medium">
                      处理错误
                    </div>
                    <div className="text-xs text-red-300">
                      {error}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>

          {/* 处理流程 */}
          <motion.div
            className="glass-effect rounded-xl p-6 border border-white/20 flex-grow"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h3 className="text-xl font-semibold text-white mb-4">处理流程</h3>
            
            <div className="space-y-4">
              {processingSteps.map((step, index) => {
                const status = getStepStatus(index);
                const progress = status === 'processing' ? 75 : status === 'completed' ? 100 : 0;
                
                return (
                  <motion.div
                    key={step.id}
                    className={`p-4 rounded-lg border transition-all duration-300 ${
                      status === 'completed' 
                        ? 'bg-glass-blue border-neon-green/30' 
                        : status === 'processing'
                        ? 'bg-glass-blue border-neon-blue/30'
                        : 'bg-gray-800/50 border-gray-600/30'
                    }`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <div className="flex items-center space-x-3 mb-2">
                      {getStepIcon({ ...step, status, progress })}
                      <div className="flex-1">
                        <div className="text-sm font-medium text-white">
                          {step.title}
                        </div>
                        <div className="text-xs text-gray-400">
                          {step.description}
                        </div>
                      </div>
                      <div className="text-xs text-gray-400">
                        {progress}%
                      </div>
                    </div>
                    
                    {/* 进度条 */}
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <motion.div
                        className={`h-2 rounded-full ${
                          status === 'completed' 
                            ? 'bg-neon-green' 
                            : status === 'processing'
                            ? 'bg-neon-blue'
                            : 'bg-gray-600'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </div>

        {/* 右侧：可视化区域 */}
        <div className="lg:w-2/3">
          <motion.div
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6 h-full flex flex-col"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Scan className="w-5 h-5 text-blue-400" />
                轮廓可视化与3D模型
              </h3>
              {/* 数据传输按钮 */}
              {identificationResult && (
                <button
                  onClick={handleTransitionConfirm}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors duration-200"
                >
                  <ArrowRight className="w-4 h-4" />
                  数据传输
                </button>
              )}
            </div>
            <div className="flex-grow bg-gray-900/50 rounded-lg border border-gray-600">
              <ContourVisualization 
                contourInfo={identificationResult?.contour_info}
                modelHeight={modelHeight}
                mode="3d"
                enable3DGeneration={true}
                onHeightChange={setModelHeight}
              />
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ContourProcessing;
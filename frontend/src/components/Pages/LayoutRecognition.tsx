import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileImage, Play, RefreshCw, AlertCircle, CheckCircle, Search, Layout, Plus, Trash2, Edit2, Save, X, ArrowRight } from 'lucide-react';
import api from '../../services/api';
import { useNavigation } from '../../App';
import { useActions, useLayoutData } from '../../store';

interface RoomData {
  room_id: string;
  pixel_area: number;
  total_perimeter_pixels: number;
  precise_wall_length_pixels: number;
  area_mm2?: number;
  area_m2?: number;
  perimeter_mm?: number;
  wall_length_mm?: number;
}

interface AnalysisResult {
  total_wall_length_pixels: number;
  total_wall_length_mm?: number;
  rooms: RoomData[];
  image_width: number;
  image_height: number;
  images: {
    original: string;
    segmentation: string;
  };
  scale_info?: any;
}

const LayoutRecognition: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { navigateTo } = useNavigation();

  const { setLayoutData } = useActions();
  const layoutData = useLayoutData();

  // Initialize from store if available (preserves state during navigation, resets on refresh)
  useEffect(() => {
    if (layoutData.result && !result) {
      setResult(layoutData.result);
    }
  }, []);

  // Sync to store when result changes
  useEffect(() => {
    if (result) {
      setLayoutData(result);
    }
  }, [result]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0];
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      // Only clear result if user explicitly uploads a new file and wants to re-process
      // But typically, selecting a new file implies starting over.
      // However, per requirement "only when user re-uploads", selecting file is the first step of upload.
      // We will clear result when 'Start Recognition' is clicked or we can keep it until then.
      // Let's clear it to show the new preview properly.
      setResult(null); 
      setError(null);
      // Clear storage
      localStorage.removeItem('layout_recognition_result');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
        const selectedFile = event.dataTransfer.files[0];
        setFile(selectedFile);
        setPreviewUrl(URL.createObjectURL(selectedFile));
        setResult(null);
        setError(null);
        localStorage.removeItem('layout_recognition_result');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const startRecognition = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response: any = await api.post('/layout/recognize', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.status === 'success' || response.success) {
          setResult(response.data);
      } else {
          setError(response.message || 'Unknown error');
      }

    } catch (err: any) {
      setError(err.message || '识别失败');
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const getImageUrl = (url: string) => {
      if (url.startsWith('http')) return url;
      return `http://localhost:5000${url}`;
  };

  // Editable Table Logic
  const handleRoomChange = (index: number, field: keyof RoomData, value: string) => {
    if (!result) return;
    const newRooms = [...result.rooms];
    
    if (field === 'room_id') {
        newRooms[index] = { ...newRooms[index], [field]: value };
    } else {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
             newRooms[index] = { ...newRooms[index], [field]: numValue };
             // Auto-update related mm/pixel if needed? 
             // For simplicity, we just update the displayed value (which is likely m2 or mm)
             // But our state has area_m2, perimeter_mm, etc.
             // If user edits "Area (m2)", we should update area_m2.
             // The table displays area_m2, perimeter_mm/1000 (m), wall_length_mm/1000 (m).
             
             // Wait, the state structure stores area_m2 directly.
        }
    }
    setResult({ ...result, rooms: newRooms });
  };

  // Specifically for inputs that map to displayed values
  const updateRoomValue = (index: number, type: 'area' | 'perimeter' | 'wall', value: string) => {
      if (!result) return;
      const newRooms = [...result.rooms];
      const numVal = parseFloat(value);
      
      if (type === 'area') {
          // Input is m2
          newRooms[index].area_m2 = isNaN(numVal) ? 0 : numVal;
      } else if (type === 'perimeter') {
          // Input is m, store as mm
          newRooms[index].perimeter_mm = isNaN(numVal) ? 0 : numVal * 1000;
      } else if (type === 'wall') {
          // Input is m, store as mm
          newRooms[index].wall_length_mm = isNaN(numVal) ? 0 : numVal * 1000;
      }
      
      setResult({ ...result, rooms: newRooms });
  };

  const addRow = () => {
      if (!result) return;
      const newRoom: RoomData = {
          room_id: `New-${result.rooms.length + 1}`,
          pixel_area: 0,
          total_perimeter_pixels: 0,
          precise_wall_length_pixels: 0,
          area_m2: 0,
          perimeter_mm: 0,
          wall_length_mm: 0
      };
      setResult({ ...result, rooms: [...result.rooms, newRoom] });
  };

  const deleteRow = (index: number) => {
      if (!result) return;
      const newRooms = result.rooms.filter((_, i) => i !== index);
      setResult({ ...result, rooms: newRooms });
  };

  // Calculate totals
  const totalArea = result?.rooms.reduce((acc, r) => acc + (r.area_m2 || 0), 0) || 0;
  const totalPerimeter = result?.rooms.reduce((acc, r) => acc + (r.perimeter_mm || 0), 0) || 0;
  
  // Total wall length is the global value from analysis, not the sum of rooms
  const updateGlobalWallLength = (value: string) => {
      if (!result) return;
      const numVal = parseFloat(value);
      const newVal = isNaN(numVal) ? 0 : numVal * 1000;
      setResult({ ...result, total_wall_length_mm: newVal });
  };
  
  const handleProceedToCalculation = () => {
      // Data is already synced to store via useEffect
      navigateTo('material-calculation');
  };


  return (
    <div className="p-6 h-full overflow-y-auto">
        <h1 className="text-3xl font-bold text-white mb-6 flex items-center">
            <Layout className="mr-3" /> 户型图识别
        </h1>
        
        {/* Main Grid */}
        <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)]">
            
            {/* Left: Upload & Preview */}
            <div className="flex-1 flex flex-col min-h-[400px]">
                <div 
                    className={`flex-1 glass-effect rounded-xl p-8 border-2 border-dashed transition-all flex flex-col relative
                        ${file ? 'border-blue-500/50 bg-blue-500/10' : 'border-gray-500/30 hover:border-blue-400/50 hover:bg-white/5'}
                    `}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                >
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        onChange={handleFileChange} 
                        className="hidden" 
                        accept="image/*"
                    />
                    
                    {!file && !result ? (
                        <div className="flex-1 flex flex-col items-center justify-center cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                            <Upload className="w-16 h-16 text-gray-400 mb-4" />
                            <p className="text-lg text-white font-medium">点击或拖拽上传户型图</p>
                            <p className="text-sm text-gray-400 mt-2">支持 JPG, PNG, BMP, GIF</p>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col relative h-full">
                            <div className="flex-1 relative min-h-0 bg-black/40 rounded-lg overflow-hidden flex items-center justify-center">
                                <img 
                                    src={result ? getImageUrl(result.images.segmentation) : previewUrl!} 
                                    alt="Preview" 
                                    className="max-w-full max-h-full object-contain" 
                                />
                            </div>
                            
                            {/* Controls Overlay or Bottom Bar */}
                            <div className="mt-4 flex justify-between items-center bg-black/20 p-3 rounded-lg backdrop-blur-sm">
                                <span className="text-sm text-gray-300 flex items-center truncate max-w-[200px]">
                                    <FileImage className="w-4 h-4 mr-2 flex-shrink-0" />
                                    {file ? file.name : 'Current Result'}
                                </span>
                                <div className="flex space-x-3">
                                    <button 
                                        onClick={() => fileInputRef.current?.click()}
                                        className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                                        title="重新上传"
                                    >
                                        <Upload className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={startRecognition}
                                        disabled={!file || isProcessing}
                                        className={`px-4 py-2 rounded-lg font-medium flex items-center transition-all text-sm
                                            ${!file || isProcessing 
                                                ? 'bg-gray-600 cursor-not-allowed' 
                                                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg'}
                                        `}
                                    >
                                        {isProcessing ? (
                                            <>
                                                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                                处理中...
                                            </>
                                        ) : (
                                            <>
                                                <Play className="w-4 h-4 mr-2" />
                                                开始识别
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Error Message */}
                <AnimatePresence>
                    {error && (
                        <motion.div 
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="mt-4 bg-red-500/20 border border-red-500/50 rounded-lg p-4 flex items-center text-red-200"
                        >
                            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
                            {error}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Right: Results */}
            <div className="flex-1 flex flex-col min-h-[400px]">
                {result ? (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex-1 glass-effect rounded-xl p-6 border border-white/10 flex flex-col"
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-white flex items-center">
                                <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                                识别结果
                            </h2>
                            <div className="flex gap-2">
                                <button 
                                    onClick={addRow}
                                    className="flex items-center px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm transition-colors border border-blue-500/30"
                                >
                                    <Plus className="w-4 h-4 mr-1" />
                                    新增房间
                                </button>
                                <button 
                                    onClick={handleProceedToCalculation}
                                    className="flex items-center px-4 py-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg text-sm transition-all shadow-lg font-medium"
                                >
                                    前往物料计算
                                    <ArrowRight className="w-4 h-4 ml-1" />
                                </button>
                            </div>
                        </div>
                        
                        {/* Metrics Table */}
                        <div className="flex-1 overflow-auto rounded-lg border border-white/10 bg-black/20">
                            <table className="w-full text-left border-collapse">
                                <thead className="sticky top-0 bg-[#1a1f2e] z-10">
                                    <tr className="border-b border-white/10 text-gray-400 text-sm">
                                        <th className="py-3 px-4">房间</th>
                                        <th className="py-3 px-4">面积 (m²)</th>
                                        <th className="py-3 px-4">周长 (m)</th>
                                        <th className="py-3 px-4">墙长 (m)</th>
                                        <th className="py-3 px-4 w-16">操作</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {result.rooms.map((room, index) => (
                                        <tr key={index} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                                            <td className="py-2 px-4">
                                                <input 
                                                    type="text" 
                                                    value={room.room_id}
                                                    onChange={(e) => handleRoomChange(index, 'room_id', e.target.value)}
                                                    className="bg-transparent border border-transparent hover:border-white/20 focus:border-blue-500 rounded px-2 py-1 w-full text-white outline-none transition-colors"
                                                />
                                            </td>
                                            <td className="py-2 px-4">
                                                <input 
                                                    type="number" 
                                                    step="0.01"
                                                    value={room.area_m2?.toFixed(2) || ''}
                                                    onChange={(e) => updateRoomValue(index, 'area', e.target.value)}
                                                    className="bg-transparent border border-transparent hover:border-white/20 focus:border-blue-500 rounded px-2 py-1 w-full text-gray-300 outline-none transition-colors"
                                                />
                                            </td>
                                            <td className="py-2 px-4">
                                                <input 
                                                    type="number"
                                                    step="0.01"
                                                    value={room.perimeter_mm ? (room.perimeter_mm / 1000).toFixed(2) : ''}
                                                    onChange={(e) => updateRoomValue(index, 'perimeter', e.target.value)}
                                                    className="bg-transparent border border-transparent hover:border-white/20 focus:border-blue-500 rounded px-2 py-1 w-full text-gray-300 outline-none transition-colors"
                                                />
                                            </td>
                                            <td className="py-2 px-4">
                                                <input 
                                                    type="number"
                                                    step="0.01"
                                                    value={room.wall_length_mm ? (room.wall_length_mm / 1000).toFixed(2) : ''}
                                                    onChange={(e) => updateRoomValue(index, 'wall', e.target.value)}
                                                    className="bg-transparent border border-transparent hover:border-white/20 focus:border-blue-500 rounded px-2 py-1 w-full text-gray-300 outline-none transition-colors"
                                                />
                                            </td>
                                            <td className="py-2 px-4 text-center">
                                                <button 
                                                    onClick={() => deleteRow(index)}
                                                    className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot className="bg-white/5 font-medium sticky bottom-0">
                                    <tr className="bg-white/5 font-medium sticky bottom-0">
                                        <td className="py-3 px-4 text-blue-300">总计</td>
                                        <td className="py-3 px-4 text-blue-300">
                                            {totalArea.toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-blue-300">
                                            {(totalPerimeter / 1000).toFixed(2)}
                                        </td>
                                        <td className="py-3 px-4 text-blue-300">
                                            <input 
                                                type="number"
                                                step="0.01"
                                                value={result.total_wall_length_mm ? (result.total_wall_length_mm / 1000).toFixed(2) : ''}
                                                onChange={(e) => updateGlobalWallLength(e.target.value)}
                                                className="bg-transparent border border-transparent hover:border-white/20 focus:border-blue-500 rounded px-2 py-1 w-full text-blue-300 outline-none transition-colors font-medium"
                                            />
                                        </td>
                                        <td></td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>

                    </motion.div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 min-h-[300px] glass-effect rounded-xl border border-white/5">
                        <Search className="w-12 h-12 mb-4 opacity-50" />
                        <p>上传图片并点击“开始识别”查看结果</p>
                    </div>
                )}
            </div>
        </div>
    </div>
  );
};

export default LayoutRecognition;
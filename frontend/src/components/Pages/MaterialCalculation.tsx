import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Clock, X, Grid, Layout, AlertTriangle, ArrowRight, Settings, Calculator } from 'lucide-react';
import constructionData from '../../data/constructionPractices.json';
import { bomService } from '../../services/bomService';
import { useModuleData, useActions, useLayoutData } from '../../store';
import { useNavigation } from '../../App';

// Define a type for the selections
type Selections = {
  [key: string]: string;
};

// Define a type for module data
  type ModuleData = {
    height: string;
    floorArea: string;
    wallArea: string;
    ceilingArea: string;
    // 新增可编辑指标
    vertices: string;
    perimeter: string;
    moduleArea: string;
    moduleVolume: string;
    roomType?: string; // Room type for MEP calculation
  };

// Define a type for BOM material item
type BOMItem = {
  name: string;
  specification: string;
  quantity: number;
  unit: string;
  category: string;
  layer_type: string;
  notes?: string;
  material_code?: string;
  calculation_formula?: string;
  usage?: string;
};

// Define a type for BOM result
type BOMResult = {
  materials: BOMItem[];
  summary: {
    total_items: number;
    categories: string[];
  };
  processing_info: {
    timestamp: string;
    processing_time: number;
  };
};

// Types for Layout Mode
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
}

type CalculationMode = 'module' | 'layout';

const MaterialCalculation: React.FC = () => {
  const [mode, setMode] = useState<CalculationMode>('module');
  const [constructionPractices, setConstructionPractices] = useState<any>(null);
  
  // Module Mode State
  const [selections, setSelections] = useState<Selections>({});
  const [customValues, setCustomValues] = useState<Selections>({});
  const [moduleData, setModuleData] = useState<ModuleData>({
    height: '',
    floorArea: '',
    wallArea: '',
    ceilingArea: '',
    vertices: '',
    perimeter: '',
    moduleArea: '',
    moduleVolume: '',
  });

  // Layout Mode State
  const [layoutResult, setLayoutResult] = useState<AnalysisResult | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [roomSettings, setRoomSettings] = useState<{
    [roomId: string]: {
      height: string;
      selections: Selections;
      customValues: Selections;
      // New editable fields
      perimeter?: string; // Room perimeter
      floorArea?: string; // Floor area
      wallArea?: string; // Wall area
      ceilingArea?: string; // Ceiling area
      wallLength?: string; // Wall length
      roomType?: string; // Room type
    }
  }>({});
  const [globalHeight, setGlobalHeight] = useState<string>('2800'); // Default 2.8m
  const [projectType, setProjectType] = useState<string>('住宅'); // Project Type

  // BOM相关状态
  const [bomResult, setBomResult] = useState<BOMResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingModuleInfo, setIsLoadingModuleInfo] = useState(false);
  const [showViewBOMModal, setShowViewBOMModal] = useState(false);
  const [showBOMGenerateButton, setShowBOMGenerateButton] = useState(false);
  
  // 数据载入提示相关状态
  const [showDataLoadNotification, setShowDataLoadNotification] = useState(false);
  const [loadedDataTimestamp, setLoadedDataTimestamp] = useState<string>('');
  
  // 获取全局模块数据
  const globalModuleData = useModuleData();
  const layoutData = useLayoutData();
  const { setMaterialBom, ackModuleTransfer } = useActions();
  const { navigateTo } = useNavigation();
  
  // Helper to map room ID/name to Chinese room type
  const mapRoomType = (name: string): string => {
      const lower = name.toLowerCase();
      if (lower.includes('living')) return '客厅';
      if (lower.includes('bed')) return '卧室';
      if (lower.includes('kitchen')) return '厨房';
      if (lower.includes('bath') || lower.includes('toilet') || lower.includes('restroom') || lower.includes('wash')) return '卫生间';
      if (lower.includes('balcony')) return '阳台';
      if (lower.includes('corridor') || lower.includes('hall')) return '走廊';
      return '其余';
  };

  // 基本信息区和必填输入框的引用，用于滚动与聚焦
  const moduleInfoRef = useRef<HTMLDivElement | null>(null);
  const perimeterInputRef = useRef<HTMLInputElement | null>(null);
  const heightInputRef = useRef<HTMLInputElement | null>(null);
  const ceilingAreaInputRef = useRef<HTMLInputElement | null>(null);
  const wallAreaInputRef = useRef<HTMLInputElement | null>(null);
  const floorAreaInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setConstructionPractices(constructionData);
    // Initialize selections with the first option for each
    const initialSelections: Selections = {};
    if (constructionData) {
      for (const [category, layers] of Object.entries(constructionData)) {
        for (const [layerType, options] of Object.entries(layers as any)) {
          initialSelections[`${category}-${layerType}`] = (options as string[])[0];
        }
      }
    }
    setSelections(initialSelections);
    
    // Load layout result from STORE (fresh on refresh, persisted via store on navigation)
    if (layoutData.result) {
        setLayoutResult(layoutData.result);
        if (layoutData.result.rooms && layoutData.result.rooms.length > 0) {
            setSelectedRoomId(layoutData.result.rooms[0].room_id);
            // Initialize room settings
            const settings: any = {};
            layoutData.result.rooms.forEach((room: any) => {
                const h = '2800';
                const p = ((room.perimeter_mm || 0) / 1000).toFixed(2);
                const a = room.area_m2?.toFixed(2) || '0.00';
                // Calculate wall area: Wall Length (m) * Height (m)
                // Note: Original code used Wall Length for wall area calculation.
                // Assuming wall_length_mm is available.
                const wl = ((room.wall_length_mm || 0) / 1000).toFixed(2);
                const wa = (parseFloat(wl) * (parseFloat(h) / 1000)).toFixed(2);

                settings[room.room_id] = {
                    height: h, 
                    selections: { ...initialSelections },
                    customValues: {},
                    perimeter: p,
                    floorArea: a,
                    wallArea: wa,
                    ceilingArea: a, // Usually same as floor area
                    wallLength: wl,
                    roomType: mapRoomType(room.room_id)
                };
            });
            setRoomSettings(settings);
            // Switch to layout mode
            setMode('layout');
        }
    }
  }, [layoutData.result]); // Dependency on layoutData.result

  // Update room settings when global height changes
  const handleGlobalHeightChange = (val: string) => {
      setGlobalHeight(val);
      setRoomSettings(prev => {
          const next = { ...prev };
          Object.keys(next).forEach(roomId => {
              next[roomId].height = val;
              // Re-calculate wall area based on new height if wall length is available
              if (next[roomId].wallLength) {
                  const wl = parseFloat(next[roomId].wallLength || '0');
                  const h = parseFloat(val || '0') / 1000;
                  next[roomId].wallArea = (wl * h).toFixed(2);
              }
          });
          return next;
      });
  };

  const handleRoomSettingChange = (roomId: string, field: string, value: string) => {
    setRoomSettings(prev => {
      const next = { ...prev };
      if (!next[roomId]) return prev;
      
      next[roomId] = { ...next[roomId], [field]: value };
      
      // If height changes, update wall area automatically?
      // Or if wall length changes?
      // For now, let's keep it simple. If user manually edits wall area, it stays.
      // But if they change height here (though height is global now?), we might want to update.
      // Wait, user asked for "Module Height" global setting, but also "values in Room Info are editable".
      // So if user edits height in Room Info, does it detach from global? 
      // Let's assume Room Info edits are specific overrides.
      
      if (field === 'height' && next[roomId].wallLength) {
           const wl = parseFloat(next[roomId].wallLength || '0');
           const h = parseFloat(value || '0') / 1000;
           next[roomId].wallArea = (wl * h).toFixed(2);
      }
      
      if (field === 'wallLength') {
           const wl = parseFloat(value || '0');
           const h = parseFloat(next[roomId].height || globalHeight || '0') / 1000;
           next[roomId].wallArea = (wl * h).toFixed(2);
      }
      
      return next;
    });
  };

  // 处理从全局状态加载模块数据
  useEffect(() => {
    if (globalModuleData.identificationResult && 
        globalModuleData.lastProcessedAt && 
        globalModuleData.isTransferredByButton) { // 只有通过按钮传输的数据才显示提示
      // 更新模块数据
      setModuleData({
        height: globalModuleData.identificationResult.height.toString(),
        floorArea: globalModuleData.identificationResult.floor_area.toString(),
        wallArea: globalModuleData.identificationResult.wall_area.toString(),
        ceilingArea: globalModuleData.identificationResult.ceiling_area.toString(),
        vertices: (globalModuleData.identificationResult.vertices_count ?? '').toString(),
        perimeter: globalModuleData.identificationResult.perimeter !== undefined 
          ? Number(globalModuleData.identificationResult.perimeter).toFixed(2)
          : '',
        moduleArea: globalModuleData.identificationResult.module_area !== undefined 
          ? Number(globalModuleData.identificationResult.module_area).toFixed(2)
          : '',
        moduleVolume: globalModuleData.identificationResult.module_volume !== undefined 
          ? Number(globalModuleData.identificationResult.module_volume).toFixed(2)
          : '',
      });
      
      // 格式化时间戳
      const timestamp = new Date(globalModuleData.lastProcessedAt).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      setLoadedDataTimestamp(timestamp);
      setShowDataLoadNotification(true);
      // 立即确认一次性提示，防止返回页面重复显示
      ackModuleTransfer();
      
      // 3秒后自动隐藏提示
      setTimeout(() => {
        setShowDataLoadNotification(false);
      }, 3000);
    }
  }, [globalModuleData]);

  const handleSelectionChange = (category: string, layerType: string, option: string) => {
    if (mode === 'module') {
        setSelections(prev => ({
          ...prev,
          [`${category}-${layerType}`]: option,
        }));
    } else if (selectedRoomId) {
        setRoomSettings(prev => ({
            ...prev,
            [selectedRoomId]: {
                ...prev[selectedRoomId],
                selections: {
                    ...prev[selectedRoomId].selections,
                    [`${category}-${layerType}`]: option,
                }
            }
        }));
    }
  };

  const handleCustomValueChange = (category: string, layerType: string, value: string) => {
    if (mode === 'module') {
        setCustomValues(prev => ({
          ...prev,
          [`${category}-${layerType}`]: value,
        }));
    } else if (selectedRoomId) {
        setRoomSettings(prev => ({
            ...prev,
            [selectedRoomId]: {
                ...prev[selectedRoomId],
                customValues: {
                    ...prev[selectedRoomId].customValues,
                    [`${category}-${layerType}`]: value,
                }
            }
        }));
    }
  };
  
  const handleRoomHeightChange = (val: string) => {
      if (selectedRoomId) {
          setRoomSettings(prev => ({
              ...prev,
              [selectedRoomId]: {
                  ...prev[selectedRoomId],
                  height: val
              }
          }));
      }
  };
  
  const applyCurrentSettingsToAll = () => {
      if (!selectedRoomId) return;
      const current = roomSettings[selectedRoomId];
      setRoomSettings(prev => {
          const next = { ...prev };
          Object.keys(next).forEach(rid => {
              if (rid !== selectedRoomId) {
                  next[rid] = {
                      height: current.height,
                      selections: { ...current.selections },
                      customValues: { ...current.customValues }
                  };
              }
          });
          return next;
      });
      alert('已将当前房间的设置应用到所有房间');
  };

  const handleModuleDataChange = (field: keyof ModuleData, value: string) => {
    let nextValue = value;
    if (field === 'moduleVolume') {
      const num = parseFloat(value);
      nextValue = isNaN(num) ? '' : num.toFixed(2);
    }
    setModuleData(prev => ({
      ...prev,
      [field]: nextValue,
    }));
  };

  // 判断是否为基层
  const isBaseLayer = (layerType: string) => {
    return layerType.includes('基层');
  };

  // 获取图片路径
  const getImagePath = (option: string) => {
    try {
      return require(`../../data/${option}.jpg`);
    } catch (error) {
      return null;
    }
  };

  // Helper to generate BOM for one item
  const generateBOMForRequest = async (data: ModuleData, sels: Selections) => {
      // 构建构造做法数据 - 转换为后端期望的扁平化结构
      const constructionPracticesData: Record<string, string> = {};
      
      // 定义类别映射，将中文类别名转换为英文键名
      const categoryMapping: Record<string, string> = {
        '天花构造选型': 'ceiling',
        '墙体构造选型': 'wall', 
        '地面构造选型': 'floor'
      };

      // 规范化层类型：支持“天花基层/墙体基层/地面基层”等后缀判断
      const normalizeLayerType = (layerType: string): 'baseLayer' | 'surfaceLayer' | undefined => {
        if (layerType.endsWith('基层')) return 'baseLayer';
        if (layerType.endsWith('饰面层')) return 'surfaceLayer';
        return undefined;
      };

      // 遍历构造做法选择，构建API所需的扁平化数据格式
      Object.entries(sels).forEach(([key, value]) => {
        const [category, layerType] = key.split('-');
        const englishCategory = categoryMapping[category];
        const englishLayerType = normalizeLayerType(layerType);

        if (englishCategory && englishLayerType && value) {
          const flatKey = `${englishCategory}-${englishLayerType}`;
          constructionPracticesData[flatKey] = value;
        }
      });

      // 构建请求数据
      const requestData = {
        module_data: {
          height: parseFloat(data.height || '0'),
          floor_area: parseFloat(data.floorArea || '0'),
          wall_area: parseFloat(data.wallArea || '0'),
          ceiling_area: parseFloat(data.ceilingArea || '0'),
          perimeter: parseFloat(data.perimeter || '0'),
        },
        construction_practices: constructionPracticesData,
        project_type: projectType,
        room_type: data.roomType || '标准房间',
        debug: false,
      };

      const response = await bomService.generateMaterialBOM(requestData);
      return response;
  };

  // 生成物料清单
  const generateMaterialBOM = async () => {
    setError(null);
    setBomResult(null);
    setIsGenerating(true);

    try {
        if (mode === 'module') {
            // 前置校验：必填项是否填写
            const requiredOrder: (keyof ModuleData)[] = [
              'perimeter',
              'height',
              'ceilingArea',
              'wallArea',
              'floorArea',
            ];

            const refsMap: Partial<Record<keyof ModuleData, React.RefObject<HTMLInputElement | null>>> = {
              height: heightInputRef,
              floorArea: floorAreaInputRef,
              wallArea: wallAreaInputRef,
              ceilingArea: ceilingAreaInputRef,
              perimeter: perimeterInputRef,
            };

            const missingKey = requiredOrder.find((key) => {
              const v = moduleData[key];
              return v === undefined || v === null || v === '' || isNaN(parseFloat(v as string));
            });

            if (missingKey) {
              setError('模块基本信息中必选项未填写，无法生成');
              moduleInfoRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              setTimeout(() => refsMap[missingKey]?.current?.focus(), 150);
              setIsGenerating(false);
              return;
            }
            
            const response = await generateBOMForRequest(moduleData, selections);
            if (response.success && response.data) {
                setBomResult(response.data);
                setShowViewBOMModal(true);
            } else {
                throw new Error(response.message || '生成物料清单失败');
            }

        } else {
            // Layout Mode Calculation
            if (!layoutResult || !layoutResult.rooms || layoutResult.rooms.length === 0) {
                throw new Error("没有有效的房间数据");
            }

            const allMaterials: BOMItem[] = [];
            const allCategories = new Set<string>();
            let totalTime = 0;

            for (const room of layoutResult.rooms) {
                const settings = roomSettings[room.room_id];
                const height = parseFloat(settings.height || '2800');
                const perimeterM = (room.perimeter_mm || 0) / 1000;
                const areaM2 = room.area_m2 || 0;
                const wallLengthM = (room.wall_length_mm || 0) / 1000;
                
                // 关键逻辑：墙面面积 = 墙长 * 高度
                const wallAreaM2 = wallLengthM * (height / 1000); 

                const roomModuleData: ModuleData = {
                    height: settings.height || '2800',
                    floorArea: areaM2.toFixed(2),
                    ceilingArea: areaM2.toFixed(2),
                    wallArea: wallAreaM2.toFixed(2),
                    perimeter: perimeterM.toFixed(2),
                    vertices: '0',
                    moduleArea: areaM2.toFixed(2),
                    moduleVolume: (areaM2 * height / 1000).toFixed(2),
                    roomType: settings.roomType || mapRoomType(room.room_id)
                };
                
                const res = await generateBOMForRequest(roomModuleData, settings.selections);
                if (res.success && res.data) {
                    res.data.materials.forEach((item: BOMItem) => {
                        // Add room info to notes or name?
                        const itemWithRoom = { ...item, notes: item.notes ? `${item.notes} (${room.room_id})` : `(${room.room_id})` };
                        allMaterials.push(itemWithRoom);
                        allCategories.add(item.category);
                    });
                    totalTime += res.data.processing_info.processing_time;
                }
            }

            // Aggregate materials by name + specification + room_id (to keep separate per room as requested)
            // Or just append without aggregation if we want completely separate entries.
            // Requirement: "不同房间的同一物料不需要合并"
            // So we skip aggregation or aggregate only within same room (which is already done by generateBOMForRequest per room call?)
            // generateBOMForRequest returns a list for ONE room.
            // So we just need to collect all items.
            
            // However, `allMaterials` is a flat list. We might want to sort them by room or category.
            // The existing logic was:
            /*
            allMaterials.forEach(item => {
                const key = `${item.name}-${item.specification}`;
                // ... aggregation ...
            });
            */
            
            // New logic: No global aggregation. Just pass allMaterials directly?
            // But generateBOMForRequest might return multiple items with same name/spec for one room if backend does so (unlikely for standard BOM).
            // Let's assume backend returns aggregated items per call.
            // So we just use allMaterials directly.
            
            const finalMaterials = allMaterials;
            
            setBomResult({
                materials: finalMaterials,
                summary: {
                    total_items: finalMaterials.length,
                    categories: Array.from(allCategories)
                },
                processing_info: {
                    timestamp: new Date().toISOString(),
                    processing_time: totalTime
                }
            });
            setShowViewBOMModal(true);
        }
    } catch (err: any) {
      console.error('生成物料清单失败:', err);
      setError(err.message || '生成物料清单失败，请稍后重试');
    } finally {
      setIsGenerating(false);
    }
  };

  // 弹窗交互：查看完整BOM清单
  const handleConfirmViewBOM = () => {
    if (bomResult) {
      setMaterialBom(bomResult);
    }
    setShowViewBOMModal(false);
    navigateTo('bom-generation');
  };

  const handleCancelViewBOM = () => {
    setShowViewBOMModal(false);
    // 在页面底部显示“BOM生成”按钮，用户可稍后跳转
    setShowBOMGenerateButton(true);
  };

  // 格式化数量显示
  const formatQuantity = (quantity: number, unit: string) => {
    return `${quantity.toFixed(2)} ${unit}`;
  };

  const currentSelections = mode === 'module' ? selections : (selectedRoomId ? roomSettings[selectedRoomId]?.selections : {});
  const currentCustomValues = mode === 'module' ? customValues : (selectedRoomId ? roomSettings[selectedRoomId]?.customValues : {});

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* 生成后弹窗：查看完整BOM清单 */}
      <AnimatePresence>
        {showViewBOMModal && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="absolute inset-0 bg-black/60" onClick={handleCancelViewBOM} />
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="glass-effect rounded-xl p-6 border border-white/20 w-full max-w-md relative"
            >
              <h3 className="text-xl font-semibold text-white mb-2">查看完整的BOM清单</h3>
              <p className="text-gray-300 mb-4">已生成物料组成，是否跳转到BOM生成页面并显示完整清单（支持编辑与导出）？</p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={handleCancelViewBOM}
                  className="px-4 py-2 rounded-lg bg-gray-700 text-gray-200 hover:bg-gray-600"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmViewBOM}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700"
                >
                  确认查看
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* 底部持久按钮：BOM生成（在用户取消弹框后显示） */}
      <AnimatePresence>
        {showBOMGenerateButton && (
          <motion.div
            className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            transition={{ duration: 0.3 }}
          >
            <button
              onClick={() => {
                if (bomResult) {
                  setMaterialBom(bomResult);
                }
                navigateTo('bom-generation');
              }}
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:from-blue-700 hover:to-purple-700 border border-white/10"
            >
              BOM生成
            </button>
          </motion.div>
        )}
      </AnimatePresence>
      {/* 数据载入提示 */}
      <AnimatePresence>
        {showDataLoadNotification && (
          <motion.div
            className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50"
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -50, scale: 0.9 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-green-600/90 backdrop-blur-sm text-white px-6 py-3 rounded-lg shadow-lg border border-green-500/30 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-200" />
              <span className="text-sm font-medium">
                已自动载入刚刚生成的分析结果（{loadedDataTimestamp}）
              </span>
              <button
                onClick={() => setShowDataLoadNotification(false)}
                className="ml-2 text-green-200 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex justify-between items-center mb-6">
        <div>
            <h1 className="text-3xl font-bold text-white flex items-center">
                <Calculator className="mr-3" /> 物料计算
            </h1>
        </div>
        
        {/* Mode Switcher & Project Type */}
        <div className="flex items-center gap-4">
            {/* Project Type Selector */}
            <div className="bg-gray-800/50 p-1 rounded-lg flex items-center border border-white/10 px-3 h-10">
                <span className="text-sm text-gray-400 mr-2">项目类型:</span>
                <select 
                    value={projectType}
                    onChange={(e) => setProjectType(e.target.value)}
                    className="bg-transparent text-white text-sm font-medium outline-none cursor-pointer [&>option]:bg-gray-800"
                >
                    <option value="住宅">住宅</option>
                    <option value="公寓">公寓</option>
                    <option value="酒店">酒店</option>
                </select>
            </div>

            <div className="bg-gray-800/50 p-1 rounded-lg flex space-x-1 border border-white/10 h-10 items-center">
                <button
                    onClick={() => setMode('module')}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                        mode === 'module' 
                            ? 'bg-blue-600 text-white shadow-lg' 
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Grid className="w-4 h-4 inline-block mr-2" />
                    单模块计算
                </button>
                <button
                    onClick={() => setMode('layout')}
                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                        mode === 'layout' 
                            ? 'bg-purple-600 text-white shadow-lg' 
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Layout className="w-4 h-4 inline-block mr-2" />
                    整屋户型计算
                </button>
            </div>
        </div>
      </div>

      {/* Mode Content */}
      {mode === 'module' ? (
          <>
            {/* 模块单元信息 */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="glass-effect rounded-xl p-6 border border-white/20"
                ref={moduleInfoRef}
            >
                <div className="flex justify-between items-center mb-4 border-l-4 border-blue-500 pl-3">
                    <h2 className="text-xl font-semibold text-white">模块基本信息</h2>
                    <div className="flex items-center bg-gray-800/50 rounded px-3 py-1.5 border border-white/10">
                        <span className="text-xs text-gray-400 mr-2">房间类型:</span>
                        <select
                            value={moduleData.roomType || '标准房间'}
                            onChange={(e) => handleModuleDataChange('roomType', e.target.value)}
                            className="bg-transparent text-white text-sm outline-none cursor-pointer [&>option]:bg-gray-800"
                        >
                            <option value="标准房间">标准房间</option>
                            <option value="客厅">客厅</option>
                            <option value="卧室">卧室</option>
                            <option value="厨房">厨房</option>
                            <option value="卫生间">卫生间</option>
                            <option value="阳台">阳台</option>
                            <option value="走廊">走廊</option>
                            <option value="其余">其余</option>
                        </select>
                    </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-white">
                {/* 第一排：顶点数、模块轮廓周长、模块高度、模块面积 */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">顶点数</p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="1"
                        value={moduleData.vertices}
                        onChange={(e) => handleModuleDataChange('vertices', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">模块轮廓周长<span className="text-red-400 ml-1">*</span></p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.perimeter}
                        onChange={(e) => handleModuleDataChange('perimeter', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        ref={perimeterInputRef}
                    />
                    <span className="text-2xl font-bold ml-1">m</span>
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">模块高度<span className="text-red-400 ml-1">*</span></p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="1"
                        value={moduleData.height}
                        onChange={(e) => handleModuleDataChange('height', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        ref={heightInputRef}
                    />
                    <span className="text-2xl font-bold ml-1">mm</span>
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">模块面积</p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.moduleArea}
                        onChange={(e) => handleModuleDataChange('moduleArea', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <span className="text-2xl font-bold ml-1">m²</span>
                    </div>
                </div>

                {/* 第二排：天花装修面积、地面装修面积、墙面装修面积、模块体积 */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">天花装修面积<span className="text-red-400 ml-1">*</span></p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.ceilingArea}
                        onChange={(e) => handleModuleDataChange('ceilingArea', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        ref={ceilingAreaInputRef}
                    />
                    <span className="text-2xl font-bold ml-1">m²</span>
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">墙面装修面积<span className="text-red-400 ml-1">*</span></p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.wallArea}
                        onChange={(e) => handleModuleDataChange('wallArea', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        ref={wallAreaInputRef}
                    />
                    <span className="text-2xl font-bold ml-1">m²</span>
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">地面装修面积<span className="text-red-400 ml-1">*</span></p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.floorArea}
                        onChange={(e) => handleModuleDataChange('floorArea', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        ref={floorAreaInputRef}
                    />
                    <span className="text-2xl font-bold ml-1">m²</span>
                    </div>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <p className="text-sm text-gray-400">模块体积</p>
                    <div className="flex items-baseline justify-center">
                    <input
                        type="number"
                        step="0.01"
                        value={moduleData.moduleVolume}
                        onChange={(e) => handleModuleDataChange('moduleVolume', e.target.value)}
                        placeholder="--"
                        className="text-2xl font-bold bg-transparent border-none outline-none text-white w-20 focus:bg-gray-700/50 rounded px-1 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <span className="text-2xl font-bold ml-1">m³</span>
                    </div>
                </div>
                </div>
            </motion.div>
          </>
      ) : (
          /* Layout Mode UI */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col gap-6"
          >
              {!layoutResult ? (
                  <div className="glass-effect rounded-xl p-8 border border-white/20 text-center py-20">
                      <Layout className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                      <h3 className="text-xl font-bold text-white mb-2">未找到户型数据</h3>
                      <p className="text-gray-400 mb-6">请先前往“户型图识别”页面上传并分析户型图</p>
                      <button 
                        onClick={() => navigateTo('layout-recognition')}
                        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                      >
                          前往户型识别
                      </button>
                  </div>
              ) : (
                  <div className="flex flex-col gap-6">
                      {/* Top Section: Global Settings & Room List & Room Info */}
                      <div className="glass-effect rounded-xl p-6 border border-white/20">
                          <div className="flex flex-col md:flex-row gap-8 mb-6">
                              {/* Global Settings */}
                              <div className="w-full md:w-1/4 min-w-[200px] border-r border-white/10 pr-6">
                                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                                      <Settings className="w-4 h-4 mr-2" /> 全局设置
                                  </h3>
                                  <div>
                                      <label className="text-sm text-gray-400 block mb-1">模块高度 (mm)</label>
                                      <input 
                                        type="number" 
                                        value={globalHeight}
                                        onChange={(e) => handleGlobalHeightChange(e.target.value)}
                                        className="w-full bg-gray-900/50 border border-gray-600 rounded px-3 py-2 text-white"
                                      />
                                      <p className="text-xs text-gray-500 mt-1">设置所有房间的默认高度</p>
                                  </div>
                              </div>
                              
                              {/* Room List */}
                              <div className="flex-1">
                                  <h3 className="text-lg font-semibold text-white mb-4">房间列表</h3>
                                  <div className="flex flex-wrap gap-2 max-h-[150px] overflow-y-auto pr-2 custom-scrollbar">
                                      {layoutResult.rooms.map(room => (
                                          <button
                                            key={room.room_id}
                                            onClick={() => setSelectedRoomId(room.room_id)}
                                            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 border ${
                                                selectedRoomId === room.room_id 
                                                    ? 'bg-purple-600 text-white shadow-md border-purple-400' 
                                                    : 'bg-white/5 text-gray-300 hover:bg-white/10 border-white/10'
                                            }`}
                                          >
                                              <span className="font-medium">{room.room_id}</span>
                                              <span className="text-xs opacity-70 bg-black/20 px-1.5 py-0.5 rounded">{room.area_m2?.toFixed(1)}m²</span>
                                          </button>
                                      ))}
                                  </div>
                              </div>
                          </div>

                          {/* Selected Room Info */}
                          {selectedRoomId && (
                              <div className="mt-6 pt-6 border-t border-white/10">
                                  <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                      <div className="flex-1">
                                          <div className="flex items-center gap-4 mb-2 flex-wrap">
                                            <h2 className="text-2xl font-bold text-white">房间: {selectedRoomId}</h2>
                                            <span className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded border border-purple-500/30">
                                              当前选中
                                            </span>
                                            <div className="flex items-center bg-gray-800/50 rounded px-2 py-1 border border-white/10 ml-2">
                                                <span className="text-xs text-gray-400 mr-2">类型:</span>
                                                <select
                                                    value={roomSettings[selectedRoomId]?.roomType || '标准房间'}
                                                    onChange={(e) => handleRoomSettingChange(selectedRoomId, 'roomType', e.target.value)}
                                                    className="bg-transparent text-white text-sm outline-none cursor-pointer [&>option]:bg-gray-800"
                                                >
                                                    <option value="标准房间">标准房间</option>
                                                    <option value="客厅">客厅</option>
                                                    <option value="卧室">卧室</option>
                                                    <option value="厨房">厨房</option>
                                                    <option value="卫生间">卫生间</option>
                                                    <option value="阳台">阳台</option>
                                                    <option value="走廊">走廊</option>
                                                    <option value="其余">其余</option>
                                                </select>
                                            </div>
                                          </div>
                                          
                                          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm mt-3">
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">房间周长 (m)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.perimeter || ''}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'perimeter', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">房间墙长 (m)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.wallLength || ''}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'wallLength', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">模块高度 (mm)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.height || globalHeight}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'height', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">天花面积 (m²)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.ceilingArea || ''}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'ceilingArea', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">地面面积 (m²)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.floorArea || ''}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'floorArea', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                            <div className="bg-gray-800/50 p-2 rounded border border-white/5">
                                              <span className="text-gray-400 block text-xs mb-1">墙面面积 (m²)</span>
                                              <input
                                                type="number"
                                                value={roomSettings[selectedRoomId]?.wallArea || ''}
                                                onChange={(e) => handleRoomSettingChange(selectedRoomId, 'wallArea', e.target.value)}
                                                className="w-full bg-transparent border-b border-gray-600 focus:border-purple-500 outline-none text-white font-medium text-center"
                                              />
                                            </div>
                                          </div>
                                      </div>
                                      
                                      <div className="flex items-center">
                                          <button 
                                            onClick={applyCurrentSettingsToAll}
                                            className="px-4 py-2 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 text-sm border border-blue-500/30 transition-colors flex items-center gap-2"
                                          >
                                              <Settings className="w-4 h-4" />
                                              将当前构造应用到所有房间
                                          </button>
                                      </div>
                                  </div>
                              </div>
                          )}
                      </div>

                      {/* Construction Selections (Moved below) */}
                      {selectedRoomId && (
                          <div className="glass-effect rounded-xl p-6 border border-white/20">
                              <h2 className="text-xl font-semibold text-white mb-6 border-l-4 border-blue-500 pl-3">构造选型</h2>
                              {constructionPractices && (
                                <div className="space-y-8">
                                    {Object.entries(constructionPractices).map(([category, layers]: [string, any]) => (
                                    <div key={category} className="bg-gray-800/30 rounded-xl p-4 border border-white/5">
                                        <h3 className="text-lg font-medium text-blue-400 mb-4 pb-2 border-b border-white/10">{category}</h3>
                                        {Object.entries(layers).map(([layerType, options]: [string, any]) => (
                                        <div key={layerType} className="mb-6 last:mb-0">
                                            <label className="block text-sm font-medium text-gray-300 mb-3 flex items-center">
                                              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mr-2"></span>
                                              {layerType}
                                            </label>
                                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                            {options.filter((option: string) => option !== '无').map((option: string) => (
                                                <div
                                                key={option}
                                                onClick={() => handleSelectionChange(category, layerType, option)}
                                                className={`cursor-pointer rounded-lg p-3 border-2 transition-all duration-200 ${
                                                    (roomSettings[selectedRoomId]?.selections?.[`${category}-${layerType}`]) === option
                                                    ? 'border-purple-500 bg-purple-900/50 shadow-lg shadow-purple-900/20'
                                                    : 'border-gray-700 bg-gray-800/50 hover:border-purple-400 hover:bg-gray-700/50'
                                                }`}
                                                >
                                                    {!isBaseLayer(layerType) && (
                                                        <div className="w-full aspect-[3/2] rounded-md mb-3 flex items-center justify-center overflow-hidden bg-gray-900">
                                                        {getImagePath(option) ? (
                                                            <img 
                                                            src={getImagePath(option)} 
                                                            alt={option}
                                                            className="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
                                                            />
                                                        ) : (
                                                            <div className="w-full h-full flex items-center justify-center">
                                                            <span className="text-gray-600 text-xs">暂无图片</span>
                                                            </div>
                                                        )}
                                                        </div>
                                                    )}
                                                    <p className={`text-white text-sm font-medium text-center ${
                                                      isBaseLayer(layerType) 
                                                        ? 'whitespace-normal min-h-[3.5rem] flex items-center justify-center' 
                                                        : 'truncate'
                                                    }`}>{option}</p>
                                                </div>
                                            ))}
                                            </div>
                                            {(roomSettings[selectedRoomId]?.selections?.[`${category}-${layerType}`]) === '自定义' && (
                                                <div className="mt-3">
                                                    <input
                                                    type="text"
                                                    placeholder={`请输入自定义${layerType}`}
                                                    value={roomSettings[selectedRoomId]?.customValues?.[`${category}-${layerType}`] || ''}
                                                    onChange={(e) => handleCustomValueChange(category, layerType, e.target.value)}
                                                    className="w-full bg-gray-900/70 border border-gray-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                                                    />
                                                </div>
                                            )}
                                        </div>
                                        ))}
                                    </div>
                                    ))}
                                </div>
                                )}
                          </div>
                      )}
                  </div>
              )}
          </motion.div>
      )}

      {/* 模块单元构造做法 (Only for Module Mode) */}
      {mode === 'module' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="glass-effect rounded-xl p-6 border border-white/20"
          >
            <h2 className="text-xl font-semibold text-white mb-4 border-l-4 border-blue-500 pl-3">模块室内设计选型</h2>
            {constructionPractices && (
            <div className="space-y-6">
                {Object.entries(constructionPractices).map(([category, layers]: [string, any]) => (
                <div key={category}>
                    {Object.entries(layers).map(([layerType, options]: [string, any]) => (
                    <div key={layerType} className="mb-6">
                        <label className="block text-base font-medium text-gray-300 mb-3">{layerType}</label>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {options.filter((option: string) => option !== '无').map((option: string) => (
                            <div
                            key={option}
                            onClick={() => handleSelectionChange(category, layerType, option)}
                            className={`cursor-pointer rounded-lg p-3 border-2 transition-all duration-200 ${
                                selections[`${category}-${layerType}`] === option
                                ? 'border-blue-500 bg-blue-900/50'
                                : 'border-gray-700 bg-gray-800/50 hover:border-blue-600'
                            }`}
                            >
                            {/* 根据是否为基层决定是否显示图片 */}
                            {!isBaseLayer(layerType) && (
                                <div className="w-full aspect-[3/2] rounded-md mb-2 flex items-center justify-center overflow-hidden">
                                {getImagePath(option) ? (
                                    <img 
                                    src={getImagePath(option)} 
                                    alt={option}
                                    className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <div className="w-full h-full bg-gray-700 flex items-center justify-center">
                                    <span className="text-gray-500 text-sm">图片</span>
                                    </div>
                                )}
                                </div>
                            )}
                            <p className={`text-white text-sm font-medium text-center ${
                                isBaseLayer(layerType) ? 'py-2' : ''
                            }`}>{option}</p>
                            </div>
                        ))}
                        </div>
                        {selections[`${category}-${layerType}`] === '自定义' && (
                        <div className="mt-3">
                            <input
                            type="text"
                            placeholder={`请输入自定义${layerType}`}
                            value={customValues[`${category}-${layerType}`] || ''}
                            onChange={(e) => handleCustomValueChange(category, layerType, e.target.value)}
                            className="w-full bg-gray-900/70 border border-gray-600 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        )}
                    </div>
                    ))}
                </div>
                ))}
            </div>
            )}
          </motion.div>
      )}

      {/* 物料分析 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="glass-effect-2 rounded-xl p-6 border border-white/20"
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">物料分析</h2>
          <button 
            onClick={generateMaterialBOM}
            disabled={isGenerating}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg transition-all duration-300 shadow-lg flex items-center gap-2"
          >
            {isGenerating && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            {isGenerating ? '生成中...' : mode === 'layout' ? '生成整屋物料清单' : '一键生成物料组成'}
          </button>
        </div>
        
        {/* 错误提示 */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-4">
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* BOM结果显示 */}
        {bomResult ? (
          <div className="space-y-4">
            {/* 汇总信息 */}
            <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">生成汇总</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">物料总数：</span>
                  <span className="text-white font-medium">{bomResult.summary.total_items} 项</span>
                </div>
                <div>
                  <span className="text-gray-400">涉及类别：</span>
                  <span className="text-white font-medium">{bomResult.summary.categories?.join(', ') || '无'}</span>
                </div>
                <div>
                  <span className="text-gray-400">生成时间：</span>
                  <span className="text-white font-medium">
                    {new Date(bomResult.processing_info.timestamp).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">处理耗时：</span>
                  <span className="text-white font-medium">{bomResult.processing_info.processing_time.toFixed(2)}s</span>
                </div>
              </div>
            </div>

            {/* 物料列表 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-white">
              {bomResult.materials && bomResult.materials.length > 0 ? (
                bomResult.materials.map((material, index) => (
                  <div key={index} className="glowing-border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-semibold text-white">{material.name}</p>
                      <span className="text-xs bg-blue-500/30 text-blue-300 px-2 py-1 rounded">
                        {material.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-1">
                      规格: {material.specification}
                    </p>
                    <p className="text-sm text-gray-400 mb-1">
                      用量: {formatQuantity(material.quantity, material.unit)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {material.layer_type}
                    </p>
                    {material.notes && (
                      <p className="text-xs text-yellow-400 mt-2">
                        备注: {material.notes}
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <div className="col-span-full text-center py-8">
                  <p className="text-red-400 text-lg">
                    没有找到物料数据，请重新生成
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-white">
            {/* 默认提示 */}
            <div className="col-span-full text-center py-8">
              <p className="text-gray-400 text-lg">
                请点击"{mode === 'layout' ? '生成整屋物料清单' : '一键生成物料组成'}"按钮开始计算物料清单
              </p>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default MaterialCalculation;

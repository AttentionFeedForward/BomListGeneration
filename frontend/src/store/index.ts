import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// 导入模块识别结果类型
import { ModuleIdentificationResult } from '../services/bomService';

// 模块识别数据类型（包含识别结果和计算的面积数据）
export interface ModuleIdentificationData {
  identificationResult: ModuleIdentificationResult;
  height: number;
  floor_area: number;
  wall_area: number;
  ceiling_area: number;
  timestamp: string;
  processing_time?: number;
  vertices_count?: number;
  perimeter?: number; // m
  module_area?: number; // m²
  module_volume?: number; // m³
}

// 简化的BOM结果类型（与物料计算接口返回结构保持一致）
export interface SimpleBOMItem {
  name: string;
  specification: string;
  quantity: number;
  unit: string;
  category: string;
  notes?: string;
  usage?: string; // 材料用途
  material_code?: string;
  calculation_formula?: string;
}

export interface SimpleBOMResult {
  materials: SimpleBOMItem[];
  summary: {
    total_items: number;
    categories: string[];
  };
  processing_info: {
    timestamp: string;
    processing_time: number;
  };
  // 后端返回的完整版BOM表（可选），字段名与界面列标题一致
  full_bom?: Array<{
    项次: string;
    物料编码: string;
    物料名称: string;
    规格: string;
    数量: number;
    单位: string;
    计算公式: string;
    材料用途: string;
    备注: string;
  }>;
}

// 简化的状态类型定义
export interface AppState {
  user: {
    isAuthenticated: boolean;
    profile: {
      id: string;
      name: string;
      email: string;
      role: string;
    } | null;
  };
  app: {
    loading: boolean;
    error: string | null;
    notifications: Array<{
      id: string;
      type: 'success' | 'error' | 'warning' | 'info';
      title: string;
      message: string;
      timestamp: Date;
    }>;
    ui?: {
      triggerUpload?: boolean;
    };
  };
  moduleData: {
    identificationResult: ModuleIdentificationData | null;
    lastProcessedAt: string | null;
    isTransferredByButton: boolean; // 标记数据是否通过按钮传输
  };
  layoutData: {
    result: any | null;
    lastProcessedAt: string | null;
  };
  bom: {
    materialBom: SimpleBOMResult | null;
  };
}

// 动作类型定义
export type AppAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_NOTIFICATION'; payload: AppState['app']['notifications'][0] }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'SET_USER'; payload: AppState['user']['profile'] }
  | { type: 'LOGOUT' }
  | { type: 'SET_MODULE_DATA'; payload: ModuleIdentificationData }
  | { type: 'CLEAR_MODULE_DATA' }
  | { type: 'ACK_MODULE_TRANSFER' }
  | { type: 'SET_LAYOUT_DATA'; payload: any }
  | { type: 'CLEAR_LAYOUT_DATA' }
  | { type: 'SET_MATERIAL_BOM'; payload: SimpleBOMResult }
  | { type: 'CLEAR_MATERIAL_BOM' }
  | { type: 'TRIGGER_UPLOAD_PROMPT' }
  | { type: 'CLEAR_UPLOAD_PROMPT' };

// 初始状态
const initialState: AppState = {
  user: {
    isAuthenticated: false,
    profile: null,
  },
  app: {
    loading: false,
    error: null,
    notifications: [],
    ui: { triggerUpload: false },
  },
  moduleData: {
    identificationResult: null,
    lastProcessedAt: null,
    isTransferredByButton: false,
  },
  layoutData: {
    result: null,
    lastProcessedAt: null,
  },
  bom: {
    materialBom: null,
  },
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        app: {
          ...state.app,
          loading: action.payload,
        },
      };
    case 'SET_ERROR':
      return {
        ...state,
        app: {
          ...state.app,
          error: action.payload,
        },
      };
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        app: {
          ...state.app,
          notifications: [...state.app.notifications, action.payload],
        },
      };
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        app: {
          ...state.app,
          notifications: state.app.notifications.filter(n => n.id !== action.payload),
        },
      };
    case 'SET_USER':
      return {
        ...state,
        user: {
          isAuthenticated: true,
          profile: action.payload,
        },
      };
    case 'LOGOUT':
      return {
        ...state,
        user: {
          isAuthenticated: false,
          profile: null,
        },
      };
    case 'SET_MODULE_DATA':
      return {
        ...state,
        moduleData: {
          identificationResult: action.payload,
          lastProcessedAt: new Date().toISOString(),
          isTransferredByButton: true, // 标记为通过按钮传输
        },
      };
    case 'CLEAR_MODULE_DATA':
      return {
        ...state,
        moduleData: {
          identificationResult: null,
          lastProcessedAt: null,
          isTransferredByButton: false,
        },
      };
    case 'ACK_MODULE_TRANSFER':
      return {
        ...state,
        moduleData: state.moduleData.identificationResult ? {
          identificationResult: state.moduleData.identificationResult,
          lastProcessedAt: state.moduleData.lastProcessedAt,
          isTransferredByButton: false,
        } : {
          identificationResult: null,
          lastProcessedAt: null,
          isTransferredByButton: false,
        },
      };
    case 'SET_LAYOUT_DATA':
      return {
        ...state,
        layoutData: {
          result: action.payload,
          lastProcessedAt: new Date().toISOString(),
        },
      };
    case 'CLEAR_LAYOUT_DATA':
      return {
        ...state,
        layoutData: {
          result: null,
          lastProcessedAt: null,
        },
      };
    case 'SET_MATERIAL_BOM':
      return {
        ...state,
        bom: {
          materialBom: action.payload,
        },
      };
    case 'CLEAR_MATERIAL_BOM':
      return {
        ...state,
        bom: {
          materialBom: null,
        },
      };
    case 'TRIGGER_UPLOAD_PROMPT':
      return {
        ...state,
        app: {
          ...state.app,
          ui: { ...(state.app.ui || {}), triggerUpload: true },
        },
      };
    case 'CLEAR_UPLOAD_PROMPT':
      return {
        ...state,
        app: {
          ...state.app,
          ui: { ...(state.app.ui || {}), triggerUpload: false },
        },
      };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Provider组件
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return React.createElement(
    AppContext.Provider,
    { value: { state, dispatch } },
    children
  );
}

// Hook for using context
export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppProvider');
  }
  return context;
}

// 选择器hooks
export function useUser() {
  const { state } = useAppState();
  return state.user;
}

export function useApp() {
  const { state } = useAppState();
  return state.app;
}

export function useModuleData() {
  const { state } = useAppState();
  return state.moduleData;
}

export function useLayoutData() {
  const { state } = useAppState();
  return state.layoutData;
}

export function useBOM() {
  const { state } = useAppState();
  return state.bom;
}

export function useActions() {
  const { dispatch } = useAppState();
  
  return {
    setLoading: (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error: string | null) => dispatch({ type: 'SET_ERROR', payload: error }),
    addNotification: (notification: AppState['app']['notifications'][0]) => 
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification }),
    removeNotification: (id: string) => dispatch({ type: 'REMOVE_NOTIFICATION', payload: id }),
    setUser: (user: AppState['user']['profile']) => dispatch({ type: 'SET_USER', payload: user }),
    logout: () => dispatch({ type: 'LOGOUT' }),
    setModuleData: (data: ModuleIdentificationData) => dispatch({ type: 'SET_MODULE_DATA', payload: data }),
    clearModuleData: () => dispatch({ type: 'CLEAR_MODULE_DATA' }),
    ackModuleTransfer: () => dispatch({ type: 'ACK_MODULE_TRANSFER' }),
    setLayoutData: (data: any) => dispatch({ type: 'SET_LAYOUT_DATA', payload: data }),
    clearLayoutData: () => dispatch({ type: 'CLEAR_LAYOUT_DATA' }),
    setMaterialBom: (data: SimpleBOMResult) => dispatch({ type: 'SET_MATERIAL_BOM', payload: data }),
    clearMaterialBom: () => dispatch({ type: 'CLEAR_MATERIAL_BOM' }),
    triggerUploadPrompt: () => dispatch({ type: 'TRIGGER_UPLOAD_PROMPT' }),
    clearUploadPrompt: () => dispatch({ type: 'CLEAR_UPLOAD_PROMPT' }),
  };
}
// BOM相关业务hooks
import { useCallback } from 'react';
import { useQuery, useMutation, useInfiniteQuery, useRealTimeData } from './useApi';
import bomService, { 
  ContourData, 
  MaterialItem, 
  BOMData, 
  ProcessingStatus,
  UploadResponse 
} from '../services/bomService';

// 轮廓相关hooks
export function useContours(params?: {
  page?: number;
  limit?: number;
  type?: string;
  search?: string;
}) {
  return useQuery(
    ['contours', JSON.stringify(params || {})],
    () => bomService.getContours(params),
    {
      staleTime: 2 * 60 * 1000, // 2分钟
      refetchOnWindowFocus: true,
    }
  );
}

export function useContour(id: string, enabled = true) {
  return useQuery(
    ['contour', id],
    () => bomService.getContour(id),
    {
      enabled: enabled && !!id,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );
}

export function useUploadContour() {
  return useMutation<UploadResponse, { file: File; onProgress?: (progress: number) => void }>(
    ({ file, onProgress }) => bomService.uploadContourFile(file, onProgress),
    {
      onSuccess: (data) => {
        console.log('轮廓文件上传成功:', data);
      },
      onError: (error) => {
        console.error('轮廓文件上传失败:', error);
      },
    }
  );
}

export function useDeleteContour() {
  return useMutation<void, string>(
    (id) => bomService.deleteContour(id),
    {
      onSuccess: () => {
        console.log('轮廓删除成功');
      },
      onError: (error) => {
        console.error('轮廓删除失败:', error);
      },
    }
  );
}

export function useProcessContour() {
  return useMutation<ProcessingStatus, { 
    id: string; 
    options?: {
      algorithm?: string;
      precision?: number;
      filters?: string[];
    }
  }>(
    ({ id, options }) => bomService.processContourById(id, options),
    {
      onSuccess: (data) => {
        console.log('轮廓处理已开始:', data);
      },
      onError: (error) => {
        console.error('轮廓处理失败:', error);
      },
    }
  );
}

// 物料相关hooks
export function useMaterials(params?: {
  page?: number;
  limit?: number;
  category?: string;
  search?: string;
}) {
  return useQuery(
    ['materials', JSON.stringify(params || {})],
    () => bomService.getMaterials(params),
    {
      staleTime: 10 * 60 * 1000, // 10分钟
      refetchOnWindowFocus: false,
    }
  );
}

export function useInfiniteMaterials(params?: {
  category?: string;
  search?: string;
}) {
  return useInfiniteQuery(
    ['materials', 'infinite', JSON.stringify(params || {})],
    async (page) => {
      const response = await bomService.getMaterials({ ...params, page, limit: 20 });
      return {
        ...response,
        data: {
          ...response.data,
          hasMore: response.data.page * response.data.limit < response.data.total
        }
      };
    },
    {
      staleTime: 10 * 60 * 1000,
    }
  );
}

export function useMaterial(id: string, enabled = true) {
  return useQuery(
    ['material', id],
    () => bomService.getMaterial(id),
    {
      enabled: enabled && !!id,
      staleTime: 15 * 60 * 1000, // 15分钟
    }
  );
}

export function useCreateMaterial() {
  return useMutation<MaterialItem, Omit<MaterialItem, 'id'>>(
    (data) => bomService.createMaterial(data),
    {
      onSuccess: (data) => {
        console.log('物料创建成功:', data);
      },
      onError: (error) => {
        console.error('物料创建失败:', error);
      },
    }
  );
}

export function useUpdateMaterial() {
  return useMutation<MaterialItem, { id: string; data: Partial<MaterialItem> }>(
    ({ id, data }) => bomService.updateMaterial(id, data),
    {
      onSuccess: (data) => {
        console.log('物料更新成功:', data);
      },
      onError: (error) => {
        console.error('物料更新失败:', error);
      },
    }
  );
}

export function useDeleteMaterial() {
  return useMutation<void, string>(
    (id) => bomService.deleteMaterial(id),
    {
      onSuccess: () => {
        console.log('物料删除成功');
      },
      onError: (error) => {
        console.error('物料删除失败:', error);
      },
    }
  );
}

// BOM相关hooks
export function useBOMs(params?: {
  page?: number;
  limit?: number;
  status?: string;
  project_name?: string;
}) {
  return useQuery(
    ['boms', JSON.stringify(params || {})],
    () => bomService.getBOMs(params),
    {
      staleTime: 2 * 60 * 1000, // 2分钟
      refetchOnWindowFocus: true,
    }
  );
}

export function useBOM(id: string, enabled = true) {
  return useQuery(
    ['bom', id],
    () => bomService.getBOM(id),
    {
      enabled: enabled && !!id,
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );
}

export function useGenerateBOM() {
  return useMutation<ProcessingStatus, {
    contourId: string;
    options?: {
      construction_method?: string;
      material_preferences?: string[];
      cost_optimization?: boolean;
    };
  }>(
    ({ contourId, options }) => bomService.generateBOM(contourId, options),
    {
      onSuccess: (data) => {
        console.log('BOM生成已开始:', data);
      },
      onError: (error) => {
        console.error('BOM生成失败:', error);
      },
    }
  );
}

export function useUpdateBOM() {
  return useMutation<BOMData, { id: string; data: Partial<BOMData> }>(
    ({ id, data }) => bomService.updateBOM(id, data),
    {
      onSuccess: (data) => {
        console.log('BOM更新成功:', data);
      },
      onError: (error) => {
        console.error('BOM更新失败:', error);
      },
    }
  );
}

export function useDeleteBOM() {
  return useMutation<void, string>(
    (id) => bomService.deleteBOM(id),
    {
      onSuccess: () => {
        console.log('BOM删除成功');
      },
      onError: (error) => {
        console.error('BOM删除失败:', error);
      },
    }
  );
}

export function useExportBOM() {
  return useMutation<void, { id: string; format?: 'csv' | 'excel' | 'pdf' }>(
    async ({ id, format = 'csv' }) => {
      await bomService.exportBOM(id, format);
      return { data: undefined, success: true, message: 'BOM导出成功' };
    },
    {
      onSuccess: () => {
        console.log('BOM导出成功');
      },
      onError: (error) => {
        console.error('BOM导出失败:', error);
      },
    }
  );
}

// 处理状态相关hooks
export function useProcessingStatus(id: string, enabled = true) {
  return useQuery(
    ['processing-status', id],
    () => bomService.getProcessingStatus(id),
    {
      enabled: enabled && !!id,
      staleTime: 0, // 实时数据
      refetchOnWindowFocus: true,
    }
  );
}

export function useRealTimeProcessingStatus(id: string, enabled = true) {
  return useRealTimeData(
    () => bomService.getProcessingStatus(id),
    2000, // 2秒刷新
    {
      enabled: enabled && !!id,
    }
  );
}

export function useProcessingHistory(params?: {
  page?: number;
  limit?: number;
  status?: string;
  type?: string;
}) {
  return useQuery(
    ['processing-history', JSON.stringify(params || {})],
    () => bomService.getProcessingHistory(params),
    {
      staleTime: 5 * 60 * 1000, // 5分钟
    }
  );
}

export function useCancelProcessing() {
  return useMutation<void, string>(
    (id) => bomService.cancelProcessing(id),
    {
      onSuccess: () => {
        console.log('处理已取消');
      },
      onError: (error) => {
        console.error('取消处理失败:', error);
      },
    }
  );
}

// 统计数据hooks
export function useDashboardStats() {
  return useQuery(
    ['dashboard-stats'],
    () => bomService.getDashboardStats(),
    {
      staleTime: 30 * 1000, // 30秒
      refetchOnWindowFocus: true,
    }
  );
}

export function useRealTimeDashboardStats() {
  return useRealTimeData(
    () => bomService.getDashboardStats(),
    10000, // 10秒刷新
    {
      refetchOnWindowFocus: true,
    }
  );
}

export function useRecentActivity(limit: number = 10) {
  return useQuery(
    ['recent-activity', limit.toString()],
    () => bomService.getRecentActivity(limit),
    {
      staleTime: 60 * 1000, // 1分钟
      refetchOnWindowFocus: true,
    }
  );
}

export function useProcessingMetrics() {
  return useRealTimeData(
    () => bomService.getProcessingMetrics(),
    5000, // 5秒刷新
    {
      refetchOnWindowFocus: true,
    }
  );
}

// 系统配置hooks
export function useSystemConfig() {
  return useQuery(
    ['system-config'],
    () => bomService.getSystemConfig(),
    {
      staleTime: 30 * 60 * 1000, // 30分钟
      refetchOnWindowFocus: false,
    }
  );
}

export function useUpdateSystemConfig() {
  return useMutation<void, Record<string, any>>(
    (config) => bomService.updateSystemConfig(config),
    {
      onSuccess: () => {
        console.log('系统配置更新成功');
      },
      onError: (error) => {
        console.error('系统配置更新失败:', error);
      },
    }
  );
}

// 健康检查hook
export function useHealthCheck() {
  return useRealTimeData(
    () => bomService.healthCheck(),
    30000, // 30秒检查
    {
      retry: 1,
      onError: (error) => {
        console.warn('健康检查失败:', error);
      },
    }
  );
}

// 组合hooks
export function useBOMWorkflow() {
  const uploadContour = useUploadContour();
  const processContour = useProcessContour();
  const generateBOM = useGenerateBOM();
  const exportBOM = useExportBOM();

  const executeWorkflow = useCallback(async (
    file: File,
    options?: {
      processOptions?: {
        algorithm?: string;
        precision?: number;
        filters?: string[];
      };
      bomOptions?: {
        construction_method?: string;
        material_preferences?: string[];
        cost_optimization?: boolean;
      };
      exportFormat?: 'csv' | 'excel' | 'pdf';
    }
  ) => {
    try {
      // 1. 上传轮廓文件
      const uploadResult = await uploadContour.mutateAsync({ file });
      const contourId = uploadResult.file_id;

      // 2. 处理轮廓
      const processResult = await processContour.mutateAsync({
        id: contourId,
        options: options?.processOptions,
      });

      // 3. 等待处理完成（这里需要轮询状态）
      // 实际应用中可能需要更复杂的状态管理

      // 4. 生成BOM
      const bomResult = await generateBOM.mutateAsync({
        contourId,
        options: options?.bomOptions,
      });

      return {
        contourId,
        processId: processResult.id,
        bomId: bomResult.id,
      };
    } catch (error) {
      console.error('BOM工作流执行失败:', error);
      throw error;
    }
  }, [uploadContour, processContour, generateBOM]);

  return {
    executeWorkflow,
    uploadContour,
    processContour,
    generateBOM,
    exportBOM,
    isLoading: uploadContour.loading || processContour.loading || generateBOM.loading || exportBOM.loading,
  };
}

// 导出所有hooks
export default {
  // 轮廓相关
  useContours,
  useContour,
  useUploadContour,
  useDeleteContour,
  useProcessContour,
  
  // 物料相关
  useMaterials,
  useInfiniteMaterials,
  useMaterial,
  useCreateMaterial,
  useUpdateMaterial,
  useDeleteMaterial,
  
  // BOM相关
  useBOMs,
  useBOM,
  useGenerateBOM,
  useUpdateBOM,
  useDeleteBOM,
  useExportBOM,
  
  // 处理状态相关
  useProcessingStatus,
  useRealTimeProcessingStatus,
  useProcessingHistory,
  useCancelProcessing,
  
  // 统计数据相关
  useDashboardStats,
  useRealTimeDashboardStats,
  useRecentActivity,
  useProcessingMetrics,
  
  // 系统配置相关
  useSystemConfig,
  useUpdateSystemConfig,
  
  // 健康检查
  useHealthCheck,
  
  // 组合hooks
  useBOMWorkflow,
};
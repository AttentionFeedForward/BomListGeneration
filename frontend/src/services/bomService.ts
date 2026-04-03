// BOM相关API服务
import apiClient, { ApiResponse } from './api';

// 数据类型定义
export interface ContourData {
  id: string;
  name: string;
  type: string;
  points: Array<{ x: number; y: number; z?: number }>;
  area: number;
  perimeter: number;
  created_at: string;
  updated_at: string;
}

// 模块识别相关类型
export interface ModuleIdentificationRequest {
  image: File;
  json_data?: File;
  confidence_threshold?: number;
  debug?: boolean;
}

export interface Point {
  x: number;
  y: number;
}

export interface EndpointPair {
  start_point: Point;
  end_point: Point;
}

export interface TextBox {
  corners: Point[];
}

export interface Measurements {
  pixel_distance: number;
  actual_size: number;
  scale_factor: number;
}

export interface ModuleMatch {
  id: string;
  endpoint_pair: EndpointPair;
  text_box: TextBox;
  text_content: string;
  measurements: Measurements;
  match_score: number;
  is_outlier: boolean;
}

export interface ModuleIdentificationResult {
  matches: ModuleMatch[];
  summary: {
    total_matches: number;
    average_score: number;
    processing_time: number;
  };
  unmatched_endpoints: any[];
  unmatched_texts: any[];
  contour_info?: ContourInfo;
}

// 轮廓处理相关类型 - 匹配后端API返回结构


export interface ContourGeometry {
  points: [number, number][];
  edge_lengths: number[];
  perimeter: number;
  area: number;
  num_points: number;
  unit: string;
}

export interface ContourData {
  id: string;
  geometry: ContourGeometry;
}

export interface ContourSummary {
  total_contours: number;
  total_area: number;
  total_perimeter: number;
  unit: string;
}

export interface ContourInfo {
  contours: ContourData[];
  summary: ContourSummary;
}

export interface ContourProcessResult {
  contour_info: ContourInfo;
  processing_time: number;
}

export interface MaterialItem {
  id: string;
  name: string;
  category: string;
  unit: string;
  price: number;
  supplier?: string;
  specifications?: Record<string, any>;
}

export interface BOMItem {
  id: string;
  material_id: string;
  material_name: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  category: string;
  specifications?: Record<string, any>;
}

export interface BOMData {
  id: string;
  project_name: string;
  contour_id: string;
  items: BOMItem[];
  total_cost: number;
  created_at: string;
  updated_at: string;
  status: 'draft' | 'processing' | 'completed' | 'error';
}

export interface ProcessingStatus {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  size: number;
  type: string;
  upload_url?: string;
}

class BOMService {
  // 轮廓相关API
  async uploadContourFile(file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<UploadResponse>> {
    return apiClient.upload('/contours/upload', file, onProgress);
  }

  async getContours(params?: {
    page?: number;
    limit?: number;
    type?: string;
    search?: string;
  }): Promise<ApiResponse<{ items: ContourData[]; total: number; page: number; limit: number }>> {
    return apiClient.get('/contours', { params });
  }

  async getContour(id: string): Promise<ApiResponse<ContourData>> {
    return apiClient.get(`/contours/${id}`);
  }

  async deleteContour(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/contours/${id}`);
  }

  async processContourById(id: string, options?: {
    algorithm?: string;
    precision?: number;
    filters?: string[];
  }): Promise<ApiResponse<ProcessingStatus>> {
    return apiClient.post(`/contours/${id}/process`, options);
  }

  // 物料相关API
  async getMaterials(params?: {
    page?: number;
    limit?: number;
    category?: string;
    search?: string;
  }): Promise<ApiResponse<{ items: MaterialItem[]; total: number; page: number; limit: number }>> {
    return apiClient.get('/materials', { params });
  }

  async getMaterial(id: string): Promise<ApiResponse<MaterialItem>> {
    return apiClient.get(`/materials/${id}`);
  }

  async createMaterial(data: Omit<MaterialItem, 'id'>): Promise<ApiResponse<MaterialItem>> {
    return apiClient.post('/materials', data);
  }

  async updateMaterial(id: string, data: Partial<MaterialItem>): Promise<ApiResponse<MaterialItem>> {
    return apiClient.put(`/materials/${id}`, data);
  }

  async deleteMaterial(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/materials/${id}`);
  }

  // BOM相关API
  async generateBOM(contourId: string, options?: {
    construction_method?: string;
    material_preferences?: string[];
    cost_optimization?: boolean;
  }): Promise<ApiResponse<ProcessingStatus>> {
    return apiClient.post('/bom/generate', {
      contour_id: contourId,
      ...options,
    });
  }

  async getBOMs(params?: {
    page?: number;
    limit?: number;
    status?: string;
    project_name?: string;
  }): Promise<ApiResponse<{ items: BOMData[]; total: number; page: number; limit: number }>> {
    return apiClient.get('/bom', { params });
  }

  async getBOM(id: string): Promise<ApiResponse<BOMData>> {
    return apiClient.get(`/bom/${id}`);
  }

  async updateBOM(id: string, data: Partial<BOMData>): Promise<ApiResponse<BOMData>> {
    return apiClient.put(`/bom/${id}`, data);
  }

  async deleteBOM(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete(`/bom/${id}`);
  }

  async exportBOM(id: string, format: 'csv' | 'excel' | 'pdf' = 'csv'): Promise<void> {
    return apiClient.download(`/bom/${id}/export?format=${format}`, `BOM_${id}.${format}`);
  }

  // 处理状态相关API
  async getProcessingStatus(id: string): Promise<ApiResponse<ProcessingStatus>> {
    return apiClient.get(`/processing/${id}`);
  }

  async getProcessingHistory(params?: {
    page?: number;
    limit?: number;
    status?: string;
    type?: string;
  }): Promise<ApiResponse<{ items: ProcessingStatus[]; total: number; page: number; limit: number }>> {
    return apiClient.get('/processing', { params });
  }

  async cancelProcessing(id: string): Promise<ApiResponse<void>> {
    return apiClient.post(`/processing/${id}/cancel`);
  }

  // 统计数据API
  async getDashboardStats(): Promise<ApiResponse<{
    today_processed: number;
    contours_recognized: number;
    materials_calculated: number;
    cost_saved: number;
    processing_queue: number;
    processing_active: number;
    processing_completed: number;
  }>> {
    return apiClient.get('/stats/dashboard');
  }

  async getRecentActivity(limit: number = 10): Promise<ApiResponse<Array<{
    id: string;
    type: 'upload' | 'process' | 'generate' | 'export';
    title: string;
    description: string;
    status: 'success' | 'warning' | 'error' | 'info';
    timestamp: string;
    metadata?: Record<string, any>;
  }>>> {
    return apiClient.get('/stats/recent-activity', { params: { limit } });
  }

  async getProcessingMetrics(): Promise<ApiResponse<{
    queue_count: number;
    processing_count: number;
    completed_count: number;
    error_count: number;
    average_processing_time: number;
    success_rate: number;
  }>> {
    return apiClient.get('/stats/processing-metrics');
  }

  // 物料计算相关API
  async getModuleInfo(moduleId?: string): Promise<ApiResponse<{
    height: number;
    floor_area: number;
    wall_area: number;
    ceiling_area: number;
    source: string;
  }>> {
    const params = moduleId ? { module_id: moduleId } : {};
    return apiClient.get('/material/module-info', { params });
  }

  async generateMaterialBOM(data: {
    module_data: {
      height: number;
      floor_area: number;
      wall_area: number;
      ceiling_area: number;
    };
    construction_practices: Record<string, any>;
    room_type?: string;
    debug?: boolean;
  }): Promise<ApiResponse<{
    materials: Array<{
      name: string;
      specification: string;
      quantity: number;
      unit: string;
      category: string;
      layer_type: string;
      notes?: string;
    }>;
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
    summary: {
      total_items: number;
      categories: string[];
    };
    processing_info: {
      timestamp: string;
      processing_time: number;
    };
  }>> {
    return apiClient.post('/material/generate-bom', data);
  }

  async materialHealthCheck(): Promise<ApiResponse<{
    service: string;
    status: string;
    timestamp: string;
  }>> {
    return apiClient.get('/material/health');
  }

  // 系统配置API
  async getSystemConfig(): Promise<ApiResponse<{
    max_file_size: number;
    supported_formats: string[];
    processing_algorithms: string[];
    material_categories: string[];
    construction_methods: string[];
  }>> {
    return apiClient.get('/config/system');
  }

  async updateSystemConfig(config: Record<string, any>): Promise<ApiResponse<void>> {
    return apiClient.put('/config/system', config);
  }

  // 健康检查API
  async healthCheck(): Promise<ApiResponse<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: Record<string, 'up' | 'down'>;
    version: string;
    uptime: number;
  }>> {
    return apiClient.get('/health');
  }

  // 模块识别健康检查
  async moduleHealthCheck(): Promise<ApiResponse<{
    status: string;
    message: string;
    dependencies: Record<string, any>;
  }>> {
    return apiClient.get('/module/health');
  }

  // 轮廓处理与模块识别
  async processContour(request: ModuleIdentificationRequest): Promise<ApiResponse<ModuleIdentificationResult>> {
    const formData = new FormData();
    formData.append('image', request.image);
    
    // 添加JSON数据文件（如果有）
    if (request.json_data) {
      formData.append('json_data', request.json_data);
    }
    
    // 添加可选参数
    if (request.confidence_threshold !== undefined) {
      formData.append('confidence_threshold', request.confidence_threshold.toString());
    }
    
    if (request.debug !== undefined) {
      formData.append('debug', request.debug.toString());
    }

    // 调用后端的轮廓处理端点，该端点现在也处理模块识别
    return apiClient.post('/module/process-contour', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}

// 创建BOM服务实例
export const bomService = new BOMService();

// 导出类型和实例
export default bomService;
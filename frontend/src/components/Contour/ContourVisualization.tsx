import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  RotateCw, 
  ZoomIn, 
  ZoomOut, 
  Move3D, 
  Grid3X3,
  Download,
  Settings,
  Box
} from 'lucide-react';
import { ContourData as BackendContourData, ContourInfo } from '../../services/bomService';

interface ContourPoint {
  x: number;
  y: number;
  z?: number;
}

interface LegacyContourData {
  id: string;
  name: string;
  points: ContourPoint[];
  area: number;
  perimeter: number;
  height?: number;
  material?: string;
  unit?: string;
  edge_lengths?: number[];
  num_points?: number;
}

interface ContourVisualizationProps {
  // 支持后端轮廓数据
  contourInfo?: ContourInfo;
  // 用户输入的高度
  modelHeight?: number;
  // 兼容旧的数据格式
  data?: LegacyContourData;
  mode?: '2d' | '3d';
  showGrid?: boolean;
  showMeasurements?: boolean;
  // 3D模型生成控制
  enable3DGeneration?: boolean;
  onHeightChange?: (height: number) => void;
}

const ContourVisualization: React.FC<ContourVisualizationProps> = ({
  contourInfo,
  modelHeight = 2950,
  data,
  mode = '3d',
  showGrid = true,
  showMeasurements = true,
  enable3DGeneration = true,
  onHeightChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>(mode);
  const [viewAngle, setViewAngle] = useState<'top' | 'side' | 'front' | 'isometric'>('top');
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState({ x: 30, y: 45, z: 0 }); // 默认等轴测视图
  const [isAnimating, setIsAnimating] = useState(false);
  const [showGridState, setShowGrid] = useState(showGrid);
  const [showMeasurementsState, setShowMeasurements] = useState(showMeasurements);
  const [currentHeight, setCurrentHeight] = useState(modelHeight);
  // 高度输入框字符串，支持占位符0且输入时移除前导0
  const [heightInput, setHeightInput] = useState<string>(
    (Number.isFinite(modelHeight) ? String(modelHeight) : '')
  );

  // 单位转换（显示使用米与平方米）
  const toMeters = (length: number, unit?: string) => {
    if (!length && length !== 0) return 0;
    return unit === 'mm' ? length / 1000 : length;
  };
  const toSquareMeters = (area: number, unit?: string) => {
    if (!area && area !== 0) return 0;
    return unit === 'mm' ? area / 1_000_000 : area;
  };

  // 测量标注统一以毫米显示
  const toMillimeters = (length: number, unit?: string) => {
    if (!Number.isFinite(length)) return 0;
    if (unit === 'mm') return length;
    if (unit === 'm') return length * 1000;
    return length * 1000; // 默认按米处理
  };

  // 处理高度变化
  const handleHeightChange = (newHeight: number) => {
    setCurrentHeight(newHeight);
    setHeightInput(String(newHeight));
    onHeightChange?.(newHeight);
  };

  // 处理轮廓数据 - 支持后端数据和兼容旧格式
  const processedContours = useMemo(() => {
    if (contourInfo && contourInfo.contours.length > 0) {
      // 使用后端返回的轮廓数据
      return contourInfo.contours.map((contour: BackendContourData) => ({
        id: contour.id,
        name: `轮廓 ${contour.id}`,
        points: contour.geometry.points.map(([x, y]: [number, number]) => ({ x, y, z: 0 })),
        area: contour.geometry.area,
        perimeter: contour.geometry.perimeter,
        edge_lengths: contour.geometry.edge_lengths,
        num_points: contour.geometry.num_points,
        height: currentHeight, // 使用用户输入的高度
        material: '建筑材料',
        unit: contour.geometry.unit
      }));
    } else if (data) {
      // 兼容旧的数据格式
      return [{
        ...data,
        height: currentHeight,
        edge_lengths: data.edge_lengths || [],
        num_points: data.num_points || data.points?.length || 0,
        unit: data.unit || 'mm'
      }];
    } else {
      // 默认示例数据
      return [{
        id: 'sample-1',
        name: '建筑轮廓A',
        points: [
          { x: 50, y: 50, z: 0 },
          { x: 6050, y: 50, z: 0 },
          { x: 6050, y: 3050, z: 0 },
          { x: 50, y: 3050, z: 0 }
        ],
        area: 24000000,
        perimeter: 22000,
        height: currentHeight,
        material: '钢筋混凝土',
        unit: 'mm',
        edge_lengths: [6000, 3000, 6000, 3000],
        num_points: 4
      }];
    }
  }, [contourInfo, data, currentHeight]);

  // 主要显示的轮廓数据（取第一个）
  const mainContour = processedContours[0];

  // 计算模型的边界框和缩放比例
  const modelBounds = useMemo(() => {
    if (!mainContour || !mainContour.points.length) return { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0 };
    
    const xs = mainContour.points.map((p: any) => p.x);
    const ys = mainContour.points.map((p: any) => p.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    
    return {
      minX,
      maxX,
      minY,
      maxY,
      width: maxX - minX,
      height: maxY - minY
    };
  }, [mainContour]);

  // 计算投影后的边界（3D等轴视角）用于精确居中与缩放
  const projectedBounds = useMemo(() => {
    if (!mainContour || !mainContour.points.length) {
      return { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0, centerX: 0, centerY: 0 };
    }
    const height = mainContour.height || 3000;
    const angleX = rotation.x * Math.PI / 180;
    const angleY = rotation.y * Math.PI / 180;
    const project3D = (x: number, y: number, z: number) => {
      const projX = x * Math.cos(angleY) + y * Math.sin(angleY);
      const projY = -x * Math.sin(angleY) * Math.sin(angleX) + y * Math.cos(angleY) * Math.sin(angleX) + z * Math.cos(angleX);
      return { x: projX, y: projY };
    };
    const projected: { x: number; y: number }[] = [];
    for (const p of mainContour.points) {
      const b = project3D(p.x, p.y, 0);
      const t = project3D(p.x, p.y, height);
      projected.push(b, t);
    }
    const xs = projected.map(pt => pt.x);
    const ys = projected.map(pt => pt.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const width = maxX - minX;
    const height2 = maxY - minY;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    return { minX, maxX, minY, maxY, width, height: height2, centerX, centerY };
  }, [mainContour, rotation]);

  // 计算适合画布的缩放比例 - 优化算法确保模型完全可见
  const calculateScale = useCallback((canvasWidth: number, canvasHeight: number) => {
    const padding = 80; // 边距，确保标注信息也能显示
    const availableWidth = canvasWidth - padding * 2;
    const availableHeight = canvasHeight - padding * 2;

    const bounds = viewMode === '3d' ? projectedBounds : { width: modelBounds.width, height: modelBounds.height };
    const effectiveWidth = Math.max(bounds.width, 1);
    const effectiveHeight = Math.max(bounds.height, 1);

    const scaleX = availableWidth / effectiveWidth;
    const scaleY = availableHeight / effectiveHeight;
    return Math.min(scaleX, scaleY, 1.0);
  }, [modelBounds, projectedBounds, viewMode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    canvas.width = 600;
    canvas.height = 400;

    const drawVisualization = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // 计算自动缩放比例
      const autoScale = calculateScale(canvas.width, canvas.height);
      const finalScale = autoScale * zoom;
      
      // 计算模型中心点（3D模式使用投影后的中心）
      const centerX = viewMode === '3d'
        ? projectedBounds.centerX
        : (modelBounds.minX + modelBounds.maxX) / 2;
      const centerY = viewMode === '3d'
        ? projectedBounds.centerY
        : (modelBounds.minY + modelBounds.maxY) / 2;
      
      // 设置变换矩阵 - 确保模型永远居中显示
      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.scale(finalScale, finalScale);
      ctx.translate(-centerX, -centerY);

      // 绘制网格
      if (showGridState) {
        drawGrid(ctx, centerX, centerY);
      }

      // 绘制轮廓
      if (viewMode === '3d') {
        draw3DContour(ctx, mainContour);
      } else {
        draw2DContour(ctx, mainContour);
      }

      // 绘制测量标注
      if (showMeasurementsState) {
        drawMeasurements(ctx, mainContour);
      }

      ctx.restore();
      // 绘制右下角的三维坐标轴覆盖层
      drawAxesOverlay(ctx);
    };

    const drawGrid = (ctx: CanvasRenderingContext2D, centerX: number, centerY: number) => {
      ctx.strokeStyle = '#1a365d';
      ctx.lineWidth = 0.5;
      ctx.globalAlpha = 0.3;

      const gridSize = 500; // 500mm网格
      const gridRange = Math.max(modelBounds.width, modelBounds.height) * 0.6;

      // 计算网格起始点，确保网格对齐
      const startX = Math.floor((centerX - gridRange) / gridSize) * gridSize;
      const endX = Math.ceil((centerX + gridRange) / gridSize) * gridSize;
      const startY = Math.floor((centerY - gridRange) / gridSize) * gridSize;
      const endY = Math.ceil((centerY + gridRange) / gridSize) * gridSize;

      // 绘制垂直线
      for (let x = startX; x <= endX; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, startY);
        ctx.lineTo(x, endY);
        ctx.stroke();
      }

      // 绘制水平线
      for (let y = startY; y <= endY; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(startX, y);
        ctx.lineTo(endX, y);
        ctx.stroke();
      }

      ctx.globalAlpha = 1;
    };

    const draw2DContour = (ctx: CanvasRenderingContext2D, contour: typeof mainContour) => {
      if (!contour) return;
      
      const points = contour.points;
      
      // 绘制轮廓填充
      ctx.fillStyle = 'rgba(0, 245, 255, 0.1)';
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.closePath();
      ctx.fill();

      // 绘制轮廓边框
      ctx.strokeStyle = '#00F5FF';
      ctx.lineWidth = 2;
      ctx.shadowBlur = 10;
      ctx.shadowColor = '#00F5FF';
      ctx.stroke();

      // 绘制关键点
      points.forEach((point: any, index: number) => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#00F5FF';
        ctx.fill();
        
        // 点标签
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '14px Inter';
        ctx.fillText(`P${index + 1}`, point.x + 5, point.y - 5);
      });
    };

    const draw3DContour = (ctx: CanvasRenderingContext2D, contour: typeof mainContour) => {
      if (!contour) return;
      const points = contour.points;
      // 以Z轴方向拉伸高度，优先使用当前输入高度
      const height = (currentHeight ?? contour.height ?? 3000);
      
      // 3D投影参数
      const angleX = rotation.x * Math.PI / 180;
      const angleY = rotation.y * Math.PI / 180;
      
      // 投影函数 - 修正为更直观的Z轴高度表示
      const project3D = (x: number, y: number, z: number) => {
        // 标准等轴测投影：Z轴为垂直高度
        const projX = x * Math.cos(angleY) + y * Math.sin(angleY);
        const projY = -x * Math.sin(angleY) * Math.sin(angleX) + y * Math.cos(angleY) * Math.sin(angleX) + z * Math.cos(angleX);
        return { x: projX, y: projY };
      };

      // 绘制底面
      ctx.fillStyle = 'rgba(0, 245, 255, 0.2)';
      ctx.strokeStyle = '#00F5FF';
      ctx.lineWidth = 2;
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#00F5FF';

      ctx.beginPath();
      const firstPoint = project3D(points[0].x, points[0].y, 0);
      ctx.moveTo(firstPoint.x, firstPoint.y);
      
      for (let i = 1; i < points.length; i++) {
        const projPoint = project3D(points[i].x, points[i].y, 0);
        ctx.lineTo(projPoint.x, projPoint.y);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // 绘制顶面
      ctx.fillStyle = 'rgba(0, 245, 255, 0.3)';
      ctx.strokeStyle = '#00BFFF';
      
      ctx.beginPath();
      const firstTopPoint = project3D(points[0].x, points[0].y, height);
      ctx.moveTo(firstTopPoint.x, firstTopPoint.y);
      
      for (let i = 1; i < points.length; i++) {
        const projPoint = project3D(points[i].x, points[i].y, height);
        ctx.lineTo(projPoint.x, projPoint.y);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // 绘制侧面
      ctx.fillStyle = 'rgba(0, 191, 255, 0.15)';
      ctx.strokeStyle = '#0080FF';
      ctx.lineWidth = 1;

      for (let i = 0; i < points.length; i++) {
        const nextIndex = (i + 1) % points.length;
        
        const bottomCurrent = project3D(points[i].x, points[i].y, 0);
        const bottomNext = project3D(points[nextIndex].x, points[nextIndex].y, 0);
        const topCurrent = project3D(points[i].x, points[i].y, height);
        const topNext = project3D(points[nextIndex].x, points[nextIndex].y, height);

        ctx.beginPath();
        ctx.moveTo(bottomCurrent.x, bottomCurrent.y);
        ctx.lineTo(bottomNext.x, bottomNext.y);
        ctx.lineTo(topNext.x, topNext.y);
        ctx.lineTo(topCurrent.x, topCurrent.y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }

      // 绘制顶点
      points.forEach((point: any, index: number) => {
        const bottomProj = project3D(point.x, point.y, 0);
        const topProj = project3D(point.x, point.y, height);
        
        // 底部点
        ctx.beginPath();
        ctx.arc(bottomProj.x, bottomProj.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#00F5FF';
        ctx.fill();
        
        // 顶部点
        ctx.beginPath();
        ctx.arc(topProj.x, topProj.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#00BFFF';
        ctx.fill();
        
        // 连接线
        ctx.strokeStyle = '#0080FF';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(bottomProj.x, bottomProj.y);
        ctx.lineTo(topProj.x, topProj.y);
        ctx.stroke();
      });
    };

    // 绘制三维坐标轴（覆盖层，固定在画布右下角）
    const drawAxesOverlay = (ctx: CanvasRenderingContext2D) => {
      if (viewMode !== '3d') return;
      const angleX = rotation.x * Math.PI / 180;
      const angleY = rotation.y * Math.PI / 180;
      const projectDir = (x: number, y: number, z: number) => {
        const projX = x * Math.cos(angleY) + y * Math.sin(angleY);
        const projY = -x * Math.sin(angleY) * Math.sin(angleX) + y * Math.cos(angleY) * Math.sin(angleX) + z * Math.cos(angleX);
        return { x: projX, y: projY };
      };

      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      const margin = 18;
      const len = 42;
      const baseX = ctx.canvas.width - margin - len;
      const baseY = ctx.canvas.height - margin - len;

      const normalize = (v: { x: number; y: number }) => {
        const s = Math.sqrt(v.x * v.x + v.y * v.y) || 1;
        return { x: v.x / s, y: v.y / s };
      };
      const xDir = normalize(projectDir(1, 0, 0));
      const yDir = normalize(projectDir(0, 1, 0));
      const zDir = normalize(projectDir(0, 0, 1));

      ctx.lineWidth = 2;
      ctx.strokeStyle = '#ff4d4f';
      ctx.beginPath();
      ctx.moveTo(baseX, baseY);
      ctx.lineTo(baseX + xDir.x * len, baseY - xDir.y * len);
      ctx.stroke();

      ctx.strokeStyle = '#52c41a';
      ctx.beginPath();
      ctx.moveTo(baseX, baseY);
      ctx.lineTo(baseX + yDir.x * len, baseY - yDir.y * len);
      ctx.stroke();

      ctx.strokeStyle = '#1677ff';
      ctx.beginPath();
      ctx.moveTo(baseX, baseY);
      ctx.lineTo(baseX + zDir.x * len, baseY - zDir.y * len);
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.font = '12px Inter';
      ctx.fillText('X', baseX + xDir.x * len + 6, baseY - xDir.y * len + 2);
      ctx.fillText('Y', baseX + yDir.x * len + 6, baseY - yDir.y * len + 2);
      ctx.fillText('Z', baseX + zDir.x * len + 6, baseY - zDir.y * len + 2);

      ctx.restore();
    };

    const drawMeasurements = (ctx: CanvasRenderingContext2D, contour: typeof mainContour) => {
      if (!contour) return;
      // 等轴视图不显示测量标注
      if (viewMode === '3d' && viewAngle === 'isometric') return;
      // 3D模式下的投影函数（与draw3DContour一致）
      let projectForMeasure: (x: number, y: number, z: number) => { x: number; y: number } = (x, y, z) => ({ x, y });
      if (viewMode === '3d') {
        const angleX = rotation.x * Math.PI / 180;
        const angleY = rotation.y * Math.PI / 180;
        projectForMeasure = (x: number, y: number, z: number) => {
          const projX = x * Math.cos(angleY) + y * Math.sin(angleY);
          const projY = -x * Math.sin(angleY) * Math.sin(angleX) + y * Math.cos(angleY) * Math.sin(angleX) + z * Math.cos(angleX);
          return { x: projX, y: projY };
        };
      }
      // 基于画布尺寸的自适应字体与偏移（按屏幕像素固定），抵消当前缩放以保证可读性
      const baseDim = Math.min(ctx.canvas.width, ctx.canvas.height);
      const transform = ctx.getTransform();
      const currentScale = Math.max(transform.a || 1, transform.d || 1);
      // 目标屏幕像素字号：取当前基础的0.6倍
      const targetFontPx = Math.round(Math.min(Math.max(baseDim * 0.08, 26), 72));
      const targetFontPxScaled = Math.max(12, Math.round(targetFontPx * 0.6));
      const targetLabelOffsetPx = Math.round(targetFontPxScaled * 1.6);

      // 转换为世界坐标系的字号/偏移，抵消ctx.scale带来的缩放
      const worldFontSize = targetFontPxScaled / currentScale;
      const worldLabelOffset = targetLabelOffsetPx / currentScale;

      ctx.strokeStyle = '#FFFFFF';
      ctx.fillStyle = '#FFFFFF';
      ctx.lineWidth = 1 / currentScale; // 保持测量线宽约为1屏幕像素
      ctx.font = `${worldFontSize}px Inter`;
      ctx.shadowBlur = 0;

      // 绘制尺寸标注
      const points = contour.points;

      // 计算用于“外侧”判断的屏幕空间多边形质心
      const screenPoints = points.map((p: any) => {
        if (viewMode === '3d') {
          const zUse = viewAngle === 'top' ? (currentHeight || 0) : 0; // 俯视图使用顶部面
          return projectForMeasure(p.x, p.y, zUse);
        }
        return { x: p.x, y: p.y };
      });
      const centroid = screenPoints.reduce(
        (acc: { x: number; y: number }, sp: any) => ({ x: acc.x + sp.x, y: acc.y + sp.y }),
        { x: 0, y: 0 }
      );
      centroid.x /= Math.max(screenPoints.length, 1);
      centroid.y /= Math.max(screenPoints.length, 1);
      
      // 侧视/正视仅显示模型高度，不标注当前面的周边边长
      const skipPerimeterInSideOrFront = viewMode === '3d' && (viewAngle === 'front' || viewAngle === 'side');
      for (let i = 0; i < points.length && !skipPerimeterInSideOrFront; i++) {
        const current = points[i];
        const next = points[(i + 1) % points.length];

        // 边长（按毫米显示）
        const worldDistance = Math.sqrt(
          Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
        );
        const distanceMM = toMillimeters(worldDistance, contour.unit);

        // 标注位置与偏移（根据视角使用投影坐标或二维坐标）
        let pCurrent = { x: current.x, y: current.y };
        let pNext = { x: next.x, y: next.y };
        if (viewMode === '3d') {
          const zUse = viewAngle === 'top' ? (currentHeight || 0) : 0; // 俯视图使用顶部面，其他使用底部面
          pCurrent = projectForMeasure(current.x, current.y, zUse);
          pNext = projectForMeasure(next.x, next.y, zUse);
        }

        const midX = (pCurrent.x + pNext.x) / 2;
        const midY = (pCurrent.y + pNext.y) / 2;

        const dx = pNext.x - pCurrent.x;
        const dy = pNext.y - pCurrent.y;
        const screenLength = Math.sqrt(dx * dx + dy * dy) || 1;
        // 计算法线方向，并根据质心方向判定外侧（指向远离质心）
        let nX = -dy / screenLength;
        let nY = dx / screenLength;
        const toCentroidX = centroid.x - midX;
        const toCentroidY = centroid.y - midY;
        const dot = nX * toCentroidX + nY * toCentroidY;
        if (dot > 0) { // 指向质心则翻转
          nX = -nX;
          nY = -nY;
        }
        const offsetX = nX * worldLabelOffset;
        const offsetY = nY * worldLabelOffset;

        const labelX = midX + offsetX;
        const labelY = midY + offsetY;

        // 不需要标记线条（去除连接线）

        // 边长文字（mm，两位小数）
        ctx.fillStyle = '#FFFFFF';
        ctx.font = `${worldFontSize}px Inter`;
        ctx.fillText(`${Number(distanceMM).toFixed(2)} mm`, labelX - Math.round(worldFontSize * 1.2), labelY + Math.round(worldFontSize * 0.3));
      }

      // 在侧视/正视视角标注垂直边高度（mm）
      if (viewMode === '3d' && (viewAngle === 'side' || viewAngle === 'front') && currentHeight) {
        points.forEach((point: any) => {
          const bottomProj = projectForMeasure(point.x, point.y, 0);
          const topProj = projectForMeasure(point.x, point.y, currentHeight);
          const midX = (bottomProj.x + topProj.x) / 2;
          const midY = (bottomProj.y + topProj.y) / 2;
          const dx = topProj.x - bottomProj.x;
          const dy = topProj.y - bottomProj.y;
          const len = Math.sqrt(dx * dx + dy * dy) || 1;
          // 垂直边的外侧方向：同样依据质心远离方向
          let nXv = -dy / len;
          let nYv = dx / len;
          const toCentroidXv = centroid.x - midX;
          const toCentroidYv = centroid.y - midY;
          const dotv = nXv * toCentroidXv + nYv * toCentroidYv;
          if (dotv > 0) {
            nXv = -nXv;
            nYv = -nYv;
          }
          const offsetX = nXv * Math.round(worldLabelOffset * 0.8);
          const offsetY = nYv * Math.round(worldLabelOffset * 0.8);
          const labelX = midX + offsetX;
          const labelY = midY + offsetY;
          // 不需要标记线条（去除连接线）
          ctx.fillStyle = '#FFFFFF';
          ctx.font = `${worldFontSize}px Inter`;
          ctx.fillText(`${Number(toMillimeters(currentHeight, 'mm')).toFixed(2)} mm`, labelX - Math.round(worldFontSize * 1.2), labelY + Math.round(worldFontSize * 0.3));
        });
      }
    };

    drawVisualization();

    // 自动旋转动画
    if (isAnimating && viewMode === '3d') {
      const animationId = setInterval(() => {
        setRotation(prev => ({
          ...prev,
          y: (prev.y + 1) % 360
        }));
      }, 50);

      return () => clearInterval(animationId);
    }
  }, [viewMode, rotation, zoom, showGridState, showMeasurementsState, isAnimating, mainContour, modelBounds, calculateScale]);

  const handleRotate = () => {
    setRotation(prev => ({
      ...prev,
      y: (prev.y + 45) % 360
    }));
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.5));
  };

  const toggleAnimation = () => {
    setIsAnimating(!isAnimating);
  };

  const handleViewAngleChange = (angle: 'top' | 'side' | 'front' | 'isometric') => {
    setViewAngle(angle);
    
    // 根据视角设置旋转角度，参考building_streamlit_3d.py的实现
    switch (angle) {
      case 'top': // 俯视图 (类似view_xy)
        if (viewMode === '3d') setRotation({ x: 0, y: 0, z: 0 });
        break;
      case 'side': // 侧视图 (类似view_xz)
        if (viewMode === '3d') setRotation({ x: 90, y: 0, z: 0 });
        break;
      case 'front': // 正视图 (类似view_yz)
        if (viewMode === '3d') setRotation({ x: 0, y: 90, z: 0 });
        break;
      case 'isometric': // 等轴视图
        setRotation({ x: 30, y: 45, z: 0 });
        break;
    }
  };

  // 当切换到3D模式时，自动设置为等轴测视图
  useEffect(() => {
    if (viewMode === '3d') {
      setRotation({ x: 30, y: 45, z: 0 }); // 等轴测视图
      setViewAngle('isometric');
    }
  }, [viewMode]);

  return (
    <div className="glass-effect rounded-xl p-6 border border-white/20 h-full min-h-[400px]">
      {/* 标题与2D/3D切换 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">模块可视化</h3>
          <div className="flex bg-glass-blue rounded-lg p-1 border border-neon-blue/30">
            <motion.button
              className={`px-3 py-1 rounded text-sm transition-all duration-300 ${
                viewMode === '2d' 
                  ? 'bg-neon-blue text-black' 
                  : 'text-gray-300 hover:text-white'
              }`}
              onClick={() => { setViewMode('2d'); setViewAngle('top'); }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              2D
            </motion.button>
            <motion.button
              className={`px-3 py-1 rounded text-sm transition-all duration-300 ${
                viewMode === '3d' 
                  ? 'bg-neon-blue text-black' 
                  : 'text-gray-300 hover:text-white'
              }`}
              onClick={() => setViewMode('3d')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              3D
            </motion.button>
          </div>
        </div>

        {/* 工具栏 */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          {/* 3D模型高度（置于最前，位于缩放组左侧，仅3D显示） */}
          {viewMode === '3d' && enable3DGeneration && (
            <div className="flex items-center gap-2 p-2 rounded-lg glass-effect border border-neon-purple/30 h-8">
              <Box className="w-4 h-4 text-neon-purple" />
              <span className="text-xs text-gray-300">高度:</span>
              <input
                type="number"
                min="1"
                max="100000"
                placeholder="0"
                value={heightInput}
                onFocus={() => { if (heightInput === '0') setHeightInput(''); }}
                onChange={(e) => {
                  const raw = e.target.value;
                  // 输入时移除前导0，避免出现“0后面加数字”的情况
                  const cleaned = raw.length > 1 && raw.startsWith('0') ? raw.replace(/^0+/, '') : raw;
                  setHeightInput(cleaned);
                  const num = Number(cleaned);
                  if (!Number.isNaN(num)) {
                    setCurrentHeight(num);
                    onHeightChange?.(num);
                  }
                }}
                className="h-6 w-20 px-2 text-xs bg-gray-700 border border-gray-600 rounded text-white"
              />
              <span className="text-xs text-gray-400">mm</span>
            </div>
          )}

          {/* 缩放控制 */}
          <div className="flex items-center space-x-1">
            <motion.button
              className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
              onClick={handleZoomIn}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              title="放大"
            >
              <ZoomIn className="w-4 h-4 text-gray-300" />
            </motion.button>
            
            <motion.button
              className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
              onClick={handleZoomOut}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              title="缩小"
            >
              <ZoomOut className="w-4 h-4 text-gray-300" />
            </motion.button>
          </div>

          {/* 3D控制（已将高度组件前移到缩放组左侧） */}
          {viewMode === '3d' && (
            <div className="flex items-center space-x-1">
              <motion.button
                className="p-2 rounded-lg glass-effect hover:bg-white/20 transition-all duration-300"
                onClick={handleRotate}
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.95 }}
                title="旋转"
              >
                <RotateCw className="w-4 h-4 text-gray-300" />
              </motion.button>

              <motion.button
                className={`p-2 rounded-lg glass-effect transition-all duration-300 ${
                  isAnimating 
                    ? 'bg-neon-green/20 text-neon-green' 
                    : 'hover:bg-white/20 text-gray-300'
                }`}
                onClick={toggleAnimation}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                title="自动旋转"
              >
                <Move3D className="w-4 h-4" />
              </motion.button>
            </div>
          )}

          {/* 显示控制 */}
          <div className="flex items-center space-x-1">
            <motion.button
              className={`p-2 rounded-lg glass-effect transition-all duration-300 ${
                showGridState 
                  ? 'bg-neon-cyan/20 text-neon-cyan' 
                  : 'hover:bg-white/20 text-gray-300'
              }`}
              onClick={() => setShowGrid(!showGridState)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              title="显示网格"
            >
              <Grid3X3 className="w-4 h-4" />
            </motion.button>

            <motion.button
              className={`p-2 rounded-lg glass-effect transition-all duration-300 ${
                showMeasurementsState 
                  ? 'bg-neon-cyan/20 text-neon-cyan' 
                  : 'hover:bg-white/20 text-gray-300'
              }`}
              onClick={() => setShowMeasurements(!showMeasurementsState)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              title="显示测量"
            >
              <Settings className="w-4 h-4" />
            </motion.button>
          </div>

          {/* 操作按钮（移除下载） */}
        </div>
      </div>

      {/* 可视化画布 */}
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

        {/* 状态指示器 */}
        <div className="absolute top-4 left-4">
          <div className="flex items-center space-x-2 bg-glass-blue rounded-lg px-3 py-2 border border-neon-blue/30">
            <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">实时渲染</span>
          </div>
        </div>


      </div>

      {/* 数据信息面板 */}
      <div className="mt-4 space-y-4">
        {/* 主要轮廓数据 */}
        {viewMode === '2d' ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-purple/30">
              <div className="text-sm text-gray-400">顶点数</div>
              <div className="text-lg font-bold text-neon-purple">
                {mainContour?.num_points || mainContour?.points?.length || 0}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-cyan/30">
              <div className="text-sm text-gray-400">周长</div>
              <div className="text-lg font-bold text-neon-cyan">
                {toMeters(mainContour?.perimeter || 0, mainContour?.unit).toFixed(2)} m
              </div>
            </div>
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-blue/30">
              <div className="text-sm text-gray-400">面积</div>
              <div className="text-lg font-bold text-neon-blue">
                {Number(toSquareMeters(mainContour?.area || 0, mainContour?.unit)).toFixed(2)} ㎡
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-purple/30">
              <div className="text-sm text-gray-400">模块高度</div>
              <div className="text-lg font-bold text-neon-purple">
                {currentHeight} mm
              </div>
            </div>
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-blue/30">
              <div className="text-sm text-gray-400">模块面积</div>
              <div className="text-lg font-bold text-neon-blue">
                {Number(toSquareMeters(mainContour?.area || 0, mainContour?.unit)).toFixed(2)} ㎡
              </div>
            </div>
            <div className="p-3 rounded-lg bg-glass-blue border border-neon-green/30">
              <div className="text-sm text-gray-400">模块体积</div>
              <div className="text-lg font-bold text-neon-green">
                {(
                  Number(toSquareMeters(mainContour?.area || 0, mainContour?.unit)) *
                  (currentHeight / 1000)
                ).toFixed(2)}{' '}
                m³
              </div>
            </div>
          </div>
        )}

        {/* 汇总信息 */}
        {contourInfo?.summary && (
          <div className="p-3 rounded-lg bg-glass-blue border border-neon-green/30">
            <div className="text-sm text-gray-400 mb-2">轮廓汇总</div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">总轮廓数: </span>
                <span className="text-neon-green font-semibold">
                  {contourInfo.summary.total_contours}
                </span>
              </div>
              <div>
                <span className="text-gray-400">总面积: </span>
                <span className="text-neon-green font-semibold">
                  {Number(toSquareMeters(contourInfo.summary.total_area || 0, contourInfo.summary.unit)).toFixed(2)} ㎡
                </span>
              </div>
              <div>
                <span className="text-gray-400">总周长: </span>
                <span className="text-neon-green font-semibold">
                  {toMeters(contourInfo.summary.total_perimeter || 0, contourInfo.summary.unit).toFixed(2)} m
                </span>
              </div>
            </div>
          </div>
        )}

        {/* 边长详情面板已移除，改为在画布实时标注尺寸 */}
      </div>
    </div>
  );
};

export default ContourVisualization;
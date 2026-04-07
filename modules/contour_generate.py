"""
图像分割模型轮廓提取和可视化模块
实现从YOLO分割模型中提取轮廓并进行可视化
"""

import matplotlib.pyplot as plt
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from ultralytics import YOLO
import os
import json
from pathlib import Path
import glob
import torch
import gc  # 垃圾回收

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

class ContourGenerator:
    """轮廓生成器类"""
    
    def __init__(self, model_path):
        """
        初始化轮廓生成器
        
        Args:
            model_path (str): YOLO分割模型路径
        """
        self.model_path = model_path
        self.model = None
        self.load_model()
    
    def load_model(self):
        """加载YOLO分割模型"""
        try:
            print(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            print("模型加载成功!")
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise
    
    def segment_image(self, image_path):
        """
        对图像进行分割
        
        Args:
            image_path (str): 图像路径
            
        Returns:
            tuple: (原图, 分割掩码)
        """
        # 读取原图
        original_image = cv2.imread(image_path)
        if original_image is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        # 检查图像尺寸，如果过大则进行缩放
        height, width = original_image.shape[:2]
        max_size = 1024  # 最大尺寸限制 1280,1024
        scale_factor = 1.0
        
        if height > max_size or width > max_size:
            print(f"图像尺寸过大 ({width}x{height})，正在缩放...")
            scale_factor = max_size / max(height, width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            original_image = cv2.resize(original_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"缩放后尺寸: {new_width}x{new_height}")
        
        # 保存缩放因子供后续使用
        self.last_scale_factor = scale_factor
        
        original_image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        
        # 进行分割预测
        results = self.model(image_path)
        
        # 提取分割掩码
        if results[0].masks is not None:
            # 获取第一个实例的掩码
            mask = results[0].masks.data[0].cpu().numpy()
            # 将掩码调整为原图尺寸
            mask_resized = cv2.resize(mask, (original_image.shape[1], original_image.shape[0]))
            # 二值化掩码
            mask_binary = (mask_resized > 0.5).astype(np.uint8) * 255
        else:
            print(f"警告: 图像 {image_path} 未检测到分割掩码")
            mask_binary = np.zeros((original_image.shape[0], original_image.shape[1]), dtype=np.uint8)
        
        return original_image_rgb, mask_binary
    
    def extract_contours(self, mask):
        """
        从分割掩码中提取外轮廓
        
        Args:
            mask (np.ndarray): 二值化掩码
            
        Returns:
            list: 轮廓列表
        """
        # 使用OpenCV提取轮廓
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print("警告: 未找到轮廓")
            return []
        
        # 选择最大的轮廓作为主要轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 轮廓近似，减少点数
        epsilon = 0.005 * cv2.arcLength(largest_contour, True)  #0.003拐点太多
        approx_contour = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        return [approx_contour]
    
    def visualize_results(self, original_image, mask, contours, save_path=None):
        """
        可视化结果：在同一个原图上显示分割掩码和外轮廓点
        
        Args:
            original_image (np.ndarray): 原图
            mask (np.ndarray): 分割掩码
            contours (list): 轮廓列表
            save_path (str, optional): 保存路径
        """
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # 显示原图
        axes[0].imshow(original_image)
        axes[0].set_title('原图', fontsize=14)
        axes[0].axis('off')
        
        # 显示分割掩码
        axes[1].imshow(original_image)
        # 创建彩色掩码覆盖层
        mask_colored = np.zeros_like(original_image)
        mask_colored[:, :, 0] = mask  # 红色通道
        mask_overlay = cv2.addWeighted(original_image, 0.7, mask_colored, 0.3, 0)
        axes[1].imshow(mask_overlay)
        axes[1].set_title('原图 + 分割掩码', fontsize=14)
        axes[1].axis('off')
        
        # 显示原图 + 掩码 + 轮廓点
        axes[2].imshow(original_image)
        # 添加掩码覆盖层
        axes[2].imshow(mask_overlay)
        
        # 绘制轮廓线和轮廓点
        for contour in contours:
            if len(contour) > 0:
                # 提取轮廓点
                points = contour.reshape(-1, 2)
                
                # 绘制轮廓线（闭合）
                points_closed = np.vstack([points, points[0]])  # 闭合轮廓
                axes[2].plot(points_closed[:, 0], points_closed[:, 1], 'lime', linewidth=1, label='轮廓线')
                
                # 绘制轮廓点
                axes[2].scatter(points[:, 0], points[:, 1], c='yellow', s=10, label='轮廓点', zorder=5)
                
                # 标注点的序号
                for i, (x, y) in enumerate(points):
                    axes[2].annotate(str(i), (x, y), xytext=(5, 5), textcoords='offset points',
                                   fontsize=8, color='white', weight='bold')
        
        axes[2].set_title('原图 + 掩码 + 轮廓线 + 轮廓点', fontsize=14)
        axes[2].axis('off')
        axes[2].legend(loc='upper right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"可视化结果已保存到: {save_path}")
        
    
    def save_contour_data(self, contours, save_path):
        """
        保存轮廓数据到JSON文件
        
        Args:
            contours (list): 轮廓列表
            save_path (str): 保存路径
        """
        contour_data = []
        for i, contour in enumerate(contours):
            points = contour.reshape(-1, 2).tolist()
            contour_info = {
                'contour_id': i,
                'num_points': len(points),
                'points': points,
                'area': float(cv2.contourArea(contour)),
                'perimeter': float(cv2.arcLength(contour, True))
            }
            contour_data.append(contour_info)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(contour_data, f, indent=2, ensure_ascii=False)
        
        print(f"轮廓数据已保存到: {save_path}")
    
    def process_single_image(self, image_path, output_dir=None):
        """
        处理单张图像的完整流程
        
        Args:
            image_path (str): 图像路径
            output_dir (str, optional): 输出目录
            
        Returns:
            tuple: (原图, 掩码, 轮廓)
        """
        print(f"正在处理图像: {image_path}")
        
        # 检查图像是否存在
        if not os.path.exists(image_path):
            raise ValueError(f"图像文件不存在: {image_path}")
        
        # 1. 图像分割
        original_image, mask = self.segment_image(image_path)
        
        # 2. 轮廓提取
        contours = self.extract_contours(mask)
        
        # 3. 可视化
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            image_name = Path(image_path).stem
            viz_path = os.path.join(output_dir, f"{image_name}_contour_visualization.png")
            self.visualize_results(original_image, mask, contours, viz_path)
            
            # 保存轮廓数据
            contour_data_path = os.path.join(output_dir, f"{image_name}_contour_data.json")
            self.save_contour_data(contours, contour_data_path)
        else:
            self.visualize_results(original_image, mask, contours)
        
        return original_image, mask, contours
    
    def process_batch_images(self, image_dir, output_dir=None):
        """
        批量处理图像
        
        Args:
            image_dir (str): 图像目录
            output_dir (str, optional): 输出目录
        """
        # 获取所有PNG图像
        image_paths = glob.glob(os.path.join(image_dir, "*.png"))
        
        if not image_paths:
            print(f"在目录 {image_dir} 中未找到PNG图像")
            return
        
        print(f"找到 {len(image_paths)} 张图像，开始批量处理...")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        for i, image_path in enumerate(image_paths):  # 限制处理前5张图像作为示例
            print(f"\n处理进度: {i+1}/{len(image_paths)}")
            try:
                self.process_single_image(image_path, output_dir)
                
                # 每处理5张图像后进行内存清理
                if (i + 1) % 5 == 0:
                    print("正在清理内存...")
                    gc.collect()  # 强制垃圾回收
                    torch.cuda.empty_cache() if torch.cuda.is_available() else None  # 清理GPU缓存
                    
            except MemoryError as e:
                print(f"内存不足，跳过图像 {image_path}: {e}")
                # 强制内存清理
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                continue
            except Exception as e:
                print(f"处理图像 {image_path} 时出错: {e}")
                continue


def main():
    """主函数"""
    # 模型路径
    model_path = r"E://Github_project//BOM//extract_info//corner_text_modeldetection//training_outputs//contour_segmentation//contour_segmentation_segmentation_20251024_185244//weights//best.pt"
    
    # 图像数据目录
    image_dir = r"E://Github_project//BOM//extract_info//corner_text_modeldetection//contour_detection_data"

    # 输出目录
    output_dir = r"E://Github_project//BOM//extract_info//corner_text_modeldetection//contour_visualization_outputs1"


    
    try:
        # 创建轮廓生成器
        contour_generator = ContourGenerator(model_path)
        
        # 批量处理图像
        contour_generator.process_batch_images(image_dir, output_dir)

        
        print("\n所有图像处理完成!")
        
    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from pathlib import Path
from ultralytics import YOLO
import torch
import argparse
from glob import glob

def save_dimension_detection_results(model_path, input_dir="dimension_detection_data", output_dir="dimension_detection_results", generate_summary=False):
    """
    使用YOLO模型进行dimension检测并保存结果
    
    Args:
        model_path (str): YOLO模型权重路径
        input_dir (str): 输入图像目录
        output_dir (str): 输出目录
        generate_summary (bool): 是否生成detection_summary.json文件，默认为False
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的图像格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
    
    # 获取所有图像文件（大小写扩展去重）
    image_paths_set = set()
    for ext in image_extensions:
        for p in glob(os.path.join(input_dir, ext)):
            image_paths_set.add(os.path.normcase(os.path.abspath(p)))
        for p in glob(os.path.join(input_dir, ext.upper())):
            image_paths_set.add(os.path.normcase(os.path.abspath(p)))
    image_files = sorted(list(image_paths_set))
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return False
    
    print(f"Found {len(image_files)} images to process")
    
    try:
        # 加载模型
        print(f"Loading model: {model_path}")
        model = YOLO(model_path)
        
        # 获取类别名称
        class_names = model.names if hasattr(model, 'names') else {}
        print(f"Model classes: {class_names}")
        
        # 存储所有检测结果的汇总
        all_results = []
        
        # 处理每个图像
        for img_idx, image_path in enumerate(image_files):
            print(f"\nProcessing {img_idx + 1}/{len(image_files)}: {os.path.basename(image_path)}")
            
            # 设置不同类别的置信度阈值
            conf_thresholds = {
                'dimension_text': 0.3,   # dimension_text 的置信度阈值
                'dimension_point': 0.3   # dimension_point 的置信度阈值
            }
            
            # 进行预测（使用较低的全局置信度，后续按类别过滤）
            results = model(image_path, conf=0.1, iou=0.1)
            
            # 处理预测结果
            for i, result in enumerate(results):
                # 获取原始图像
                original_img = result.orig_img
                img_height, img_width = original_img.shape[:2]
                
                # 获取检测结果
                boxes = result.boxes.xyxy if result.boxes is not None else None
                classes = result.boxes.cls if result.boxes is not None else None
                confidences = result.boxes.conf if result.boxes is not None else None
                
                # 生成输出文件名
                base_name = Path(image_path).stem
                
                # 创建可视化图像
                vis_img = original_img.copy()
                detection_info = []
                
                if boxes is not None and len(boxes) > 0:
                    print(f"Found {len(boxes)} detections")
                    
                    # 为不同类别定义颜色
                    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
                    
                    for j, box in enumerate(boxes):
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.cpu().numpy().astype(int)
                        
                        # 获取类别和置信度
                        cls_id = int(classes[j].cpu().numpy()) if classes is not None else -1
                        conf = float(confidences[j].cpu().numpy()) if confidences is not None else 0.0
                        
                        # 获取类别名称
                        cls_name = class_names.get(cls_id, f"class_{cls_id}") if class_names else f"class_{cls_id}"
                        
                        # 根据类别检查置信度阈值
                        min_conf = conf_thresholds.get(cls_name, 0.3)  # 默认阈值0.3
                        if conf < min_conf:
                            print(f"  Skipping {cls_name} detection with confidence {conf:.3f} < {min_conf}")
                            continue
                        
                        # 选择颜色
                        color = colors[cls_id % len(colors)] if cls_id >= 0 else (128, 128, 128)
                        
                        # 绘制边界框
                        cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
                        
                        # 添加标签
                        label = f"{cls_name}: {conf:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(vis_img, (x1, y1 - label_size[1] - 10), 
                                    (x1 + label_size[0], y1), color, -1)
                        cv2.putText(vis_img, label, (x1, y1 - 5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        # 记录检测信息
                        detection_info.append({
                            "class_id": cls_id,
                            "class_name": cls_name,
                            "confidence": conf,
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "bbox_center": [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                            "bbox_area": int((x2 - x1) * (y2 - y1))
                        })
                        
                        print(f"  Detection {j+1}: {cls_name} ({conf:.3f}) at [{x1}, {y1}, {x2}, {y2}]")
                else:
                    print("No detections found")
                
                # 保存推理后的图像（只保存一张）
                result_img_path = os.path.join(output_dir, f"{base_name}_optimized.jpg")
                cv2.imwrite(result_img_path, vis_img)
                
                # 保存对应的JSON文件（只保存一个）
                result_json = {
                    "image_name": base_name,
                    "image_path": image_path,
                    "image_size": [img_width, img_height],
                    "num_detections": len(detection_info),
                    "detections": detection_info,
                    "result_image": result_img_path
                }
                
                json_path = os.path.join(output_dir, f"{base_name}_optimized.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result_json, f, ensure_ascii=False, indent=2)
                
                all_results.append(result_json)
                
                print(f"Saved: {result_img_path}")
                print(f"Saved: {json_path}")
        
        # 保存汇总JSON文件（仅当generate_summary为True时）
        if generate_summary:
            summary_path = os.path.join(output_dir, "detection_summary.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"Summary saved to: {summary_path}")
        
        print(f"\nProcessing completed!")
        print(f"Processed {len(image_files)} images")
        print(f"Total detections: {sum(len(r['detections']) for r in all_results)}")
        print(f"Results saved to: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def predict_single_image(model, image_path, output_dir=None, conf_thresholds=None):
    """
    对单张图片进行检测
    
    Args:
        model: YOLO模型对象或模型路径字符串
        image_path (str): 图片路径
        output_dir (str, optional): 输出目录，如果提供则保存结果
        conf_thresholds (dict, optional): 置信度阈值配置
        
    Returns:
        dict: 检测结果字典，包含检测框信息等，失败返回None
    """
    try:
        # 加载模型
        if isinstance(model, str):
            print(f"Loading model: {model}")
            model = YOLO(model)
            
        # 默认阈值
        if conf_thresholds is None:
            conf_thresholds = {
                'dimension_text': 0.3,
                'dimension_point': 0.3
            }
            
        # 获取类别名称
        class_names = model.names if hasattr(model, 'names') else {}
        
        # 进行预测
        print(f"Processing image: {image_path}")
        results = model(image_path, conf=0.1, iou=0.1)
        
        if not results:
            return None
            
        result = results[0]
        original_img = result.orig_img
        img_height, img_width = original_img.shape[:2]
        
        # 获取检测结果
        boxes = result.boxes.xyxy if result.boxes is not None else None
        classes = result.boxes.cls if result.boxes is not None else None
        confidences = result.boxes.conf if result.boxes is not None else None
        
        # 准备结果数据
        detection_info = []
        vis_img = original_img.copy()
        
        if boxes is not None and len(boxes) > 0:
            colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            
            for j, box in enumerate(boxes):
                # 获取基本信息
                x1, y1, x2, y2 = box.cpu().numpy().astype(int)
                cls_id = int(classes[j].cpu().numpy()) if classes is not None else -1
                conf = float(confidences[j].cpu().numpy()) if confidences is not None else 0.0
                cls_name = class_names.get(cls_id, f"class_{cls_id}")
                
                # 检查阈值
                min_conf = conf_thresholds.get(cls_name, 0.3)
                if conf < min_conf:
                    continue
                    
                # 记录检测信息
                detection_info.append({
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "bbox_center": [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                    "bbox_area": int((x2 - x1) * (y2 - y1))
                })
                
                # 绘制可视化
                color = colors[cls_id % len(colors)] if cls_id >= 0 else (128, 128, 128)
                cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
                
                label = f"{cls_name}: {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(vis_img, (x1, y1 - label_size[1] - 10), 
                            (x1 + label_size[0], y1), color, -1)
                cv2.putText(vis_img, label, (x1, y1 - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                          
        # 构建结果对象
        base_name = Path(image_path).stem
        result_json = {
            "image_name": base_name,
            "image_path": image_path,
            "image_size": [img_width, img_height],
            "num_detections": len(detection_info),
            "detections": detection_info
        }
        
        # 如果需要保存结果
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存图片
            result_img_path = os.path.join(output_dir, f"{base_name}_optimized.jpg")
            cv2.imwrite(result_img_path, vis_img)
            result_json["result_image"] = result_img_path
            
            # 保存JSON
            json_path = os.path.join(output_dir, f"{base_name}_optimized.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            
            print(f"Saved results to {output_dir}")
            
        return result_json
        
    except Exception as e:
        print(f"Error predicting image {image_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Dimension Detection using YOLO')
    parser.add_argument('--model', type=str, 
                       default="training_outputs/dimension/dimension_smart_training_20251205_150157/weights/best.pt",
                       help='Path to model weights')
    parser.add_argument('--input', type=str, 
                       default="layout_test",
                       help='Input directory containing images')
    parser.add_argument('--output', type=str, 
                       default="layout_results",
                       help='Output directory for results')
    parser.add_argument('--generate-summary', action='store_true',
                       help='Generate detection_summary.json file (default: False)')
    
    args = parser.parse_args()
    
    # 检查模型文件是否存在
    if not os.path.exists(args.model):
        print(f"Model file {args.model} not found!")
        return
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"Input directory {args.input} not found!")
        print(f"Creating directory: {args.input}")
        os.makedirs(args.input, exist_ok=True)
        print(f"Please add images to {args.input} and run again.")
        return
    
    # 执行检测
    success = save_dimension_detection_results(
        model_path=args.model,
        input_dir=args.input,
        output_dir=args.output
    )
    
    if success:
        print("\nDimension detection completed successfully!")
    else:
        print("\nDimension detection failed!")
    # predict_single_image("training_outputs/dimension/dimension_smart_training_20251205_150157/weights/best.pt",r"E:\Github_project\BOM\extract_info\corner_text_modeldetection\room.png","dimension_detection_results")

if __name__ == "__main__":
    main()
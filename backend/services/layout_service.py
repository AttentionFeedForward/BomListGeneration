import os
import cv2
import numpy as np
import json
import logging
from pathlib import Path
from ultralytics import YOLO
from typing import Dict, Any, List, Tuple

# Add project root to path to import extract_info
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from extract_info.corner_text_modeldetection.dimension_matcher import DimensionMatcher

logger = logging.getLogger(__name__)

class LayoutService:
    _layout_model = None
    _dimension_model = None
    _matcher = None

    # Paths to models
    LAYOUT_MODEL_PATH = r"E:\Github_project\BOM\extract_info\layout_detection\training_outputs\layout_segmentation\layout_segmentation_segmentation_20251202_091457\weights\best.pt"
    DIMENSION_MODEL_PATH = r"E:\Github_project\BOM\extract_info\corner_text_modeldetection\training_outputs\dimension\dimension_smart_training_20251205_150157\weights\best.pt"
    
    # Class names for layout segmentation
    CLASS_NAMES = ['column', 'wall', 'door', 'window', 'other']
    BOUNDARY_CLASSES = ['column', 'wall', 'door', 'window', 'other']

    @classmethod
    def get_layout_model(cls):
        if cls._layout_model is None:
            logger.info(f"Loading Layout Model from {cls.LAYOUT_MODEL_PATH}")
            if not os.path.exists(cls.LAYOUT_MODEL_PATH):
                raise FileNotFoundError(f"Layout model not found at {cls.LAYOUT_MODEL_PATH}")
            cls._layout_model = YOLO(cls.LAYOUT_MODEL_PATH)
        return cls._layout_model

    @classmethod
    def get_dimension_model(cls):
        if cls._dimension_model is None:
            logger.info(f"Loading Dimension Model from {cls.DIMENSION_MODEL_PATH}")
            if not os.path.exists(cls.DIMENSION_MODEL_PATH):
                # Fallback or error
                logger.warning(f"Dimension model not found at {cls.DIMENSION_MODEL_PATH}, trying alternative path...")
                # Try to find any best.pt in dimension training outputs
                # For now raise error to be safe
                pass
            cls._dimension_model = YOLO(cls.DIMENSION_MODEL_PATH)
        return cls._dimension_model

    @classmethod
    def get_matcher(cls):
        if cls._matcher is None:
            cls._matcher = DimensionMatcher()
        return cls._matcher

    def analyze_layout(self, image_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Full pipeline:
        1. Segment rooms and calculate pixel metrics.
        2. Detect dimensions and calculate scale factor.
        3. Convert pixel metrics to real-world units.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Segment Rooms
        logger.info("Starting room segmentation...")
        pixel_results = self._segment_rooms(image_path, output_dir)
        
        # 2. Detect Dimensions & Calculate Scale
        logger.info("Starting dimension detection...")
        scale_info = self._calculate_scale(image_path, output_dir)
        
        # 3. Merge Results
        scale_factor = scale_info.get("scale_factor", 0)
        
        final_results = {
            "pixel_results": pixel_results,
            "scale_info": scale_info,
            "real_results": self._convert_to_real_units(pixel_results, scale_factor)
        }
        
        # Save final result
        with open(os.path.join(output_dir, "final_analysis.json"), 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2, default=str)
            
        return final_results

    def _segment_rooms(self, image_path: str, output_dir: str) -> Dict[str, Any]:
        model = self.get_layout_model()
        
        # Run prediction
        results = model(image_path, verbose=False)
        result = results[0]
        original_img = result.orig_img
        img_h, img_w = original_img.shape[:2]
        
        # Initialize masks
        combined_boundary_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        wall_mask = np.zeros((img_h, img_w), dtype=np.uint8)
        
        if result.masks is not None:
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            for i, mask_tensor in enumerate(result.masks.data):
                class_id = class_ids[i]
                class_name = self.CLASS_NAMES[class_id]
                
                mask_np = mask_tensor.cpu().numpy()
                mask_resized = cv2.resize(mask_np, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
                mask_binary = (mask_resized > 0.5).astype(np.uint8)

                if class_name in self.BOUNDARY_CLASSES:
                    combined_boundary_mask = cv2.bitwise_or(combined_boundary_mask, mask_binary)
                
                if class_name == 'wall':
                    wall_mask = cv2.bitwise_or(wall_mask, mask_binary)

        # Classification Dilation
        scale = 20
        hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (scale, 1))
        horizontal_mask = cv2.morphologyEx(combined_boundary_mask, cv2.MORPH_OPEN, hor_kernel)

        ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, scale))
        vertical_mask = cv2.morphologyEx(combined_boundary_mask, cv2.MORPH_OPEN, ver_kernel)

        dilation_kernel_size = 5
        dilation_iterations = 1

        h_dilate_kernel = np.ones((1, dilation_kernel_size), np.uint8)
        dilated_horizontal = cv2.dilate(horizontal_mask, h_dilate_kernel, iterations=dilation_iterations)

        v_dilate_kernel = np.ones((dilation_kernel_size, 1), np.uint8)
        dilated_vertical = cv2.dilate(vertical_mask, v_dilate_kernel, iterations=dilation_iterations)

        other_mask = cv2.subtract(combined_boundary_mask, horizontal_mask)
        other_mask = cv2.subtract(other_mask, vertical_mask)
        other_dilate_kernel = np.ones((3, 3), np.uint8)
        dilated_other = cv2.dilate(other_mask, other_dilate_kernel, iterations=dilation_iterations)

        dilated_mask = cv2.bitwise_or(dilated_horizontal, dilated_vertical)
        dilated_mask = cv2.bitwise_or(dilated_mask, dilated_other)

        room_areas = cv2.bitwise_not(dilated_mask * 255)
        
        # Connected Components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(room_areas, connectivity=8)

        # --- 优化：将墙体区域分配给最近的房间（Voronoi/膨胀策略）---
        # 目的：使房间面积包含其一半的墙体厚度，符合实际建筑面积计算标准
        expanded_labels = labels.copy()
        mask_to_fill = (dilated_mask > 0)
        max_iters = 50 
        kernel_3x3 = np.ones((3, 3), np.uint8)
        
        for _ in range(max_iters):
            unassigned_walls = mask_to_fill & (expanded_labels == 0)
            if not np.any(unassigned_walls):
                break
            
            # cv2.dilate doesn't support int32, use float32 instead
            dilated_lbls_float = cv2.dilate(expanded_labels.astype(np.float32), kernel_3x3)
            dilated_lbls = dilated_lbls_float.astype(np.int32)
            
            valid_update = unassigned_walls & (dilated_lbls > 0)
            if not np.any(valid_update):
                break
            expanded_labels[valid_update] = dilated_lbls[valid_update]

        labels = expanded_labels

        # Skeletons
        combined_boundary_mask_8u = (combined_boundary_mask * 255).astype(np.uint8)
        boundary_skeleton = self._skeletonize(combined_boundary_mask_8u)
        
        wall_mask_8u = (wall_mask * 255).astype(np.uint8)
        wall_skeleton = self._skeletonize(wall_mask_8u)
        
        total_wall_length = np.sum(wall_skeleton > 0)
        
        # Filter rooms
        min_area_threshold = 50
        room_data = []
        
        border_labels = set()
        border_labels.update(labels[0, :].tolist())
        border_labels.update(labels[img_h-1, :].tolist())
        border_labels.update(labels[:, 0].tolist())
        border_labels.update(labels[:, img_w-1].tolist())

        for i in range(1, num_labels):
            if i in border_labels:
                continue
                
            # Recalculate area and mask based on expanded labels
            room_mask = (labels == i).astype(np.uint8)
            area = np.sum(room_mask)
            
            if area > min_area_threshold:
                room_id = chr(ord('A') + len(room_data))
                
                # Contours
                contours, _ = cv2.findContours(room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    continue
                room_contour = max(contours, key=cv2.contourArea)
                
                # Metrics
                contour_mask = np.zeros((img_h, img_w), dtype=np.uint8)
                cv2.drawContours(contour_mask, [room_contour], 0, 1, 1)
                
                bridge_kernel = np.ones((3, 3), np.uint8)
                dilated_contour_mask = cv2.dilate(contour_mask, bridge_kernel, iterations=20)
                
                perimeter_boundary_mask = cv2.bitwise_and(dilated_contour_mask, boundary_skeleton)
                total_perimeter_pixels = np.sum(perimeter_boundary_mask > 0)
                
                perimeter_wall_mask = cv2.bitwise_and(dilated_contour_mask, wall_skeleton)
                precise_wall_length = np.sum(perimeter_wall_mask > 0)
                
                room_data.append({
                    "room_id": room_id,
                    "pixel_area": int(area),
                    "centroid": (int(centroids[i][0]), int(centroids[i][1])),
                    "polygon": room_contour.squeeze().tolist(),
                    "total_perimeter_pixels": int(total_perimeter_pixels),
                    "precise_wall_length_pixels": int(precise_wall_length)
                })

        # Save visualization
        self._save_visualization(original_img, room_data, output_dir)
        
        return {
            "total_wall_length_pixels": float(total_wall_length),
            "rooms": room_data,
            "image_width": img_w,
            "image_height": img_h
        }

    def _skeletonize(self, img_8u):
        skeleton = np.zeros(img_8u.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        temp = img_8u.copy()
        while True:
            eroded = cv2.erode(temp, element)
            dilated = cv2.dilate(eroded, element)
            subset = temp - dilated
            skeleton = cv2.bitwise_or(skeleton, subset)
            temp = eroded.copy()
            if cv2.countNonZero(temp) == 0:
                break
        return skeleton

    def _calculate_scale(self, image_path: str, output_dir: str) -> Dict[str, Any]:
        try:
            model = self.get_dimension_model()
            matcher = self.get_matcher()
            
            # Run prediction
            results = model(image_path, verbose=False)
            result = results[0]
            
            scattered_points = []
            text_boxes = []
            
            # Parse detections
            if result.boxes is not None:
                boxes = result.boxes.data.cpu().numpy() # [x1, y1, x2, y2, conf, cls]
                for box in boxes:
                    x1, y1, x2, y2, conf, cls_id = box
                    cls_id = int(cls_id)
                    class_name = result.names[cls_id]
                    
                    if class_name == 'dimension_point': # or similar
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        scattered_points.append((int(center_x), int(center_y)))
                    elif class_name == 'dimension_text':
                        text_box = (
                            (int(x1), int(y1)),
                            (int(x2), int(y1)),
                            (int(x2), int(y2)),
                            (int(x1), int(y2))
                        )
                        text_boxes.append(text_box)
            
            # OCR
            ocr_texts = matcher.extract_text_with_ocr(image_path, text_boxes)
            
            # Match
            match_result = matcher.match_dimensions(
                scattered_points,
                text_boxes,
                ocr_texts,
                debug=False
            )
            
            # Save dimension visualization
            # We can use matcher's visualize if available, or just rely on the frontend
            
            return {
                "scale_factor": match_result.get("summary", {}).get("average_scale_factor", 0),
                "match_details": match_result
            }
            
        except Exception as e:
            logger.error(f"Error in scale calculation: {e}")
            return {"scale_factor": 0, "error": str(e)}

    def _convert_to_real_units(self, pixel_results: Dict, scale_factor: float) -> Dict:
        if not scale_factor or scale_factor <= 0:
            return pixel_results
            
        real_results = {
            "total_wall_length_mm": pixel_results["total_wall_length_pixels"] * scale_factor,
            "rooms": []
        }
        
        for room in pixel_results["rooms"]:
            real_room = room.copy()
            real_room["area_mm2"] = room["pixel_area"] * (scale_factor ** 2)
            real_room["area_m2"] = real_room["area_mm2"] / 1_000_000
            real_room["perimeter_mm"] = room["total_perimeter_pixels"] * scale_factor
            real_room["wall_length_mm"] = room["precise_wall_length_pixels"] * scale_factor
            real_results["rooms"].append(real_room)
            
        return real_results

    def _save_visualization(self, original_img, room_data, output_dir):
        vis_img = original_img.copy()
        for room in room_data:
            centroid = room["centroid"]
            contour = np.array(room["polygon"]).reshape((-1, 1, 2)).astype(np.int32)
            cv2.drawContours(vis_img, [contour], -1, (0, 255, 0), 2)
            
            cv2.putText(vis_img, room["room_id"], centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
        cv2.imwrite(os.path.join(output_dir, "segmentation_vis.jpg"), vis_img)

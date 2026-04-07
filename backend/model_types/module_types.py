"""
模块识别相关数据类型定义
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union


@dataclass
class Point:
    """坐标点"""

    x: int
    y: int
    z: Optional[int] = None


@dataclass
class BoundingBox:
    """边界框"""

    x: float
    y: float
    width: float
    height: float


@dataclass
class TextBox:
    """文本框"""

    corners: List[Point]


@dataclass
class EndpointPair:
    """端点对"""

    start_point: Point
    end_point: Point


@dataclass
class Measurements:
    """测量数据"""

    pixel_distance: float
    actual_size: Union[float, str]
    scale_factor: float


@dataclass
class MatchResult:
    """匹配结果"""

    id: int
    endpoint_pair: EndpointPair
    text_box: TextBox
    text_content: str
    measurements: Measurements
    match_score: float
    is_outlier: bool = False


@dataclass
class UnmatchedEndpoint:
    """未匹配的端点"""

    id: int
    start_point: Point
    end_point: Point


@dataclass
class UnmatchedText:
    """未匹配的文本"""

    id: int
    text_box: TextBox
    text_content: str


@dataclass
class MatchSummary:
    """匹配摘要"""

    total_matches: int
    total_endpoints: int
    total_texts: int
    match_rate: float
    average_scale_factor: float


@dataclass
class ScaleFilterInfo:
    """比例因子过滤信息"""

    enabled: bool
    original_count: int
    filtered_count: int
    outliers_removed: int
    filter_threshold: float
    statistics: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingInfo:
    """处理信息"""

    confidence_threshold: float
    angle_threshold: float
    enable_scale_filter: bool
    scale_deviation_threshold: float
    collinear_threshold: float


@dataclass
class DebugInfo:
    """调试信息"""

    input_data: Dict[str, int]
    raw_match_results: Dict[str, Any]


@dataclass
class ModuleIdentificationResult:
    """模块识别结果"""

    matches: List[MatchResult]
    unmatched_endpoints: List[UnmatchedEndpoint]
    unmatched_texts: List[UnmatchedText]
    summary: MatchSummary
    scale_filter_info: ScaleFilterInfo
    processing_info: ProcessingInfo
    debug_info: Optional[DebugInfo] = None


@dataclass
class ApiResponse:
    """API响应格式"""

    success: bool
    data: Optional[ModuleIdentificationResult] = None
    error: Optional[str] = None
    details: Optional[str] = None
    processing_info: Optional[Dict[str, Any]] = None


# 输入数据验证相关类型
@dataclass
class DetectionItem:
    """检测项"""

    class_name: str  # 'dimension_point' 或 'dimension_text'
    confidence: float
    bbox_center: Optional[List[float]] = None  # 用于dimension_point
    bbox: Optional[List[float]] = None  # 用于dimension_text


@dataclass
class DetectionData:
    """检测数据"""

    detections: List[DetectionItem]


# 健康检查相关类型
@dataclass
class DependencyStatus:
    """依赖状态"""

    dimension_matcher: str
    ocr: str
    histogram_filter: str


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    service_name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    dependencies: DependencyStatus
    configuration: ProcessingInfo
    timestamp: str
    error: Optional[str] = None


# 与前端兼容的响应格式转换函数
def to_frontend_format(result: ModuleIdentificationResult) -> Dict[str, Any]:
    """
    将后端数据格式转换为前端期望的格式

    Args:
        result: 模块识别结果

    Returns:
        前端兼容的数据格式
    """
    return {
        "matches": [
            {
                "id": match.id,
                "endpoint_pair": {
                    "start_point": {
                        "x": match.endpoint_pair.start_point.x,
                        "y": match.endpoint_pair.start_point.y,
                    },
                    "end_point": {
                        "x": match.endpoint_pair.end_point.x,
                        "y": match.endpoint_pair.end_point.y,
                    },
                },
                "text_box": {
                    "corners": [{"x": corner.x, "y": corner.y} for corner in match.text_box.corners]
                },
                "text_content": match.text_content,
                "measurements": {
                    "pixel_distance": match.measurements.pixel_distance,
                    "actual_size": match.measurements.actual_size,
                    "scale_factor": match.measurements.scale_factor,
                },
                "match_score": match.match_score,
                "is_outlier": match.is_outlier,
            }
            for match in result.matches
        ],
        "unmatched_endpoints": [
            {
                "id": endpoint.id,
                "start_point": {"x": endpoint.start_point.x, "y": endpoint.start_point.y},
                "end_point": {"x": endpoint.end_point.x, "y": endpoint.end_point.y},
            }
            for endpoint in result.unmatched_endpoints
        ],
        "unmatched_texts": [
            {
                "id": text.id,
                "text_box": {
                    "corners": [{"x": corner.x, "y": corner.y} for corner in text.text_box.corners]
                },
                "text_content": text.text_content,
            }
            for text in result.unmatched_texts
        ],
        "summary": {
            "total_matches": result.summary.total_matches,
            "total_endpoints": result.summary.total_endpoints,
            "total_texts": result.summary.total_texts,
            "match_rate": result.summary.match_rate,
            "average_scale_factor": result.summary.average_scale_factor,
        },
        "scale_filter_info": {
            "enabled": result.scale_filter_info.enabled,
            "original_count": result.scale_filter_info.original_count,
            "filtered_count": result.scale_filter_info.filtered_count,
            "outliers_removed": result.scale_filter_info.outliers_removed,
            "filter_threshold": result.scale_filter_info.filter_threshold,
            "statistics": result.scale_filter_info.statistics,
        },
        "processing_info": {
            "confidence_threshold": result.processing_info.confidence_threshold,
            "angle_threshold": result.processing_info.angle_threshold,
            "enable_scale_filter": result.processing_info.enable_scale_filter,
            "scale_deviation_threshold": result.processing_info.scale_deviation_threshold,
            "collinear_threshold": result.processing_info.collinear_threshold,
        },
        "debug_info": (
            {
                "input_data": result.debug_info.input_data,
                "raw_match_results": result.debug_info.raw_match_results,
            }
            if result.debug_info
            else None
        ),
    }


def from_dimension_matcher_result(
    raw_result: Dict[str, Any], processing_params: Dict[str, Any], debug: bool = False
) -> ModuleIdentificationResult:
    """
    将dimension_matcher的原始结果转换为标准化的数据结构

    Args:
        raw_result: dimension_matcher的原始结果
        processing_params: 处理参数
        debug: 是否包含调试信息

    Returns:
        标准化的模块识别结果
    """
    # 转换匹配结果
    matches = []
    for i, match in enumerate(raw_result.get("matches", [])):
        matches.append(
            MatchResult(
                id=i + 1,
                endpoint_pair=EndpointPair(
                    start_point=Point(
                        x=int(match["endpoint_pair"][0][0]), y=int(match["endpoint_pair"][0][1])
                    ),
                    end_point=Point(
                        x=int(match["endpoint_pair"][1][0]), y=int(match["endpoint_pair"][1][1])
                    ),
                ),
                text_box=TextBox(
                    corners=[
                        Point(x=int(corner[0]), y=int(corner[1])) for corner in match["text_box"]
                    ]
                ),
                text_content=match["text_content"],
                measurements=Measurements(
                    pixel_distance=round(match["pixel_distance"], 2),
                    actual_size=match["actual_size"],
                    scale_factor=(
                        round(match["scale_factor"], 6) if match["scale_factor"] > 0 else 0
                    ),
                ),
                match_score=round(match["match_score"], 4),
                is_outlier=match.get("is_outlier", False),
            )
        )

    # 转换未匹配的端点
    unmatched_endpoints = []
    for i, (p1, p2) in enumerate(raw_result.get("unmatched_endpoints", [])):
        unmatched_endpoints.append(
            UnmatchedEndpoint(
                id=i + 1,
                start_point=Point(x=int(p1[0]), y=int(p1[1])),
                end_point=Point(x=int(p2[0]), y=int(p2[1])),
            )
        )

    # 转换未匹配的文本
    unmatched_texts = []
    for i, unmatched_text in enumerate(raw_result.get("unmatched_texts", [])):
        unmatched_texts.append(
            UnmatchedText(
                id=i + 1,
                text_box=TextBox(
                    corners=[
                        Point(x=int(corner[0]), y=int(corner[1]))
                        for corner in unmatched_text["text_box"]
                    ]
                ),
                text_content=unmatched_text["text_content"],
            )
        )

    # 转换摘要信息
    summary = MatchSummary(
        total_matches=len(matches),
        total_endpoints=raw_result["summary"]["total_endpoints"],
        total_texts=raw_result["summary"]["total_texts"],
        match_rate=round(raw_result["summary"]["match_rate"], 4),
        average_scale_factor=round(raw_result["summary"]["average_scale_factor"], 6),
    )

    # 转换比例因子过滤信息
    scale_filter_raw = raw_result.get("scale_filter_info", {})
    scale_filter_info = ScaleFilterInfo(
        enabled=processing_params.get("enable_scale_filter", True),
        original_count=scale_filter_raw.get("original_count", 0),
        filtered_count=scale_filter_raw.get("filtered_count", 0),
        outliers_removed=scale_filter_raw.get("outliers_removed", 0),
        filter_threshold=scale_filter_raw.get("filter_threshold", 0.0),
        statistics=scale_filter_raw.get("statistics"),
    )

    # 转换处理信息
    processing_info = ProcessingInfo(
        confidence_threshold=processing_params.get("confidence_threshold", 0.5),
        angle_threshold=processing_params.get("angle_threshold", 2.0),
        enable_scale_filter=processing_params.get("enable_scale_filter", True),
        scale_deviation_threshold=processing_params.get("scale_deviation_threshold", 0.05),
        collinear_threshold=processing_params.get("collinear_threshold", 3.0),
    )

    # 转换调试信息
    debug_info = None
    if debug and "debug_info" in raw_result:
        debug_info = DebugInfo(
            input_data=raw_result["debug_info"]["input_data"],
            raw_match_results=raw_result["debug_info"]["raw_match_results"],
        )

    return ModuleIdentificationResult(
        matches=matches,
        unmatched_endpoints=unmatched_endpoints,
        unmatched_texts=unmatched_texts,
        summary=summary,
        scale_filter_info=scale_filter_info,
        processing_info=processing_info,
        debug_info=debug_info,
    )

import React, { useEffect, useRef, useState, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { Card, Spin, Empty, Button, Space, Tooltip, Badge } from 'antd';
import { 
  ReloadOutlined, 
  FullscreenOutlined, 
  ZoomInOutlined, 
  ZoomOutOutlined,
  ExpandOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import { GraphData, GraphNode, GraphEdge, EntityType } from '../../types/knowledgeGraph';
import './KnowledgeGraphVisualizer.css';

interface KnowledgeGraphVisualizerProps {
  data: GraphData;
  loading?: boolean;
  height?: number | string;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onNodeDoubleClick?: (node: GraphNode) => void;
  centerNodeId?: string;
  showToolbar?: boolean;
  showLegend?: boolean;
  interactive?: boolean;
}

// 实体类型颜色映射
const typeColors: Record<EntityType, string> = {
  equipment: '#1677ff',    // 蓝色
  process: '#52c41a',      // 绿色
  material: '#faad14',     // 黄色
  parameter: '#722ed1',    // 紫色
  document: '#eb2f96',     // 粉色
  person: '#13c2c2',       // 青色
  organization: '#fa8c16', // 橙色
  location: '#2f54eb',     // 深蓝
};

// 实体类型名称映射
const typeNames: Record<EntityType, string> = {
  equipment: '设备',
  process: '工艺',
  material: '材料',
  parameter: '参数',
  document: '文档',
  person: '人员',
  organization: '组织',
  location: '位置',
};

const KnowledgeGraphVisualizer: React.FC<KnowledgeGraphVisualizerProps> = ({
  data,
  loading = false,
  height = 600,
  onNodeClick,
  onEdgeClick,
  onNodeDoubleClick,
  centerNodeId,
  showToolbar = true,
  showLegend = true,
  interactive = true,
}) => {
  const chartRef = useRef<ReactECharts>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 生成图表配置
  const getOption = useCallback(() => {
    const categories = data.categories || Object.keys(typeNames).map((type, index) => ({
      name: typeNames[type as EntityType],
      itemStyle: { color: typeColors[type as EntityType] },
    }));

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e8e8e8',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#262626',
          fontSize: 13,
        },
        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px;',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const node = params.data as GraphNode;
            const entity = node.data;
            return `
              <div style="max-width: 280px;">
                <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: ${params.color};">
                  ${node.name}
                </div>
                <div style="color: #666; font-size: 12px; margin-bottom: 4px;">
                  类型: ${typeNames[entity?.type as EntityType] || '未知'}
                </div>
                ${entity?.description ? `
                  <div style="color: #666; font-size: 12px; line-height: 1.5; margin-top: 8px;">
                    ${entity.description.slice(0, 100)}${entity.description.length > 100 ? '...' : ''}
                  </div>
                ` : ''}
              </div>
            `;
          } else if (params.dataType === 'edge') {
            const edge = params.data as GraphEdge;
            return `
              <div style="max-width: 200px;">
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">
                  ${edge.name || '关联关系'}
                </div>
                <div style="color: #666; font-size: 12px;">
                  ${edge.source} → ${edge.target}
                </div>
              </div>
            `;
          }
          return '';
        },
      },
      legend: showLegend ? {
        data: categories.map(c => c.name),
        orient: 'vertical',
        right: 20,
        top: 20,
        itemGap: 12,
        textStyle: {
          fontSize: 12,
          color: '#595959',
        },
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: [12, 16],
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#e8e8e8',
      } : undefined,
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: data.nodes.map(node => ({
            ...node,
            symbolSize: node.symbolSize || (centerNodeId && node.id === centerNodeId ? 60 : 40),
            itemStyle: {
              color: typeColors[node.data?.type as EntityType] || '#999',
              borderColor: '#fff',
              borderWidth: 2,
              shadowBlur: 10,
              shadowColor: 'rgba(0,0,0,0.1)',
              ...(centerNodeId && node.id === centerNodeId ? {
                shadowBlur: 20,
                shadowColor: typeColors[node.data?.type as EntityType] || '#999',
              } : {}),
            },
            label: {
              show: true,
              position: 'bottom',
              fontSize: 12,
              color: '#262626',
              formatter: '{b}',
              backgroundColor: 'rgba(255,255,255,0.8)',
              padding: [4, 8],
              borderRadius: 4,
            },
            emphasis: {
              scale: 1.2,
              label: {
                show: true,
                fontSize: 14,
                fontWeight: 'bold',
              },
              itemStyle: {
                shadowBlur: 20,
                shadowColor: 'rgba(0,0,0,0.2)',
              },
            },
          })),
          edges: data.edges.map(edge => ({
            ...edge,
            lineStyle: {
              color: '#bfbfbf',
              width: 1.5,
              curveness: 0.2,
              ...edge.lineStyle,
            },
            label: edge.name ? {
              show: true,
              fontSize: 10,
              color: '#8c8c8c',
              formatter: edge.name,
            } : undefined,
            emphasis: {
              lineStyle: {
                width: 3,
                color: '#1677ff',
              },
            },
          })),
          categories: categories,
          roam: interactive,
          draggable: interactive,
          focusNodeAdjacency: interactive,
          force: {
            repulsion: 300,
            gravity: 0.1,
            edgeLength: [80, 150],
            layoutAnimation: true,
          },
          zoom: 0.8,
          center: centerNodeId ? undefined : ['50%', '50%'],
        },
      ],
    };

    return option;
  }, [data, centerNodeId, showLegend, interactive]);

  // 处理节点点击
  const handleNodeClick = useCallback((params: any) => {
    if (params.dataType === 'node' && onNodeClick) {
      onNodeClick(params.data as GraphNode);
    } else if (params.dataType === 'edge' && onEdgeClick) {
      onEdgeClick(params.data as GraphEdge);
    }
  }, [onNodeClick, onEdgeClick]);

  // 处理节点双击
  const handleNodeDoubleClick = useCallback((params: any) => {
    if (params.dataType === 'node' && onNodeDoubleClick) {
      onNodeDoubleClick(params.data as GraphNode);
    }
  }, [onNodeDoubleClick]);

  // 缩放控制
  const handleZoomIn = () => {
    const chart = chartRef.current?.getEchartsInstance();
    if (chart) {
      const option = chart.getOption();
      const series = option.series as any[] | undefined;
      const currentZoom = series?.[0]?.zoom || 1;
      chart.setOption({
        series: [{ zoom: currentZoom * 1.2 }],
      });
    }
  };

  const handleZoomOut = () => {
    const chart = chartRef.current?.getEchartsInstance();
    if (chart) {
      const option = chart.getOption();
      const series = option.series as any[] | undefined;
      const currentZoom = series?.[0]?.zoom || 1;
      chart.setOption({
        series: [{ zoom: currentZoom / 1.2 }],
      });
    }
  };

  // 重置视图
  const handleReset = () => {
    const chart = chartRef.current?.getEchartsInstance();
    if (chart) {
      chart.dispatchAction({
        type: 'restore',
      });
    }
  };

  // 切换全屏
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    setTimeout(() => {
      chartRef.current?.getEchartsInstance()?.resize();
    }, 100);
  };

  // 监听数据变化，调整中心
  useEffect(() => {
    if (centerNodeId && chartRef.current) {
      const chart = chartRef.current.getEchartsInstance();
      chart.dispatchAction({
        type: 'focusNodeAdjacency',
        seriesIndex: 0,
        dataIndex: data.nodes.findIndex(n => n.id === centerNodeId),
      });
    }
  }, [centerNodeId, data.nodes]);

  const chartHeight = isFullscreen ? 'calc(100vh - 100px)' : height;

  return (
    <Card
      className={`knowledge-graph-card ${isFullscreen ? 'fullscreen' : ''}`}
      bodyStyle={{ padding: 0, position: 'relative' }}
      style={{ height: isFullscreen ? '100vh' : 'auto' }}
    >
      {/* 工具栏 */}
      {showToolbar && (
        <div className="graph-toolbar">
          <Space>
            <Tooltip title="刷新">
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
                size="small"
              />
            </Tooltip>
            <Tooltip title="放大">
              <Button
                icon={<ZoomInOutlined />}
                onClick={handleZoomIn}
                size="small"
              />
            </Tooltip>
            <Tooltip title="缩小">
              <Button
                icon={<ZoomOutOutlined />}
                onClick={handleZoomOut}
                size="small"
              />
            </Tooltip>
            <Tooltip title={isFullscreen ? "退出全屏" : "全屏"}>
              <Button
                icon={isFullscreen ? <ExpandOutlined /> : <FullscreenOutlined />}
                onClick={toggleFullscreen}
                size="small"
              />
            </Tooltip>
          </Space>
          <div className="graph-stats">
            <Badge 
              count={data.nodes.length} 
              style={{ backgroundColor: '#1677ff' }}
            >
              <span className="stat-label"><NodeIndexOutlined /> 实体</span>
            </Badge>
            <Badge 
              count={data.edges.length} 
              style={{ backgroundColor: '#52c41a', marginLeft: 16 }}
            >
              <span className="stat-label">关联</span>
            </Badge>
          </div>
        </div>
      )}

      {/* 图表区域 */}
      <div className="graph-container" style={{ height: chartHeight }}>
        {loading ? (
          <div className="graph-loading">
            <Spin size="large" tip="加载知识图谱..." />
          </div>
        ) : data.nodes.length === 0 ? (
          <Empty
            description="暂无知识图谱数据"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 100 }}
          />
        ) : (
          <ReactECharts
            ref={chartRef}
            option={getOption()}
            style={{ height: '100%', width: '100%' }}
            onEvents={{
              click: handleNodeClick,
              dblclick: handleNodeDoubleClick,
            }}
            theme="light"
          />
        )}
      </div>
    </Card>
  );
};

export default KnowledgeGraphVisualizer;

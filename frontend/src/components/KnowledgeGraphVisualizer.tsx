"""
知识图谱可视化组件 - D3.js Force Directed Graph
"""

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface GraphNode {
  id: string;
  label: string;
  name: string;
  type: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  label?: string;
}

interface GraphCanvasProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onNodeClick?: (node: GraphNode) => void;
  onNodeDoubleClick?: (node: GraphNode) => void;
  width?: number;
  height?: number;
}

const nodeColors: Record<string, string> = {
  Equipment: '#1890ff',
  Process: '#52c41a',
  Material: '#faad14',
  Parameter: '#722ed1',
  Document: '#13c2c2',
  Person: '#eb2f96',
  Fault: '#f5222d',
  Term: '#8c8c8c',
  default: '#1677ff'
};

const KnowledgeGraphVisualizer: React.FC<GraphCanvasProps> = ({
  nodes,
  links,
  onNodeClick,
  onNodeDoubleClick,
  width = 800,
  height = 600
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    // 清除现有内容
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // 创建缩放容器
    const g = svg.append('g');

    // 添加缩放行为
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // 创建力导向图
    const simulation = d3.forceSimulation<GraphNode>(nodes as GraphNode[])
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // 绘制连接线
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#e8e8e8')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6);

    // 绘制节点
    const node = g.append('g')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // 节点圆形
    node.append('circle')
      .attr('r', 20)
      .attr('fill', d => nodeColors[d.type] || nodeColors.default)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 0.9);

    // 节点标签
    node.append('text')
      .text(d => d.name?.substring(0, 10) || d.id?.substring(0, 8))
      .attr('font-size', 10)
      .attr('text-anchor', 'middle')
      .attr('dy', 35)
      .attr('fill', '#595959');

    // 节点类型标签
    node.append('text')
      .text(d => d.type)
      .attr('font-size', 8)
      .attr('text-anchor', 'middle')
      .attr('dy', -30)
      .attr('fill', d => nodeColors[d.type] || nodeColors.default)
      .attr('font-weight', 600);

    // 连接线标签
    node.append('text')
      .text(d => '')
      .attr('class', 'link-label');

    // 点击事件
    node.on('click', (event, d) => {
      event.stopPropagation();
      setSelectedNode(d);
      onNodeClick?.(d);
    });

    // 双击事件
    node.on('dblclick', (event, d) => {
      event.stopPropagation();
      onNodeDoubleClick?.(d);
    });

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // 拖拽函数
    function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // 清理
    return () => {
      simulation.stop();
    };
  }, [nodes, links, width, height]);

  return (
    <div style={{ position: 'relative', width, height }}>
      <svg ref={svgRef} style={{ border: '1px solid #e8e8e8', borderRadius: 8, background: '#fafafa' }} />
      
      {/* 图例 */}
      <div style={{
        position: 'absolute',
        top: 16,
        left: 16,
        background: 'white',
        padding: '12px 16px',
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        fontSize: 12
      }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>图例</div>
        {Object.entries(nodeColors).filter(([k]) => k !== 'default').map(([type, color]) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: color }} />
            <span>{type}</span>
          </div>
        ))}
      </div>

      {/* 操作提示 */}
      <div style={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        background: 'white',
        padding: '8px 12px',
        borderRadius: 6,
        fontSize: 11,
        color: '#8c8c8c'
      }}>
        拖拽移动 · 滚轮缩放 · 点击查看详情
      </div>

      {/* 缩放控制 */}
      <div style={{
        position: 'absolute',
        bottom: 16,
        right: 16,
        display: 'flex',
        flexDirection: 'column',
        gap: 4
      }}>
        <button
          onClick={() => {
            const svg = d3.select(svgRef.current);
            svg.transition().call(
              d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
              1.5
            );
          }}
          style={{
            width: 32,
            height: 32,
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            background: 'white',
            cursor: 'pointer'
          }}
        >
          +
        </button>
        <button
          onClick={() => {
            const svg = d3.select(svgRef.current);
            svg.transition().call(
              d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
              0.67
            );
          }}
          style={{
            width: 32,
            height: 32,
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            background: 'white',
            cursor: 'pointer'
          }}
        >
          -
        </button>
      </div>
    </div>
  );
};

export default KnowledgeGraphVisualizer;

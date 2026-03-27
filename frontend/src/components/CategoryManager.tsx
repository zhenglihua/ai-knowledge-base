import React, { useState, useEffect } from 'react';
import {
  Modal, Form, Input, Select, Button, Tag, Space, Table, Card, 
  Popconfirm, message, Tabs, Badge, Tooltip, Row, Col
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, TagsOutlined,
  FolderOutlined, AppstoreOutlined
} from '@ant-design/icons';
import {
  Category, Tag as TagType, CreateCategoryRequest, CreateTagRequest,
  getCategories, createCategory, updateCategory, deleteCategory,
  getTags, createTag, deleteTag, getPopularTags
} from '../services/categoryService';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

interface CategoryManagerProps {
  visible: boolean;
  onClose: () => void;
}

const CATEGORY_COLORS = ['blue', 'green', 'purple', 'orange', 'cyan', 'red', 'magenta', 'gold'];
const ICONS = ['📄', '⚙️', '🔧', '💻', '📊', '🏭', '🛡️', '📋', '🔬', '📐'];

const CategoryManager = ({ visible, onClose }: CategoryManagerProps) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<TagType[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('categories');
  
  // 表单状态
  const [categoryForm] = Form.useForm();
  const [tagForm] = Form.useForm();
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingTag, setEditingTag] = useState<TagType | null>(null);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [tagModalVisible, setTagModalVisible] = useState(false);

  useEffect(() => {
    if (visible) {
      loadData();
    }
  }, [visible]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cats, tagsData] = await Promise.all([
        getCategories(),
        getTags()
      ]);
      setCategories(cats);
      setTags(tagsData);
    } catch (error: any) {
      message.error(error.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // ==================== 分类管理 ====================

  const handleAddCategory = () => {
    setEditingCategory(null);
    categoryForm.resetFields();
    categoryForm.setFieldsValue({
      color: 'blue',
      icon: '📄',
      sort_order: categories.length
    });
    setCategoryModalVisible(true);
  };

  const handleEditCategory = (category: Category) => {
    setEditingCategory(category);
    categoryForm.setFieldsValue({
      name: category.name,
      description: category.description,
      color: category.color,
      icon: category.icon,
      sort_order: category.sort_order
    });
    setCategoryModalVisible(true);
  };

  const handleDeleteCategory = async (id: string) => {
    try {
      await deleteCategory(id);
      message.success('删除成功');
      loadData();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const handleCategorySubmit = async (values: CreateCategoryRequest) => {
    try {
      if (editingCategory) {
        await updateCategory(editingCategory.id, values);
        message.success('更新成功');
      } else {
        await createCategory(values);
        message.success('创建成功');
      }
      setCategoryModalVisible(false);
      loadData();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  // ==================== 标签管理 ====================

  const handleAddTag = () => {
    setEditingTag(null);
    tagForm.resetFields();
    tagForm.setFieldsValue({
      tag_type: 'custom',
      color: 'default'
    });
    setTagModalVisible(true);
  };

  const handleDeleteTag = async (id: string) => {
    try {
      await deleteTag(id);
      message.success('删除成功');
      loadData();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const handleTagSubmit = async (values: CreateTagRequest) => {
    try {
      await createTag(values);
      message.success('创建成功');
      setTagModalVisible(false);
      loadData();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  // ==================== 表格列定义 ====================

  const categoryColumns = [
    {
      title: '图标',
      dataIndex: 'icon',
      key: 'icon',
      width: 60,
      render: (icon: string) => <span style={{ fontSize: 20 }}>{icon}</span>,
    },
    {
      title: '分类名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Category) => (
        <Space>
          <Tag color={record.color}>{name}</Tag>
          {record.is_preset && <Tag>预设</Tag>}
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      width: 100,
      render: (count: number) => (
        <Badge count={count} showZero style={{ backgroundColor: '#52c41a' }} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Category) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditCategory(record)}
            />
          </Tooltip>
          {!record.is_preset ? (
            <Tooltip title="删除">
              <Popconfirm
                title="确定要删除此分类吗？"
                description='该分类下的文档将被移动到"其他文档"'
                onConfirm={() => handleDeleteCategory(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Tooltip>
          ) : null}
        </Space>
      ),
    },
  ];

  const tagColumns = [
    {
      title: '标签名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: TagType) => (
        <Tag color={record.color || 'default'}>
          {name}
        </Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'tag_type',
      key: 'tag_type',
      width: 120,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          'equipment': '设备',
          'process': '工艺',
          'parameter': '参数',
          'material': '材料',
          'custom': '自定义'
        };
        return <Tag>{typeMap[type] || type}</Tag>;
      },
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 100,
      sorter: (a: TagType, b: TagType) => a.usage_count - b.usage_count,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: TagType) => (
        <Tooltip title="删除">
          <Popconfirm
            title="确定要删除此标签吗？"
            onConfirm={() => handleDeleteTag(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Tooltip>
      ),
    },
  ];

  return (
    <Modal
      title="分类和标签管理"
      open={visible}
      onCancel={onClose}
      width={900}
      footer={[
        <Button key="close" onClick={onClose}>关闭</Button>
      ]}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane 
          tab={<span><FolderOutlined /> 分类管理</span>} 
          key="categories"
        >
          <Card
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddCategory}
              >
                新建分类
              </Button>
            }
          >
            <Table
              rowKey="id"
              columns={categoryColumns}
              dataSource={categories}
              loading={loading}
              pagination={false}
              size="small"
            />
          </Card>
        </TabPane>
        
        <TabPane 
          tab={<span><TagsOutlined /> 标签管理</span>} 
          key="tags"
        >
          <Card
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddTag}
              >
                新建标签
              </Button>
            }
          >
            <Table
              rowKey="id"
              columns={tagColumns}
              dataSource={tags}
              loading={loading}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 分类表单弹窗 */}
      <Modal
        title={editingCategory ? '编辑分类' : '新建分类'}
        open={categoryModalVisible}
        onCancel={() => setCategoryModalVisible(false)}
        onOk={() => categoryForm.submit()}
      >
        <Form
          form={categoryForm}
          layout="vertical"
          onFinish={handleCategorySubmit}
        >
          <Form.Item
            name="name"
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="例如：设备文档" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="分类描述（可选）" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="color"
                label="颜色"
              >
                <Select>
                  {CATEGORY_COLORS.map(color => (
                    <Option key={color} value={color}>
                      <Tag color={color}>{color}</Tag>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="icon"
                label="图标"
              >
                <Select>
                  {ICONS.map(icon => (
                    <Option key={icon} value={icon}>
                      {icon}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="sort_order"
            label="排序"
          >
            <Input type="number" min={0} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 标签表单弹窗 */}
      <Modal
        title="新建标签"
        open={tagModalVisible}
        onCancel={() => setTagModalVisible(false)}
        onOk={() => tagForm.submit()}
      >
        <Form
          form={tagForm}
          layout="vertical"
          onFinish={handleTagSubmit}
        >
          <Form.Item
            name="name"
            label="标签名称"
            rules={[{ required: true, message: '请输入标签名称' }]}
          >
            <Input placeholder="例如：光刻机" />
          </Form.Item>

          <Form.Item
            name="tag_type"
            label="标签类型"
          >
            <Select>
              <Option value="custom">自定义</Option>
              <Option value="equipment">设备</Option>
              <Option value="process">工艺</Option>
              <Option value="parameter">参数</Option>
              <Option value="material">材料</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="标签描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </Modal>
  );
};

export default CategoryManager;
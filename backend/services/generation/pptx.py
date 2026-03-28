"""
PPT 生成服务
v0.7.0
基于文档内容或报告自动生成 PowerPoint 演示文稿
"""
from typing import Dict, List, Any, Optional
import os
import zipfile
import shutil
from datetime import datetime


class SlideContent:
    """幻灯片内容"""
    def __init__(
        self,
        title: str,
        content: str = "",
        bullets: List[str] = None,
        image_path: str = None
    ):
        self.title = title
        self.content = content
        self.bullets = bullets or []
        self.image_path = image_path


class PPTXGenerator:
    """
    PPT 生成器
    将报告内容转换为 PowerPoint 格式
    """

    def __init__(self):
        self.template_dir = "/Users/zheng/.openclaw/workspace/ai-knowledge-base/mvp/backend/templates/pptx"

    async def generate(
        self,
        title: str,
        slides: List[SlideContent],
        theme: str = "professional"
    ) -> str:
        """
        生成 PPT 文件

        Args:
            title: 演示文稿标题
            slides: 幻灯片内容列表
            theme: 主题风格 (professional/科技/简约)

        Returns:
            PPT 文件保存路径
        """
        output_dir = f"/tmp/pptx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)

        # 创建 PPTX (ZIP 格式)
        pptx_path = await self._create_pptx(output_dir, title, slides, theme)

        # 清理临时目录
        shutil.rmtree(output_dir, ignore_errors=True)

        return pptx_path

    async def _create_pptx(
        self,
        output_dir: str,
        title: str,
        slides: List[SlideContent],
        theme: str
    ) -> str:
        """创建 PPTX 文件"""
        # 创建目录结构
        os.makedirs(f"{output_dir}/ppt/slides", exist_ok=True)
        os.makedirs(f"{output_dir}/ppt/_rels", exist_ok=True)
        os.makedirs(f"{output_dir}/_rels", exist_ok=True)
        os.makedirs(f"{output_dir}/docProps", exist_ok=True)

        # [Content_Types].xml
        content_types = self._get_content_types(len(slides))
        with open(f"{output_dir}/[Content_Types].xml", "w") as f:
            f.write(content_types)

        # _rels/.rels
        rels = self._get_rels()
        with open(f"{output_dir}/_rels/.rels", "w") as f:
            f.write(rels)

        # ppt/_rels/presentation.xml.rels
        pres_rels = self._get_presentation_rels(len(slides))
        with open(f"{output_dir}/ppt/_rels/presentation.xml.rels", "w") as f:
            f.write(pres_rels)

        # 创建每一页幻灯片
        for i, slide in enumerate(slides, 1):
            slide_xml = self._create_slide_xml(i, slide, theme)
            with open(f"{output_dir}/ppt/slides/slide{i}.xml", "w") as f:
                f.write(slide_xml)

        # presentation.xml
        presentation = self._get_presentation(len(slides))
        with open(f"{output_dir}/ppt/presentation.xml", "w") as f:
            f.write(presentation)

        # docProps/app.xml
        app_xml = self._get_app_xml(title, len(slides))
        with open(f"{output_dir}/docProps/app.xml", "w") as f:
            f.write(app_xml)

        # 打包为 PPTX
        output_file = f"/tmp/{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pptx"
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        return output_file

    def _get_content_types(self, slide_count: int) -> str:
        """生成 [Content_Types].xml"""
        slides_part = "\n".join([
            f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            for i in range(1, slide_count + 1)
        ])
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
{slides_part}
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

    def _get_rels(self) -> str:
        """生成 _rels/.rels"""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/app.xml"/>
</Relationships>'''

    def _get_presentation_rels(self, slide_count: int) -> str:
        """生成 ppt/_rels/presentation.xml.rels"""
        slides_rels = "\n".join([
            f'  <Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
            for i in range(1, slide_count + 1)
        ])
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{slides_rels}
</Relationships>'''

    def _get_presentation(self, slide_count: int) -> str:
        """生成 ppt/presentation.xml"""
        slide_ids = "\n".join([
            f'    <p:sldId id="{256+i}" r:id="rId{i+1}"/>'
            for i in range(1, slide_count + 1)
        ])
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" saveSubsetFonts="1">
  <p:sldMasterIdLst/>
  <p:sldIdLst>
{slide_ids}
  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000"/>
</p:presentation>'''

    def _create_slide_xml(self, index: int, slide: SlideContent, theme: str) -> str:
        """生成单页幻灯片 XML"""
        # 标题
        title_shape = f'''<p:sp>
    <p:nvSpPr>
      <p:cNvPr id="1" name="Title"/>
      <p:cNvSpPr txBox="1"/>
      <p:nvPr/>
    </p:nvSpPr>
    <p:spPr>
      <a:xfrm><a:off x="457200" y="274638"/><a:ext cx="11277600" cy="1143000"/></a:xfrm>
    </p:spPr>
    <p:txBody>
      <a:bodyPr/>
      <a:lstStyle/>
      <a:p><a:r><a:rPr lang="zh-CN" sz="4400" b="1"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill></a:rPr><a:t>{slide.title}</a:t></a:r></a:p>
    </p:txBody>
  </p:sp>'''

        # 要点列表
        bullets_xml = ""
        if slide.bullets:
            bullets_content = "\n".join([
                f'          <a:p><a:r><a:rPr lang="zh-CN" sz="2400"/><a:t>{bullet}</a:t></a:r></a:p>'
                for bullet in slide.bullets
            ])
            bullets_xml = f'''<p:sp>
    <p:nvSpPr>
      <p:cNvPr id="2" name="Content"/>
      <p:cNvSpPr txBox="1"/>
      <p:nvPr/>
    </p:nvSpPr>
    <p:spPr>
      <a:xfrm><a:off x="457200" y="1600200"/><a:ext cx="11277600" cy="4800600"/></a:xfrm>
    </p:spPr>
    <p:txBody>
      <a:bodyPr/>
      <a:lstStyle/>
{bullets_content}
    </p:txBody>
  </p:sp>'''

        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="0" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
{title_shape}
{bullets_xml}
    </p:spTree>
  </p:cSld>
</p:sld>'''

    def _get_app_xml(self, title: str, slide_count: int) -> str:
        """生成 docProps/app.xml"""
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ExtendedProperties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Microsoft Office PowerPoint</Application>
  <Slides>{slide_count}</Slides>
  <Company/>
  <Manager/>
</ExtendedProperties>'''


# 单例
_pptx_generator = None


def get_pptx_generator() -> PPTXGenerator:
    """获取 PPT 生成器实例"""
    global _pptx_generator
    if _pptx_generator is None:
        _pptx_generator = PPTXGenerator()
    return _pptx_generator

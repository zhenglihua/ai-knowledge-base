import os
import PyPDF2
from docx import Document as DocxDocument
from typing import Optional

class DocumentParser:
    """文档解析器"""
    
    def parse(self, file_path: str, filename: str) -> str:
        """根据文件类型解析文档"""
        ext = filename.split('.')[-1].lower()
        
        if ext == 'pdf':
            return self._parse_pdf(file_path)
        elif ext in ['docx', 'doc']:
            return self._parse_docx(file_path)
        elif ext == 'txt':
            return self._parse_txt(file_path)
        else:
            # 其他类型尝试作为文本读取
            return self._parse_txt(file_path)
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            text = f"[PDF解析错误: {str(e)}]"
        return text.strip()
    
    def _parse_docx(self, file_path: str) -> str:
        """解析Word文件"""
        text = ""
        try:
            doc = DocxDocument(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"[Word解析错误: {str(e)}]"
        return text.strip()
    
    def _parse_txt(self, file_path: str) -> str:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except:
                return "[文本解析错误: 无法解码]"
        except Exception as e:
            return f"[文本解析错误: {str(e)}]"

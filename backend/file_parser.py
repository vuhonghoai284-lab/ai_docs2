"""文件解析模块"""
import PyPDF2
from docx import Document
import os

class FileParser:
    """文件解析器"""
    
    def parse(self, file_path: str) -> str:
        """根据文件类型解析文件"""
        if file_path.endswith('.pdf'):
            return self.parse_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self.parse_docx(file_path)
        elif file_path.endswith('.md'):
            return self.parse_markdown(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_path}")
    
    def parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- 第{page_num + 1}页 ---\n"
                        text += page_text
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}")
        return text
    
    def parse_docx(self, file_path: str) -> str:
        """解析Word文档"""
        try:
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            return '\n'.join(paragraphs)
        except Exception as e:
            raise Exception(f"Word文档解析失败: {str(e)}")
    
    def parse_markdown(self, file_path: str) -> str:
        """解析Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Markdown文件解析失败: {str(e)}")
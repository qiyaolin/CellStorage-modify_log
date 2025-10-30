#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DYMO Label Template Parser
解析.label文件并提取textbox和labelbox对象，支持动态模板更新
"""

import xml.etree.ElementTree as ET
import os
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class LabelTemplateParser:
    def __init__(self):
        self.template_cache = {}
        
    def parse_label_file(self, label_file_path: str) -> Dict[str, Any]:
        """
        解析.label文件，提取textbox和barcode对象信息
        
        Args:
            label_file_path: .label文件路径
            
        Returns:
            包含模板信息的字典
        """
        try:
            if not os.path.exists(label_file_path):
                raise FileNotFoundError(f"Label file not found: {label_file_path}")
                
            # 检查缓存
            file_mtime = os.path.getmtime(label_file_path)
            cache_key = f"{label_file_path}:{file_mtime}"
            
            if cache_key in self.template_cache:
                logger.info(f"Using cached template for {label_file_path}")
                return self.template_cache[cache_key]
            
            # 解析XML文件
            tree = ET.parse(label_file_path)
            root = tree.getroot()
            
            template_info = {
                'file_path': label_file_path,
                'file_mtime': file_mtime,
                'label_type': root.tag,
                'text_objects': [],
                'barcode_objects': [],
                'raw_xml': ET.tostring(root, encoding='unicode')
            }
            
            # 提取基本标签信息
            template_info.update(self._extract_label_properties(root))
            
            # 查找所有TextObject和BarcodeObject
            self._extract_objects(root, template_info)
            
            # 缓存结果
            self.template_cache[cache_key] = template_info
            logger.info(f"Parsed label template: {len(template_info['text_objects'])} text objects, {len(template_info['barcode_objects'])} barcode objects")
            
            return template_info
            
        except Exception as e:
            logger.error(f"Failed to parse label file {label_file_path}: {e}")
            raise
    
    def _extract_label_properties(self, root: ET.Element) -> Dict[str, Any]:
        """提取标签基本属性"""
        properties = {}
        
        # 标签类型相关属性
        properties['version'] = root.get('Version', '8.0')
        properties['units'] = root.get('Units', 'twips')
        
        # 查找基本属性
        for child in root:
            if child.tag == 'PaperOrientation':
                properties['paper_orientation'] = child.text
            elif child.tag == 'Id':
                properties['label_id'] = child.text
            elif child.tag == 'PaperName':
                properties['paper_name'] = child.text
            elif child.tag == 'LengthMode':
                properties['length_mode'] = child.text
            elif child.tag == 'LabelLength':
                properties['label_length'] = child.text
                
        return properties
    
    def _extract_objects(self, element: ET.Element, template_info: Dict[str, Any]):
        """递归提取TextObject和BarcodeObject"""
        
        # 检查当前元素
        if element.tag == 'TextObject':
            text_obj = self._parse_text_object(element)
            template_info['text_objects'].append(text_obj)
        elif element.tag == 'BarcodeObject':
            barcode_obj = self._parse_barcode_object(element)
            template_info['barcode_objects'].append(barcode_obj)
        
        # 递归处理子元素
        for child in element:
            self._extract_objects(child, template_info)
    
    def _parse_text_object(self, text_element: ET.Element) -> Dict[str, Any]:
        """解析TextObject元素"""
        text_obj = {
            'name': None,
            'is_variable': False,
            'horizontal_alignment': 'Center',
            'vertical_alignment': 'Middle',
            'text_fit_mode': 'ShrinkToFit',
            'styled_text': None,
            'font_family': 'Arial',
            'font_size': '8',
            'font_bold': False,
            'fore_color': {'Alpha': '255', 'Red': '0', 'Green': '0', 'Blue': '0'}
        }
        
        for child in text_element:
            if child.tag == 'Name':
                text_obj['name'] = child.text
            elif child.tag == 'IsVariable':
                text_obj['is_variable'] = child.text == 'True'
            elif child.tag == 'HorizontalAlignment':
                text_obj['horizontal_alignment'] = child.text
            elif child.tag == 'VerticalAlignment':
                text_obj['vertical_alignment'] = child.text
            elif child.tag == 'TextFitMode':
                text_obj['text_fit_mode'] = child.text
            elif child.tag == 'ForeColor':
                text_obj['fore_color'] = dict(child.attrib)
            elif child.tag == 'StyledText':
                text_obj['styled_text'] = self._parse_styled_text(child)
        
        return text_obj
    
    def _parse_barcode_object(self, barcode_element: ET.Element) -> Dict[str, Any]:
        """解析BarcodeObject元素"""
        barcode_obj = {
            'name': None,
            'is_variable': False,
            'text': '',
            'type': 'Code128Auto',
            'size': 'Small',
            'text_position': 'None',
            'horizontal_alignment': 'Center',
            'fore_color': {'Alpha': '255', 'Red': '0', 'Green': '0', 'Blue': '0'}
        }
        
        for child in barcode_element:
            if child.tag == 'Name':
                barcode_obj['name'] = child.text
            elif child.tag == 'IsVariable':
                barcode_obj['is_variable'] = child.text == 'True'
            elif child.tag == 'Text':
                barcode_obj['text'] = child.text or ''
            elif child.tag == 'Type':
                barcode_obj['type'] = child.text
            elif child.tag == 'Size':
                barcode_obj['size'] = child.text
            elif child.tag == 'TextPosition':
                barcode_obj['text_position'] = child.text
            elif child.tag == 'HorizontalAlignment':
                barcode_obj['horizontal_alignment'] = child.text
            elif child.tag == 'ForeColor':
                barcode_obj['fore_color'] = dict(child.attrib)
        
        return barcode_obj
    
    def _parse_styled_text(self, styled_text_element: ET.Element) -> Dict[str, Any]:
        """解析StyledText元素"""
        styled_text = {
            'elements': []
        }
        
        for element in styled_text_element.findall('Element'):
            element_info = {
                'string': '',
                'font_family': 'Arial',
                'font_size': '8',
                'font_bold': False,
                'font_italic': False,
                'font_underline': False,
                'fore_color': {'Alpha': '255', 'Red': '0', 'Green': '0', 'Blue': '0'}
            }
            
            string_elem = element.find('String')
            if string_elem is not None:
                element_info['string'] = string_elem.text or ''
            
            attributes = element.find('Attributes')
            if attributes is not None:
                font = attributes.find('Font')
                if font is not None:
                    element_info['font_family'] = font.get('Family', 'Arial')
                    element_info['font_size'] = font.get('Size', '8')
                    element_info['font_bold'] = font.get('Bold', 'False') == 'True'
                    element_info['font_italic'] = font.get('Italic', 'False') == 'True'
                    element_info['font_underline'] = font.get('Underline', 'False') == 'True'
                
                fore_color = attributes.find('ForeColor')
                if fore_color is not None:
                    element_info['fore_color'] = dict(fore_color.attrib)
            
            styled_text['elements'].append(element_info)
        
        return styled_text
    
    def generate_dynamic_xml(self, template_info: Dict[str, Any], data: Dict[str, str]) -> str:
        """
        基于模板信息和数据生成动态XML
        
        Args:
            template_info: 从parse_label_file获取的模板信息
            data: 包含实际数据的字典，如{'item_name': 'Test Item', 'barcode': '123456'}
        
        Returns:
            生成的XML字符串
        """
        try:
            # 解析原始XML
            root = ET.fromstring(template_info['raw_xml'])
            
            # 更新所有变量对象
            self._update_xml_objects(root, template_info, data)
            
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic XML: {e}")
            raise
    
    def _update_xml_objects(self, element: ET.Element, template_info: Dict[str, Any], data: Dict[str, str]):
        """递归更新XML中的可变对象"""
        
        if element.tag == 'TextObject':
            self._update_text_object(element, data)
        elif element.tag == 'BarcodeObject':
            self._update_barcode_object(element, data)
        
        # 递归处理子元素
        for child in element:
            self._update_xml_objects(child, template_info, data)
    
    def _update_text_object(self, text_element: ET.Element, data: Dict[str, str]):
        """更新TextObject中的文本内容"""
        name_elem = text_element.find('Name')
        
        if name_elem is not None:
            name = name_elem.text
            
            if name:
                # 根据对象名称匹配数据 - 不论是否为变量都更新
                text_content = self._match_text_content(name, data)
                if text_content:
                    self._update_styled_text(text_element, text_content)
    
    def _update_barcode_object(self, barcode_element: ET.Element, data: Dict[str, str]):
        """更新BarcodeObject中的条码内容"""
        name_elem = barcode_element.find('Name')
        text_elem = barcode_element.find('Text')
        
        if name_elem is not None and text_elem is not None:
            name = name_elem.text
            
            if name:
                # 根据对象名称匹配数据 - 不论是否为变量都更新
                barcode_content = self._match_barcode_content(name, data)
                if barcode_content:
                    text_elem.text = barcode_content
    
    def _match_text_content(self, object_name: str, data: Dict[str, str]) -> Optional[str]:
        """根据对象名称匹配文本内容"""
        name_lower = object_name.lower()
        
        # 优先匹配特定的对象名称
        if name_lower == 'textbox':
            return data.get('custom_text') or data.get('item_name', '')
        elif 'text' in name_lower:
            return data.get('custom_text') or data.get('item_name', '')
        elif 'item' in name_lower or 'name' in name_lower:
            return data.get('item_name', '')
        elif 'custom' in name_lower:
            return data.get('custom_text', '')
        
        # 默认返回item_name或custom_text
        return data.get('custom_text') or data.get('item_name', '')
    
    def _match_barcode_content(self, object_name: str, data: Dict[str, str]) -> Optional[str]:
        """根据对象名称匹配条码内容"""
        name_lower = object_name.lower()
        
        # 优先匹配特定的对象名称
        if name_lower == 'labelbox':
            return data.get('barcode', '')
        elif 'barcode' in name_lower or 'code' in name_lower:
            return data.get('barcode', '')
        elif 'label' in name_lower:
            return data.get('barcode', '')
        
        # 默认返回barcode
        return data.get('barcode', '')
    
    def _update_styled_text(self, text_element: ET.Element, content: str):
        """更新StyledText元素的内容"""
        styled_text = text_element.find('StyledText')
        if styled_text is not None:
            # 查找第一个Element
            element = styled_text.find('Element')
            if element is not None:
                string_elem = element.find('String')
                if string_elem is not None:
                    string_elem.text = content
                else:
                    # 创建新的String元素
                    string_elem = ET.SubElement(element, 'String')
                    string_elem.set('xml:space', 'preserve')
                    string_elem.text = content
            else:
                # 如果没有Element，创建一个完整的Element结构
                element = ET.SubElement(styled_text, 'Element')
                string_elem = ET.SubElement(element, 'String')
                string_elem.set('xml:space', 'preserve')
                string_elem.text = content
                
                # 添加默认的Attributes
                attributes = ET.SubElement(element, 'Attributes')
                font = ET.SubElement(attributes, 'Font')
                font.set('Family', 'Arial')
                font.set('Size', '8')
                font.set('Bold', 'False')
                font.set('Italic', 'False')
                font.set('Underline', 'False')
                font.set('Strikeout', 'False')
                
                fore_color = ET.SubElement(attributes, 'ForeColor')
                fore_color.set('Alpha', '255')
                fore_color.set('Red', '0')
                fore_color.set('Green', '0')
                fore_color.set('Blue', '0')
                fore_color.set('HueScale', '100')
    
    def get_available_templates(self, template_dir: str) -> List[str]:
        """获取指定目录下所有可用的.label模板文件"""
        templates = []
        try:
            if os.path.exists(template_dir):
                for file in os.listdir(template_dir):
                    if file.lower().endswith('.label'):
                        templates.append(os.path.join(template_dir, file))
        except Exception as e:
            logger.error(f"Failed to scan template directory {template_dir}: {e}")
        
        return templates
    
    def clear_cache(self):
        """清空模板缓存"""
        self.template_cache.clear()
        logger.info("Template cache cleared")


# 便捷函数
def parse_label_template(label_file_path: str) -> Dict[str, Any]:
    """便捷函数：解析单个标签模板文件"""
    parser = LabelTemplateParser()
    return parser.parse_label_file(label_file_path)

def generate_label_xml(label_file_path: str, data: Dict[str, str]) -> str:
    """便捷函数：生成标签XML"""
    parser = LabelTemplateParser()
    template_info = parser.parse_label_file(label_file_path)
    return parser.generate_dynamic_xml(template_info, data)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        label_file = sys.argv[1]
        parser = LabelTemplateParser()
        
        try:
            # 解析模板
            template_info = parser.parse_label_file(label_file)
            print("Template Info:")
            print(json.dumps(template_info, indent=2, ensure_ascii=False))
            
            # 生成示例XML
            sample_data = {
                'item_name': 'Test Item',
                'barcode': 'TEST123456',
                'custom_text': 'Custom Text'
            }
            
            xml_output = parser.generate_dynamic_xml(template_info, sample_data)
            print("\nGenerated XML:")
            print(xml_output)
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python label_template_parser.py <label_file_path>")
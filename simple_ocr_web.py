#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易OCR Web服务
使用PaddleOCR提供的在线API服务
"""

import os
import json
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify
import requests
from PIL import Image
import numpy as np

app = Flask(__name__)

# PaddleOCR在线API接口（使用第三方服务或本地服务）
def call_ocr_api(image_data):
    """调用OCR API进行文字识别"""
    try:
        # 首先尝试使用本地安装的PaddleOCR
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            result = ocr.ocr(image_data)
            
            # 格式化结果
            text_results = []
            for line in result:
                for word_info in line:
                    text = word_info[1][0]
                    confidence = word_info[1][1]
                    box = word_info[0]
                    text_results.append({
                        'text': text,
                        'confidence': float(confidence),
                        'bbox': box
                    })
            
            return text_results
        except ImportError:
            # 如果没有安装PaddleOCR，使用在线API
            pass
        
        # 使用在线OCR服务（示例，需要替换为真实的API）
        # 注意：这里只是一个示例，实际使用时需要申请相应的API服务
        url = "https://api.ocr.space/parse/image"
        
        # 将图像转换为base64
        img_str = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            'base64Image': f'data:image/jpeg;base64,{img_str}',
            'apikey': 'helloworld',  # 需要替换为真实的API密钥
            'language': 'chs'
        }
        
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('IsErroredOnProcessing'):
                return {'error': 'OCR处理错误'}
            
            # 解析结果
            text_results = []
            for parsed_result in result.get('ParsedResults', []):
                text = parsed_result.get('ParsedText', '')
                text_results.append({
                    'text': text.strip(),
                    'confidence': 0.9,  # 在线服务可能不提供置信度
                    'bbox': []
                })
            
            return text_results
        else:
            return {'error': f'API请求失败: {response.status_code}'}
            
    except Exception as e:
        return {'error': f'OCR处理异常: {str(e)}'}

def preprocess_image(image_file):
    """预处理上传的图像"""
    try:
        # 读取图像
        image = Image.open(image_file.stream)
        
        # 转换为RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整图像大小（避免过大图像）
        max_size = (2000, 2000)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转换为字节流
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        return img_byte_arr
    except Exception as e:
        raise Exception(f'图像预处理失败: {str(e)}')

@app.route('/')
def index():
    """主页面"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OCR文字识别服务</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin-bottom: 20px;
                cursor: pointer;
                transition: border-color 0.3s;
            }
            .upload-area:hover {
                border-color: #007bff;
            }
            .upload-area.dragover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            #file-input {
                display: none;
            }
            .upload-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .upload-btn:hover {
                background: #0056b3;
            }
            .result-area {
                margin-top: 30px;
            }
            .image-preview {
                max-width: 100%;
                max-height: 400px;
                margin: 20px 0;
            }
            .text-result {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                white-space: pre-wrap;
                line-height: 1.6;
            }
            .loading {
                display: none;
                text-align: center;
                color: #666;
            }
            .error {
                color: #dc3545;
                background: #f8d7da;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>OCR文字识别服务</h1>
            
            <div class="upload-area" id="upload-area">
                <input type="file" id="file-input" accept="image/*">
                <p>点击选择图片或拖拽图片到此处</p>
                <p style="font-size: 14px; color: #666;">支持格式: JPG, PNG, BMP等</p>
                <button class="upload-btn" onclick="document.getElementById('file-input').click()">
                    选择图片
                </button>
            </div>
            
            <div class="loading" id="loading">
                <p>正在识别中，请稍候...</p>
            </div>
            
            <div class="result-area" id="result-area">
                <!-- 结果将显示在这里 -->
            </div>
        </div>

        <script>
            const uploadArea = document.getElementById('upload-area');
            const fileInput = document.getElementById('file-input');
            const resultArea = document.getElementById('result-area');
            const loading = document.getElementById('loading');

            // 拖拽功能
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                }
            });

            // 文件选择
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });

            function handleFile(file) {
                if (!file.type.startsWith('image/')) {
                    alert('请选择图片文件');
                    return;
                }

                loading.style.display = 'block';
                resultArea.innerHTML = '';

                const formData = new FormData();
                formData.append('image', file);

                fetch('/ocr', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';
                    displayResults(data, file);
                })
                .catch(error => {
                    loading.style.display = 'none';
                    resultArea.innerHTML = `<div class="error">识别失败: ${error}</div>`;
                });
            }

            function displayResults(data, file) {
                let html = '';

                // 显示图片预览
                const reader = new FileReader();
                reader.onload = function(e) {
                    html += `<h3>上传的图片:</h3>`;
                    html += `<img src="${e.target.result}" class="image-preview" alt="预览">`;
                    
                    // 显示识别结果
                    if (data.error) {
                        html += `<div class="error">错误: ${data.error}</div>`;
                    } else {
                        html += `<h3>识别结果:</h3>`;
                        if (data.results && data.results.length > 0) {
                            data.results.forEach((result, index) => {
                                html += `<div class="text-result">`;
                                html += `<strong>文本 ${index + 1}:</strong> ${result.text}<br>`;
                                if (result.confidence) {
                                    html += `<small>置信度: ${(result.confidence * 100).toFixed(2)}%</small>`;
                                }
                                html += `</div>`;
                            });
                        } else {
                            html += `<div class="text-result">未识别到文字</div>`;
                        }
                    }
                    
                    resultArea.innerHTML = html;
                };
                reader.readAsDataURL(file);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/ocr', methods=['POST'])
def ocr():
    """OCR识别接口"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 预处理图像
        processed_image = preprocess_image(image_file)
        
        # 调用OCR API
        ocr_results = call_ocr_api(processed_image)
        
        if 'error' in ocr_results:
            return jsonify({'error': ocr_results['error']}), 500
        
        return jsonify({'results': ocr_results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 检查是否安装了PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("PaddleOCR已安装，使用本地OCR引擎")
    except ImportError:
        print("PaddleOCR未安装，将使用在线OCR服务（需要配置API密钥）")
    
    # 启动Web服务
    app.run(host='0.0.0.0', port=5000, debug=True)
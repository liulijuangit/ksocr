#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础OCR Web服务
使用基本的Python库实现OCR功能
"""

import os
import json
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify
import requests
from PIL import Image

app = Flask(__name__)

# 简化的OCR功能
def call_ocr_api(image_data):
    """调用OCR API进行文字识别"""
    try:
        # 这里使用一个简单的文本识别示例
        # 实际使用时应该调用OCR服务
        
        # 尝试使用在线OCR服务（免费版本）
        url = "https://api.ocr.space/parse/image"
        
        # 将图像转换为base64
        img_str = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            'base64Image': f'data:image/jpeg;base64,{img_str}',
            'apikey': 'K83885682688957',  # 免费API密钥
            'language': 'chs',
            'OCREngine': '2'
        }
        
        response = requests.post(url, data=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('IsErroredOnProcessing'):
                return {'error': 'OCR处理错误: ' + result.get('ErrorMessage', '未知错误')}
            
            # 解析结果
            text_results = []
            for parsed_result in result.get('ParsedResults', []):
                text = parsed_result.get('ParsedText', '')
                if text.strip():
                    text_results.append({
                        'text': text.strip(),
                        'confidence': 0.9,
                        'bbox': []
                    })
            
            if not text_results:
                return {'error': '未识别到文字'}
            
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
            .success {
                color: #155724;
                background: #d4edda;
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
                        html += `<div class="success">识别成功！</div>`;
                        html += `<h3>识别结果:</h3>`;
                        if (data.results && data.results.length > 0) {
                            data.results.forEach((result, index) => {
                                html += `<div class="text-result">`;
                                html += `<strong>文本 ${index + 1}:</strong> ${result.text}<br>`;
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
    print("启动OCR Web服务...")
    print("服务地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    
    # 启动Web服务
    app.run(host='0.0.0.0', port=5000, debug=True)
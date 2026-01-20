import os
import random
from docx import Document

# Configuration - 请根据实际情况修改以下路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(PROJECT_ROOT, 'sample_data')  # 原始文档目录
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'noise_analysis_sample.txt')

def get_all_docx_files(root_dir):
    docx_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.docx') and not file.startswith('~'): # Ignore temp files
                docx_files.append(os.path.join(root, file))
    return docx_files

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            # We preserve empty lines to see structure, but maybe trim whitespace
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading file: {str(e)}"

def main():
    all_files = get_all_docx_files(BASE_DIR)
    
    if not all_files:
        print("No .docx files found!")
        return

    # Randomly sample 10 files (or fewer if less than 10 exist)
    sample_size = min(10, len(all_files))
    sampled_files = random.sample(all_files, sample_size)
    
    output_lines = []
    output_lines.append(f"=== 随机抽取 {sample_size} 篇文档进行噪音分析 ===\n")
    
    for i, file_path in enumerate(sampled_files, 1):
        filename = os.path.basename(file_path)
        content = extract_text_from_docx(file_path)
        
        output_lines.append(f"\n{'='*20} 文档 {i}: {filename} {'='*20}")
        output_lines.append(f"路径: {file_path}")
        output_lines.append(f"{'-'*20} 原始内容开始 {'-'*20}")
        output_lines.append(content)
        output_lines.append(f"{'-'*20} 原始内容结束 {'-'*20}\n")

    # Write to file for inspection
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        
    print(f"Sampling complete. Analysis saved to: {OUTPUT_FILE}")
    print(f"Total files found: {len(all_files)}")

if __name__ == "__main__":
    main()

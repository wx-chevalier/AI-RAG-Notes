import os
import json
import mimetypes
from minio import Minio
from minio.error import S3Error
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MinIO 配置
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "industrial-kb-images"
SECURE = False  # 如果是 https 则设为 True

# 路径配置
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "Cleaned_Knowledge_Base" / "images"
MAPPING_FILE = PROJECT_ROOT / "POC" / "image_url_mapping.json"

def get_content_type(filename):
    """根据文件名猜测 Content-Type"""
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def set_bucket_public_read(client, bucket_name):
    """设置 Bucket 为公开只读"""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
            }
        ]
    }
    try:
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        logging.info(f"Bucket '{bucket_name}' set to public read.")
    except Exception as e:
        logging.error(f"Failed to set bucket policy: {e}")

def main():
    # 1. 初始化 MinIO 客户端
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=SECURE
        )
        logging.info("Connected to MinIO.")
    except Exception as e:
        logging.error(f"Failed to connect to MinIO: {e}")
        return

    # 2. 创建 Bucket
    try:
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            logging.info(f"Bucket '{BUCKET_NAME}' created.")
        else:
            logging.info(f"Bucket '{BUCKET_NAME}' already exists.")
        
        # 设置公开访问权限
        set_bucket_public_read(client, BUCKET_NAME)

    except S3Error as e:
        logging.error(f"MinIO S3 Error: {e}")
        return

    # 3. 遍历并上传图片
    if not IMAGES_DIR.exists():
        logging.error(f"Images directory not found at {IMAGES_DIR}")
        return

    image_mapping = {}
    files = list(IMAGES_DIR.glob("**/*"))
    total_files = len([f for f in files if f.is_file()])
    logging.info(f"Found {total_files} files to process.")

    for i, file_path in enumerate(files):
        if not file_path.is_file():
            continue
            
        object_name = file_path.name # 使用文件名作为对象名，假设文件名唯一
        # 如果需要保留子目录结构，可以使用: object_name = str(file_path.relative_to(IMAGES_DIR))

        try:
            content_type = get_content_type(file_path.name)
            client.fput_object(
                BUCKET_NAME,
                object_name,
                str(file_path),
                content_type=content_type
            )
            
            # 生成可访问的 URL
            # 注意: localhost:9000 在 docker 内部可能无法访问，前端访问需要是浏览器可达的地址
            # 这里生成标准的 HTTP URL
            protocol = "https" if SECURE else "http"
            url = f"{protocol}://localhost:9000/{BUCKET_NAME}/{object_name}"
            
            # 记录在映射表中
            # 假设 Cleaned Markdown 里的图片引用是 images/xxx.png
            # Map key format: "images/xxx.png" -> "http://..."
            image_mapping[f"images/{object_name}"] = url
            
            if (i + 1) % 100 == 0:
                logging.info(f"Uploaded {i + 1}/{total_files} images...")

        except Exception as e:
            logging.error(f"Failed to upload {file_path.name}: {e}")

    # 4. 保存映射文件
    try:
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(image_mapping, f, indent=2, ensure_ascii=False)
        logging.info(f"Migration completed. Mapping saved to {MAPPING_FILE}")
        logging.info(f"Total images mapped: {len(image_mapping)}")
    except Exception as e:
        logging.error(f"Failed to save mapping file: {e}")

if __name__ == "__main__":
    main()

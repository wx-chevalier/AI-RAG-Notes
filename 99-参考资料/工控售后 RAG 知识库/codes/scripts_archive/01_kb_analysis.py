import os

# Configuration - 请根据实际情况修改以下路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_ROOT_DIR = os.path.join(PROJECT_ROOT, 'sample_data')  # 原始文档目录
OUTPUT_REPORT_PATH = os.path.join(PROJECT_ROOT, 'kb_analysis_report.md')

def generate_directory_structure(root_dir, output_file):
    """
    Generates a markdown report of the directory structure and file statistics.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Knowledge Base Directory Analysis Report\n\n")
            f.write(f"**Root Directory:** `{root_dir}`\n\n")
            f.write("## 1. Directory Structure\n\n")
            f.write("```text\n")

            total_files = 0
            total_dirs = 0
            total_size_bytes = 0
            file_extensions = {}
            empty_dirs = []

            for root, dirs, files in os.walk(root_dir):
                level = root.replace(root_dir, '').count(os.sep)
                indent = ' ' * 4 * (level)
                f.write(f"{indent}{os.path.basename(root)}/\n")
                
                total_dirs += 1
                if not dirs and not files:
                     empty_dirs.append(root)

                subindent = ' ' * 4 * (level + 1)
                for file in files:
                    if file.startswith('.'): continue # skip hidden files
                    f.write(f"{subindent}{file}\n")
                    total_files += 1
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size_bytes += size
                    except OSError:
                        pass
                    
                    ext = os.path.splitext(file)[1].lower()
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            f.write("```\n\n")
            
            # --- Statistics ---
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            f.write("## 2. Statistical Summary\n\n")
            f.write(f"- **Total Directories:** {total_dirs}\n")
            f.write(f"- **Total Files:** {total_files}\n")
            f.write(f"- **Total Size:** {total_size_mb:.2f} MB\n")
            
            f.write("\n### File Types Distribution:\n")
            for ext, count in file_extensions.items():
                f.write(f"- **{ext or 'No Extension'}**: {count}\n")
                
            f.write("\n### Empty Directories:\n")
            if empty_dirs:
                 for ed in empty_dirs:
                     rel_path = ed.replace(root_dir, '')
                     f.write(f"- `{rel_path}`\n")
            else:
                f.write("None\n")

        print(f"Report generated successfully at: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_directory_structure(KB_ROOT_DIR, OUTPUT_REPORT_PATH)

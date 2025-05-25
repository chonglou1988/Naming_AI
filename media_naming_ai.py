import os
import csv
import requests
from pathlib import Path

# Optional: import only if used
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

def is_media_file(filename):
    """Check if the file is a media file based on its extension."""
    media_extensions = {
        # Video formats
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.m4v', '.3gp','.rmvb','.iso'
        # Audio formats
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a'
    }
    return os.path.splitext(filename.lower())[1] in media_extensions

def get_media_files(directory):
    """Get a list of media files in the specified directory and subdirectories."""
    media_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if is_media_file(file):
                full_path = os.path.join(root, file)
                media_files.append(full_path)
    return media_files

def suggest_normalized_name(file_path, backend="grok", **kwargs):
    """
    根据所选后端调用不同的大模型建议文件名。
    
    参数:
        file_path (str): 原始文件路径
        backend (str): 可选值："openai"、"claude"、"local"、"grok" (暂时只使用"grok")
        kwargs: 各后端所需额外参数（如 api_key、endpoint）

    返回:
        str: 建议的新文件名
    """
    file_name = os.path.basename(file_path)
    folder_name = os.path.basename(os.path.dirname(file_path))

    prompt = (
        f"请根据以下信息，建议一个简洁、规范化的文件名，（只返回建议的文件名，不加解释）：**\n\n"
        f"文件地址：{file_path}"
        f"文件夹名称: {folder_name}\n"
        f"原文件名称: {file_name}"
    )

    # 暂时停用除grok之外的AI调用
    # if backend == "openai":
    #     return call_openai_chat(prompt, **kwargs)
    # elif backend == "claude":
    #     return call_claude(prompt, **kwargs)
    # elif backend == "local":
    #     return call_local_llm(prompt, **kwargs)
    # elif backend == "grok":
    return call_grok(prompt, **kwargs)
    # else:
    #     raise ValueError(f"Unsupported backend: {backend}")


# ------------------------------
# OpenAI 调用（GPT-4 或 GPT-3.5）
# ------------------------------
def call_openai_chat(prompt, api_key=None, model="gpt-4"):
    if openai is None:
        raise ImportError("openai 库未安装。请运行 pip install openai")
    openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个文件命名助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[OpenAI Error] {e}")
        return None


# ------------------------------
# Claude（Anthropic）
# ------------------------------
def call_claude(prompt, api_key=None, model="claude-3-opus-20240229"):
    if anthropic is None:
        raise ImportError("anthropic 库未安装。请运行 pip install anthropic")
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    try:
        response = client.messages.create(
            model=model,
            max_tokens=50,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[Claude Error] {e}")
        return None


# ------------------------------
# 本地部署模型接口（如 FastChat, llama.cpp）
# ------------------------------
def call_local_llm(prompt, endpoint="http://localhost:8000/v1/chat/completions", model="local-llm"):
    try:
        response = requests.post(endpoint, json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个擅长内容归类和命名的助手。现在我会提供一个文件的上下文信息，请你根据这些信息，生成一个规范、简洁的中文名称，用于命名电影、电视剧或音乐文件。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 50
        })
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Local LLM Error] {e}")
        return None


# ------------------------------
# Grok (xAI)
# ------------------------------
def call_grok(prompt, api_key=None, model="grok-3"):
    # Using OpenAI client for Grok API call as per provided template
    if openai is None:
        raise ImportError("openai 库未安装。请运行 pip install openai")
    api_key = api_key or "xai-ew92NXieWDPNM31CxB9i9zjnR88qowQ0O3dOwIBaGv7fvah4WcJMeO8fW9d7sUZeetz6xgry2FyB25eD"
    try:
        client = openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "请遵循以下规则：1. **仅输出建议的文件名本身，不要输出解释说明。**2. **名称应避免冗长，体现核心信息，便于整理归档。**3. **保留关键标识信息，例如片名、歌名、年份、季数/集数（如适用），但不包含无意义的英文或随机字符。例如：扫黑风暴（2021）S1 EP01**4. **使用中文命名，如果原名为英文且广为人知，可以保留或翻译为中文。**5. **不要添加扩展名（如 .mp4、.mp3），也不要添加多余标点。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Grok Error] {e}")
        file_name_part = prompt.split('原文件名称: ')[1].splitlines()[0]
        return f"Grok_Suggested_{os.path.basename(file_name_part)}"

def generate_csv_report(media_files, output_file):
    """Generate a CSV report with original and recommended file names."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original Path', 'Original Name', 'Recommended Name'])
        for file_path in media_files:
            original_name = os.path.basename(file_path)
            recommended_name = suggest_normalized_name(file_path)
            if not recommended_name:
                recommended_name = f"Error_Suggesting_Name_{original_name}"
            writer.writerow([file_path, original_name, recommended_name])

def main():
    """Main function to scan for media files and generate a naming report."""
    print("Starting media file naming analysis...")
    directory = input("Enter the directory path to scan for media files: ")
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return
    
    media_files = get_media_files(directory)
    if not media_files:
        print("No media files found in the specified directory.")
        return
    
    print(f"Found {len(media_files)} media files.")
    output_file = "media_naming_report.csv"
    generate_csv_report(media_files, output_file)
    print(f"CSV report generated: {output_file}")

if __name__ == "__main__":
    main()

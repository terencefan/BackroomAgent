#!/usr/bin/env python3
"""
生成 Git commit message 的脚本
使用 LLM 分析 git diff 并生成合适的 commit message
"""

import os
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_staged_diff() -> str:
    """获取暂存区的 diff"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def get_staged_files() -> list[str]:
    """获取暂存区的文件列表"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        return []


def generate_commit_message(diff: str, files: list[str]) -> str:
    """使用 LLM 生成 commit message"""
    if not diff:
        return ""

    # 构建 prompt
    system_prompt = """你是一个专业的 Git commit message 生成助手。
请根据提供的 git diff 信息，生成一个清晰、简洁、符合规范的 commit message。

要求：
1. 使用中文或英文（根据代码变更内容决定）
2. 第一行是简短的主题（不超过 50 个字符）
3. 如果需要，可以添加空行后写详细说明
4. 遵循常见的 commit message 规范（如 Conventional Commits）
5. 只返回 commit message，不要添加其他说明文字

格式示例：
feat: 添加用户认证功能

- 实现登录和注册接口
- 添加 JWT token 验证
- 更新用户模型"""

    user_prompt = f"""请为以下代码变更生成 commit message：

变更的文件：
{chr(10).join(f'  - {f}' for f in files[:10])}
{f'  ... 还有 {len(files) - 10} 个文件' if len(files) > 10 else ''}

Git Diff:
{diff[:8000]}  # 限制长度避免 token 过多
"""

    try:
        print(f"🔗 正在连接 LLM ({MODEL_NAME})...", file=sys.stderr)
        llm = ChatOpenAI(
            api_key=API_KEY, base_url=BASE_URL, model=MODEL_NAME, temperature=0.3
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        print("💭 正在生成 commit message...", file=sys.stderr)
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        print(f"⚠️  生成 commit message 时出错: {e}", file=sys.stderr)
        return ""


def main():
    """主函数"""
    commit_msg_file = sys.argv[1] if len(sys.argv) > 1 else None
    commit_type = sys.argv[2] if len(sys.argv) > 2 else None

    # 如果是 merge commit 或已有 message，跳过
    if commit_type in ("merge", "squash", "commit"):
        return

    # 读取现有的 commit message（如果有）
    existing_msg = ""
    if commit_msg_file and os.path.exists(commit_msg_file):
        with open(commit_msg_file, "r", encoding="utf-8") as f:
            existing_msg = f.read().strip()

    # 如果已有非空的 commit message，跳过自动生成
    if existing_msg and not existing_msg.startswith("#"):
        return

    # 检查 API Key
    if not API_KEY:
        print("⚠️  OPENAI_API_KEY 未设置，跳过自动生成 commit message", file=sys.stderr)
        print(
            "💡 提示：在 .env 文件中设置 OPENAI_API_KEY 以启用自动生成功能",
            file=sys.stderr,
        )
        return

    print("🚀 开始自动生成 commit message...", file=sys.stderr)

    # 获取 diff 和文件列表
    print("📝 正在分析代码变更...", file=sys.stderr)
    diff = get_staged_diff()
    files = get_staged_files()

    if not diff or not files:
        print("ℹ️  暂存区没有变更，跳过生成 commit message", file=sys.stderr)
        return

    print(f"📊 检测到 {len(files)} 个文件的变更", file=sys.stderr)
    print("🤖 正在使用 LLM 生成 commit message，请稍候...", file=sys.stderr)

    # 生成 commit message
    generated_msg = generate_commit_message(diff, files)

    if generated_msg and commit_msg_file:
        # 写入 commit message 文件
        print("💾 正在保存 commit message...", file=sys.stderr)
        with open(commit_msg_file, "w", encoding="utf-8") as f:
            f.write(generated_msg)
            if not generated_msg.endswith("\n"):
                f.write("\n")
        print(
            f"✅ 已生成 commit message: {generated_msg.split(chr(10))[0]}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

import anthropic
import json
from core.config import settings

client = anthropic.Anthropic(
    api_key=settings.KIMI_API_KEY,
    base_url=settings.KIMI_BASE_URL,
)

def stream_kimi_for_plan(prompt: str):
    system_prompt = """你是一个业务逻辑解构工程师。
用户的指令是一段关于通过Python处理数据/计算的自然语言。
请提取在这个过程中，可以作为「环境变量/动态运行参数」的常量（例如：文件路径、特定的阈值、过滤条件等），以达到更高的代码复用性。
同时，清晰勾勒出步骤。
【最重要】：分析用户的指令，判断在纯净的 Python 环境下，是否需要额外安装第三方库（如 pandas, requests, numpy）。如果需要，请将依赖包的正确 `pip` 安装名收集起来。

你必须严格以合法的 JSON 格式输出，不要包含 ```json 标签包裹。
JSON格式包括三个部分：
{
  "steps": ["字符串步骤1", "字符串步骤2"...], 
  "parameters": [
      {"name": "变量名(纯英文及下划线)", "type": "number 或 string", "default": "提取的默认值", "description": "该变量中文含义说明"}
  ],
  "dependencies": ["需要的第三方库名，如果没有则为空数组"]
}
"""
    # 让前端一开始就能接到内部的指令拼接包
    yield f"data: {json.dumps({'type': 'system_prompt', 'content': system_prompt}, ensure_ascii=False)}\n\n"

    try:
        with client.messages.stream(
            model="kimi-for-coding",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


def stream_kimi_for_code(prompt: str, plan_dict: dict):
    params_info = "\n".join([f"- {p['name']}: {p['type']} (含义: {p['description']})" for p in plan_dict.get('parameters', [])])
    steps_info = "\n".join([f"第 {i} 步: {s}" for i, s in enumerate(plan_dict.get('steps', []))])
    
    system_prompt = f"""你是一个顶级Python数据工程师。
你的任务是根据用户的需求，配合已知的“执行计划”和“动态参数表”，生成一段纯Python代码。

已知的抽象执行步骤（请在代码内部严格对齐这些逻辑）：
{steps_info}

重要指示：
外部沙箱环境在执行这段代码前，已经向全局作用域(globals)中注入了以下预定好的变量名称，**你可以直接在代码中使用它们（如阈值限制等）**，**不要**在代码里二次声明或写死赋值这些预定参数变量的值：
{params_info}

非常重要（引擎硬性规范）：
在代码中，关于每一次业务抽象步骤开始的地方，**必须在其上方**放置以下特殊格式的注释锚标（N为步骤的索引数字，从 0 开始。例如 # [__BLOCK_MARK__: 0]）。不要漏掉也不要篡改格式！！
# [__BLOCK_MARK__: N]

约束要求：
1. 绝对不要返回任何 Markdown 语法标识符（如 ```python 等）。
2. 只返回纯文本形式的 Python 源代码，不要有解释说明。
3. 请把数据处理和计算的核心结果使用 print() 打印出来，格式美观一些，以便工程师查阅反馈。
"""
    yield f"data: {json.dumps({'type': 'system_prompt', 'content': system_prompt}, ensure_ascii=False)}\n\n"

    try:
        with client.messages.stream(
            model="kimi-for-coding",  
            max_tokens=8192, 
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


def stream_kimi_for_plan_refine(old_plan: dict, prompt: str):
    system_prompt = f"""你是一个业务架构优化师。
你之前已经生成了一份执行计划和相关提取出的动态参数表，格式为合法JSON：
{json.dumps(old_plan, ensure_ascii=False)}

现在工程师审查了这份草案，并给出了全新的补充指令或修正意见。
请你【吸纳他的意见】，对之前的这份 JSON 进行结构上或内容上的修改（例如新增他要加的变量，或者补全某一步骤）。如果修改后需要新的外部第三方库（如 numpy），请更新依赖。
输出要求：
1. 必须依旧是严格合法的完整的 JSON 格式（不要把没改动的部分省略掉，我要全量替换）。
2. 不要包含 ```json 的标识符包装。
3. 保持 "steps", "parameters", "dependencies" 三个 key 不变。
"""
    yield f"data: {json.dumps({'type': 'system_prompt', 'content': system_prompt}, ensure_ascii=False)}\n\n"

    try:
        with client.messages.stream(
            model="kimi-for-coding",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


def stream_kimi_for_fix(original_code: str, terminal_output: str, user_feedback: str):
    """AI 智能代码修复：根据报错信息和用户反馈，自动修正代码"""
    feedback_line = f"用户的补充说明：{user_feedback}" if user_feedback.strip() else "用户未提供额外说明，请自行根据报错信息诊断修复。"
    system_prompt = f"""你是一个 Python 代码急救专家。
以下是用户运行的一段 Python 代码，在沙箱中执行后产生了错误或不符合预期的输出。
你的任务是根据终端输出信息和用户的反馈意见，修复这段代码。

原始代码：
{original_code}

沙箱终端输出（含错误信息）：
{terminal_output}

{feedback_line}

修复要求：
1. 返回修复后的完整 Python 代码（不是补丁，是完整可运行的代码）。
2. 绝对不要返回任何 Markdown 语法标识符（如 ```python 等）。
3. 只返回纯文本形式的 Python 源代码，不要有解释说明文字。
4. 保留原始代码中的 # [__BLOCK_MARK__: N] 注释锚标，不要删除或修改它们的格式。
5. 如果原始代码的逻辑本身有问题，请大胆修改逻辑，但保持原有的业务意图不变。
"""
    yield f"data: {json.dumps({'type': 'system_prompt', 'content': system_prompt}, ensure_ascii=False)}\n\n"

    try:
        with client.messages.stream(
            model="kimi-for-coding",
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": "请修复上述代码并返回完整修复后的版本。"}],
            temperature=0.2
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


def stream_kimi_for_code_chat(current_code: str, user_instruction: str):
    """代码编辑器内 AI 对话：根据用户的自然语言指令修改当前代码"""
    system_prompt = f"""你是一个嵌入在代码编辑器中的 AI 编程助手。
用户正在编辑一段 Python 代码，他会用自然语言告诉你想要怎么修改。
请根据他的指令，对代码进行修改并返回修改后的完整代码。

当前编辑器中的代码：
{current_code}

修改要求：
1. 返回修改后的完整 Python 代码（不是补丁，是完整可运行的代码）。
2. 绝对不要返回任何 Markdown 语法标识符（如 ```python 等）。
3. 只返回纯文本形式的 Python 源代码，不要有解释说明文字。
4. 保留原始代码中的 # [__BLOCK_MARK__: N] 注释锚标，不要删除或修改它们的格式。
5. 如果用户的指令会新增业务步骤，请在对应位置添加新的 BLOCK_MARK 锚标。
"""
    yield f"data: {json.dumps({'type': 'system_prompt', 'content': system_prompt}, ensure_ascii=False)}\n\n"

    try:
        with client.messages.stream(
            model="kimi-for-coding",
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_instruction}],
            temperature=0.2
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"


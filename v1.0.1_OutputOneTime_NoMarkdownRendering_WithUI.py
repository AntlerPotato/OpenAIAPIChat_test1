import tkinter as tk
from tkinter import scrolledtext
from openai import OpenAI
import json

# 定义API请求的函数
def get_response():
    user_input = user_entry.get()
    if user_input.strip() == "":
        return

    user_entry.delete(0, tk.END)
    chat_text.configure(state='normal')
    chat_text.insert(tk.END, f"你：\n{user_input}\n")

    # 使用OpenAI库来发送请求
    client = OpenAI(api_key="your api-key", base_url="https://Proxy address/v1/")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )

    # 提取AI回复的内容
    ai_reply = response.choices[0].message.content
    chat_text.insert(tk.END, f"GPT：\n{ai_reply}\n")
    chat_text.configure(state='disabled')
    chat_text.yview(tk.END)

    # 保存详细的返回数据以供debug使用
    global debug_info
    debug_info = json.dumps(response.to_dict(), indent=4, ensure_ascii=False)

# 显示详细的返回数据
def show_debug():
    debug_window = tk.Toplevel(root)
    debug_window.title("Debug Information")
    debug_text = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=60, height=20)
    debug_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    debug_text.insert(tk.END, debug_info)

# 创建主窗口
root = tk.Tk()
root.title("AI Chat")

# 创建显示聊天内容的文本框
chat_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
chat_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_text.configure(state='disabled')

# 创建输入框和发送按钮
user_entry = tk.Entry(root, width=50)
user_entry.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
send_button = tk.Button(root, text="发送", command=get_response)
send_button.pack(side=tk.LEFT, pady=5)

# 创建debug按钮
debug_button = tk.Button(root, text="Debug", command=show_debug)
debug_button.pack(side=tk.LEFT, pady=5)

# 运行主循环
root.mainloop()
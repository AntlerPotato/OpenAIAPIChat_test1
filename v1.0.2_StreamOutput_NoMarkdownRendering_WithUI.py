import tkinter as tk
from tkinter import scrolledtext, messagebox
from openai import OpenAI
import json


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat")

        # 使窗口自适应大小
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # 创建一个滚动文本框用于显示AI回复
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.text_area.grid(column=0, row=0, padx=10, pady=10, sticky="nsew", columnspan=3)

        # 创建一个输入框
        self.entry = tk.Entry(self.root)
        self.entry.grid(column=0, row=1, padx=10, pady=10, sticky="ew")

        # 创建一个发送按钮
        self.send_button = tk.Button(self.root, text="发送", command=self.send_message)
        self.send_button.grid(column=1, row=1, padx=10, pady=10, sticky="ew")

        # 创建一个debug按钮
        self.debug_button = tk.Button(self.root, text="debug", command=self.show_debug_info)
        self.debug_button.grid(column=2, row=1, padx=10, pady=10, sticky="ew")

        # 设置列的自适应宽度
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)

        # 初始化OpenAI API
        self.client = OpenAI(
            api_key="your api-key",
            base_url="https://Proxy address/v1/"
        )

        self.debug_info = ""

    def send_message(self):
        user_message = self.entry.get()
        if user_message:
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, "你: " + "\n" + user_message + "\n")
            self.text_area.config(state='disabled')
            self.entry.delete(0, tk.END)
            self.get_ai_reply(user_message)

    def get_ai_reply(self, user_message):
        # 调用OpenAI API获取流式回复
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            stream=True  # 启用流式输出
        )

        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, "GPT: " + "\n")  # 添加前缀

        debug_info_list = []

        for chunk in response:
            debug_info_list.append(chunk)
            content = chunk.choices[0].delta.content
            if content:  # 检查内容是否为None
                self.text_area.insert(tk.END, content)
            self.text_area.update_idletasks()
        self.text_area.insert(tk.END, "\n")
        self.text_area.config(state='disabled')

        # 保存详细的返回数据以供debug使用
        self.debug_info = json.dumps([chunk.to_dict() for chunk in debug_info_list], indent=4, ensure_ascii=False)

    def show_debug_info(self):
        # 这里显示API响应的详细信息
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug Information")
        debug_text = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=60, height=20)
        debug_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        debug_text.insert(tk.END, self.debug_info)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
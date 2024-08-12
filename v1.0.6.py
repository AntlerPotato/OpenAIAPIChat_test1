import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
from openai import OpenAI
import json
import threading

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("800x600")

        # 配置根窗口的网格权重
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # 创建并配置消息框架
        self.message_frame = tk.Frame(self.root)
        self.message_frame.grid(column=0, row=0, padx=10, pady=10, sticky="nsew")
        self.message_frame.grid_columnconfigure(0, weight=1)
        self.message_frame.grid_rowconfigure(0, weight=1)

        # 创建并配置画布和滚动条
        self.canvas = tk.Canvas(self.message_frame)
        self.scrollbar = tk.Scrollbar(self.message_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 输入框和发送按钮框架
        input_frame = tk.Frame(self.root)
        input_frame.grid(column=0, row=1, padx=10, pady=5, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        # 输入框
        self.entry = tk.Entry(input_frame, width=50)
        self.entry.grid(column=0, row=0, padx=(0, 5), pady=5, sticky="ew")

        # 发送按钮
        self.send_button = tk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.grid(column=1, row=0, padx=5, pady=5, sticky="e")

        # 控制按钮框架
        control_frame = tk.Frame(self.root)
        control_frame.grid(column=0, row=2, padx=10, pady=5, sticky="ew")

        # 新对话按钮
        self.new_chat_button = tk.Button(control_frame, text="新对话", command=self.new_chat)
        self.new_chat_button.grid(column=0, row=0, padx=(0, 5), pady=5, sticky="w")

        # Debug按钮
        self.debug_button = tk.Button(control_frame, text="Debug", command=self.show_debug_info)
        self.debug_button.grid(column=1, row=0, padx=5, pady=5, sticky="w")

        # 流式输出复选框
        self.stream_var = tk.BooleanVar(value=True)
        self.stream_checkbox = tk.Checkbutton(control_frame, text="流式输出", variable=self.stream_var)
        self.stream_checkbox.grid(column=2, row=0, padx=5, pady=5, sticky="w")

        # 模式选择下拉菜单
        self.context_mode_var = tk.StringVar(value="上下文连续对话")
        self.context_mode_menu = tk.OptionMenu(control_frame, self.context_mode_var, "独立对话", "上下文连续对话")
        self.context_mode_menu.grid(column=3, row=0, padx=5, pady=5, sticky="w")

        # 加载用户和助手头像
        self.user_img = self.load_and_resize_image("images/user_icon.png", (30, 30))
        self.assistant_img = self.load_and_resize_image("images/chatgpt_icon.png", (30, 30))

        # 初始化OpenAI API
        self.client = OpenAI(
            api_key="your api-key",
            base_url="https://Proxy address/v1/"
        )

        self.debug_info = ""
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def load_and_resize_image(self, path, size):
        img = Image.open(path)
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def new_chat(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        # 重新配置画布的滚动区域为初始状态
        self.canvas.configure(scrollregion=(0, 0, 0, 0))

    def send_message(self):
        user_message = self.entry.get()
        if user_message:
            self.add_message_to_frame("user", user_message)
            self.entry.delete(0, tk.END)

            if self.context_mode_var.get() == "独立对话":
                self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

            self.messages.append({"role": "user", "content": user_message})

            if self.stream_var.get():
                threading.Thread(target=self.get_ai_reply_stream, daemon=True).start()
            else:
                threading.Thread(target=self.get_ai_reply, daemon=True).start()

    def add_message_to_frame(self, role, message):
        frame = tk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        if role == "user":
            img_label = tk.Label(frame, image=self.user_img)
        else:
            img_label = tk.Label(frame, image=self.assistant_img)
        img_label.grid(row=0, column=0, sticky="nw", padx=(0, 5))

        text_widget = tk.Label(frame, text=message, wraplength=600, justify="left", anchor="w")
        text_widget.grid(row=0, column=1, sticky="nsew")

        edit_button = tk.Label(frame, text="编辑", fg="gray", cursor="hand2")
        edit_button.grid(row=0, column=2, sticky="ne", padx=(5, 0))
        edit_button.bind("<Button-1>", lambda e: self.toggle_edit_mode(frame, text_widget, edit_button, role, message))  # 修改为传递原始message

        # 更新画布滚动区域并调整滚动位置
        self.adjust_scroll_region()

    def toggle_edit_mode(self, frame, widget, edit_button, role, original_message):  # 增加original_message参数
        if edit_button["text"] == "编辑":
            # 切换到编辑模式
            text_widget = tk.Text(frame, wrap=tk.WORD)
            text_widget.insert(tk.END, widget["text"])
            text_widget.grid(row=0, column=1, sticky="nsew")
            widget.grid_remove()
            edit_button.configure(text="完成")
            # 保存对 text_widget 的引用
            frame.text_widget = text_widget

            # 自动调整Text高度以适应内容
            max_height = 20  # 设置最大行数为20行，可以根据需要调整
            num_lines = int(text_widget.index('end-1c').split('.')[0])
            # num_lines = text_widget.count("1.0", "end-1c", "displaylines")[0]
            text_widget.configure(height=num_lines)

        else:
            # 保存编辑并切换回显示模式
            new_text = frame.text_widget.get("1.0", tk.END).strip()
            widget.configure(text=new_text)
            frame.text_widget.grid_remove()
            widget.grid()
            edit_button.configure(text="编辑")
            # 删除 text_widget 的引用
            del frame.text_widget

            # 更新消息历史，替换原始消息内容
            for msg in self.messages:
                if msg["role"] == role and msg["content"] == original_message:
                    msg["content"] = new_text
                    break

        self.adjust_scroll_region()

    def adjust_scroll_region(self):
        self.scrollable_frame.update_idletasks()
        bbox = self.canvas.bbox("all")

        # 获取画布的高度
        canvas_height = self.canvas.winfo_height()

        # 如果内容高度小于画布高度，将内容固定在顶部
        if (bbox[3] - bbox[1]) < canvas_height:
            self.canvas.configure(scrollregion=(bbox[0], bbox[1], bbox[2], canvas_height))
            self.canvas.yview_moveto(0)
        else:
            self.canvas.configure(scrollregion=bbox)
            self.canvas.yview_moveto(1)

    def get_ai_reply_stream(self):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            stream=True
        )

        debug_info_list = []
        ai_reply = ""
        temp_frame = tk.Frame(self.scrollable_frame)
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        temp_frame.grid_columnconfigure(1, weight=1)

        img_label = tk.Label(temp_frame, image=self.assistant_img)
        img_label.grid(row=0, column=0, sticky="nw", padx=(0, 5))

        text_widget = tk.Label(temp_frame, wraplength=600, justify="left", anchor="w")
        text_widget.grid(row=0, column=1, sticky="nsew")

        edit_button = tk.Label(temp_frame, text="编辑", fg="gray", cursor="hand2")
        edit_button.grid(row=0, column=2, sticky="ne", padx=(5, 0))

        for chunk in response:
            debug_info_list.append(chunk)
            content = chunk.choices[0].delta.content
            if content:
                ai_reply += content
                text_widget.config(text=ai_reply)

            self.adjust_scroll_region()
            self.root.update()

        edit_button.bind("<Button-1>", lambda e: self.toggle_edit_mode(temp_frame, text_widget, edit_button, "assistant", ai_reply))

        self.debug_info = json.dumps([chunk.to_dict() for chunk in debug_info_list], indent=4, ensure_ascii=False)
        self.messages.append({"role": "assistant", "content": ai_reply})

    def get_ai_reply(self):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages
        )

        ai_reply = response.choices[0].message.content
        self.root.after(0, self.add_message_to_frame, "assistant", ai_reply)

        self.debug_info = json.dumps(response.to_dict(), indent=4, ensure_ascii=False)
        self.messages.append({"role": "assistant", "content": ai_reply})

    def show_debug_info(self):
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug Information")
        debug_text = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=60, height=20)
        debug_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        debug_text.insert(tk.END, self.debug_info)

    def _on_mousewheel(self, event):
        # 获取当前的滚动位置
        current_position = self.canvas.yview()[0]

        # 如果当前位置已经在顶部，并且尝试向上滚动，则不执行滚动
        if current_position <= 0 and event.delta > 0:
            return

        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
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

        # Stop按钮
        self.stop_button = tk.Button(input_frame, text="Stop", bg="lightcoral", command=self.stop_reply)
        self.stop_button.grid(column=0, row=0, padx=(0, 5), pady=5)
        self.stop_button.config(width=8)  # 设置宽度为100像素
        self.stop_button.grid_remove()  # 初始时隐藏

        # 输入框
        self.entry = tk.Entry(input_frame, width=50)
        self.entry.grid(column=0, row=1, padx=(0, 5), pady=5, sticky="ew")

        # 发送按钮
        self.send_button = tk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.grid(column=1, row=1, padx=5, pady=5, sticky="e")

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
        self.user_img = self.load_and_resize_image("images/user_icon.png", (25, 25))
        self.assistant_img = self.load_and_resize_image("images/chatgpt_icon.png", (25, 25))

        # 初始化OpenAI API
        self.client = OpenAI(
            api_key="your api-key",
            base_url="https://Proxy address/v1/"
        )

        self.debug_info = ""
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.stop_streaming = False  # 增加一个标志位来控制流式输出的停止

        # 绑定窗口大小变化事件以调整wraplength
        self.root.bind('<Configure>', self.update_wraplengths)

    def load_and_resize_image(self, path, size):
        img = Image.open(path)
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def new_chat(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
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
                self.stop_button.grid()
                self.stop_streaming = False
                threading.Thread(target=self.get_ai_reply_stream, daemon=True).start()
            else:
                threading.Thread(target=self.get_ai_reply, daemon=True).start()

    def add_message_to_frame(self, role, message):
        temp_frame = tk.Frame(self.scrollable_frame)
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        temp_frame.grid_columnconfigure(1, weight=1)

        if role == "user":
            img_label = tk.Label(temp_frame, image=self.user_img)
        else:
            img_label = tk.Label(temp_frame, image=self.assistant_img)
        img_label.grid(row=0, column=0, sticky="nw", padx=(0, 5))

        wraplength = self.get_wraplength()

        text_widget = tk.Label(temp_frame, text=message, wraplength=wraplength, justify="left", anchor="w")
        text_widget.grid(row=0, column=1, sticky="nsew")

        button_frame = tk.Frame(temp_frame)
        button_frame.grid(row=1, column=1, sticky="nw", pady=(5, 0))

        copy_button = tk.Label(button_frame, text="复制", fg="gray", cursor="hand2")
        copy_button.pack(side="left", padx=(0, 5))
        copy_button.bind("<Button-1>", lambda e: self.copy_to_clipboard(message, copy_button))

        edit_button = tk.Label(button_frame, text="编辑", fg="gray", cursor="hand2")
        edit_button.pack(side="left")
        edit_button.bind("<Button-1>",
                         lambda e: self.toggle_edit_mode(temp_frame, text_widget, edit_button, role, message))

        if role == "user":
            regenerate_button = tk.Label(button_frame, text="重新发送", fg="gray", cursor="hand2")
            regenerate_button.pack(side="left", padx=(5, 0))
            regenerate_button.bind("<Button-1>", lambda e, m=message: self.regenerate_message(m))

        # 创建取消按钮，但初始时不显示
        cancel_button = tk.Label(button_frame, text="取消", fg="gray", cursor="hand2")
        cancel_button.pack(side="left", padx=(5, 0))
        cancel_button.pack_forget()  # 初始时隐藏
        temp_frame.cancel_button = cancel_button

        self.adjust_scroll_region()

        return temp_frame

    def copy_to_clipboard(self, text, copy_button):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # 这将更新剪贴板
        copy_button.config(text="✔")
        self.root.after(1000, lambda: copy_button.config(text="复制"))

    def toggle_edit_mode(self, frame, widget, edit_button, role, original_message):
        if edit_button["text"] == "编辑":
            # 切换到编辑模式
            text_widget = tk.Text(frame, wrap=tk.WORD)
            a = self.get_text_width()
            text_widget.config(width=a)
            text_widget.insert(tk.END, widget["text"])
            text_widget.grid(row=0, column=1, sticky="nsew")
            widget.grid_remove()
            edit_button.configure(text="保存")
            frame.text_widget = text_widget
            frame.original_message = original_message

            max_height = 20
            extra_lines = 7
            num_lines = int(text_widget.index('end-1c').split('.')[0]) + extra_lines
            text_widget.configure(height=num_lines)

            frame.cancel_button.pack()
            frame.cancel_button.bind("<Button-1>", lambda e: self.cancel_edit_mode(frame, widget, edit_button))

        else:
            # 保存编辑并切换回显示模式
            new_text = frame.text_widget.get("1.0", tk.END).strip()
            widget.configure(text=new_text)
            frame.text_widget.grid_remove()
            widget.grid()
            edit_button.configure(text="编辑")
            frame.cancel_button.pack_forget()
            del frame.text_widget

            # 更新消息历史，替换原始消息内容
            for msg in self.messages:
                if msg["role"] == role and msg["content"] == original_message:
                    msg["content"] = new_text
                    break

            frame.original_message = new_text

            if role == "user":
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        for button in child.winfo_children():
                            if button["text"] == "重新发送":
                                button.bind("<Button-1>", lambda e, m=new_text: self.regenerate_message(m))
                                break
                        break

        self.adjust_scroll_region()

    def cancel_edit_mode(self, frame, widget, edit_button):
        widget.configure(text=frame.original_message)
        frame.text_widget.grid_remove()
        widget.grid()
        edit_button.configure(text="编辑")
        frame.cancel_button.pack_forget()
        del frame.text_widget
        self.adjust_scroll_region()

    def adjust_scroll_region(self):
        self.scrollable_frame.update_idletasks()
        bbox = self.canvas.bbox("all")
        canvas_height = self.canvas.winfo_height()

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

        wraplength = self.get_wraplength()

        text_widget = tk.Label(temp_frame, wraplength=wraplength, justify="left", anchor="w")
        text_widget.grid(row=0, column=1, sticky="nsew")

        button_frame = tk.Frame(temp_frame)
        button_frame.grid(row=1, column=1, sticky="nw", pady=(5, 0))

        copy_button = tk.Label(button_frame, text="复制", fg="gray", cursor="hand2")
        copy_button.pack(side="left", padx=(0, 5))
        copy_button.bind("<Button-1>", lambda e: self.copy_to_clipboard(ai_reply, copy_button))

        edit_button = tk.Label(button_frame, text="编辑", fg="gray", cursor="hand2")
        edit_button.pack(side="left")

        cancel_button = tk.Label(button_frame, text="取消", fg="gray", cursor="hand2")
        cancel_button.pack(side="left", padx=(5, 0))
        cancel_button.pack_forget()
        temp_frame.cancel_button = cancel_button

        for chunk in response:
            if self.stop_streaming:
                break
            debug_info_list.append(chunk)
            content = chunk.choices[0].delta.content
            if content:
                ai_reply += content
                text_widget.config(text=ai_reply)

            self.adjust_scroll_region()
            self.root.update()

        self.stop_button.grid_remove()
        edit_button.bind("<Button-1>",
                         lambda e: self.toggle_edit_mode(temp_frame, text_widget, edit_button, "assistant", ai_reply))

        self.debug_info = json.dumps([chunk.to_dict() for chunk in debug_info_list], indent=4, ensure_ascii=False)

        # 只保存实际显示的内容
        self.messages.append({"role": "assistant", "content": ai_reply})

    def get_ai_reply(self):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages
        )

        ai_reply = response.choices[0].message.content

        # 创建新的框架来显示AI回复
        temp_frame = tk.Frame(self.scrollable_frame)
        temp_frame.pack(fill=tk.X, padx=5, pady=5)
        temp_frame.grid_columnconfigure(1, weight=1)

        img_label = tk.Label(temp_frame, image=self.assistant_img)
        img_label.grid(row=0, column=0, sticky="nw", padx=(0, 5))

        wraplength = self.get_wraplength()

        text_widget = tk.Label(temp_frame, text=ai_reply, wraplength=wraplength, justify="left", anchor="w")
        text_widget.grid(row=0, column=1, sticky="nsew")

        button_frame = tk.Frame(temp_frame)
        button_frame.grid(row=1, column=1, sticky="nw", pady=(5, 0))

        copy_button = tk.Label(button_frame, text="复制", fg="gray", cursor="hand2")
        copy_button.pack(side="left", padx=(0, 5))
        copy_button.bind("<Button-1>", lambda e: self.copy_to_clipboard(ai_reply, copy_button))

        edit_button = tk.Label(button_frame, text="编辑", fg="gray", cursor="hand2")
        edit_button.pack(side="left")
        edit_button.bind("<Button-1>",
                         lambda e: self.toggle_edit_mode(temp_frame, text_widget, edit_button, "assistant", ai_reply))

        # 创建取消按钮，但初始时不显示
        cancel_button = tk.Label(button_frame, text="取消", fg="gray", cursor="hand2")
        cancel_button.pack(side="left", padx=(5, 0))
        cancel_button.pack_forget()  # 初始时隐藏
        temp_frame.cancel_button = cancel_button

        self.adjust_scroll_region()

        self.debug_info = json.dumps(response.to_dict(), indent=4, ensure_ascii=False)
        self.messages.append({"role": "assistant", "content": ai_reply})

    def stop_reply(self):
        self.stop_streaming = True
        self.stop_button.grid_remove()

    def show_debug_info(self):
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug Information")
        debug_text = scrolledtext.ScrolledText(debug_window, wrap=tk.WORD, width=60, height=20)
        debug_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        debug_text.insert(tk.END, self.debug_info)

    def _on_mousewheel(self, event):
        current_position = self.canvas.yview()[0]
        if (current_position <= 0 and event.delta > 0):
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_wraplengths(self, event=None):
        wraplength = self.get_wraplength()
        text_width = self.get_text_width()

        for frame in self.scrollable_frame.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(wraplength=wraplength)
                elif isinstance(widget, tk.Text):
                    widget.config(width=text_width)

    def get_wraplength(self):
        window_width = self.root.winfo_width()
        return window_width - 110

    def get_text_width(self):
        window_width = self.root.winfo_width()
        return (window_width - 130) // 9

    def regenerate_message(self, message):
        user_frame = None
        for i in range(len(self.scrollable_frame.winfo_children()) - 1, -1, -1):
            frame = self.scrollable_frame.winfo_children()[i]
            if frame.winfo_children()[1]["text"] == message:
                user_frame = frame
                if i + 1 < len(self.scrollable_frame.winfo_children()):
                    self.scrollable_frame.winfo_children()[i + 1].destroy()
                break

        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "user" and self.messages[i]["content"] == message:
                del self.messages[i:i + 2]
                break

        self.messages.append({"role": "user", "content": message})
        if self.stream_var.get():
            self.stop_button.grid()  # 显示Stop按钮
            self.stop_streaming = False
            threading.Thread(target=self.get_ai_reply_stream, daemon=True).start()
        else:
            threading.Thread(target=self.get_ai_reply, daemon=True).start()

        if user_frame:
            for child in user_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    for button in child.winfo_children():
                        if button["text"] == "重新发送":
                            button.bind("<Button-1>", lambda e, m=message: self.regenerate_message(m))
                            break
                    break

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
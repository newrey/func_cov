import tkinter as tk
from tkinterdnd2 import DND_TEXT, TkinterDnD
from tkinter import ttk, filedialog
import configparser

original_prefix_entry_default = "harness.U_DUT.XXX.SUB"
target_prefix_entry_default = "harness.U_DUT.HARDENED_TOP.XXX.SUB"

class SignalDragMode(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # 保存对父窗口的引用
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="本模式支持将前仿verdi中的信号拖入，并转换输出为后仿verdi中的信号").pack()

        drop_frame = ttk.Frame(self)
        drop_frame.pack(pady=10, padx=10, fill='x')

        self.drop_label = tk.Label(drop_frame, text="将前仿verdi中的信号拖拽到这里", width=40, height=13, relief="groove", bg="lightgray")
        self.drop_label.pack(fill='x')
        self.drop_label.drop_target_register(DND_TEXT)
        self.drop_label.dnd_bind('<<Drop>>', self.drop)

        # 添加悬浮的粘贴按钮
        paste_button = ttk.Button(drop_frame, text="粘贴", command=self.paste_from_clipboard)
        paste_button.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)
        
        # 创建一个框架来容纳转换成功的Label和处理结果输出区域
        self.result_frame = ttk.Frame(self, height=10)
        self.result_frame.pack(pady=10, padx=10, fill='both', expand=True)
        self.result_frame.pack_forget()

        # 添加处理结果输出区域
        self.result_text = tk.Text(self.result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill='both', expand=True)

        # 创建一个框架来容纳勾选框和按钮
        self.control_frame = ttk.Frame(self.result_frame)

        # 添加自动复制复选框
        self.auto_copy_var = tk.BooleanVar(value=False)  # 默认勾选
        self.auto_copy_check = ttk.Checkbutton(self.control_frame, text="自动将结果放到剪贴板", variable=self.auto_copy_var, command=self.toggle_copy_button)
        self.auto_copy_check.pack(side='left', padx=(0, 10))

        # 添加复制按钮
        self.copy_button = ttk.Button(self.control_frame, text="复制结果到剪贴板", command=self.copy_to_clipboard)
        self.copy_button.pack(side='left')

        # 将control_frame悬浮到result_text右下角
        self.control_frame.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)

        self.toggle_copy_button()

    def paste_from_clipboard(self):
        try:
            clipboard_content = self.clipboard_get()
        except tk.TclError:
            clipboard_content = ""
        if clipboard_content:
            self.drop(type('Event', (), {'data': clipboard_content})())

    def drop(self, event):
        text = event.data
        self.drop_label.config(text=f"拖入的信号: {text[:500]} ...")
        
        # 这里添加信号处理逻辑
        self.processed_result = self.process_signal(text)
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, f"转换成功！将以下转换成的信号复制粘贴到后仿veridi中: \n{self.processed_result[:500]} ...")

        # 显示控制框架
        self.result_frame.pack(side='top', fill='x')
        self.update_window_height()  # 更新窗口高度

        if self.auto_copy_var.get():
            self.copy_to_clipboard()

        self.parent.master.save_config()

    def update_window_height(self):
        self.update_idletasks()  # 更新所有挂起的任务
        self.drop_label.config(height=5)
        # 自适应高度，确保不多出一截
        # new_height = self.parent.master.winfo_height() + 200  # 200为额外的边距
        new_height = 480
        self.parent.master.geometry(f"{self.parent.master.winfo_width()}x{new_height}")  # 使用主窗口的 geometry 方法

    def process_signal(self, signal):
        # 这里添加实际的信号处理逻辑
        # 现在只是简单地返回原始信号
        return signal

    def copy_to_clipboard(self):
        result = self.processed_result
        self.clipboard_clear()
        self.clipboard_append(result)
        self.update()  # 刷新剪贴板

    def toggle_copy_button(self):
        if self.auto_copy_var.get():
            self.copy_button.pack_forget()  # 隐藏复制按钮
        else:
            self.copy_button.pack(side='left')  # 显示复制按钮

class WaveformMode(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="波形模式: 配置参数并打开波形").pack(pady=10)

        self.config_frame = ttk.LabelFrame(self, text="参数配置")
        self.config_frame.pack(pady=10, padx=10, fill='x')

        # 前仿波形输入框
        ttk.Label(self.config_frame, text="前仿波形:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.pre_waveform_entry = ttk.Entry(self.config_frame, width=55)
        self.pre_waveform_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')  # 修改为 'ew'
        ttk.Button(self.config_frame, text="浏览", command=self.browse_pre_waveform).grid(row=0, column=2, padx=5, pady=5)

        # 前仿信号输入框
        ttk.Label(self.config_frame, text="前仿信号:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.pre_signal_entry = ttk.Entry(self.config_frame, width=55)
        self.pre_signal_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')  # 修改为 'ew'
        ttk.Button(self.config_frame, text="浏览", command=self.browse_pre_signal).grid(row=1, column=2, padx=5, pady=5)

        # 分隔线
        ttk.Separator(self.config_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky='ew', pady=10)

        # 后方波形输入框
        ttk.Label(self.config_frame, text="后仿波形:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.post_waveform_entry = ttk.Entry(self.config_frame, width=55)
        self.post_waveform_entry.grid(row=3, column=1, padx=5, pady=5, sticky='ew')  # 修改为 'ew'
        ttk.Button(self.config_frame, text="浏览", command=self.browse_post_waveform).grid(row=3, column=2, padx=5, pady=5)

        tk.Button(self, text="打开波形", command=self.open_waveform).pack(pady=20)

    def browse_pre_waveform(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.pre_waveform_entry.delete(0, tk.END)
            self.pre_waveform_entry.insert(0, file_path)

    def browse_pre_signal(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.pre_signal_entry.delete(0, tk.END)
            self.pre_signal_entry.insert(0, file_path)

    def browse_post_waveform(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.post_waveform_entry.delete(0, tk.END)
            self.post_waveform_entry.insert(0, file_path)

    def open_waveform(self):
        # 这里添加打开波形的逻辑
        self.parent.master.save_config()
        pass

class MultiModeReceiver(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("多功能接收窗口")
        self.geometry("600x480")  # 初始窗口高度调整为480
        self.config_file = 'config.ini'  # 配置文件路径
        self.create_widgets()
        self.load_config()  # 加载配置

    def create_widgets(self):
        self.create_mapping_frame()
        self.create_notebook()

    def create_mapping_frame(self):
        mapping_frame = ttk.LabelFrame(self, text="映射关系配置")
        mapping_frame.pack(pady=10, padx=10, fill='x')

        # tcl 路径配置
        ttk.Label(mapping_frame, text="tcl路径:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.path_entry = ttk.Entry(mapping_frame, width=40)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2, sticky='we')
        ttk.Button(mapping_frame, text="浏览文件夹", command=self.browse_path).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(mapping_frame, text="浏览文件", command=self.browse_files).grid(row=0, column=4, padx=5, pady=5)

        # hdl_path 前缀替换配置
        self.prefix_var = tk.BooleanVar()
        self.prefix_check = ttk.Checkbutton(mapping_frame, text="启用 hdl_path 前缀替换", variable=self.prefix_var, command=self.toggle_prefix_entries)
        self.prefix_check.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky='w')

        ttk.Label(mapping_frame, text="原始前缀:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.original_prefix_entry = ttk.Entry(mapping_frame, state='disabled')
        # self.original_prefix_entry.insert(0, original_prefix_entry_default)  # 默认文本
        # self.original_prefix_entry.config(state='disabled')
        self.original_prefix_entry.grid(row=2, column=1, columnspan=4, padx=5, pady=5, sticky='we')

        ttk.Label(mapping_frame, text="目标前缀:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.target_prefix_entry = ttk.Entry(mapping_frame, state='disabled')
        # self.target_prefix_entry.insert(0, target_prefix_entry_default)  # 默认文本
        # self.target_prefix_entry.config(state='disabled')
        self.target_prefix_entry.grid(row=3, column=1, columnspan=4, padx=5, pady=5, sticky='we')

        # 配置列的权重,使其能够自适应调整大小
        mapping_frame.columnconfigure(1, weight=1)
        mapping_frame.columnconfigure(3, weight=1)

        # 添加保存按钮
        # ttk.Button(mapping_frame, text="保存配置", command=self.save_config).grid(row=0, column=5, padx=5, pady=5)

    def toggle_prefix_entries(self):
        state = 'normal' if self.prefix_var.get() else 'disabled'
        self.original_prefix_entry.config(state=state)
        self.target_prefix_entry.config(state=state)

    def create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.signal_drag_mode = SignalDragMode(self.notebook)
        self.waveform_mode = WaveformMode(self.notebook)

        self.notebook.add(self.signal_drag_mode, text='信号拖拽模式')
        self.notebook.add(self.waveform_mode, text='波形模式')

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def browse_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, ';'.join(files))

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' in config:
            self.path_entry.insert(0, config.get('Settings', 'tcl_path', fallback=''))
            # 读取其他Entry的值并填入
            self.waveform_mode.pre_waveform_entry.insert(0, config.get('Settings', 'pre_waveform', fallback=''))
            self.waveform_mode.pre_signal_entry.insert(0, config.get('Settings', 'pre_signal', fallback=''))
            self.waveform_mode.post_waveform_entry.insert(0, config.get('Settings', 'post_waveform', fallback=''))
            # 读取 hdl_path 前缀替换配置
            self.prefix_var.set(config.getboolean('Settings', 'enable_hdl_path_prefix', fallback=False))  # 读取复选框状态
        self.original_prefix_entry.config(state='normal')
        self.original_prefix_entry.delete(0, tk.END)  # 删除从第一个字符到最后一个字符的内容
        self.original_prefix_entry.insert(0, config.get('Settings', 'original_prefix', fallback=original_prefix_entry_default))  # 读取原始前缀
        self.original_prefix_entry.config(state='disabled')
        self.target_prefix_entry.config(state='normal')
        self.target_prefix_entry.delete(0, tk.END)  # 删除从第一个字符到最后一个字符的内容
        self.target_prefix_entry.insert(0, config.get('Settings', 'target_prefix', fallback=target_prefix_entry_default))  # 读取目标前缀
        self.target_prefix_entry.config(state='disabled')
        self.toggle_prefix_entries()

    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'tcl_path': self.path_entry.get(),
            'pre_waveform': self.waveform_mode.pre_waveform_entry.get(),
            'pre_signal': self.waveform_mode.pre_signal_entry.get(),
            'post_waveform': self.waveform_mode.post_waveform_entry.get(),
            'enable_hdl_path_prefix': self.prefix_var.get(),  # 保存复选框状态
            'original_prefix': self.original_prefix_entry.get(),  # 保存原始前缀
            'target_prefix': self.target_prefix_entry.get(),  # 保存目标前缀
        }
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

if __name__ == "__main__":
    app = MultiModeReceiver()
    app.mainloop()

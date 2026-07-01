#!/usr/bin/env python3
"""
番茄钟应用 - Pomodoro Timer
工作25分钟，休息5分钟，帮助你提高专注力
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import winsound

# 尝试导入plyer用于系统通知（可选功能）
try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("🍅 番茄钟")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#ff6b6b")

        # 番茄钟设置（单位：秒）
        self.work_time = 25 * 60  # 25分钟
        self.short_break = 5 * 60  # 5分钟
        self.long_break = 15 * 60  # 15分钟

        # 状态变量
        self.time_left = self.work_time
        self.is_running = False
        self.is_work_mode = True
        self.pomodoros_completed = 0
        self.timer_thread = None

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="🍅 番茄钟",
            font=("Microsoft YaHei", 28, "bold"),
            bg="#ff6b6b",
            fg="white"
        )
        title_label.pack(pady=20)

        # 模式标签
        self.mode_label = tk.Label(
            self.root,
            text="工作时间",
            font=("Microsoft YaHei", 16),
            bg="#ff6b6b",
            fg="white"
        )
        self.mode_label.pack(pady=10)

        # 时间显示框
        time_frame = tk.Frame(self.root, bg="#ff6b6b")
        time_frame.pack(pady=20)

        self.time_label = tk.Label(
            time_frame,
            text="25:00",
            font=("Consolas", 72, "bold"),
            bg="#ff6b6b",
            fg="white"
        )
        self.time_label.pack()

        # 进度条
        self.progress = ttk.Progressbar(
            self.root,
            length=300,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(pady=20)
        self.progress['value'] = 100

        # 按钮框架
        button_frame = tk.Frame(self.root, bg="#ff6b6b")
        button_frame.pack(pady=20)

        # 开始按钮
        self.start_button = tk.Button(
            button_frame,
            text="▶ 开始",
            font=("Microsoft YaHei", 14),
            width=10,
            command=self.toggle_timer,
            bg="#4ecdc4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        # 重置按钮
        self.reset_button = tk.Button(
            button_frame,
            text="↻ 重置",
            font=("Microsoft YaHei", 14),
            width=10,
            command=self.reset_timer,
            bg="#95a5a6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.reset_button.pack(side=tk.LEFT, padx=10)

        # 模式切换按钮
        mode_frame = tk.Frame(self.root, bg="#ff6b6b")
        mode_frame.pack(pady=10)

        self.work_btn = tk.Button(
            mode_frame,
            text="💼 工作",
            font=("Microsoft YaHei", 11),
            width=8,
            command=lambda: self.switch_mode(True),
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.work_btn.pack(side=tk.LEFT, padx=5)

        self.break_btn = tk.Button(
            mode_frame,
            text="☕ 休息",
            font=("Microsoft YaHei", 11),
            width=8,
            command=lambda: self.switch_mode(False),
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.break_btn.pack(side=tk.LEFT, padx=5)

        # 统计标签
        self.stats_label = tk.Label(
            self.root,
            text="已完成: 0 个番茄",
            font=("Microsoft YaHei", 12),
            bg="#ff6b6b",
            fg="white"
        )
        self.stats_label.pack(pady=20)

        # 设置框架
        settings_frame = tk.LabelFrame(
            self.root,
            text="设置 (分钟)",
            font=("Microsoft YaHei", 10),
            bg="#ff6b6b",
            fg="white"
        )
        settings_frame.pack(pady=10, padx=20, fill=tk.X)

        # 工作时间设置
        work_setting = tk.Frame(settings_frame, bg="#ff6b6b")
        work_setting.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(work_setting, text="工作:", bg="#ff6b6b", fg="white").pack(side=tk.LEFT)
        self.work_spinbox = tk.Spinbox(
            work_setting, from_=1, to=60, width=5,
            font=("Consolas", 10)
        )
        self.work_spinbox.delete(0, tk.END)
        self.work_spinbox.insert(0, "25")
        self.work_spinbox.pack(side=tk.RIGHT)

        # 休息时间设置
        break_setting = tk.Frame(settings_frame, bg="#ff6b6b")
        break_setting.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(break_setting, text="休息:", bg="#ff6b6b", fg="white").pack(side=tk.LEFT)
        self.break_spinbox = tk.Spinbox(
            break_setting, from_=1, to=30, width=5,
            font=("Consolas", 10)
        )
        self.break_spinbox.delete(0, tk.END)
        self.break_spinbox.insert(0, "5")
        self.break_spinbox.pack(side=tk.RIGHT)

        # 应用设置按钮
        apply_btn = tk.Button(
            settings_frame,
            text="应用设置",
            font=("Microsoft YaHei", 9),
            command=self.apply_settings,
            bg="#9b59b6",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        apply_btn.pack(pady=5)

    def toggle_timer(self):
        """切换计时器状态"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(text="▶ 继续", bg="#4ecdc4")
        else:
            self.is_running = True
            self.start_button.config(text="⏸ 暂停", bg="#f39c12")
            if self.timer_thread is None or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
                self.timer_thread.start()

    def run_timer(self):
        """计时器主循环"""
        while self.is_running and self.time_left > 0:
            time.sleep(1)
            if self.is_running:
                self.time_left -= 1
                self.update_display()

        if self.time_left <= 0:
            self.timer_complete()

    def update_display(self):
        """更新显示"""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_str)

        # 更新进度条
        total_time = self.work_time if self.is_work_mode else self.short_break
        progress = (self.time_left / total_time) * 100
        self.progress['value'] = progress

    def timer_complete(self):
        """计时完成"""
        self.is_running = False
        self.start_button.config(text="▶ 开始", bg="#4ecdc4")

        # 播放提示音
        self.play_alarm()

        # 发送系统通知
        if self.is_work_mode:
            self.pomodoros_completed += 1
            self.show_notification(
                "🍅 番茄钟",
                f"工作时间结束！已完成 {self.pomodoros_completed} 个番茄\n休息一下吧~"
            )
            # 自动切换到休息模式
            self.root.after(1000, lambda: self.switch_mode(False))
        else:
            self.show_notification(
                "🍅 番茄钟",
                "休息时间结束！准备好继续工作了吗？"
            )
            # 自动切换到工作模式
            self.root.after(1000, lambda: self.switch_mode(True))

        # 更新统计
        self.stats_label.config(text=f"已完成: {self.pomodoros_completed} 个番茄")

    def switch_mode(self, is_work):
        """切换工作/休息模式"""
        self.is_running = False
        self.is_work_mode = is_work

        if is_work:
            self.time_left = self.work_time
            self.mode_label.config(text="工作时间")
            self.root.configure(bg="#ff6b6b")
            self.time_label.config(bg="#ff6b6b")
            self.mode_label.config(bg="#ff6b6b")
            self.stats_label.config(bg="#ff6b6b")
        else:
            self.time_left = self.short_break
            self.mode_label.config(text="休息时间")
            self.root.configure(bg="#4ecdc4")
            self.time_label.config(bg="#4ecdc4")
            self.mode_label.config(bg="#4ecdc4")
            self.stats_label.config(bg="#4ecdc4")

        self.start_button.config(text="▶ 开始", bg="#4ecdc4")
        self.update_display()

    def reset_timer(self):
        """重置计时器"""
        self.is_running = False
        if self.is_work_mode:
            self.time_left = self.work_time
        else:
            self.time_left = self.short_break
        self.start_button.config(text="▶ 开始", bg="#4ecdc4")
        self.update_display()

    def apply_settings(self):
        """应用设置"""
        try:
            self.work_time = int(self.work_spinbox.get()) * 60
            self.short_break = int(self.break_spinbox.get()) * 60
            self.reset_timer()
            messagebox.showinfo("设置", "设置已应用！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")

    def play_alarm(self):
        """播放提示音"""
        try:
            # 播放系统提示音（3次）
            for _ in range(3):
                winsound.Beep(1000, 500)  # 频率1000Hz，持续500ms
                time.sleep(0.2)
        except:
            pass

    def show_notification(self, title, message):
        """显示系统通知"""
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="番茄钟",
                    timeout=10
                )
            except:
                pass


def main():
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
"""
终端显示工具
"""
import sys
import time
import threading
from typing import List, Optional

# 直接定义颜色常量，避免循环导入
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 默认终端宽度
TERM_WIDTH = 120


def clear_screen():
    """清屏"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str, width: Optional[int] = None):
    """打印标题"""
    if width is None:
        width = TERM_WIDTH
    
    print(f"\n{Colors.HEADER}{'=' * width}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text.center(width)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * width}{Colors.ENDC}\n")


def print_section(text: str, width: Optional[int] = None):
    """打印章节标题"""
    if width is None:
        width = TERM_WIDTH
    
    print(f"\n{Colors.OKBLUE}{'-' * width}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * width}{Colors.ENDC}")


def print_subsection(text: str):
    """打印子章节标题"""
    print(f"\n{Colors.OKCYAN}▶ {text}{Colors.ENDC}")


def print_step_start(step: str, step_number: int = None, total_steps: int = None):
    """打印步骤开始"""
    if step_number and total_steps:
        print(f"{Colors.BOLD}🔄 [{step_number}/{total_steps}] {step}...{Colors.ENDC}")
    else:
        print(f"{Colors.BOLD}🔄 {step}...{Colors.ENDC}")


def print_step_complete(step: str, step_number: int = None, total_steps: int = None):
    """打印步骤完成"""
    if step_number and total_steps:
        print(f"{Colors.OKGREEN}✅ [{step_number}/{total_steps}] {step} 完成{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✅ {step} 完成{Colors.ENDC}")


def print_ai_choice(choice: str, explanation: str = ""):
    """打印AI选择"""
    print(f"{Colors.BOLD}🤖 AI选择: {Colors.OKGREEN}{choice}{Colors.ENDC}")
    if explanation:
        print(f"   理由: {explanation}")


def print_progress_bar(current: int, total: int, prefix: str = "", width: int = 50):
    """打印进度条"""
    percent = (current / total) * 100
    filled_length = int(width * current // total)
    bar = '█' * filled_length + '-' * (width - filled_length)
    
    print(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
    if current == total:
        print()


def print_info(message: str):
    """打印信息"""
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")


def print_warning(message: str):
    """打印警告"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_error(message: str):
    """打印错误"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_success(message: str):
    """打印成功"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_detail(message: str, indent: int = 2):
    """打印详细信息"""
    spaces = " " * indent
    print(f"{spaces}{message}")


def print_options(options: List[str], title: str = "请选择:"):
    """打印选项列表"""
    print(f"\n{Colors.BOLD}{title}{Colors.ENDC}")
    for i, option in enumerate(options, 1):
        print(f"  {Colors.OKCYAN}{i}.{Colors.ENDC} {option}")


def print_explanation_box(title: str, content: str, width: Optional[int] = None):
    """打印解释框"""
    if width is None:
        width = TERM_WIDTH
    
    print(f"\n{Colors.HEADER}┌{'─' * (width - 2)}┐{Colors.ENDC}")
    print(f"{Colors.HEADER}│ {title.ljust(width - 4)} │{Colors.ENDC}")
    print(f"{Colors.HEADER}├{'─' * (width - 2)}┤{Colors.ENDC}")
    
    # 分行显示内容
    lines = content.split('\n')
    for line in lines:
        # 处理长行
        while len(line) > width - 4:
            print(f"{Colors.HEADER}│ {line[:width-4].ljust(width - 4)} │{Colors.ENDC}")
            line = line[width-4:]
        print(f"{Colors.HEADER}│ {line.ljust(width - 4)} │{Colors.ENDC}")
    
    print(f"{Colors.HEADER}└{'─' * (width - 2)}┘{Colors.ENDC}\n")


class Spinner:
    """旋转加载指示器"""
    
    def __init__(self, message: str = "处理中..."):
        self.message = message
        self.spinning = False
        self.thread = None
        self.chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    
    def _spin(self):
        """旋转动画"""
        i = 0
        while self.spinning:
            sys.stdout.write(f'\r{self.chars[i % len(self.chars)]} {self.message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    
    def start(self):
        """开始旋转"""
        self.spinning = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
    
    def stop(self):
        """停止旋转"""
        self.spinning = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stdout.flush()


def show_spinner(message: str = "处理中..."):
    """显示旋转指示器的上下文管理器"""
    class SpinnerContext:
        def __init__(self, msg):
            self.spinner = Spinner(msg)
        
        def __enter__(self):
            self.spinner.start()
            return self.spinner
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.spinner.stop()
    
    return SpinnerContext(message)

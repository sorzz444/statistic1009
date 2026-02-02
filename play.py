#!/usr/bin/env python3
"""
觉道 - 禅修模拟游戏
命令行交互版本

操作：
- 按 Enter：归返所缘（发现走神时按）
- 输入 r：放松（对治掉举）
- 输入 u：提起（对治惛沉）
- 输入 q：结束禅修
"""

import sys
import time
import threading
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dharma_engine.meditation import MeditationEngine, NineStages


class MeditationGame:
    def __init__(self):
        self.engine = MeditationEngine()
        self.running = False
        self.paused = False
        
    def clear_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def draw_bar(self, value: float, width: int = 20, label: str = "") -> str:
        """绘制进度条"""
        filled = int(value * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{label}[{bar}] {value*100:.0f}%"
    
    def draw_state(self):
        """绘制当前状态"""
        s = self.engine.state
        elapsed = self.engine.elapsed_seconds
        minutes = elapsed // 60
        seconds = elapsed % 60
        
        # 清屏
        self.clear_screen()
        
        print("=" * 50)
        print("        觉 道 · 禅 修 模 拟")
        print("=" * 50)
        print(f"  时间: {minutes:02d}:{seconds:02d}")
        print()
        
        # 双轴显示
        print(self.draw_bar(s.stability, 25, "稳定 "))
        print(self.draw_bar(s.clarity, 25, "明晰 "))
        print()
        
        # 状态指示
        if s.on_object:
            print("  🧘 心住所缘")
        else:
            print(f"  💭 心已散乱 ({s.wandering_duration:.0f}秒)")
        
        if s.is_dull:
            print("  😴 惛沉现起 - 按 u 提起")
        if s.is_restless:
            print("  😰 掉举现起 - 按 r 放松")
        
        # 激活的盖
        if s.active_hindrances:
            hindrances = list(s.active_hindrances.keys())
            print(f"  ⚠️ 障碍: {', '.join(hindrances)}")
        
        print()
        print("-" * 50)
        print("  [Enter] 归返  [r] 放松  [u] 提起  [q] 结束")
        print("-" * 50)
    
    def input_thread(self):
        """输入处理线程"""
        while self.running:
            try:
                cmd = input().strip().lower()
                if cmd == 'q':
                    self.running = False
                elif cmd == 'r':
                    result = self.engine.player_adjust("relax")
                    # 效果会在下一帧显示
                elif cmd == 'u':
                    result = self.engine.player_adjust("raise")
                elif cmd == '':
                    # Enter键：归返
                    if not self.engine.state.on_object:
                        self.engine.player_notice()
                        self.engine.player_return()
            except EOFError:
                break
    
    def run(self, duration_minutes: int = 5):
        """运行游戏"""
        self.clear_screen()
        
        print("=" * 50)
        print("        觉 道 · 禅 修 模 拟")
        print("=" * 50)
        print()
        print(f"  即将开始 {duration_minutes} 分钟禅修")
        print()
        print("  目标：保持心在所缘上")
        print("  - 发现走神时，按 Enter 归返")
        print("  - 惛沉时，按 u 提起")
        print("  - 掉举时，按 r 放松")
        print()
        print("  记住：不是追求\"从不走神\"")
        print("  而是追求\"更快觉知，温柔归返\"")
        print()
        input("  按 Enter 开始...")
        
        # 开始禅修
        self.engine.start_session(duration_minutes=duration_minutes)
        self.running = True
        
        # 启动输入线程
        input_handler = threading.Thread(target=self.input_thread, daemon=True)
        input_handler.start()
        
        # 主循环
        try:
            while self.running and self.engine.elapsed_seconds < self.engine.session_duration:
                # 更新状态
                self.engine.tick()
                
                # 绘制
                self.draw_state()
                
                # 等待1秒
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.running = False
        
        # 结束并显示结果
        result = self.engine.end_session()
        self.show_result(result)
    
    def show_result(self, result: dict):
        """显示结果"""
        self.clear_screen()
        
        print("=" * 50)
        print("        禅 修 结 束")
        print("=" * 50)
        print()
        print(result["review"])
        print()
        
        # 统计
        stats = result["stats"]
        print("-" * 50)
        print("详细统计:")
        print(f"  走神次数: {stats['wander_count']}")
        print(f"  归返次数: {stats['return_count']}")
        print(f"  惛沉发作: {stats['dull_episodes']}")
        print(f"  掉举发作: {stats['restless_episodes']}")
        print()
        
        # 段位
        print(f"  当前段位: {result['stage']}")
        print()
        
        # 九住心进度
        print("九住心进度:")
        stages = list(NineStages)
        current_idx = -1
        for i, stage in enumerate(stages):
            if stage.value == result['stage']:
                current_idx = i
        
        for i, stage in enumerate(stages):
            if i <= current_idx:
                print(f"  ✅ {stage.value}")
            else:
                print(f"  ⬜ {stage.value}")
        
        print()
        input("按 Enter 退出...")


def main():
    print("觉道 · 禅修模拟")
    print()
    print("选择禅修时长:")
    print("  1. 3分钟 (快速)")
    print("  2. 5分钟 (标准)")
    print("  3. 10分钟 (深度)")
    print()
    
    choice = input("请选择 (1/2/3): ").strip()
    
    durations = {"1": 3, "2": 5, "3": 10}
    duration = durations.get(choice, 5)
    
    game = MeditationGame()
    game.run(duration_minutes=duration)


if __name__ == "__main__":
    main()

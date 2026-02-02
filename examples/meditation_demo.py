#!/usr/bin/env python3
"""
禅修模拟演示

展示核心机制：
1. 定 = 稳定度 + 明晰度
2. 五盖障碍
3. 觉知-归返循环
4. 九住心段位判定
"""

import sys
import random
sys.path.insert(0, '..')

from dharma_engine.meditation import (
    MeditationEngine, 
    FIVE_HINDRANCES, 
    NineStages,
    STAGE_THRESHOLDS
)


def print_separator(title: str = ""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def demo_basic_session():
    """基础禅修演示"""
    print_separator("基础禅修演示（模拟5分钟）")
    
    engine = MeditationEngine()
    engine.start_session(duration_minutes=5)
    
    print(f"初始状态:")
    print(f"  稳定度: {engine.state.stability:.2f}")
    print(f"  明晰度: {engine.state.clarity:.2f}")
    
    # 模拟禅修过程
    print("\n开始禅修...")
    
    for second in range(300):  # 5分钟
        result = engine.tick()
        
        # 显示关键事件
        for event in result["events"]:
            print(f"  [{second}s] {event}")
        
        # 模拟玩家在走神时的觉知
        if not result["on_object"]:
            # 觉知延迟：根据念的强度
            notice_delay = random.randint(2, 8)
            if engine.state.wandering_duration >= notice_delay:
                notice_result = engine.player_notice()
                if notice_result["noticed"]:
                    print(f"  [{second}s] 觉知! (延迟{notice_result['latency']:.1f}s)")
                    
                    # 归返
                    engine.player_return()
                    print(f"  [{second}s] 归返所缘")
        
        # 模拟玩家调整
        if engine.state.is_dull and random.random() < 0.3:
            engine.player_adjust("raise")
            print(f"  [{second}s] 提起（对治惛沉）")
        
        if engine.state.is_restless and random.random() < 0.3:
            engine.player_adjust("relax")
            print(f"  [{second}s] 放松（对治掉举）")
        
        # 每分钟显示状态
        if (second + 1) % 60 == 0:
            print(f"\n  --- 第{(second+1)//60}分钟 ---")
            print(f"  稳定度: {engine.state.stability:.2f}")
            print(f"  明晰度: {engine.state.clarity:.2f}")
    
    # 结束并复盘
    result = engine.end_session()
    
    print("\n" + result["review"])
    
    return engine


def demo_hindrances():
    """五盖系统演示"""
    print_separator("五盖系统")
    
    print("\n五盖及其食/非食（对治）:\n")
    
    for hid, hindrance in FIVE_HINDRANCES.items():
        print(f"【{hindrance.name}】")
        print(f"  损害: 稳定-{hindrance.stability_damage:.1f}, 明晰-{hindrance.clarity_damage:.1f}")
        print(f"  食（触发）: {', '.join(hindrance.foods[:2])}...")
        print(f"  非食（对治）: {', '.join(hindrance.antidotes[:2])}...")
        print()


def demo_nine_stages():
    """九住心段位演示"""
    print_separator("九住心段位")
    
    print("\n段位及达标条件:\n")
    
    for stage in NineStages:
        thresholds = STAGE_THRESHOLDS.get(stage, {})
        print(f"【{stage.value}】")
        for key, val in thresholds.items():
            if "ratio" in key:
                print(f"  {key}: > {val*100:.0f}%")
            elif "latency" in key or "time" in key:
                print(f"  {key}: < {val:.0f}s")
            else:
                print(f"  {key}: < {val}")
        print()


def demo_different_practitioners():
    """不同修行者的禅修演示"""
    print_separator("不同修行者对比")
    
    # 散乱型
    print("\n【散乱型修行者】(掉举种子高)")
    engine1 = MeditationEngine(
        seed_bank={"restlessness": 0.8, "sloth_torpor": 0.3},
        particular={"samadhi": 0.4, "smrti": 0.4}
    )
    engine1.start_session(duration_minutes=3)
    
    for _ in range(180):
        result = engine1.tick()
        if not result["on_object"] and engine1.state.wandering_duration > 5:
            engine1.player_notice()
            engine1.player_return()
    
    result1 = engine1.end_session()
    print(f"  在所缘比例: {result1['stats']['on_object_ratio']*100:.0f}%")
    print(f"  掉举发作: {result1['stats']['restless_episodes']}次")
    print(f"  段位: {result1['stage']}")
    
    # 昏沉型
    print("\n【昏沉型修行者】(惛沉种子高)")
    engine2 = MeditationEngine(
        seed_bank={"restlessness": 0.3, "sloth_torpor": 0.8},
        particular={"samadhi": 0.4, "prajna": 0.3}
    )
    engine2.start_session(duration_minutes=3)
    
    for _ in range(180):
        result = engine2.tick()
        if not result["on_object"] and engine2.state.wandering_duration > 5:
            engine2.player_notice()
            engine2.player_return()
        if engine2.state.is_dull:
            engine2.player_adjust("raise")
    
    result2 = engine2.end_session()
    print(f"  在所缘比例: {result2['stats']['on_object_ratio']*100:.0f}%")
    print(f"  惛沉发作: {result2['stats']['dull_episodes']}次")
    print(f"  段位: {result2['stage']}")
    
    # 熟练修行者
    print("\n【熟练修行者】(念和定都高)")
    engine3 = MeditationEngine(
        seed_bank={"restlessness": 0.3, "sloth_torpor": 0.3, "mindfulness": 0.8},
        particular={"samadhi": 0.7, "smrti": 0.7, "prajna": 0.6}
    )
    engine3.start_session(duration_minutes=3)
    
    for _ in range(180):
        result = engine3.tick()
        if not result["on_object"] and engine3.state.wandering_duration > 2:
            engine3.player_notice()
            engine3.player_return()
    
    result3 = engine3.end_session()
    print(f"  在所缘比例: {result3['stats']['on_object_ratio']*100:.0f}%")
    print(f"  平均觉知延迟: {result3['stats']['avg_noticing_latency']:.1f}s")
    print(f"  段位: {result3['stage']}")


def demo_training_effect():
    """训练效果演示：种子会随着练习改变"""
    print_separator("训练效果演示（种子熏习）")
    
    # 初始：散乱型
    seeds = {"restlessness": 0.7, "sloth_torpor": 0.4, "mindfulness": 0.4}
    particular = {"samadhi": 0.4, "smrti": 0.4}
    
    print(f"初始种子: 散乱={seeds['restlessness']:.2f}, 念={seeds['mindfulness']:.2f}")
    
    # 模拟7天训练
    for day in range(7):
        engine = MeditationEngine(seed_bank=seeds.copy(), particular=particular)
        engine.start_session(duration_minutes=10)
        
        for _ in range(600):
            result = engine.tick()
            if not result["on_object"]:
                # 训练觉知越来越快
                notice_delay = max(2, 8 - day)
                if engine.state.wandering_duration >= notice_delay:
                    notice_result = engine.player_notice()
                    engine.player_return()
                    
                    # 累积种子变化
                    for sid, delta in notice_result.get("seed_changes", {}).items():
                        if sid in seeds:
                            seeds[sid] = max(0, min(1, seeds[sid] + delta))
        
        result = engine.end_session()
        print(f"  第{day+1}天: 段位={result['stage']}, "
              f"散乱种子={seeds['restlessness']:.2f}, "
              f"念种子={seeds['mindfulness']:.2f}")
    
    print(f"\n7天后种子: 散乱={seeds['restlessness']:.2f}, 念={seeds['mindfulness']:.2f}")


def main():
    print("=" * 60)
    print("  禅修模拟引擎演示")
    print("  稳定度 + 明晰度 | 五盖 | 九住心")
    print("=" * 60)
    
    demo_hindrances()
    demo_nine_stages()
    demo_different_practitioners()
    demo_training_effect()
    demo_basic_session()
    
    print_separator("演示完成")


if __name__ == "__main__":
    main()

"""
禅修模拟引擎 (Meditation Simulation Engine)

核心设计：
1. 定 = 稳定度(Stability) + 明晰度(Clarity)
2. 五盖作为主要障碍
3. 九住心作为段位
4. 奖励"更快觉知"，不是"从不走神"
"""

import math
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class HindranceType(Enum):
    """五盖"""
    SENSUAL_DESIRE = "贪欲盖"      # kāmacchanda
    ILL_WILL = "嗔恚盖"            # vyāpāda  
    SLOTH_TORPOR = "惛沉睡眠盖"    # thīna-middha
    RESTLESSNESS = "掉举恶作盖"    # uddhacca-kukkucca
    DOUBT = "疑盖"                 # vicikicchā


class NineStages(Enum):
    """九住心"""
    INNER_ABIDING = "内住"           # 1. 能稳定10-20秒
    CONTINUOUS_ABIDING = "等住"      # 2. 断线后能快速回来
    RESTORATIVE_ABIDING = "安住"     # 3. 减少长时间走神
    CLOSE_ABIDING = "近住"           # 4. 很少完全忘掉所缘
    TAMING = "调伏"                  # 5. 能压住掉举
    PACIFYING = "寂静"               # 6. 止息细微烦恼波
    FULLY_PACIFYING = "最极寂静"     # 7. 细微掉举都能察觉
    SINGLE_POINTED = "一趣"          # 8. 长时间一境
    EQUIPOISE = "等持"               # 9. 稳且明，不靠硬顶


@dataclass
class Hindrance:
    """盖的定义"""
    type: HindranceType
    name: str
    
    # 食（触发/加剧条件）
    foods: List[str]
    
    # 非食（对治）
    antidotes: List[str]
    
    # 对稳定度/明晰度的影响
    stability_damage: float = 0.0
    clarity_damage: float = 0.0
    
    # 对别境五的打断
    disrupts: List[str] = field(default_factory=list)


# 五盖详细定义
FIVE_HINDRANCES: Dict[str, Hindrance] = {
    "sensual_desire": Hindrance(
        type=HindranceType.SENSUAL_DESIRE,
        name="贪欲盖",
        foods=["美境现前", "不净观未修", "根门不守", "食不知量"],
        antidotes=["不净观", "守护根门", "食知量", "亲近善知识"],
        stability_damage=0.3,
        clarity_damage=0.1,
        disrupts=["adhimoksa"]  # 让人犹豫不决
    ),
    "ill_will": Hindrance(
        type=HindranceType.ILL_WILL,
        name="嗔恚盖",
        foods=["逆境现前", "忆念过去怨", "不修慈心", "内热"],
        antidotes=["慈心观", "忍辱", "观缘起", "调身"],
        stability_damage=0.4,
        clarity_damage=0.2,
        disrupts=["samadhi"]
    ),
    "sloth_torpor": Hindrance(
        type=HindranceType.SLOTH_TORPOR,
        name="惛沉睡眠盖",
        foods=["食过量", "身疲劳", "心无精进", "不作光明想"],
        antidotes=["光明想", "精进", "调身", "经行", "少食"],
        stability_damage=0.1,
        clarity_damage=0.5,  # 主要损害明晰
        disrupts=["prajna", "samadhi"]
    ),
    "restlessness": Hindrance(
        type=HindranceType.RESTLESSNESS,
        name="掉举恶作盖",
        foods=["心不寂静", "多虑多思", "追悔过去", "刺激过多"],
        antidotes=["奢摩他", "数息", "身念住", "减少刺激"],
        stability_damage=0.5,  # 主要损害稳定
        clarity_damage=0.1,
        disrupts=["smrti", "samadhi"]
    ),
    "doubt": Hindrance(
        type=HindranceType.DOUBT,
        name="疑盖",
        foods=["不闻正法", "不如理作意", "信根未成熟"],
        antidotes=["闻正法", "如理作意", "亲近善知识", "读经"],
        stability_damage=0.3,
        clarity_damage=0.2,
        disrupts=["adhimoksa", "chanda"]
    ),
}


@dataclass
class MeditationState:
    """禅修状态（每秒更新）"""
    # 双轴核心
    stability: float = 0.5      # 稳定度 [0, 1]
    clarity: float = 0.5        # 明晰度 [0, 1]
    
    # 觉知相关
    on_object: bool = True      # 是否在所缘上
    wandering_duration: float = 0.0  # 走神持续时间（秒）
    noticing_latency: float = 0.0    # 觉知延迟（秒）
    
    # 当前激活的盖
    active_hindrances: Dict[str, float] = field(default_factory=dict)
    
    # 状态标记
    is_dull: bool = False       # 惛沉中
    is_restless: bool = False   # 掉举中
    is_wandering: bool = False  # 走神中


@dataclass
class SessionStats:
    """一局统计"""
    duration_seconds: int = 0
    
    # 核心指标
    on_object_ratio: float = 0.0        # 在所缘上的时间比例
    clarity_ratio: float = 0.0          # 清明区间比例
    avg_noticing_latency: float = 0.0   # 平均觉知延迟
    avg_recovery_time: float = 0.0      # 平均回归时间
    oscillation_count: int = 0          # 惛沉↔掉举摆动次数
    
    # 事件计数
    wander_count: int = 0               # 走神次数
    return_count: int = 0               # 归返次数
    dull_episodes: int = 0              # 惛沉发作
    restless_episodes: int = 0          # 掉举发作
    
    # 盖的统计
    hindrance_activations: Dict[str, int] = field(default_factory=dict)
    
    # 用于计算
    on_object_time: float = 0.0
    clarity_time: float = 0.0
    noticing_latencies: List[float] = field(default_factory=list)
    recovery_times: List[float] = field(default_factory=list)


# 九住心段位阈值
STAGE_THRESHOLDS = {
    NineStages.INNER_ABIDING: {
        "on_object_ratio": 0.30,
        "min_continuous_seconds": 10,
    },
    NineStages.CONTINUOUS_ABIDING: {
        "on_object_ratio": 0.40,
        "avg_recovery_time": 8.0,
    },
    NineStages.RESTORATIVE_ABIDING: {
        "on_object_ratio": 0.50,
        "avg_noticing_latency": 10.0,
    },
    NineStages.CLOSE_ABIDING: {
        "on_object_ratio": 0.60,
        "avg_noticing_latency": 7.0,
    },
    NineStages.TAMING: {
        "on_object_ratio": 0.65,
        "max_oscillation": 5,
        "restless_episodes": 3,
    },
    NineStages.PACIFYING: {
        "on_object_ratio": 0.70,
        "clarity_ratio": 0.60,
    },
    NineStages.FULLY_PACIFYING: {
        "on_object_ratio": 0.75,
        "avg_noticing_latency": 3.0,
    },
    NineStages.SINGLE_POINTED: {
        "on_object_ratio": 0.85,
        "clarity_ratio": 0.80,
    },
    NineStages.EQUIPOISE: {
        "on_object_ratio": 0.90,
        "clarity_ratio": 0.85,
        "oscillation_count": 2,
    },
}


class MeditationEngine:
    """
    禅修模拟引擎
    
    核心循环：
    1. 每秒更新状态（稳定度、明晰度、盖的压力）
    2. 根据状态触发事件（走神、惛沉、掉举）
    3. 玩家觉知并归返
    4. 记录统计，用于段位判定和种子熏习
    """
    
    def __init__(
        self,
        seed_bank: Optional[Dict[str, float]] = None,
        particular: Optional[Dict[str, float]] = None
    ):
        # 种子库（潜伏层）
        self.seeds = seed_bank or {
            "sloth_torpor": 0.5,
            "restlessness": 0.5,
            "sensual_desire": 0.5,
            "ill_will": 0.5,
            "doubt": 0.5,
            # 善种子
            "mindfulness": 0.5,
            "concentration": 0.5,
            "diligence": 0.5,
            "tranquility": 0.5,
            "equanimity": 0.5,
        }
        
        # 别境五（能力条）
        self.particular = particular or {
            "chanda": 0.5,      # 欲
            "adhimoksa": 0.5,   # 胜解
            "smrti": 0.5,       # 念
            "samadhi": 0.5,     # 定
            "prajna": 0.5,      # 慧
        }
        
        # 当前状态
        self.state = MeditationState()
        
        # 本局统计
        self.stats = SessionStats()
        
        # 时间
        self.elapsed_seconds = 0
        self.session_duration = 600  # 默认10分钟
        
        # 事件日志
        self.event_log: List[str] = []
        
        # 内部状态
        self._last_on_object = True
        self._wander_start_time = 0
        self._last_state_change = 0
    
    def start_session(self, duration_minutes: int = 10):
        """开始一局禅修"""
        self.session_duration = duration_minutes * 60
        self.elapsed_seconds = 0
        self.state = MeditationState()
        self.stats = SessionStats(duration_seconds=self.session_duration)
        self.event_log = []
        self._last_on_object = True
        self._wander_start_time = 0
        
        # 根据种子设置初始状态
        self.state.stability = self._calculate_base_stability()
        self.state.clarity = self._calculate_base_clarity()
        
        self._log("禅修开始")
    
    def _calculate_base_stability(self) -> float:
        """计算基础稳定度"""
        samadhi = self.particular.get("samadhi", 0.5)
        smrti = self.particular.get("smrti", 0.5)
        adhimoksa = self.particular.get("adhimoksa", 0.5)
        
        # 减去惛沉和掉举的潜伏影响
        restless_seed = self.seeds.get("restlessness", 0.5)
        
        base = (samadhi * 0.4 + smrti * 0.3 + adhimoksa * 0.2 + 0.1)
        base -= restless_seed * 0.2
        
        return max(0.1, min(0.9, base))
    
    def _calculate_base_clarity(self) -> float:
        """计算基础明晰度"""
        samadhi = self.particular.get("samadhi", 0.5)
        prajna = self.particular.get("prajna", 0.5)
        
        # 减去惛沉的潜伏影响
        sloth_seed = self.seeds.get("sloth_torpor", 0.5)
        
        base = (samadhi * 0.3 + prajna * 0.4 + 0.3)
        base -= sloth_seed * 0.3
        
        return max(0.1, min(0.9, base))
    
    def tick(self) -> Dict:
        """
        每秒更新（核心循环）
        
        Returns:
            当前状态和事件
        """
        self.elapsed_seconds += 1
        events = []
        
        # 1. 计算盖的压力
        hindrance_pressure = self._calculate_hindrance_pressure()
        
        # 2. 更新稳定度和明晰度
        self._update_stability_clarity(hindrance_pressure)
        
        # 3. 检查是否触发走神/惛沉/掉举
        events.extend(self._check_state_changes())
        
        # 4. 更新统计
        self._update_stats()
        
        return {
            "elapsed": self.elapsed_seconds,
            "stability": self.state.stability,
            "clarity": self.state.clarity,
            "on_object": self.state.on_object,
            "is_dull": self.state.is_dull,
            "is_restless": self.state.is_restless,
            "events": events,
            "active_hindrances": list(self.state.active_hindrances.keys()),
        }
    
    def _calculate_hindrance_pressure(self) -> Dict[str, float]:
        """计算各盖的当前压力"""
        pressure = {}
        
        for hid, hindrance in FIVE_HINDRANCES.items():
            # 基础压力来自种子
            base = self.seeds.get(hid, 0.5)
            
            # 随时间可能累积（疲劳等）
            fatigue_factor = min(1.0, self.elapsed_seconds / self.session_duration)
            
            # 惛沉随时间增加
            if hid == "sloth_torpor":
                base += fatigue_factor * 0.2
            
            # 掉举在开始时较高
            if hid == "restlessness":
                base += (1 - fatigue_factor) * 0.1
            
            # 念可以压制
            smrti = self.particular.get("smrti", 0.5)
            base -= smrti * 0.2
            
            pressure[hid] = max(0.0, min(1.0, base))
            
            # 超过阈值则激活
            if base > 0.6 and random.random() < base * 0.1:
                if hid not in self.state.active_hindrances:
                    self.state.active_hindrances[hid] = base
                    self.stats.hindrance_activations[hid] = \
                        self.stats.hindrance_activations.get(hid, 0) + 1
                    self._log(f"{hindrance.name}现起")
        
        return pressure
    
    def _update_stability_clarity(self, pressure: Dict[str, float]):
        """更新稳定度和明晰度"""
        # 基础恢复
        base_stability = self._calculate_base_stability()
        base_clarity = self._calculate_base_clarity()
        
        # 向基础值缓慢回归
        self.state.stability += (base_stability - self.state.stability) * 0.05
        self.state.clarity += (base_clarity - self.state.clarity) * 0.05
        
        # 盖的损害
        for hid, strength in self.state.active_hindrances.items():
            hindrance = FIVE_HINDRANCES[hid]
            self.state.stability -= hindrance.stability_damage * strength * 0.1
            self.state.clarity -= hindrance.clarity_damage * strength * 0.1
        
        # 掉举压力直接损害稳定
        restless_p = pressure.get("restlessness", 0)
        self.state.stability -= restless_p * 0.05
        
        # 惛沉压力直接损害明晰
        sloth_p = pressure.get("sloth_torpor", 0)
        self.state.clarity -= sloth_p * 0.05
        
        # 限制范围
        self.state.stability = max(0.1, min(0.95, self.state.stability))
        self.state.clarity = max(0.1, min(0.95, self.state.clarity))
    
    def _check_state_changes(self) -> List[str]:
        """检查状态变化（走神、惛沉、掉举）"""
        events = []
        
        # 走神概率
        if self.state.on_object:
            wander_prob = self._sigmoid(
                -self.state.stability * 2 + 
                self.seeds.get("restlessness", 0.5) - 
                self.particular.get("smrti", 0.5)
            ) * 0.05  # 每秒5%基础概率
            
            if random.random() < wander_prob:
                self.state.on_object = False
                self.state.is_wandering = True
                self._wander_start_time = self.elapsed_seconds
                self.stats.wander_count += 1
                events.append("走神")
                self._log("心离所缘")
        
        # 惛沉检测
        old_dull = self.state.is_dull
        self.state.is_dull = self.state.clarity < 0.4
        if self.state.is_dull and not old_dull:
            self.stats.dull_episodes += 1
            events.append("惛沉")
            self._log("惛沉现起")
        
        # 掉举检测
        old_restless = self.state.is_restless
        self.state.is_restless = self.state.stability < 0.4
        if self.state.is_restless and not old_restless:
            self.stats.restless_episodes += 1
            events.append("掉举")
            self._log("掉举现起")
        
        # 惛沉↔掉举摆动
        if old_dull and self.state.is_restless:
            self.stats.oscillation_count += 1
        if old_restless and self.state.is_dull:
            self.stats.oscillation_count += 1
        
        return events
    
    def _update_stats(self):
        """更新统计"""
        if self.state.on_object:
            self.stats.on_object_time += 1
        
        if self.state.clarity > 0.5:
            self.stats.clarity_time += 1
        
        # 走神持续时间
        if not self.state.on_object:
            self.state.wandering_duration = \
                self.elapsed_seconds - self._wander_start_time
    
    def player_notice(self) -> Dict:
        """
        玩家觉知（按下"归返"按钮）
        
        Returns:
            觉知结果和种子变化
        """
        result = {
            "noticed": False,
            "latency": 0.0,
            "seed_changes": {},
        }
        
        if not self.state.on_object:
            # 记录觉知延迟
            latency = self.state.wandering_duration
            result["latency"] = latency
            result["noticed"] = True
            
            self.state.noticing_latency = latency
            self.stats.noticing_latencies.append(latency)
            
            self._log(f"觉知（延迟{latency:.1f}秒）")
            
            # 种子熏习：奖励更快觉知
            if latency < 3:
                # 非常快的觉知
                result["seed_changes"]["mindfulness"] = 0.02
                result["seed_changes"]["diligence"] = 0.01
            elif latency < 7:
                # 较快的觉知
                result["seed_changes"]["mindfulness"] = 0.01
            else:
                # 慢觉知
                result["seed_changes"]["mindfulness"] = -0.005
                result["seed_changes"]["restlessness"] = 0.005
            
            # 应用种子变化
            for seed_id, delta in result["seed_changes"].items():
                self.seeds[seed_id] = max(0, min(1, 
                    self.seeds.get(seed_id, 0.5) + delta))
        
        return result
    
    def player_return(self) -> Dict:
        """
        玩家归返（回到所缘）
        
        Returns:
            归返结果
        """
        result = {
            "returned": False,
            "recovery_time": 0.0,
        }
        
        if not self.state.on_object:
            recovery_time = self.state.wandering_duration
            result["recovery_time"] = recovery_time
            result["returned"] = True
            
            self.stats.recovery_times.append(recovery_time)
            self.stats.return_count += 1
            
            # 回到所缘
            self.state.on_object = True
            self.state.is_wandering = False
            self.state.wandering_duration = 0
            
            # 稳定度小幅恢复
            self.state.stability += 0.05
            
            self._log(f"归返（用时{recovery_time:.1f}秒）")
            
            # 清除激活的盖
            self.state.active_hindrances.clear()
        
        return result
    
    def player_adjust(self, action: str) -> Dict:
        """
        玩家调整（对治惛沉/掉举）
        
        Args:
            action: "raise" (提起) 或 "relax" (放松)
        
        Returns:
            调整结果
        """
        result = {"adjusted": True, "effect": ""}
        
        if action == "raise":
            # 提起：对治惛沉，但可能增加掉举
            if self.state.is_dull:
                self.state.clarity += 0.1
                self.state.stability -= 0.03  # 轻微代价
                result["effect"] = "明晰度提升"
                
                # 如果过度提起
                if self.state.stability < 0.4:
                    result["effect"] += "，但稳定度下降"
                    self.seeds["restlessness"] = min(1, 
                        self.seeds.get("restlessness", 0.5) + 0.01)
            else:
                result["effect"] = "当前不需要提起"
                
        elif action == "relax":
            # 放松：对治掉举，但可能增加惛沉
            if self.state.is_restless:
                self.state.stability += 0.1
                self.state.clarity -= 0.03  # 轻微代价
                result["effect"] = "稳定度提升"
                
                # 如果过度放松
                if self.state.clarity < 0.4:
                    result["effect"] += "，但明晰度下降"
                    self.seeds["sloth_torpor"] = min(1,
                        self.seeds.get("sloth_torpor", 0.5) + 0.01)
            else:
                result["effect"] = "当前不需要放松"
        
        return result
    
    def end_session(self) -> Dict:
        """
        结束禅修，计算最终统计和段位
        """
        # 计算比例
        total = self.elapsed_seconds or 1
        self.stats.on_object_ratio = self.stats.on_object_time / total
        self.stats.clarity_ratio = self.stats.clarity_time / total
        
        # 计算平均值
        if self.stats.noticing_latencies:
            self.stats.avg_noticing_latency = \
                sum(self.stats.noticing_latencies) / len(self.stats.noticing_latencies)
        
        if self.stats.recovery_times:
            self.stats.avg_recovery_time = \
                sum(self.stats.recovery_times) / len(self.stats.recovery_times)
        
        # 判定段位
        stage = self._determine_stage()
        
        # 生成复盘
        review = self._generate_review(stage)
        
        self._log("禅修结束")
        
        return {
            "stats": {
                "duration": self.elapsed_seconds,
                "on_object_ratio": self.stats.on_object_ratio,
                "clarity_ratio": self.stats.clarity_ratio,
                "avg_noticing_latency": self.stats.avg_noticing_latency,
                "avg_recovery_time": self.stats.avg_recovery_time,
                "oscillation_count": self.stats.oscillation_count,
                "wander_count": self.stats.wander_count,
                "return_count": self.stats.return_count,
                "dull_episodes": self.stats.dull_episodes,
                "restless_episodes": self.stats.restless_episodes,
            },
            "stage": stage.value if stage else "未达标",
            "review": review,
            "event_log": self.event_log,
        }
    
    def _determine_stage(self) -> Optional[NineStages]:
        """判定达到的最高段位"""
        achieved = None
        
        for stage in NineStages:
            thresholds = STAGE_THRESHOLDS.get(stage, {})
            passed = True
            
            for key, threshold in thresholds.items():
                if key == "on_object_ratio":
                    if self.stats.on_object_ratio < threshold:
                        passed = False
                elif key == "clarity_ratio":
                    if self.stats.clarity_ratio < threshold:
                        passed = False
                elif key == "avg_noticing_latency":
                    if self.stats.avg_noticing_latency > threshold:
                        passed = False
                elif key == "avg_recovery_time":
                    if self.stats.avg_recovery_time > threshold:
                        passed = False
                elif key == "max_oscillation" or key == "oscillation_count":
                    if self.stats.oscillation_count > threshold:
                        passed = False
                elif key == "restless_episodes":
                    if self.stats.restless_episodes > threshold:
                        passed = False
            
            if passed:
                achieved = stage
            else:
                break  # 段位是递进的
        
        return achieved
    
    def _generate_review(self, stage: Optional[NineStages]) -> str:
        """生成复盘文字"""
        lines = []
        
        lines.append(f"【禅修复盘】{self.elapsed_seconds//60}分{self.elapsed_seconds%60}秒")
        lines.append("")
        
        # 双轴评价
        if self.stats.on_object_ratio > 0.7:
            lines.append("稳定度：良好，心能常住所缘")
        elif self.stats.on_object_ratio > 0.5:
            lines.append("稳定度：尚可，偶有散乱")
        else:
            lines.append("稳定度：需加强，散乱较多")
        
        if self.stats.clarity_ratio > 0.7:
            lines.append("明晰度：良好，心明不昏")
        elif self.stats.clarity_ratio > 0.5:
            lines.append("明晰度：尚可，偶有惛沉")
        else:
            lines.append("明晰度：需加强，惛沉较重")
        
        lines.append("")
        
        # 觉知评价
        if self.stats.avg_noticing_latency < 5:
            lines.append(f"觉知速度：敏锐（平均{self.stats.avg_noticing_latency:.1f}秒）")
        elif self.stats.avg_noticing_latency < 10:
            lines.append(f"觉知速度：中等（平均{self.stats.avg_noticing_latency:.1f}秒）")
        else:
            lines.append(f"觉知速度：迟钝（平均{self.stats.avg_noticing_latency:.1f}秒）")
        
        lines.append("")
        
        # 主要障碍
        if self.stats.dull_episodes > self.stats.restless_episodes:
            lines.append(f"主要障碍：惛沉（{self.stats.dull_episodes}次）")
            lines.append("建议：修光明想、提起精进")
        elif self.stats.restless_episodes > self.stats.dull_episodes:
            lines.append(f"主要障碍：掉举（{self.stats.restless_episodes}次）")
            lines.append("建议：放松身心、减少刺激")
        else:
            lines.append("障碍均衡，继续保持平衡")
        
        lines.append("")
        
        # 段位
        if stage:
            lines.append(f"【段位】{stage.value}")
        else:
            lines.append("【段位】继续努力")
        
        return "\n".join(lines)
    
    def _log(self, msg: str):
        """记录事件"""
        self.event_log.append(f"[{self.elapsed_seconds}s] {msg}")
    
    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

"""
智能穿衣助理的工具函数
"""
import math
import requests
from datetime import datetime, timedelta
from functools import wraps

# 常量定义
RELATIVE_DATE_MAP = {
    "今天": 0, "today": 0, "今日": 0,
    "明天": 1, "tomorrow": 1, "明日": 1,
    "后天": 2, "day after tomorrow": 2, "后日": 2,
    "大后天": 3
}

# 温度阈值
TEMP_VERY_COLD = 0
TEMP_COLD = 5
TEMP_MILD = 15
TEMP_WARM = 25
TEMP_HOT = 27
TEMP_VERY_HOT = 30

# 湿度阈值
HUMIDITY_HIGH = 70
HUMIDITY_VERY_HIGH = 80
HUMIDITY_EXTREME = 90

# 风力阈值
WIND_STRONG = 4
WIND_VERY_STRONG = 7
WIND_MAX_LEVEL = 12

# 降水概率阈值
RAIN_CHANCE_MODERATE = 20
RAIN_CHANCE_HIGH = 40
RAIN_CHANCE_VERY_HIGH = 50
RAIN_CHANCE_EXTREME = 70

# API 超时时间
API_TIMEOUT = 10


def _parse_relative_date(date: str) -> str:
    """
    解析相对日期并转换为具体日期
    
    Args:
        date: 相对日期字符串（如"今天"、"明天"）或具体日期（YYYY-MM-DD）
    
    Returns:
        具体日期字符串（YYYY-MM-DD）
    """
    date_lower = date.lower()
    today = datetime.now()
    
    if date_lower in RELATIVE_DATE_MAP:
        days_offset = RELATIVE_DATE_MAP[date_lower]
        target_date = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    else:
        # 假设是具体日期格式（YYYY-MM-DD）
        target_date = date
    
    return target_date


def _extract_official_real_feel(daily: dict, index: int) -> tuple:
    """
    提取官方体感温度数据
    
    Args:
        daily: 每日天气数据字典
        index: 数据索引
    
    Returns:
        (官方体感最高温, 官方体感最低温, 官方体感平均温度)
    """
    apparent_temp_max = daily.get("apparent_temperature_max", [])
    apparent_temp_min = daily.get("apparent_temperature_min", [])
    
    official_real_feel_max = None
    official_real_feel_min = None
    
    if apparent_temp_max and len(apparent_temp_max) > index:
        official_real_feel_max = round(apparent_temp_max[index], 1)
    if apparent_temp_min and len(apparent_temp_min) > index:
        official_real_feel_min = round(apparent_temp_min[index], 1)
    
    if official_real_feel_max is not None and official_real_feel_min is not None:
        official_real_feel_avg = round((official_real_feel_max + official_real_feel_min) / 2, 1)
    else:
        official_real_feel_avg = None
    
    return official_real_feel_max, official_real_feel_min, official_real_feel_avg


def tool_logger(tool_name: str, description: str):
    """
    工具函数日志装饰器
    
    Args:
        tool_name: 工具名称
        description: 工具描述
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 格式化参数用于日志显示
            args_str = ", ".join([str(arg) for arg in args])
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            params_str = ", ".join(filter(None, [args_str, kwargs_str]))
            
            # 调用前日志
            print(f"[行动] 调用工具 {tool_name}({params_str})")
            
            try:
                # 执行工具函数
                result = func(*args, **kwargs)
                
                # 格式化结果用于日志显示（只显示关键信息，避免过长）
                if isinstance(result, dict):
                    # 对于字典，显示关键字段
                    key_fields = ['city', 'date', 'temp_max', 'temp_min', 'wind', 'humidity', 'precipitation', 
                                 'clothing', 'special_items']
                    result_summary = {k: v for k, v in result.items() if k in key_fields}
                    result_str = str(result_summary)
                else:
                    result_str = str(result)
                
                # 调用后日志
                print(f"[结果] {tool_name} 执行成功: {result_str}")
                
                return result
            except Exception as e:
                # 错误日志
                print(f"[结果] {tool_name} 执行失败: {str(e)}")
                raise
        
        return wrapper
    return decorator


@tool_logger("Get_Weather", "获取指定城市和日期的天气信息")
def Get_Weather(city: str, date: str) -> dict:
    """
    获取指定城市和日期的天气信息（调用 Open-Meteo API，无需 API Key）
    
    Args:
        city: 城市名称（支持中英文，如：北京、Shanghai）
        date: 日期（格式：YYYY-MM-DD，或相对日期如"今天"、"明天"、"后天"等）
    
    Returns:
        包含最高温、最低温、风力、降水概率、湿度的字典
    """
    # 处理相对日期：自动计算"今天"、"明天"、"后天"等
    target_date = _parse_relative_date(date)
    
    try:
        # 第一步：通过城市名获取经纬度
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocoding_params = {
            "name": city,
            "count": 1,  # 只取第一个结果
            "language": "zh"  # 中文
        }
        
        geo_response = requests.get(geocoding_url, params=geocoding_params, timeout=API_TIMEOUT)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        # 检查是否找到城市
        if not geo_data.get("results") or len(geo_data["results"]) == 0:
            raise ValueError(f"未找到城市：{city}，请检查城市名称是否正确。")
        
        # 获取第一个结果的经纬度
        location = geo_data["results"][0]
        latitude = location["latitude"]
        longitude = location["longitude"]
        city_name = location.get("name", city)  # 使用 API 返回的标准城市名
        
        # 第二步：使用经纬度获取天气数据
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",  # 获取当前湿度和风速
            "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_probability_max,windspeed_10m_max,relative_humidity_2m_max",  # 获取每日数据，包括湿度和官方体感温度
            "timezone": "auto",  # 自动时区
            "start_date": target_date,
            "end_date": target_date
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=API_TIMEOUT)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # 提取天气信息
        daily = weather_data.get("daily", {})
        current = weather_data.get("current", {})
        dates = daily.get("time", [])
        
        # 查找目标日期的数据（如果找不到，使用第一个可用日期）
        if target_date in dates:
            index = dates.index(target_date)
        elif len(dates) > 0:
            index = 0  # 使用第一个可用日期
            target_date = dates[0]  # 更新实际使用的日期
        else:
            raise ValueError("未找到指定日期的天气数据。")
        
        temp_max = daily.get("temperature_2m_max", [0])[index]
        temp_min = daily.get("temperature_2m_min", [0])[index]
        precipitation = daily.get("precipitation_probability_max", [0])[index]
        wind_speed = daily.get("windspeed_10m_max", [0])[index]
        
        # 获取官方体感温度（Open-Meteo API 提供的）
        official_real_feel_max, official_real_feel_min, official_real_feel_avg = _extract_official_real_feel(daily, index)
        
        # 获取湿度：优先使用 daily 的湿度数据，如果没有则使用 current 的湿度
        humidity_daily = daily.get("relative_humidity_2m_max", [])
        if humidity_daily and len(humidity_daily) > index:
            humidity = humidity_daily[index]
        else:
            humidity = current.get("relative_humidity_2m", 50)  # 默认50%
        
        # 将风速（m/s）转换为风力等级（简化转换：1 m/s ≈ 0.5级）
        wind_level = round(wind_speed * 0.5)
        # 将风速（m/s）转换为 km/h（1 m/s = 3.6 km/h）
        wind_speed_kmh = wind_speed * 3.6
        
        result = {
            "city": city_name,
            "date": target_date,
            "temp_max": round(temp_max),
            "temp_min": round(temp_min),
            "wind": max(0, min(WIND_MAX_LEVEL, wind_level)),  # 限制在 0-12 级（保留用于显示）
            "wind_speed_kmh": round(wind_speed_kmh, 1),  # 风速（km/h），用于体感温度计算
            "precipitation": round(precipitation),
            "humidity": round(humidity),  # 添加湿度信息
            # 官方体感温度（用于交叉验证）
            "official_real_feel_max": official_real_feel_max,  # 官方体感最高温
            "official_real_feel_min": official_real_feel_min,  # 官方体感最低温
            "official_real_feel_avg": official_real_feel_avg,  # 官方体感平均温度
            "description": f"最高温 {round(temp_max)}°C，最低温 {round(temp_min)}°C，湿度 {round(humidity)}%"
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        # API 调用失败时的错误处理
        raise ConnectionError(f"无法获取天气数据：{str(e)}。请检查网络连接。")
    except (KeyError, IndexError) as e:
        # API 返回数据格式异常
        raise ValueError(f"天气 API 返回数据格式异常：{str(e)}")


@tool_logger("Calc_RealFeel", "科学计算体感温度（考虑风寒效应和湿度影响）")
def Calc_RealFeel(temperature: float, wind_speed_kmh: float, humidity: float = 50.0) -> float:
    """
    使用简化的气象学模型计算体感温度
    
    Args:
        temperature: 实际温度（摄氏度）
        wind_speed_kmh: 风速（km/h）
        humidity: 相对湿度（0-100%），默认50%
    
    Returns:
        体感温度（摄氏度）
    """
    # 1. 低温区：考虑风寒效应 (主要针对 ≤ 10°C)
    if temperature <= 10:
        # 简化的风寒公式：温度 - 2 * sqrt(风速)
        # 风速越大，体感温度下降越明显（非线性关系）
        wind_chill = 2 * math.sqrt(max(0, wind_speed_kmh))
        real_feel = temperature - wind_chill
    
    # 2. 高温区：考虑湿度影响 (主要针对 ≥ TEMP_WARM°C)
    elif temperature >= TEMP_WARM:
        # 湿度每增加 10%，体感约上升 1°C
        # 以50%为基准，湿度越高体感越热
        humidity_extra = (humidity - 50) * 0.1
        real_feel = temperature + humidity_extra
        
    # 3. 中间区域：线性过渡（10°C < temperature < TEMP_WARM°C）
    else:
        # 在中间区域，风寒和湿度影响都较小，但仍有轻微影响
        # 风寒效应：随温度升高而减弱
        temp_range = TEMP_WARM - 10
        wind_factor = (TEMP_WARM - temperature) / temp_range * 1.5 * math.sqrt(max(0, wind_speed_kmh)) / 5
        # 湿度影响：高温时增强，低温时减弱
        humidity_factor = (temperature - 10) / temp_range * (humidity - 50) * 0.05
        real_feel = temperature - wind_factor + humidity_factor
        
    # 4. 湿冷修正（南方特供逻辑：低温高湿环境）
    # 在低温高湿环境下（如南方冬雨），体感温度应显著低于实际温度
    if temperature < TEMP_MILD and humidity > HUMIDITY_HIGH:
        # 湿冷带来的额外体感下降
        # 湿度越高、温度越低，影响越大
        wet_cold_factor = (humidity - 70) / 30 * (15 - temperature) / 5 * 2
        real_feel -= wet_cold_factor
        
    return round(real_feel, 1)


@tool_logger("Match_Clothing", "多维度场景化穿衣决策")
def Match_Clothing(real_feel: float, weather_condition: dict) -> dict:
    """
    基于体感温度、湿度、风力、降水的深度决策模型
    重点区分湿冷和湿热两个极端场景
    
    Args:
        real_feel: 经过科学计算后的体感温度（摄氏度）
        weather_condition: 包含温度、湿度、风力、降水概率的天气数据字典
    
    Returns:
        包含基础穿搭、配饰、鞋履、逻辑说明的字典
    """
    temp = weather_condition.get("temp_max", 20)  # 使用最高温做上限参考
    temp_min = weather_condition.get("temp_min", 20)
    temp_avg = (temp + temp_min) / 2
    humidity = weather_condition.get("humidity", 50)
    wind = weather_condition.get("wind", 0)  # 风力等级
    wind_speed_kmh = weather_condition.get("wind_speed_kmh", 0)
    rain_chance = weather_condition.get("precipitation", 0)
    
    extra_items = []
    footwear = "常规运动鞋"
    logic_parts = []
    
    # 1. 核心分层建议（基于体感温度）
    if real_feel < TEMP_VERY_COLD:
        base = "保暖层（长袖内衣+毛衣）+ 加厚防风羽绒服"
        accessories = ["围巾", "手套"]
    elif TEMP_VERY_COLD <= real_feel < TEMP_MILD:
        base = "长袖衬衫/针织衫 + 防风夹克或呢大衣"
        accessories = []
    elif TEMP_MILD <= real_feel < TEMP_WARM:
        base = "短袖/薄长袖 + 轻便外套（如薄开衫）"
        accessories = []
    else:
        base = "吸湿排汗短袖 + 宽松短裤/短裙"
        accessories = []
    
    # 2. 深度环境决策 - 场景化处理
    
    # --- 场景 A：湿热桑拿天 (如新加坡、夏季南方) ---
    if temp > TEMP_HOT and humidity > HUMIDITY_HIGH:
        base = "【清爽模式】极薄透气面料（亚麻/速干材质）"
        extra_items.append("极薄防晒衣（预防强冷气房温差）")
        footwear = "透气凉鞋或网面运动鞋"
        logic_parts.append(f"检测到湿热桑拿环境（温度{temp}°C，湿度{humidity}%），已为您优化为速干排汗方案，禁止厚重衣物")
    
    # --- 场景 B：湿冷魔法伤害 (如南方冬雨) ---
    elif temp < 12 and humidity > HUMIDITY_HIGH:
        # 湿冷场景：强调防风拨水
        if base.find("羽绒服") == -1 and base.find("夹克") == -1:
            base = "防风拨水外套 + " + base
        extra_items.append("暖宝宝或发热内衣（湿气会加速体温流失）")
        footwear = "防水靴或防拨水运动鞋"
        logic_parts.append(f"检测到湿冷环境（温度{temp}°C，湿度{humidity}%），已强化防风拨水方案，避免衣物受潮失去保暖性")
    
    # --- 场景 C：防风与降水（包含强风加固逻辑）---
    wind_protection_added_to_base = False  # 标记是否已在base中添加防风属性
    
    def _handle_wind_protection(wind_level: int, temperature: float, is_strong_wind: bool = False):
        """处理防风逻辑的辅助函数"""
        nonlocal base, wind_protection_added_to_base
        
        if temperature < TEMP_HOT:
            # 低温强风：需要防风保暖
            if "防风" not in base:
                if is_strong_wind:
                    base = "强风加固型外套（冲锋衣/防风夹克） + " + base
                else:
                    base = "防风层（冲锋衣/风衣） + " + base
                wind_protection_added_to_base = True
            
            if is_strong_wind:
                extra_items.append("【强风加固型建议】避免易兜风衣物（如宽松长裙、大摆外套），选择贴身剪裁")
                logic_parts.append(f"检测到{wind_level}级强风，已启用强风加固方案，避免易兜风衣物")
            elif not wind_protection_added_to_base:
                # 去重：如果base中已有防风属性，不在extra中重复推荐
                extra_items.append("防风层（冲锋衣/风衣）")
                logic_parts.append(f"考虑{wind_level}级强风降温影响，已添加防风层")
        else:
            # 高温强风：矛盾天气的综合权衡
            extra_items.append("【强风vs高温权衡】建议轻薄防风外套，避免完全暴露于强风中，同时保持透气性")
            extra_items.append("防风墨镜（预防风沙/强风）")
            logic_parts.append(f"检测到高温强风矛盾天气（温度{temperature}°C，{wind_level}级风），已平衡防风与散热需求")
    
    if wind >= WIND_VERY_STRONG:
        _handle_wind_protection(wind, temp, is_strong_wind=True)
    elif wind >= WIND_STRONG:
        _handle_wind_protection(wind, temp, is_strong_wind=False)
    
    # 处理降水逻辑
    if rain_chance > RAIN_CHANCE_HIGH:
        extra_items.append("折叠伞/雨具")
        if rain_chance > RAIN_CHANCE_EXTREME:
            footwear = "专业防滑雨鞋或备用袜子"
            logic_parts.append(f"降水概率{rain_chance}%，建议专业防滑雨鞋")
        else:
            logic_parts.append(f"降水概率{rain_chance}%，建议携带雨具")
    
    # --- 场景 D：紫外线/防晒 ---
    if temp > 20 and rain_chance < RAIN_CHANCE_MODERATE:
        if "防晒霜" not in accessories:
            accessories.append("防晒霜")
        if temp >= TEMP_WARM:
            accessories.extend(["遮阳帽", "墨镜"])
        logic_parts.append("晴天高温，已添加防晒装备")
    
    # 3. 鞋履智能推荐（根据降水概率和气温）
    if footwear == "常规运动鞋":
        if rain_chance > RAIN_CHANCE_EXTREME:
            footwear = "专业防滑雨鞋或备用袜子"
        elif rain_chance > RAIN_CHANCE_HIGH:
            footwear = "防滑运动鞋（建议防水处理）"
        elif temp < 5:
            footwear = "保暖防滑靴"
        elif temp > TEMP_VERY_HOT:
            footwear = "透气凉鞋或网面运动鞋"
        elif temp > TEMP_WARM:
            footwear = "透气运动鞋或凉鞋"
    
    # --- 场景 E：多因素关联 - 极高湿度且无雨（浓雾预警）---
    if humidity > HUMIDITY_EXTREME and rain_chance < RAIN_CHANCE_MODERATE:
        # 极高湿度且无雨，可能是浓雾天气（多因素关联）
        extra_items.append("【浓雾预警】湿度极高且无降水，可能存在浓雾，建议选择颜色鲜艳或反光材质的衣物，提高可见度")
        logic_parts.append(f"检测到极高湿度（{humidity}%）且无降水，已触发浓雾预警方案（多因素关联分析）")
    elif humidity > HUMIDITY_VERY_HIGH and rain_chance < RAIN_CHANCE_VERY_HIGH:
        # 常规高湿度防潮提醒（但如果有降水，则优先考虑防雨）
        if "防潮" not in " ".join(extra_items):
            logic_parts.append(f"检测到极高湿度（{humidity}%），已切换至防潮排汗方案")
    
    # 4. 构建逻辑说明（包含矛盾天气的综合权衡说明）
    logic_desc = f"基于体感{real_feel}°C判断。"
    if logic_parts:
        logic_desc += " " + "；".join(logic_parts)
    
    # 特别强调矛盾天气的综合权衡
    if temp >= TEMP_HOT and wind >= WIND_STRONG:
        logic_desc += " 【矛盾天气权衡】在高温强风环境下，已综合考虑防风需求与散热需求，建议轻薄防风材质。"
    elif humidity > HUMIDITY_EXTREME and rain_chance < RAIN_CHANCE_MODERATE:
        logic_desc += " 【多因素关联】极高湿度且无降水，可能存在浓雾，已优化为浓雾预警方案。"
    
    # 5. 汇总输出
    accessories_str = "、".join(list(set(accessories))) if accessories else "无"
    extra_items_str = "、".join(list(set(extra_items))) if extra_items else "无"
    
    return {
        "clothing_base": base,  # 基础穿搭
        "base_clothing": base,  # 保持兼容
        "accessories": accessories_str,  # 配饰
        "extra_items": extra_items_str,  # 额外装备
        "footwear": footwear,  # 鞋履建议
        "logic": logic_desc,  # 逻辑说明
        "logic_summary": logic_desc,  # 保持兼容
        "protection_layer": extra_items_str,  # 防护层建议
        "protection_tips": logic_parts,  # 防护类型列表
        # 保持向后兼容的字段
        "clothing": base,
        "special_items": accessories_str if accessories_str != "无" else "无特殊装备",
        "special_items_list": accessories
    }


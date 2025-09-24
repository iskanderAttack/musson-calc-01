import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
from datetime import timedelta

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор печи Муссон",
    page_icon="🔥",
    layout="wide"
)

# --- Параметры материалов (теплопроводность, Вт/м·К) ---
MATERIALS = {
    "кирпич": 0.81,
    "газоблок": 0.12,
    "дерево": 0.18,
    "сэндвич-панель": 0.04,
    "керамзит блок": 0.43,
    "пенобетон": 0.14
}

# --- Модели "Муссон" ---
MUSSON_MODELS = {
    "Муссон 300": {"volume_l": 77, "price": 45000},
    "Муссон 600": {"volume_l": 125, "price": 65000},
    "Муссон 1000": {"volume_l": 200, "price": 85000},
    "Муссон 1500": {"volume_l": 311, "price": 110000},
    "Муссон 2000": {"volume_l": 467, "price": 135000},
}

# --- Плотность и теплотворная способность материалов ---
FUEL_TYPES = {
    "хвойные": {"density": 350, "q": 17, "price_per_ton": 2500},
    "берёза": {"density": 450, "q": 18, "price_per_ton": 3500},
    "дуб": {"density": 550, "q": 19.5, "price_per_ton": 5000},
    "ясень": {"density": 520, "q": 19.0, "price_per_ton": 4500},
    "ЛДСП": {"density": 650, "q": 16.5, "price_per_ton": 1500},
    "ДСП": {"density": 680, "q": 16.0, "price_per_ton": 1200},
    "фанера": {"density": 600, "q": 16.8, "price_per_ton": 1800},
    "мебельные отходы": {"density": 550, "q": 15.5, "price_per_ton": 1000},
    "строительные отходы": {"density": 500, "q": 14.0, "price_per_ton": 800}
}

def calc_heat_loss(area_m2, height_m, wall_thickness_m, material, t_in, t_out, 
                   windows_m2=0, doors_m2=0, roof_insulation=True):
    """Расчёт теплопотерь с учётом окон, дверей и крыши"""
    volume_m3 = area_m2 * height_m
    
    # Теплопотери через стены
    lambda_wall = MATERIALS[material]
    r_wall = wall_thickness_m / lambda_wall
    wall_area = 2 * height_m * (math.sqrt(area_m2) * 4) - windows_m2 - doors_m2  # упрощённо
    q_walls = wall_area * (t_in - t_out) / r_wall
    
    # Теплопотери через окна (примерное сопротивление)
    q_windows = windows_m2 * (t_in - t_out) / 0.4  # R≈0.4 для стандартных окон
    
    # Теплопотери через двери
    q_doors = doors_m2 * (t_in - t_out) / 0.6  # R≈0.6 для дверей
    
    # Теплопотери через крышу
    roof_r = 0.2 if not roof_insulation else 1.0
    q_roof = area_m2 * (t_in - t_out) / roof_r
    
    # Теплопотери через вентиляцию (примерно 0.3 Вт/м³·К)
    q_vent = 0.3 * volume_m3 * (t_in - t_out)
    
    total_w = q_walls + q_windows + q_doors + q_roof + q_vent
    return total_w / 1000  # кВт

def musson_power(volume_l, fill_fraction, fuel_type, efficiency, burn_hours):
    """Расчёт мощности и энергии от одной закладки"""
    vol_m3 = volume_l / 1000
    filled_vol_m3 = vol_m3 * fill_fraction
    m_fuel = filled_vol_m3 * FUEL_TYPES[fuel_type]["density"]
    q_fuel = m_fuel * FUEL_TYPES[fuel_type]["q"]  # МДж
    q_kwh = q_fuel / 3.6
    useful_kwh = q_kwh * efficiency
    p_kw = useful_kwh / burn_hours
    return useful_kwh, p_kw, m_fuel

def calculate_fuel_consumption(heat_loss_kw, working_hours, fuel_energy_kwh_per_kg):
    """Расчёт расхода топлива за рабочий день"""
    daily_heat_kwh = heat_loss_kw * working_hours
    return daily_heat_kwh / fuel_energy_kwh_per_kg

# --- Streamlit UI ---
st.title("🔥 Калькулятор подбора пиролизной печи Муссон для производственных помещений")

# Боковая панель с улучшенным оформлением
st.sidebar.header("🏭 ХАРАКТЕРИСТИКИ ПОМЕЩЕНИЯ")
st.sidebar.markdown("---")

col1, col2 = st.sidebar.columns(2)
with col1:
    area_m2 = st.number_input("Площадь помещения (м²)", 20, 500, 100)
with col2:
    height_m = st.number_input("Высота потолков (м)", 2.0, 5.0, 3.5)

material = st.sidebar.selectbox("Материал стен", list(MATERIALS.keys()))
wall_thickness = st.sidebar.slider("Толщина стен (см)", 10, 100, 40) / 100

st.sidebar.markdown("---")
st.sidebar.header("🪟 ОКОННЫЕ И ДВЕРНЫЕ ПРОЁМЫ")
windows_m2 = st.sidebar.number_input("Площадь окон (м²)", 0, 50, 10)
doors_m2 = st.sidebar.number_input("Площадь дверей (м²)", 0, 10, 3)
roof_insulation = st.sidebar.checkbox("Утеплённая крыша", value=False)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ ТЕМПЕРАТУРНЫЙ РЕЖИМ")
col1, col2 = st.sidebar.columns(2)
with col1:
    t_in = st.sidebar.slider("Внутренняя температура (°C)", 10, 25, 18)
with col2:
    t_out = st.sidebar.slider("Наружная температура (°C)", -50, 10, -15)

st.sidebar.markdown("---")
st.sidebar.header("⚡ РЕЖИМ РАБОТЫ")
working_hours = st.sidebar.selectbox("Рабочий день (часов)", [8, 12, 16], index=0)

st.sidebar.markdown("---")
st.sidebar.header("🪵 ПАРАМЕТРЫ ТОПЛИВА")
fuel_type = st.sidebar.selectbox("Тип топлива", list(FUEL_TYPES.keys()))
fill_fraction = st.sidebar.slider("Заполнение топки (%)", 50, 100, 90) / 100
efficiency = st.sidebar.slider("КПД пиролизного котла (%)", 70, 95, 85) / 100
burn_hours = st.sidebar.selectbox("Время горения одной закладки (ч)", [2, 4, 6, 12], index=2)

# --- Расчёт ---
heat_loss_kw = calc_heat_loss(area_m2, height_m, wall_thickness, material, 
                             t_in, t_out, windows_m2, doors_m2, roof_insulation)

volume_m3 = area_m2 * height_m

st.header("📊 РЕЗУЛЬТАТЫ РАСЧЁТА")

# Основные метрики
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Теплопотери здания", f"{heat_loss_kw:.1f} кВт")
with col2:
    st.metric("Рекомендуемая мощность", f"{heat_loss_kw * 1.2:.1f} кВт")
with col3:
    st.metric("Объём помещения", f"{volume_m3:.0f} м³")

# Детализированный расчёт теплопотерь
with st.expander("📋 Детальный расчёт теплопотерь"):
    st.write(f"• Через стены: {heat_loss_kw * 0.6:.1f} кВт (примерно 60%)")
    st.write(f"• Через окна и двери: {heat_loss_kw * 0.25:.1f} кВт (примерно 25%)")
    st.write(f"• Через крышу: {heat_loss_kw * 0.1:.1f} кВт (примерно 10%)")
    st.write(f"• На вентиляцию: {heat_loss_kw * 0.05:.1f} кВт (примерно 5%)")

# Сравнение моделей
st.subheader("🔥 СРАВНЕНИЕ МОДЕЛЕЙ МУССОН")

results = []
for model, params in MUSSON_MODELS.items():
    useful_kwh, p_kw, m_fuel = musson_power(params["volume_l"], fill_fraction, 
                                           fuel_type, efficiency, burn_hours)
    results.append({
        "model": model, 
        "power": p_kw, 
        "energy": useful_kwh, 
        "fuel_per_load": m_fuel,
        "volume_l": params["volume_l"],
        "price": params["price"]
    })

# Таблица результатов
df = pd.DataFrame(results)
df["Соответствие"] = df["power"] >= heat_loss_kw * 1.2
df["Рекомендация"] = df["Соответствие"].map({True: "✅ Подходит", False: "❌ Маломощна"})

# Форматирование таблицы
display_df = df[["model", "power", "fuel_per_load", "Рекомендация"]].copy()
display_df.columns = ["Модель", "Мощность (кВт)", "Топлива за закладку (кг)", "Рекомендация"]
display_df["Мощность (кВт)"] = display_df["Мощность (кВт)"].round(1)
display_df["Топлива за закладку (кг)"] = display_df["Топлива за закладку (кг)"].round(1)

st.dataframe(display_df, use_container_width=True)

# График сравнения (только мощность)
fig, ax = plt.subplots(figsize=(10, 6))

models = [r["model"] for r in results]
powers = [r["power"] for r in results]
colors = ['green' if p >= heat_loss_kw * 1.2 else 'red' for p in powers]

ax.bar(models, powers, color=colors, alpha=0.7)
ax.axhline(y=heat_loss_kw * 1.2, color="blue", linestyle="--", 
           label=f"Требуется: {heat_loss_kw * 1.2:.1f} кВт")
ax.set_ylabel("Мощность, кВт")
ax.set_title("Сравнение мощности моделей")
ax.legend()
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
st.pyplot(fig)

# Рекомендации
st.subheader("💡 РЕКОМЕНДАЦИИ")

suitable_models = [r for r in results if r["power"] >= heat_loss_kw * 1.2]

if suitable_models:
    best_model = min(suitable_models, key=lambda x: x["price"])
    st.success(f"**Рекомендуемая модель: {best_model['model']}**")
    
    st.write("**Характеристики выбранной модели:**")
    st.write(f"• Мощность: {best_model['power']:.1f} кВт (требуется {heat_loss_kw * 1.2:.1f} кВт)")
    st.write(f"• Время горения одной закладки: до {burn_hours} часов")
    st.write(f"• Расход топлива за закладку: {best_model['fuel_per_load']:.1f} кг")
    st.write(f"• Примерная стоимость: {best_model['price']:,} руб.".replace(',', ' '))
    
    # Расчёт расхода топлива за рабочий день
    fuel_energy_kwh_kg = (FUEL_TYPES[fuel_type]["q"] / 3.6) * efficiency
    daily_fuel_kg = calculate_fuel_consumption(heat_loss_kw, working_hours, fuel_energy_kwh_kg)
    
    # Количество закладок в рабочий день
    loads_per_day = max(1, math.ceil(working_hours / burn_hours))
    
    st.write("**Расход топлива за рабочий день:**")
    st.write(f"• Продолжительность рабочего дня: {working_hours} часов")
    st.write(f"• Количество закладок: {loads_per_day}")
    st.write(f"• Расход топлива в день: {daily_fuel_kg:.1f} кг")
    st.write(f"• Расход топлива в месяц (22 рабочих дня): {daily_fuel_kg * 22:.0f} кг")
    st.write(f"• За отопительный сезон (7 месяцев): {daily_fuel_kg * 22 * 7:.0f} кг")
    
    # Стоимость отопления
    fuel_price_per_kg = FUEL_TYPES[fuel_type]["price_per_ton"] / 1000
    daily_cost = daily_fuel_kg * fuel_price_per_kg
    monthly_cost = daily_cost * 22
    seasonal_cost = monthly_cost * 7
    
    st.write("**Экономика отопления:**")
    st.write(f"• Стоимость отопления в день: {daily_cost:.0f} руб.")
    st.write(f"• Стоимость отопления в месяц: {monthly_cost:.0f} руб.")
    st.write(f"• Стоимость за сезон: {seasonal_cost:.0f} руб.")
    
else:
    st.error("❌ Ни одна модель не покрывает теплопотери при текущих настройках")
    st.write("**Рекомендации по улучшению:**")
    st.write("• Увеличьте заполнение топки до 90-100%")
    st.write("• Выберите топливо с большей теплотворной способностью")
    st.write("• Рассмотрите утепление здания")
    st.write("• Увеличьте время горения закладки")

# Дополнительная информация
with st.expander("💡 СОВЕТЫ ПО ЭКСПЛУАТАЦИИ ДЛЯ ПРОИЗВОДСТВЕННЫХ ПОМЕЩЕНИЙ"):
    st.write("""
    1. **Режим работы**: Запускайте печь за 1-2 часа до начала рабочего дня
    2. **Качество топлива**: Используйте сухое топливо (влажность менее 20%)
    3. **Оптимальная загрузка**: Заполняйте топку на 90-100% для максимальной эффективности
    4. **Техобслуживание**: Чистите дымоход и топку раз в 2-3 недели при интенсивной эксплуатации
    5. **Безопасность**: Обеспечьте свободное пространство вокруг печи (не менее 1 метра)
    6. **Вентиляция**: Поддерживайте приточную вентиляцию для эффективного горения
    """)

# Footer
st.markdown("---")
st.markdown("*Расчёт является ориентировочным. Для точного подбора обратитесь к специалистам.*")

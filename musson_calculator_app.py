import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор печи Муссон",
    page_icon="🔥",
    layout="wide"
)

# --- Параметры материалов ---
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

# --- Плотность и теплотворная способность топлива ---
WOOD_TYPES = {
    "хвойные": {"density": 350, "q": 17, "price_per_ton": 2500},
    "берёза": {"density": 450, "q": 18, "price_per_ton": 3500},
    "дуб": {"density": 550, "q": 19.5, "price_per_ton": 5000},
    "плита (ЛДСП/ДСП/фанера/OSB/мебельные отходы)": {"density": 600, "q": 17.5, "price_per_ton": 2000}
}

def calc_heat_loss(area_m2, height_m, wall_thickness_m, material, t_in, t_out, 
                   windows_m2=0, doors_m2=0, roof_insulation=True):
    volume_m3 = area_m2 * height_m
    lambda_wall = MATERIALS[material]
    r_wall = wall_thickness_m / lambda_wall
    wall_area = 2 * height_m * (math.sqrt(area_m2) * 4) - windows_m2 - doors_m2
    q_walls = wall_area * (t_in - t_out) / r_wall
    q_windows = windows_m2 * (t_in - t_out) / 0.4
    q_doors = doors_m2 * (t_in - t_out) / 0.6
    roof_r = 0.2 if not roof_insulation else 1.0
    q_roof = area_m2 * (t_in - t_out) / roof_r
    q_vent = 0.3 * volume_m3 * (t_in - t_out)
    total_w = q_walls + q_windows + q_doors + q_roof + q_vent
    return total_w / 1000  # кВт

def musson_power(volume_l, fill_fraction, wood_type, efficiency, burn_hours):
    vol_m3 = volume_l / 1000
    filled_vol_m3 = vol_m3 * fill_fraction
    m_wood = filled_vol_m3 * WOOD_TYPES[wood_type]["density"]
    q_fuel = m_wood * WOOD_TYPES[wood_type]["q"]
    q_kwh = q_fuel / 3.6
    useful_kwh = q_kwh * efficiency
    p_kw = useful_kwh / burn_hours
    return useful_kwh, p_kw, m_wood

def calculate_fuel_consumption(daily_heat_loss_kwh, wood_energy_kwh_per_kg):
    return daily_heat_loss_kwh / wood_energy_kwh_per_kg

# --- Streamlit UI ---
st.title("🔥 Калькулятор подбора пиролизной печи Муссон")

st.sidebar.header("📐 Параметры здания")
col1, col2 = st.sidebar.columns(2)
with col1:
    area_m2 = st.number_input("Площадь помещения (м²)", 20, 500, 100)
with col2:
    height_m = st.number_input("Высота потолков (м)", 2.0, 5.0, 2.5)

material = st.sidebar.selectbox("Материал стен", list(MATERIALS.keys()))
wall_thickness = st.sidebar.slider("Толщина стен (см)", 10, 100, 40) / 100

st.sidebar.header("🪟 Дополнительные параметры")
windows_m2 = st.sidebar.number_input("Площадь окон (м²)", 0, 50, 5)
doors_m2 = st.sidebar.number_input("Площадь дверей (м²)", 0, 10, 2)
roof_insulation = st.sidebar.checkbox("Утеплённая крыша", value=True)

st.sidebar.header("🌡️ Климатические условия")
col1, col2 = st.sidebar.columns(2)
with col1:
    t_in = st.slider("Внутренняя температура (°C)", 15, 30, 22)
with col2:
    t_out = st.slider("Наружная температура (°C)", -50, 10, -20)

st.sidebar.header("🪵 Параметры топлива")
wood_type = st.sidebar.selectbox("Тип топлива", list(WOOD_TYPES.keys()))
fill_fraction = st.sidebar.slider("Заполнение топки (%)", 50, 100, 85) / 100
efficiency = st.sidebar.slider("КПД пиролизного котла (%)", 70, 95, 88) / 100
burn_hours = st.sidebar.selectbox("Время горения одной закладки (ч)", [6, 8, 10, 12], index=2)

# --- Новая опция стоимости топлива ---
use_price_per_m3 = st.sidebar.checkbox("Использовать стоимость топлива в м³", value=False)
if use_price_per_m3:
    fuel_price_m3 = st.sidebar.number_input("Цена топлива (руб./м³)", 1000, 10000, 2500)
else:
    fuel_price_per_ton = WOOD_TYPES[wood_type]["price_per_ton"]

import streamlit as st
import math

# --- Параметры материалов (теплопроводность, Вт/м·К) ---
MATERIALS = {
    "кирпич": 0.81,
    "газоблок": 0.12,
    "дерево": 0.18,
    "сэндвич-панель": 0.04
}

# --- Модели "Муссон" ---
MUSSON_MODELS = {
    "Муссон 300": {"volume_l": 77},
    "Муссон 600": {"volume_l": 125},
    "Муссон 1000": {"volume_l": 200},
    "Муссон 1500": {"volume_l": 311},
    "Муссон 2000": {"volume_l": 467},
}

# --- Плотность и теплотворная способность древесины ---
WOOD_TYPES = {
    "хвойные": {"density": 350, "q": 17},
    "берёза": {"density": 450, "q": 18},
    "дуб": {"density": 550, "q": 19.5},
}


def calc_heat_loss(area, wall_thickness_m, material, t_in, t_out):
    """Расчёт теплопотерь через стены (очень упрощённо)."""
    lambda_wall = MATERIALS[material]
    r = wall_thickness_m / lambda_wall
    delta_t = t_in - t_out
    q_w = area * delta_t / r  # Вт
    return q_w / 1000  # кВт


def musson_power(volume_l, fill_fraction, wood_type, efficiency, burn_hours):
    vol_m3 = volume_l / 1000
    filled_vol_m3 = vol_m3 * fill_fraction
    m_wood = filled_vol_m3 * WOOD_TYPES[wood_type]["density"]
    q_fuel = m_wood * WOOD_TYPES[wood_type]["q"]  # МДж
    q_kwh = q_fuel / 3.6
    useful_kwh = q_kwh * efficiency
    p_kw = useful_kwh / burn_hours
    return useful_kwh, p_kw


# --- Streamlit UI ---
st.title("Калькулятор подбора печи Муссон")

st.sidebar.header("Параметры здания")
area = st.sidebar.number_input("Площадь помещения (м²)", 20, 1000, 100)
material = st.sidebar.selectbox("Материал стен", list(MATERIALS.keys()))
wall_thickness = st.sidebar.slider("Толщина стен (см)", 10, 100, 40) / 100

st.sidebar.header("Климат")
t_in = st.sidebar.slider("Внутренняя температура (°C)", 15, 30, 22)
t_out = st.sidebar.slider("Наружная температура (°C)", -50, 10, -20)

st.sidebar.header("Топливо")
wood_type = st.sidebar.selectbox("Порода древесины", list(WOOD_TYPES.keys()))
fill_fraction = st.sidebar.slider("Заполнение топки (%)", 50, 100, 70) / 100
efficiency = st.sidebar.slider("КПД пиролизного котла (%)", 70, 95, 85) / 100
burn_hours = st.sidebar.selectbox("Время горения одной закладки (ч)", [2, 6, 12])

# --- Расчёт ---
heat_loss_kw = calc_heat_loss(area, wall_thickness, material, t_in, t_out)

st.subheader("Требуемая мощность")
st.write(f"Теплопотери здания: **{heat_loss_kw:.1f} кВт** (с запасом ≈ {heat_loss_kw*1.2:.1f} кВт)")

results = []
for model, params in MUSSON_MODELS.items():
    useful_kwh, p_kw = musson_power(params["volume_l"], fill_fraction, wood_type, efficiency, burn_hours)
    results.append((model, p_kw, useful_kwh))

st.subheader("Сравнение моделей Муссон")
for model, p_kw, useful_kwh in results:
    st.write(f"{model}: мощность ≈ **{p_kw:.1f} кВт**, энергия = {useful_kwh:.0f} кВт·ч")

# --- Рекомендация ---
best = [m for m, p, _ in results if p >= heat_loss_kw*1.2]
if best:    st.success(f"Рекомендуется: {best[0]} (достаточно мощности при выбранных условиях)")
else:    st.error("Ни одна модель не покрывает теплопотери при текущих настройках. Увеличьте заполнение или выберите более плотную древесину.")

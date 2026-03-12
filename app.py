import streamlit as st
import pandas as pd
import math

# --- HELPER FUNCTIONS ---
def calc_time(mean, sd, mode):
    """Calculates time based on Mean or 95th Percentile."""
    if mode == "95th Percentile":
        return round(mean + (1.645 * sd), 1)
    return round(mean, 1)

def calc_speed(mean, sd, mode, min_recorded_speed):
    """Calculates speed. 95th percentile time = 5th percentile speed (slower)."""
    if mode == "95th Percentile":
        stat_speed = mean - (1.645 * sd)
        return round(max(stat_speed, min_recorded_speed), 2)
    return round(mean, 2)

@st.cache_data
def convert_df(df):
    """Caches the DataFrame conversion to prevent re-running on every click."""
    return df.to_csv(index=False).encode('utf-8')

# --- APP HEADER & GLOBAL SETTINGS ---
st.title("AFAC FBIM Calculator")
st.markdown("Calculates the complete Fire Brigade Intervention Model timeline.")

st.sidebar.header("Global Settings")
stat_mode = st.sidebar.radio("Statistical Mode", ["Mean", "95th Percentile"])
st.sidebar.markdown("*(Note: Statistical mode applies to Table M onwards. Pre-arrival uses deterministic values.)*")

# ==========================================
# MODULE 1: PRE-ARRIVAL
# ==========================================
st.header("Module 1: Pre-Arrival")

# 0. Fire Detection System
st.subheader("0. Fire Detection System")
detection_type = st.radio("Detection Type", ["Automatic", "Manual"])
detection_time = st.number_input("Fire detection time (seconds)", min_value=0, value=0)

# 1. System Depressurisation (Table A)
st.subheader("1. System Depressurisation & Alarm Activation (Table A)")
table_a_data = {
    "N/A (No suppression system linked to alarm)": 0,
    "AS 2118.1 (180-360s)": 360, 
    "Combined OHI < 1000m2": 10,
    "Combined OHI 1000m2 - 2000m2": 20,
    "Combined OHI > 2000m2": 50
}
sys_type = st.selectbox("Select System Type / Floor Area", list(table_a_data.keys()))
time_a = table_a_data[sys_type]

# 2. Alarms, Verification & Notification (Table B)
st.subheader("2. Alarms, Verification & Notification (Table B)")
notification_type = st.radio("Notification Method", ["Automatic alarm signalling equipment (ASE)", "Manual call to Fire Brigade"])

col1, col2 = st.columns(2)
with col1:
    verification_time = st.number_input("Time for verification (seconds)", min_value=0, value=0)
with col2:
    notification_delay = st.number_input("Time Delay for fire brigade notification (seconds)", min_value=0, value=0)

time_b = verification_time + notification_delay

# 3. Receipt of Information (Table C)
st.subheader("3. Receipt of Information (Table C)")
time_c = 0
receipt_selection_text = "Bypassed (ASE directly notifies fire brigade)"

if notification_type == "Manual call to Fire Brigade":
    table_c_data = {
        "Receive and take down verbal information": 60,
        "Alternative option": 0 
    }
    receipt_type = st.selectbox("Select Information Receipt Method", list(table_c_data.keys()))
    time_c = table_c_data[receipt_type]
    receipt_selection_text = receipt_type
else:
    st.info(receipt_selection_text)

# 4. Dispatch Times (Table D)
st.subheader("4. Dispatch Times (Table D)")
table_d_data = {
    "Fully electronic Computer Aided Dispatch (CAD) system": 0,
    "Part manual Computer Aided Dispatch (CAD) system": 15,
    "Phone or radio": 30
}
dispatch_type = st.selectbox("Select Dispatch Method", list(table_d_data.keys()))
time_d = table_d_data[dispatch_type]

# 5. Firefighter Response (Table E)
st.subheader("5. Firefighter Response (Table E)")
table_e_data = {
    "Volunteer - Travel to station, dress, assemble, assimilate info and leave": 480,
    "Career - Dress, assimilate information and depart": 90,
    "Make up and become mobile": 60
}
response_type = st.selectbox("Select Firefighter Turnout Activity", list(table_e_data.keys()))
time_e = table_e_data[response_type]

total_pre_arrival = detection_time + time_a + time_b + time_c + time_d + time_e
summary_data_m1 = [
    {"Phase": "0. Fire Detection", "Selection": detection_type, "Time (s)": detection_time},
    {"Phase": "1. System Depressurisation", "Selection": sys_type, "Time (s)": time_a},
    {"Phase": "2. Alarms & Notification", "Selection": f"{notification_type} (incl. delays)", "Time (s)": time_b},
    {"Phase": "3. Receipt of Info", "Selection": receipt_selection_text, "Time (s)": time_c},
    {"Phase": "4. Dispatch", "Selection": dispatch_type, "Time (s)": time_d},
    {"Phase": "5. Firefighter Response", "Selection": response_type, "Time (s)": time_e}
]

# ==========================================
# MODULE 2: TRAVEL & SITE ENTRY
# ==========================================
st.markdown("---")
st.header("Module 2: Travel & Site Entry")

# 6. Appliance Travel Time (Table F)
st.subheader("6. Appliance Travel Time (Table F)")
col3, col4 = st.columns(2)
with col3:
    travel_to_site_mins = st.number_input("Travel time to site (minutes)", min_value=0.0, value=0.0, step=0.1)
    travel_to_site_sec = int(travel_to_site_mins * 60)
with col4:
    travel_through_site_m = st.number_input("Travel distance through site (meters)", min_value=0, value=0)
    travel_through_site_sec = int(travel_through_site_m / 2.22) # 8km/h

time_f = travel_to_site_sec + travel_through_site_sec

# 7. Building Entry & Security (Table G)
st.subheader("7. Delay for Building Entry (Table G)")
time_g = st.number_input("Time for any security procedure (seconds)", min_value=0, value=0)

# 8. Communicate with Warden (Table H)
st.subheader("8. Communicate with Warden (Table H)")
table_h_data = {
    "N/A (No warden)": 0,
    "< 1000 m2": 30,
    "> 1000 m2, < 5000 m2": 45,
    "> 5000 m2": 90
}
warden_type = st.selectbox("Building Floor Area (for Warden Comm.)", list(table_h_data.keys()))
time_h = table_h_data[warden_type]

# 9. Gain / Force Entry (Tables I & J)
st.subheader("9. Gain or Force Entry (Tables I & J)")
entry_method = st.radio("Entry Method", ["Open/Unobstructed (0s)", "Gain Entry with Keys (Table J)", "Force Entry (Table I)"])
time_i_j = 0
entry_selection_text = "Open/Unobstructed"

if entry_method == "Force Entry (Table I)":
    table_i_data = {
        "Inward opening, side hung door": 30, "Outward opening, side hung fire door": 180,
        "Outward opening, side hung solid core door": 90, "Inward opening, hollow core door": 15,
        "Outward opening, hollow core door": 45, "Glass door": 15,
        "Roller security/steel door": 220, "Chained gate": 45
    }
    entry_door = st.selectbox("Select door/gate type (Forced)", list(table_i_data.keys()))
    time_i_j = table_i_data[entry_door]
    entry_selection_text = f"Forced: {entry_door}"
elif entry_method == "Gain Entry with Keys (Table J)":
    table_j_data = {"Side hung door": 10, "Roller security door": 30, "Gate": 30}
    entry_door = st.selectbox("Select door/gate type (Keys)", list(table_j_data.keys()))
    time_i_j = table_j_data[entry_door]
    entry_selection_text = f"Keys: {entry_door}"

# 10. Wayfinding (Table K)
st.subheader("10. Resolve Wayfinding (Table K)")
table_k_data = {
    "Multi-level, numerous enclosures & passages": 30, "Multi-level, open plan": 10,
    "Single storey, numerous enclosures & passages, floor area > 5000 m2": 45,
    "Single storey, open plan": 10,
    "Single storey, numerous enclosures & passages, floor area < 5000 m2": 30
}
wayfinding_type = st.selectbox("Select Complexity/Building Size", list(table_k_data.keys()))
time_k = table_k_data[wayfinding_type]

# 11. Information Gathering (Table L)
st.subheader("11. Information Gathering FDCIE (Table L)")
table_l_data = {"N/A (No FDCIE)": 0, "< 5000 m2": 30, "> 5000 m2, < 10000 m2": 60, "> 10000 m2": 90}
fdcie_type = st.selectbox("Building Floor Area (for FDCIE)", list(table_l_data.keys()))
time_l = table_l_data[fdcie_type]

total_travel_entry = time_f + time_g + time_h + time_i_j + time_k + time_l
summary_data_m2 = [
    {"Phase": "6. Appliance Travel", "Selection": f"{travel_to_site_sec}s + {travel_through_site_sec}s", "Time (s)": time_f},
    {"Phase": "7. Security Delay", "Selection": "Designer specified", "Time (s)": time_g},
    {"Phase": "8. Warden Communication", "Selection": warden_type, "Time (s)": time_h},
    {"Phase": "9. Building Entry", "Selection": entry_selection_text, "Time (s)": time_i_j},
    {"Phase": "10. Wayfinding", "Selection": wayfinding_type, "Time (s)": time_k},
    {"Phase": "11. FDCIE Info Gathering", "Selection": fdcie_type, "Time (s)": time_l}
]

# ==========================================
# MODULE 3: SETUP & FIREFIGHTING OPERATIONS
# ==========================================
st.markdown("---")
st.header("Module 3: Setup & Operations")

# 12. Dismount and Don BA (Table M)
st.subheader("12. Dismount Appliance and Don BA (Table M)")
time_m = calc_time(88.1, 34.9, stat_mode)
st.write(f"**Time ({stat_mode}):** {time_m} s")

# 13. Remove Tools from Appliance (Table P)
st.subheader("13. Remove Necessary Tools (Table P)")
table_p_data = {
    "N/A (No tools)": {"mean": 0, "sd": 0},
    "Hydrant equipment / forced entry tools (P1)": {"mean": 32.5, "sd": 18.1},
    "High rise pack or similar (P2)": {"mean": 13.5, "sd": 6.0}
}
tool_type = st.selectbox("Select Tools Required", list(table_p_data.keys()))
time_p = calc_time(table_p_data[tool_type]["mean"], table_p_data[tool_type]["sd"], stat_mode)

# 14. Horizontal Travel (Table Q)
st.subheader("14. Firefighter Horizontal Travel (Table Q)")
table_q_data = {
    "N/A (No horizontal travel)": {"mean": 0, "sd": 0, "min": 0.1},
    "Turnout uniform (Q1)": {"mean": 2.3, "sd": 1.4, "min": 0.32},
    "Turnout uniform with equipment (Q2)": {"mean": 1.9, "sd": 1.3, "min": 0.13},
    "Turnout uniform in BA +/- equipment (Q3)": {"mean": 1.4, "sd": 0.6, "min": 0.28},
    "Full hazardous incident suit in BA (Q4)": {"mean": 0.8, "sd": 0.5, "min": 0.13}
}
horiz_travel_type = st.selectbox("Select Horizontal Travel Conditions", list(table_q_data.keys()))
horiz_distance = st.number_input("Horizontal Distance (meters)", min_value=0.0, value=0.0)

time_q = 0
if horiz_distance > 0:
    q_speed = calc_speed(table_q_data[horiz_travel_type]["mean"], table_q_data[horiz_travel_type]["sd"], stat_mode, table_q_data[horiz_travel_type]["min"])
    time_q = round(horiz_distance / q_speed, 1)

# 15. Stair Travel (Table T)
st.subheader("15. Firefighter Stair Travel (Table T)")
table_t_data = {
    "N/A (No stairs)": {"mean": 0, "sd": 0, "min": 0.1},
    "Ascend in BA with equipment (T1)": {"mean": 0.9, "sd": 0.4, "min": 0.25},
    "Ascend with high pressure hose (T2)": {"mean": 0.5, "sd": 0.3, "min": 0.09},
    "Ascend with 65mm hose (T3)": {"mean": 0.7, "sd": 0.3, "min": 0.40},
    "Ascend with 38mm hose (T4)": {"mean": 0.8, "sd": 0.3, "min": 0.15},
    "Descend in BA (T5)": {"mean": 1.0, "sd": 0.5, "min": 0.20}
}
stair_travel_type = st.selectbox("Select Stair Travel Conditions", list(table_t_data.keys()))
stair_flights = st.number_input("Number of Stair Flights", min_value=0, value=0)
steps_per_flight = st.number_input("Average Steps per Flight", min_value=0, value=15)

time_t = 0
if stair_flights > 0:
    total_steps = stair_flights * steps_per_flight
    t_speed = calc_speed(table_t_data[stair_travel_type]["mean"], table_t_data[stair_travel_type]["sd"], stat_mode, table_t_data[stair_travel_type]["min"])
    time_t = round(total_steps / t_speed, 1)
    if stair_flights > 6:
        rest_speed = calc_speed(1.86, 0.82, stat_mode, 0.50)
        rest_steps = (stair_flights - 6) * steps_per_flight
        time_t += round(rest_steps / rest_speed, 1)

# 16. Hose Laying & Charging (Table V)
st.subheader("16. Lay, Connect and Charge Hose (Table V)")
table_v_data = {
    "V1.1: Hydrant to appliance (90mm)": {"mean": 144.7, "sd": 90.2},
    "V1.2: Hydrant to appliance (65mm)": {"mean": 60.4, "sd": 30.2},
    "V2.1: Appliance to branch (65mm)": {"mean": 39.4, "sd": 17.4},
    "V2.2: Appliance to branch (38mm)": {"mean": 33.3, "sd": 15.4},
    "V3: Appliance to booster (65mm)": {"mean": 45.3, "sd": 20.3},
    "V4.1: Charge delivery hose (65mm)": {"mean": 17.1, "sd": 13.2},
    "V4.2: Charge delivery hose (38mm)": {"mean": 18.4, "sd": 10.2},
    "V5.1: Boosted hydrant & charge (65mm)": {"mean": 59.6, "sd": 37.9},
    "V5.2: Boosted hydrant & charge (38mm)": {"mean": 40.9, "sd": 17.8}
}
selected_hoses = st.multiselect("Select applicable hose operations", list(table_v_data.keys()))
hose_lengths = st.number_input("Number of 30m hose lengths required", min_value=0.0, value=1.0, step=0.5)

time_v = 0
if selected_hoses and hose_lengths > 0:
    for hose in selected_hoses:
        base_time = calc_time(table_v_data[hose]["mean"], table_v_data[hose]["sd"], stat_mode)
        time_v += base_time * hose_lengths
    time_v = round(time_v, 1)

# 17. Safety & Hazmat Procedures (Tables N & O)
st.subheader("17. Safety Equipment & Procedures (Tables N & O)")
table_n_o_data = {
    "Don BA and hazmat suit (N)": {"mean": 584.4, "sd": 298.0},
    "Flush hydrant (O1)": {"mean": 32.8, "sd": 20.6},
    "Obtain hazmat info from comms (O2)": {"mean": 701.0, "sd": 409.5},
    "Decontamination unit set-up (O3)": {"mean": 764.9, "sd": 186.1},
    "Assemble misc. safety equipment (O4)": {"mean": 290.6, "sd": 132.1}
}
selected_safety = st.multiselect("Select required safety procedures", list(table_n_o_data.keys()))
time_n_o = round(sum(calc_time(table_n_o_data[p]["mean"], table_n_o_data[p]["sd"], stat_mode) for p in selected_safety), 1)

# 18. External & Static Water (Tables W & X)
st.subheader("18. External & Static Water (Tables W & X)")
table_w_data = {"N/A (No external search)": 0, "Street hydrant < 30m": 30, "Street hydrant > 30m < 60m": 90, "Street hydrant > 60m": 180}
water_search = st.selectbox("External Search for Street Main (Table W)", list(table_w_data.keys()))
time_w = table_w_data[water_search]

static_water_ops = {
    "Remove suction hose & connect (X2, per 3m)": {"mean": 18.6, "sd": 7.5},
    "Prime suction hose from tank (X3)": {"mean": 23.5, "sd": 15.3},
    "Secure suction for open water drop (X4)": {"mean": 97.7, "sd": 54.4},
    "Lower suction to open water & prime (X5)": {"mean": 60.7, "sd": 37.9}
}
time_x = 0
appliance_pos_dist = st.number_input("Position Appliance Distance (m) (X1)", min_value=0.0, value=0.0)
if appliance_pos_dist > 0:
    time_x += round(appliance_pos_dist / calc_speed(1.09, 0.48, stat_mode, 0.16), 1)

selected_static = st.multiselect("Select static water operations", list(static_water_ops.keys()))
if "Remove suction hose & connect (X2, per 3m)" in selected_static:
    suction_lengths = st.number_input("Number of 3m suction hose lengths", min_value=1, value=1)
    base_x2 = calc_time(static_water_ops["Remove suction hose & connect (X2, per 3m)"]["mean"], static_water_ops["Remove suction hose & connect (X2, per 3m)"]["sd"], stat_mode)
    time_x += (base_x2 * suction_lengths)
    selected_static.remove("Remove suction hose & connect (X2, per 3m)")

for op in selected_static:
    time_x += calc_time(static_water_ops[op]["mean"], static_water_ops[op]["sd"], stat_mode)
time_x = round(time_x, 1)

# 19. Search and Rescue (Table Y)
st.subheader("19. Search and Rescue (Table Y)")
time_y = 0
sec_search_area = st.number_input("Secondary Search Area (m2) (Y1)", min_value=0.0, value=0.0)
if sec_search_area > 0:
    time_y += round(sec_search_area / calc_speed(0.16, 0.05, stat_mode, 0.07), 1)

rescue_dist = st.number_input("Remove/Rescue Person Distance (m) (Y2)", min_value=0.0, value=0.0)
if rescue_dist > 0:
    time_y += round(rescue_dist / calc_speed(0.05, 0.03, stat_mode, 0.01), 1)

# 20. Aerial Appliances (Table Z)
st.subheader("20. Aerial Appliances (Table Z)")
time_z = 0
aerial_pos_dist = st.number_input("Position Aerial Appliance Dist (m) (Z1)", min_value=0.0, value=0.0)
if aerial_pos_dist > 0:
    time_z += round(aerial_pos_dist / calc_speed(0.54, 0.32, stat_mode, 0.02), 1)

aerial_setup_opts = {
    "N/A": {"mean": 0, "sd": 0}, "Teleboom (Z2.1)": {"mean": 56.6, "sd": 17.6},
    "TT Ladder (Z2.2)": {"mean": 292.0, "sd": 222.1}, "Platform (Z2.3)": {"mean": 145.9, "sd": 59.4}
}
aerial_setup = st.selectbox("Appliance Setup Prep", list(aerial_setup_opts.keys()))
time_z += calc_time(aerial_setup_opts[aerial_setup]["mean"], aerial_setup_opts[aerial_setup]["sd"], stat_mode)

if st.checkbox("Conduct Aerial Safety Procedures (Z3)"):
    time_z += calc_time(62.9, 33.7, stat_mode)

aerial_elevate_opts = {
    "N/A": {"mean": 0, "sd": 0, "min": 0.1}, "Teleboom 180 deg (Z4.1)": {"mean": 0.11, "sd": 0.04, "min": 0.02},
    "TT Ladder 180 deg (Z4.2)": {"mean": 0.18, "sd": 0.09, "min": 0.09}, "Platform 180 deg (Z4.3)": {"mean": 0.12, "sd": 0.05, "min": 0.04}
}
aerial_elev = st.selectbox("Elevate & Manoeuvre", list(aerial_elevate_opts.keys()))
elev_dist = st.number_input("Elevation Distance (m)", min_value=0.0, value=0.0)
if elev_dist > 0 and aerial_elev != "N/A":
    time_z += round(elev_dist / calc_speed(aerial_elevate_opts[aerial_elev]["mean"], aerial_elevate_opts[aerial_elev]["sd"], stat_mode, aerial_elevate_opts[aerial_elev]["min"]), 1)

if st.checkbox("Charge Monitor (Z5)"):
    time_z += calc_time(31.5, 25.0, stat_mode)

time_z = round(time_z, 1)

total_setup_ops = time_m + time_p + time_q + time_t + time_v + time_n_o + time_w + time_x + time_y + time_z

summary_data_m3 = [
    {"Phase": "12. Dismount & Don BA", "Selection": "Standard", "Time (s)": time_m},
    {"Phase": "13. Remove Tools", "Selection": tool_type, "Time (s)": time_p},
    {"Phase": "14. Horizontal Travel", "Selection": f"{horiz_distance}m", "Time (s)": time_q},
    {"Phase": "15. Stair Travel", "Selection": f"{stair_flights} flights", "Time (s)": time_t},
    {"Phase": "16. Hose Operations", "Selection": f"{len(selected_hoses)} ops", "Time (s)": time_v},
    {"Phase": "17. Safety & Hazmat", "Selection": f"{len(selected_safety)} ops", "Time (s)": time_n_o},
    {"Phase": "18. External/Static Water", "Selection": water_search, "Time (s)": time_w + time_x},
    {"Phase": "19. Search and Rescue", "Selection": f"{sec_search_area}m2 / {rescue_dist}m", "Time (s)": time_y},
    {"Phase": "20. Aerial Appliances", "Selection": aerial_setup, "Time (s)": time_z}
]

# ==========================================
# GRAND TOTALS & EXPORT
# ==========================================
st.markdown("---")
st.header("Total Brigade Intervention Time")
grand_total = total_pre_arrival + total_travel_entry + total_setup_ops
st.success(f"### **{round(grand_total, 1)} seconds** |  **{round(grand_total/60, 2)} minutes**")

st.markdown("---")
st.header("Export Results")

# Combine all modules into a single DataFrame for export
df_m1 = pd.DataFrame(summary_data_m1)
df_m1.insert(0, "Module", "1. Pre-Arrival")

df_m2 = pd.DataFrame(summary_data_m2)
df_m2.insert(0, "Module", "2. Travel & Entry")

df_m3 = pd.DataFrame(summary_data_m3)
df_m3.insert(0, "Module", "3. Setup & Ops")

final_summary_df = pd.concat([df_m1, df_m2, df_m3], ignore_index=True)

# Add a grand total row
total_row = pd.DataFrame([{
    "Module": "TOTAL", 
    "Phase": "", 
    "Selection": f"{round(grand_total/60, 2)} minutes", 
    "Time (s)": round(grand_total, 1)
}])
final_summary_df = pd.concat([final_summary_df, total_row], ignore_index=True)

st.dataframe(final_summary_df, use_container_width=True)

csv = convert_df(final_summary_df)

st.download_button(
    label="Download Calculation Summary (CSV)",
    data=csv,
    file_name='fbim_calculation_summary.csv',
    mime='text/csv',
)

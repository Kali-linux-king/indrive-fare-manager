"""
InDrive Smart Fare & Expense Manager
====================================
A single-file Streamlit web application designed for bike riders on InDrive to:
1. Dynamically configure fuel, mileage, maintenance, and emergency fund targets.
2. Estimate minimum acceptable fares before accepting a ride based on remaining daily goals.
3. Log completed rides during an active shift with persistent session state.
4. Track daily ride count, net earnings, shift efficiency (PKR/KM), and monthly emergency fund progress.

Run locally with:
    pip install streamlit pandas
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="InDrive Smart Fare & Expense Manager",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .verdict-accept {
        background-color: #ecfdf5;
        border: 1px solid #10b981;
        color: #065f46;
        padding: 16px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 16px;
    }
    .verdict-reject {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        color: #991b1b;
        padding: 16px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.15rem;
        margin-bottom: 16px;
    }
    .breakdown-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 18px;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. INITIALIZE SESSION STATE
# -----------------------------------------------------------------------------
if "rides_log" not in st.session_state:
    st.session_state.rides_log = []

if "total_gross_earnings" not in st.session_state:
    st.session_state.total_gross_earnings = 0.0

if "total_net_profit" not in st.session_state:
    st.session_state.total_net_profit = 0.0

if "total_rides_completed" not in st.session_state:
    st.session_state.total_rides_completed = 0

if "total_distance_km" not in st.session_state:
    st.session_state.total_distance_km = 0.0

if "total_fuel_liters" not in st.session_state:
    st.session_state.total_fuel_liters = 0.0

if "total_fuel_cost" not in st.session_state:
    st.session_state.total_fuel_cost = 0.0

if "total_maintenance_saved" not in st.session_state:
    st.session_state.total_maintenance_saved = 0.0

if "total_emergency_contributed" not in st.session_state:
    st.session_state.total_emergency_contributed = 0.0

if "total_food_expense" not in st.session_state:
    st.session_state.total_food_expense = 0.0

if "prior_emergency_balance" not in st.session_state:
    st.session_state.prior_emergency_balance = 0.0


# -----------------------------------------------------------------------------
# 3. SIDEBAR CONFIGURATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Rider Configuration")
    st.caption("Set your bike metrics and financial targets")

    st.subheader("Fuel & Bike Specs")
    petrol_price = st.number_input(
        "Current Petrol Price per Liter (PKR)",
        min_value=1.0,
        max_value=1000.0,
        value=280.0,
        step=5.0,
        help="Current petrol pump rate per liter in PKR.",
    )
    bike_mileage = st.number_input(
        "Bike Mileage (KM / Liter)",
        min_value=10.0,
        max_value=120.0,
        value=50.0,
        step=1.0,
        help="Average fuel economy of your bike in city traffic.",
    )
    maintenance_rate = st.number_input(
        "Maintenance Reserve Rate per KM (PKR)",
        min_value=0.0,
        max_value=50.0,
        value=3.0,
        step=0.5,
        help="Reserve set aside per KM for engine oil, tuning, tires, and brake pads.",
    )

    st.divider()
    st.subheader("Daily Shift Goals")
    daily_ride_goal = st.number_input(
        "Daily Ride Count Goal",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
        help="Target number of rides you plan to complete today.",
    )
    daily_net_goal = st.number_input(
        "Daily Net Earnings Goal (PKR)",
        min_value=100.0,
        max_value=25000.0,
        value=1500.0,
        step=100.0,
        help="Target take-home profit after all expenses are deducted.",
    )

    st.divider()
    st.subheader("Emergency Fund Target")
    monthly_emergency_target = st.number_input(
        "Monthly Emergency Fund Target (PKR)",
        min_value=0.0,
        max_value=200000.0,
        value=10000.0,
        step=500.0,
        help="Target monthly reserve for unexpected repairs or medical/personal emergencies.",
    )
    working_days_per_month = st.number_input(
        "Estimated Working Days / Month",
        min_value=1,
        max_value=31,
        value=25,
        step=1,
        help="Number of days you ride per month to split the monthly emergency target.",
    )

    # Dynamic Emergency Fund Breakdown
    daily_emergency_target = monthly_emergency_target / max(1, working_days_per_month)
    per_ride_emergency_share = daily_emergency_target / max(1, daily_ride_goal)
    fuel_cost_per_km = petrol_price / max(1.0, bike_mileage)

    st.info(
        f"**Dynamic Breakdown**\n"
        f"- Fuel Cost: **Rs. {fuel_cost_per_km:,.2f} / KM**\n"
        f"- Daily Emergency Goal: **Rs. {daily_emergency_target:,.0f} / day**\n"
        f"- Emergency Share: **Rs. {per_ride_emergency_share:,.1f} / ride**"
    )

    st.divider()
    if st.button("🔄 Reset Current Shift Data", use_container_width=True):
        st.session_state.rides_log = []
        st.session_state.total_gross_earnings = 0.0
        st.session_state.total_net_profit = 0.0
        st.session_state.total_rides_completed = 0
        st.session_state.total_distance_km = 0.0
        st.session_state.total_fuel_liters = 0.0
        st.session_state.total_fuel_cost = 0.0
        st.session_state.total_maintenance_saved = 0.0
        st.session_state.total_emergency_contributed = 0.0
        st.session_state.total_food_expense = 0.0
        st.rerun()


# -----------------------------------------------------------------------------
# 4. MAIN HEADER & TABS
# -----------------------------------------------------------------------------
st.title("🏍️ InDrive Smart Fare & Expense Manager")
st.caption(
    "Real-time fare evaluation, automated per-KM expense deduction, and daily net profit goal tracking."
)

tab1, tab2, tab3 = st.tabs(
    [
        "🧮 1. Ride Fare Estimator",
        "📝 2. Active Shift & Logging",
        "📊 3. Dashboard & Goals Progress",
    ]
)

# =============================================================================
# TAB 1: RIDE FARE ESTIMATOR (Before accepting a ride)
# =============================================================================
with tab1:
    st.subheader("Evaluate Ride Request Before Accepting")
    st.write(
        "Enter the trip distance and the fare offered by the passenger on InDrive to see if it meets your expenses and remaining daily profit goal."
    )

    col_input, col_result = st.columns([1, 1.25], gap="large")

    with col_input:
        est_distance_km = st.number_input(
            "Trip Distance (KM)",
            min_value=0.5,
            max_value=200.0,
            value=8.0,
            step=0.5,
            key="est_distance",
        )
        offered_fare_pkr = st.number_input(
            "Estimated InDrive Offered Fare (PKR)",
            min_value=0.0,
            max_value=20000.0,
            value=260.0,
            step=10.0,
            key="est_offered_fare",
        )

        # Core Estimator Calculations
        est_fuel_liters = est_distance_km / max(1.0, bike_mileage)
        est_fuel_cost = est_fuel_liters * petrol_price
        est_maintenance_cost = est_distance_km * maintenance_rate
        est_emergency_share = per_ride_emergency_share
        est_total_expenses = est_fuel_cost + est_maintenance_cost + est_emergency_share

        # Remaining Profit Goal & Remaining Rides Goal based on today's shift progress
        remaining_profit_goal = max(
            0.0, daily_net_goal - st.session_state.total_net_profit
        )
        remaining_rides_goal = max(
            1, daily_ride_goal - st.session_state.total_rides_completed
        )
        target_profit_this_ride = remaining_profit_goal / remaining_rides_goal

        recommended_min_fare = est_total_expenses + target_profit_this_ride
        projected_net_profit = offered_fare_pkr - est_total_expenses
        fare_difference = offered_fare_pkr - recommended_min_fare

    with col_result:
        if offered_fare_pkr >= recommended_min_fare:
            st.markdown(
                '<div class="verdict-accept">🟢 GOOD RIDE - ACCEPT</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="verdict-reject">🔴 LOW FARE - REJECT OR NEGOTIATE</div>',
                unsafe_allow_html=True,
            )

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Recommended Min Fare",
            f"Rs. {recommended_min_fare:,.0f}",
            delta=f"{fare_difference:+,.0f} PKR vs Offered",
        )
        m2.metric(
            "Total Ride Expenses",
            f"Rs. {est_total_expenses:,.0f}",
            f"{est_fuel_liters:.2f} L Petrol",
            delta_color="off",
        )
        m3.metric(
            "Projected Net Profit",
            f"Rs. {projected_net_profit:,.0f}",
            f"Target: Rs. {target_profit_this_ride:,.0f}/ride",
            delta_color="normal" if projected_net_profit >= target_profit_this_ride else "inverse",
        )

        st.markdown('<div class="breakdown-card">', unsafe_allow_html=True)
        st.markdown("#### Cost & Goal Breakdown for This Ride")
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.write(f"- **Fuel Cost ({est_distance_km:.1f} KM):** Rs. {est_fuel_cost:,.1f}")
            st.write(f"- **Maintenance Reserve:** Rs. {est_maintenance_cost:,.1f}")
            st.write(f"- **Emergency Fund Share:** Rs. {est_emergency_share:,.1f}")
            st.write(f"- **Total Ride Expenses:** **Rs. {est_total_expenses:,.1f}**")
        with b_col2:
            st.write(f"- **Remaining Profit Goal:** Rs. {remaining_profit_goal:,.0f}")
            st.write(f"- **Remaining Rides Today:** {remaining_rides_goal} ride(s)")
            st.write(f"- **Required Profit / Ride:** Rs. {target_profit_this_ride:,.1f}")
            st.write(f"- **Min Acceptable Fare:** **Rs. {recommended_min_fare:,.0f}**")
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# TAB 2: ACTIVE SHIFT & LOGGING (After completing a ride)
# =============================================================================
with tab2:
    st.subheader("Log a Completed Ride")
    st.write(
        "Record your completed trip details below. Expenses are automatically deducted and added to your daily reserves."
    )

    with st.form("log_ride_form", clear_on_submit=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            actual_fare = st.number_input(
                "Actual Fare Collected (PKR)",
                min_value=0.0,
                max_value=25000.0,
                value=280.0,
                step=10.0,
            )
        with f_col2:
            tip_received = st.number_input(
                "Tip Received (PKR)",
                min_value=0.0,
                max_value=5000.0,
                value=0.0,
                step=10.0,
            )
        with f_col3:
            trip_distance = st.number_input(
                "Trip Distance (KM)",
                min_value=0.5,
                max_value=200.0,
                value=8.0,
                step=0.5,
            )
        with f_col4:
            food_expense = st.number_input(
                "Food / Personal Expense (PKR, Optional)",
                min_value=0.0,
                max_value=5000.0,
                value=0.0,
                step=10.0,
            )

        submitted = st.form_submit_button("Log Completed Ride", type="primary", use_container_width=True)

        if submitted:
            ride_gross = actual_fare + tip_received
            ride_fuel_liters = trip_distance / max(1.0, bike_mileage)
            ride_fuel_cost = ride_fuel_liters * petrol_price
            ride_maintenance = trip_distance * maintenance_rate
            ride_emergency = per_ride_emergency_share
            ride_total_expenses = (
                ride_fuel_cost + ride_maintenance + ride_emergency + food_expense
            )
            ride_net_profit = ride_gross - ride_total_expenses

            # Update Session State Totals
            st.session_state.total_rides_completed += 1
            st.session_state.total_gross_earnings += ride_gross
            st.session_state.total_net_profit += ride_net_profit
            st.session_state.total_distance_km += trip_distance
            st.session_state.total_fuel_liters += ride_fuel_liters
            st.session_state.total_fuel_cost += ride_fuel_cost
            st.session_state.total_maintenance_saved += ride_maintenance
            st.session_state.total_emergency_contributed += ride_emergency
            st.session_state.total_food_expense += food_expense

            st.session_state.rides_log.append(
                {
                    "Ride #": st.session_state.total_rides_completed,
                    "Time": datetime.now().strftime("%I:%M %p"),
                    "Distance (KM)": round(trip_distance, 1),
                    "Fare (PKR)": round(actual_fare, 0),
                    "Tip (PKR)": round(tip_received, 0),
                    "Gross (PKR)": round(ride_gross, 0),
                    "Fuel (PKR)": round(ride_fuel_cost, 1),
                    "Maint. (PKR)": round(ride_maintenance, 1),
                    "Emergency (PKR)": round(ride_emergency, 1),
                    "Food (PKR)": round(food_expense, 0),
                    "Net Profit (PKR)": round(ride_net_profit, 1),
                }
            )
            st.success(
                f"Ride #{st.session_state.total_rides_completed} logged! Net Profit: Rs. {ride_net_profit:,.0f}"
            )

    st.divider()
    st.subheader("Active Shift Cumulative Totals")

    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("Total Gross Earnings", f"Rs. {st.session_state.total_gross_earnings:,.0f}")
    s2.metric("Total Net Profit", f"Rs. {st.session_state.total_net_profit:,.0f}")
    s3.metric(
        "Total Rides Completed",
        f"{st.session_state.total_rides_completed} / {daily_ride_goal}",
    )
    s4.metric(
        "Total Fuel Consumed",
        f"{st.session_state.total_fuel_liters:.2f} L",
        f"Rs. {st.session_state.total_fuel_cost:,.0f}",
        delta_color="off",
    )
    s5.metric(
        "Maintenance Saved",
        f"Rs. {st.session_state.total_maintenance_saved:,.0f}",
    )
    s6.metric(
        "Emergency Contributed",
        f"Rs. {st.session_state.total_emergency_contributed:,.0f}",
    )

    if st.session_state.rides_log:
        st.markdown("#### Today's Completed Rides Ledger")
        df_log = pd.DataFrame(st.session_state.rides_log)
        st.dataframe(df_log, use_container_width=True, hide_index=True)
    else:
        st.info("No rides logged in this shift yet. Complete a ride and click 'Log Completed Ride' above.")


# =============================================================================
# TAB 3: DASHBOARD & GOALS PROGRESS
# =============================================================================
with tab3:
    st.subheader("Daily & Monthly Goals Progress")

    # 1. Daily Rides Completed Progress
    rides_done = st.session_state.total_rides_completed
    rides_progress = min(1.0, max(0.0, rides_done / max(1, daily_ride_goal)))
    st.markdown(
        f"**1. Daily Rides Completed:** `{rides_done} / {daily_ride_goal} rides` ({rides_progress * 100:.0f}%)"
    )
    st.progress(rides_progress)

    # 2. Daily Net Earnings Progress
    net_done = st.session_state.total_net_profit
    net_progress = min(1.0, max(0.0, net_done / max(1.0, daily_net_goal)))
    st.markdown(
        f"**2. Daily Net Earnings:** `Rs. {net_done:,.0f} / Rs. {daily_net_goal:,.0f}` ({net_progress * 100:.0f}%)"
    )
    st.progress(net_progress)

    # 3. Monthly Emergency Fund Progress
    prior_bal = st.number_input(
        "Prior Monthly Emergency Fund Balance (PKR, Optional)",
        min_value=0.0,
        max_value=200000.0,
        value=st.session_state.prior_emergency_balance,
        step=200.0,
        help="Include emergency reserve already saved earlier this month.",
    )
    st.session_state.prior_emergency_balance = prior_bal

    total_monthly_emergency = prior_bal + st.session_state.total_emergency_contributed
    emergency_progress = min(
        1.0, max(0.0, total_monthly_emergency / max(1.0, monthly_emergency_target))
    )
    st.markdown(
        f"**3. Monthly Emergency Fund Progress:** `Rs. {total_monthly_emergency:,.0f} / Rs. {monthly_emergency_target:,.0f}` ({emergency_progress * 100:.1f}%)"
    )
    st.progress(emergency_progress)

    st.divider()
    st.subheader("Financial Summary & Shift Efficiency")

    total_expenses_deducted = (
        st.session_state.total_fuel_cost
        + st.session_state.total_maintenance_saved
        + st.session_state.total_emergency_contributed
        + st.session_state.total_food_expense
    )
    shift_efficiency = (
        st.session_state.total_net_profit / st.session_state.total_distance_km
        if st.session_state.total_distance_km > 0
        else 0.0
    )

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Gross Earnings", f"Rs. {st.session_state.total_gross_earnings:,.0f}")
    d2.metric("Total Expenses Deducted", f"Rs. {total_expenses_deducted:,.0f}")
    d3.metric("Net Pocket Profit", f"Rs. {st.session_state.total_net_profit:,.0f}")
    d4.metric(
        "Shift Efficiency (Net / KM)",
        f"Rs. {shift_efficiency:,.1f} / KM",
        f"{st.session_state.total_distance_km:.1f} KM Total",
        delta_color="off",
    )

    summary_df = pd.DataFrame(
        [
            {"Category": "Gross Earnings (Fares + Tips)", "Amount (PKR)": f"Rs. {st.session_state.total_gross_earnings:,.1f}"},
            {"Category": "[-] Fuel Cost Deducted", "Amount (PKR)": f"Rs. {st.session_state.total_fuel_cost:,.1f}"},
            {"Category": "[-] Maintenance Reserve Saved", "Amount (PKR)": f"Rs. {st.session_state.total_maintenance_saved:,.1f}"},
            {"Category": "[-] Emergency Fund Contributed", "Amount (PKR)": f"Rs. {st.session_state.total_emergency_contributed:,.1f}"},
            {"Category": "[-] Food / Personal Expense", "Amount (PKR)": f"Rs. {st.session_state.total_food_expense:,.1f}"},
            {"Category": "Total Expenses Deducted", "Amount (PKR)": f"Rs. {total_expenses_deducted:,.1f}"},
            {"Category": "Net Pocket Profit (Take-Home)", "Amount (PKR)": f"Rs. {st.session_state.total_net_profit:,.1f}"},
            {"Category": "Shift Efficiency (Net Profit per KM)", "Amount (PKR)": f"Rs. {shift_efficiency:,.2f} / KM"},
        ]
    )
    st.table(summary_df)

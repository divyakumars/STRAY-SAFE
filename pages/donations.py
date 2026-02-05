# pages/donations.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage
from components import page_header, kpi_card


@st.cache_resource
def load_qr_library():
    """Load QR code library"""
    import qrcode
    from io import BytesIO
    import base64

    return {'qrcode': qrcode, 'BytesIO': BytesIO, 'base64': base64}


def generate_qr_code(data):
    """Generate QR code for UPI payment"""
    libs = load_qr_library()
    qr = libs['qrcode']
    BytesIO = libs['BytesIO']
    base64 = libs['base64']

    qr_obj = qr.QRCode(version=1, box_size=10, border=5)
    qr_obj.add_data(data)
    qr_obj.make(fit=True)

    img = qr_obj.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def render():
    """Donation and fundraising portal"""
    user_role = st.session_state.user.get("role")
    page_header("💰", "Donations & Fundraising",
                "Support our mission to help street dogs", user_role)

    donations = storage.read("donations", [])
    campaigns = storage.read("campaigns", [])

    # Normalize data
    for d in donations:
        d.setdefault("amount", 0)
        d.setdefault("donor", "Anonymous")
        d.setdefault("campaign_id", None)

    for c in campaigns:
        c.setdefault("target", 10000)
        c.setdefault("raised", 0)
        c.setdefault("status", "active")

    # Calculate totals
    total_raised = sum(d.get("amount", 0) for d in donations)
    total_donors = len(set(d.get("donor") for d in donations if d.get("donor") != "Anonymous"))
    active_campaigns = sum(1 for c in campaigns if c.get("status") == "active")

    # KPIs
    st.markdown("### 💎 Fundraising Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card("Total Raised", f"₹{total_raised:,.0f}", "All campaigns", "💰", "success")

    with col2:
        kpi_card("Total Donors", total_donors, f"{len(donations)} donations", "❤️", "primary")

    with col3:
        kpi_card("Active Campaigns", active_campaigns, f"{len(campaigns)} total", "🎯", "info")

    with col4:
        avg_donation = total_raised / len(donations) if donations else 0
        kpi_card("Avg Donation", f"₹{avg_donation:,.0f}", "Per transaction", "📊", "warning")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["💳 Make Donation", "🎯 Active Campaigns", "📊 Donation History"])

    # TAB 1: Make Donation
    with tab1:
        st.markdown("### 💳 Make a Donation")

        col1, col2 = st.columns([1, 1])

        with col1:
            # Donation form
            st.markdown("#### Donation Details")

            donor_name = st.text_input("Your Name",
                                       value=st.session_state.user.get("name", ""),
                                       key="donor_name")

            donor_email = st.text_input("Email",
                                        value=st.session_state.user.get("email", ""),
                                        key="donor_email")

            # Campaign selection
            campaign_options = ["General Fund"] + [c["name"] for c in campaigns if c.get("status") == "active"]
            selected_campaign = st.selectbox("Select Campaign", campaign_options)

            # Amount
            preset_amounts = [100, 500, 1000, 2000, 5000]

            col_amt1, col_amt2, col_amt3 = st.columns(3)

            selected_preset = None
            with col_amt1:
                if st.button("₹100", use_container_width=True):
                    selected_preset = 100
            with col_amt2:
                if st.button("₹500", use_container_width=True):
                    selected_preset = 500
            with col_amt3:
                if st.button("₹1000", use_container_width=True):
                    selected_preset = 1000

            col_amt4, col_amt5 = st.columns(2)
            with col_amt4:
                if st.button("₹2000", use_container_width=True):
                    selected_preset = 2000
            with col_amt5:
                if st.button("₹5000", use_container_width=True):
                    selected_preset = 5000

            if "donation_amount" not in st.session_state:
                st.session_state.donation_amount = 500

            if selected_preset:
                st.session_state.donation_amount = selected_preset

            amount = st.number_input("Or Enter Custom Amount",
                                     min_value=10,
                                     value=st.session_state.donation_amount,
                                     step=10,
                                     key="custom_amount")

            # Message
            message = st.text_area("Message (Optional)",
                                   placeholder="Add a message of support...")

            # Payment method
            payment_method = st.selectbox("Payment Method",
                                          ["UPI", "Card", "Net Banking", "Wallet"])

        with col2:
            st.markdown("#### Payment Information")

            if payment_method == "UPI":
                st.markdown("""
                <div style="padding: 20px; background: rgba(51, 65, 85, 0.3); 
                            border-radius: 12px; text-align: center;">
                    <h4>Scan QR Code to Pay</h4>
                </div>
                """, unsafe_allow_html=True)

                # Generate UPI QR code
                upi_id = "9840277042-2@ybl"
                upi_string = f"upi://pay?pa={upi_id}&pn=SafePaws&am={amount}&cu=INR"

                qr_image = generate_qr_code(upi_string)

                st.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <img src="{qr_image}" style="max-width: 250px; border-radius: 12px;">
                    <p style="margin-top: 16px; color: #94a3b8;">
                        UPI ID: <strong>{upi_id}</strong><br>
                        Amount: <strong>₹{amount}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.info(f"💳 {payment_method} payment integration coming soon!")

            # Donate button
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("💖 Complete Donation", type="primary", use_container_width=True):
                # Record donation
                donation_id = f"DON-{int(dt.datetime.now().timestamp())}"

                # Find campaign ID
                campaign_id = None
                if selected_campaign != "General Fund":
                    for c in campaigns:
                        if c.get("name") == selected_campaign:
                            campaign_id = c.get("id")
                            # Update campaign raised amount
                            c["raised"] = c.get("raised", 0) + amount
                            break

                new_donation = {
                    "id": donation_id,
                    "donor": donor_name or "Anonymous",
                    "email": donor_email,
                    "amount": amount,
                    "campaign_id": campaign_id,
                    "campaign_name": selected_campaign,
                    "payment_method": payment_method,
                    "message": message,
                    "time": str(dt.datetime.now()),
                    "status": "completed"
                }

                donations.append(new_donation)
                storage.write("donations", donations)

                if campaign_id:
                    storage.write("campaigns", campaigns)

                st.success(f"✅ Thank you for your donation of ₹{amount}!")
                st.balloons()
                st.rerun()

    # TAB 2: Active Campaigns
    with tab2:
        st.markdown("### 🎯 Active Campaigns")

        if not campaigns:
            st.info("No active campaigns at the moment. Check back soon!")
        else:
            for camp in campaigns:
                if camp.get("status") != "active":
                    continue

                raised = camp.get("raised", 0)
                target = camp.get("target", 10000)
                percentage = (raised / target * 100) if target > 0 else 0

                st.markdown(f"""
                <div style="padding: 24px; background: rgba(51, 65, 85, 0.3); 
                            border-radius: 12px; margin-bottom: 20px; 
                            border: 1px solid #475569;">
                    <h3 style="margin: 0 0 8px 0;">{camp.get('name', 'Campaign')}</h3>
                    <p style="color: #94a3b8; margin: 0 0 16px 0;">
                        {camp.get('description', 'Help us achieve our goal!')}
                    </p>

                    <div style="background: rgba(30, 41, 59, 0.5); 
                                border-radius: 8px; height: 24px; overflow: hidden; 
                                margin-bottom: 12px;">
                        <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); 
                                    height: 100%; width: {min(percentage, 100)}%; 
                                    transition: width 0.3s ease;"></div>
                    </div>

                    <div style="display: flex; justify-content: space-between; 
                                color: #e8eaf6; font-size: 14px;">
                        <span>₹{raised:,} raised</span>
                        <span>{percentage:.1f}%</span>
                        <span>₹{target:,} goal</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # TAB 3: Donation History
    with tab3:
        st.markdown("### 📊 Donation History")

        if donations:
            # Sort by time
            sorted_donations = sorted(donations, key=lambda x: x.get("time", ""), reverse=True)

            # Create DataFrame - FIXED: Keep numeric values first
            df_donations = pd.DataFrame([{
                "Date": d.get("time", "")[:10],
                "Donor": d.get("donor", "Anonymous"),
                "Amount": d.get('amount', 0),  # ✅ KEEP AS NUMBER
                "Campaign": d.get("campaign_name", "General Fund"),
                "Method": d.get("payment_method", "N/A")
            } for d in sorted_donations])

            # Format Amount column after DataFrame creation
            df_donations['Amount'] = df_donations['Amount'].apply(lambda x: f"₹{x:,}")

            st.dataframe(df_donations, use_container_width=True, height=400)

            # Download CSV
            csv = df_donations.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "donations.csv",
                "text/csv",
                key="download_donations"
            )
        else:
            st.info("No donations yet. Be the first to contribute!")

    # Impact section
    st.markdown("### 🌟 Your Impact")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="padding: 20px; background: rgba(99, 102, 241, 0.1); 
                    border-radius: 12px; border: 1px solid #6366f1;">
            <div style="font-size: 48px; text-align: center;">🐕</div>
            <h3 style="text-align: center; margin: 12px 0 8px 0;">250+</h3>
            <p style="text-align: center; color: #94a3b8; margin: 0;">
                Dogs Treated
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="padding: 20px; background: rgba(16, 185, 129, 0.1); 
                    border-radius: 12px; border: 1px solid #10b981;">
            <div style="font-size: 48px; text-align: center;">💉</div>
            <h3 style="text-align: center; margin: 12px 0 8px 0;">500+</h3>
            <p style="text-align: center; color: #94a3b8; margin: 0;">
                Vaccinations Done
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="padding: 20px; background: rgba(245, 158, 11, 0.1); 
                    border-radius: 12px; border: 1px solid #f59e0b;">
            <div style="font-size: 48px; text-align: center;">🏠</div>
            <h3 style="text-align: center; margin: 12px 0 8px 0;">75+</h3>
            <p style="text-align: center; color: #94a3b8; margin: 0;">
                Dogs Adopted
            </p>
        </div>
        """, unsafe_allow_html=True)
# pages/adoption.py - COMPLETE VERSION WITH USER UPLOADS

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage, notify
from components import page_header, kpi_card, encode_file, decode_file, create_notification, audit_log


def render():
    """Complete pet adoption portal with user submissions and admin verification"""
    user_role = st.session_state.user.get("role")
    user_email = st.session_state.user.get("email")
    user_name = st.session_state.user.get("name")

    page_header("🐕", "Adoption Portal",
                "Find your perfect companion and give them a forever home", user_role)

    dogs = storage.read("adoption_dogs", [])
    applications = storage.read("adoption_applications", [])

    # Normalize dog data
    for dog in dogs:
        dog.setdefault("id", f"DOG-{int(dt.datetime.now().timestamp())}")
        dog.setdefault("name", "Unknown")
        dog.setdefault("age", "Unknown")
        dog.setdefault("breed", "Mixed")
        dog.setdefault("gender", "Unknown")
        dog.setdefault("size", "Medium")
        dog.setdefault("status", "Pending Approval")  # Default for user submissions
        dog.setdefault("vaccinated", False)
        dog.setdefault("neutered", False)
        dog.setdefault("description", "")
        dog.setdefault("image", None)
        dog.setdefault("location", "Unknown")
        dog.setdefault("added_by", "system")
        dog.setdefault("added_at", str(dt.datetime.now()))

    # Normalize application data
    for app in applications:
        app.setdefault("id", f"APP-{int(dt.datetime.now().timestamp())}")
        app.setdefault("status", "pending")
        app.setdefault("applicant", "Unknown")
        app.setdefault("applicant_email", "")
        app.setdefault("admin_notes", "")
        app.setdefault("submitted_at", str(dt.datetime.now()))

    # ============ STATISTICS ============
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        available = sum(1 for d in dogs if d.get("status") == "Available")
        kpi_card("Available", available, f"{len(dogs)} total", "🐕", "success")

    with col2:
        adopted = sum(1 for d in dogs if d.get("status") == "Adopted")
        kpi_card("Adopted", adopted, "Happy homes", "🏠", "primary")

    with col3:
        pending_apps = sum(1 for a in applications if a.get("status") == "pending")
        kpi_card("Applications", len(applications), f"{pending_apps} pending", "📋", "info")

    with col4:
        if user_role == "admin":
            pending_dogs = sum(1 for d in dogs if d.get("status") == "Pending Approval")
            kpi_card("Pending Dogs", pending_dogs, "Awaiting review", "⏳", "warning")
        else:
            my_apps = sum(1 for a in applications if a.get("applicant_email") == user_email)
            kpi_card("My Applications", my_apps, "Submitted", "👤", "warning")

    # ============ TABS BASED ON ROLE ============
    if user_role == "admin":
        tabs = st.tabs([
            "🔍 Browse Dogs",
            "📋 My Applications",
            "⚙️ Manage Applications (Admin)",
            "🛡️ Verify Dog Submissions (Admin)",
            "➕ Submit a Dog",
            "📊 Statistics"
        ])
    else:
        tabs = st.tabs([
            "🔍 Browse Dogs",
            "📋 My Applications",
            "➕ Submit a Dog",
            "📊 Statistics"
        ])

    # ============ TAB 1: BROWSE AVAILABLE DOGS ============
    with tabs[0]:
        st.markdown("### 🔍 Find Your Perfect Match")

        # Filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            size_filter = st.selectbox("Size", ["All", "Small", "Medium", "Large", "X-Large"])

        with col2:
            age_filter = st.selectbox("Age", ["All", "Puppy", "Young", "Adult", "Senior"])

        with col3:
            gender_filter = st.selectbox("Gender", ["All", "Male", "Female"])

        with col4:
            vaccinated_filter = st.checkbox("Vaccinated Only", value=False)

        # Apply filters - show only AVAILABLE dogs to regular users
        if user_role == "admin":
            filtered_dogs = dogs.copy()
        else:
            filtered_dogs = [d for d in dogs if d.get("status") == "Available"]

        if size_filter != "All":
            filtered_dogs = [d for d in filtered_dogs if d.get("size") == size_filter]

        if age_filter != "All":
            filtered_dogs = [d for d in filtered_dogs if d.get("age") == age_filter]

        if gender_filter != "All":
            filtered_dogs = [d for d in filtered_dogs if d.get("gender") == gender_filter]

        if vaccinated_filter:
            filtered_dogs = [d for d in filtered_dogs if d.get("vaccinated", False)]

        st.markdown(f"**{len(filtered_dogs)} dogs available**")

        # Display dogs in grid
        if not filtered_dogs:
            st.info("No dogs match your filters. Try adjusting your criteria.")
        else:
            for i in range(0, len(filtered_dogs), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(filtered_dogs):
                        dog = filtered_dogs[i + j]
                        with col:
                            # Status badge
                            status = dog.get("status", "Unknown")
                            status_colors = {
                                "Available": "#10b981",
                                "Adopted": "#3b82f6",
                                "Pending Approval": "#f59e0b",
                                "Rejected": "#ef4444"
                            }
                            status_color = status_colors.get(status, "#64748b")

                            st.markdown(f"""
                            <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; background: white; height: 100%;">
                                <div style="background: {status_color}; color: white; padding: 4px 12px; border-radius: 20px; display: inline-block; font-size: 12px; margin-bottom: 12px;">
                                    {status}
                                </div>
                            """, unsafe_allow_html=True)

                            # Dog image
                            if dog.get("image"):
                                try:
                                    st.image(decode_file(dog["image"]["data"]), use_container_width=True)
                                except:
                                    st.image("https://via.placeholder.com/300x200?text=No+Image",
                                             use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)

                            # Dog details
                            st.markdown(f"""
                                <h4 style="margin: 12px 0 8px 0;">{dog['name']}</h4>
                                <p style="color: #64748b; font-size: 14px; margin: 4px 0;">
                                    🐾 {dog['breed']} | {dog['gender']}<br>
                                    📏 {dog['size']} | 🎂 {dog['age']}<br>
                                    💉 {'Vaccinated ✅' if dog.get('vaccinated') else 'Not Vaccinated'}<br>
                                    ✂️ {'Neutered ✅' if dog.get('neutered') else 'Not Neutered'}
                                </p>
                            """, unsafe_allow_html=True)

                            # Action button - only for available dogs
                            if dog.get("status") == "Available":
                                if st.button("❤️ Apply to Adopt", key=f"adopt_{dog['id']}", use_container_width=True):
                                    st.session_state[f"show_form_{dog['id']}"] = True
                                    st.rerun()

                                # Show adoption form if triggered
                                if st.session_state.get(f"show_form_{dog['id']}", False):
                                    with st.form(f"adoption_form_{dog['id']}"):
                                        st.markdown("### 📝 Adoption Application")
                                        st.markdown(f"**Dog:** {dog['name']}")

                                        applicant_name = st.text_input("Full Name*", value=user_name)
                                        email = st.text_input("Email*", value=user_email)
                                        phone = st.text_input("Phone Number*")
                                        address = st.text_area("Address*")

                                        st.markdown("#### Housing Details")
                                        housing_type = st.selectbox("Housing Type",
                                                                    ["House with yard", "House without yard",
                                                                     "Apartment", "Condo", "Other"])
                                        has_yard = "yard" in housing_type.lower()

                                        other_pets = st.radio("Do you have other pets?", ["Yes", "No"])
                                        if other_pets == "Yes":
                                            pets_details = st.text_input("What pets do you have?")
                                        else:
                                            pets_details = ""

                                        st.markdown("#### Experience & Commitment")
                                        experience = st.text_area("Previous pet experience:", height=80)
                                        reason = st.text_area("Why do you want to adopt this dog?*", height=100)

                                        household_members = st.number_input("Number of people in household",
                                                                            min_value=1, value=1)

                                        col_submit, col_cancel = st.columns(2)

                                        with col_submit:
                                            submitted = st.form_submit_button("📤 Submit Application",
                                                                              use_container_width=True,
                                                                              type="primary")

                                        with col_cancel:
                                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                                st.session_state[f"show_form_{dog['id']}"] = False
                                                st.rerun()

                                        if submitted:
                                            if not all([applicant_name, email, phone, address, reason]):
                                                st.error("❌ Please fill in all required fields (*)")
                                            else:
                                                app_id = f"APP-{int(dt.datetime.now().timestamp())}"

                                                new_application = {
                                                    "id": app_id,
                                                    "dog_id": dog["id"],
                                                    "dog_name": dog["name"],
                                                    "applicant": applicant_name,
                                                    "applicant_email": email,
                                                    "phone": phone,
                                                    "address": address,
                                                    "housing_type": housing_type,
                                                    "has_yard": has_yard,
                                                    "other_pets": other_pets,
                                                    "pets_details": pets_details,
                                                    "experience": experience,
                                                    "reason": reason,
                                                    "household_members": household_members,
                                                    "status": "pending",
                                                    "submitted_at": str(dt.datetime.now()),
                                                    "admin_notes": ""
                                                }

                                                applications.append(new_application)
                                                storage.write("adoption_applications", applications)

                                                create_notification("success",
                                                                    f"New adoption application: {applicant_name} → {dog['name']}",
                                                                    "high")
                                                audit_log("ADOPTION_APPLICATION",
                                                          {"dog": dog['name'], "applicant": applicant_name})

                                                st.success("✅ Application submitted! We'll review it soon.")
                                                st.session_state[f"show_form_{dog['id']}"] = False
                                                st.rerun()

                            st.markdown("</div>", unsafe_allow_html=True)

    # ============ TAB 2: MY APPLICATIONS ============
    with tabs[1]:
        st.markdown("### 📋 My Applications")

        my_applications = [a for a in applications if a.get("applicant_email") == user_email]

        if not my_applications:
            st.info("You haven't submitted any adoption applications yet.")
        else:
            for app in sorted(my_applications, key=lambda x: x.get("submitted_at", ""), reverse=True):
                status_colors = {
                    "pending": "#f59e0b",
                    "approved": "#10b981",
                    "rejected": "#ef4444"
                }
                status_icons = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌"
                }

                status = app.get("status", "pending")

                with st.expander(f"{status_icons.get(status, '📄')} {app.get('dog_name')} - {status.title()}",
                                 expanded=(status == "approved")):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **Application ID:** {app['id']}<br>
                        **Dog:** {app.get('dog_name')}<br>
                        **Submitted:** {app.get('submitted_at', 'N/A')[:19]}<br>
                        **Status:** <span style="color: {status_colors.get(status, '#64748b')}; font-weight: bold;">{status.upper()}</span>
                        """, unsafe_allow_html=True)

                        if app.get("admin_notes"):
                            st.info(f"📝 Admin Notes: {app['admin_notes']}")

                    with col2:
                        st.markdown(f"""
                        **Your Details:**<br>
                        📧 {app.get('applicant_email')}<br>
                        📞 {app.get('phone')}<br>
                        🏠 {app.get('housing_type')}
                        """, unsafe_allow_html=True)

    # ============ TAB 3: ADMIN - MANAGE APPLICATIONS ============
    if user_role == "admin":
        with tabs[2]:
            st.markdown("### ⚙️ Manage Adoption Applications")

            pending_apps = [a for a in applications if a.get("status") == "pending"]

            if not pending_apps:
                st.success("✅ No pending applications")
            else:
                st.markdown(f"**{len(pending_apps)} applications awaiting review**")

                for app in pending_apps:
                    with st.expander(f"📋 {app['id']} - {app.get('applicant')} → {app.get('dog_name')}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"""
                            **Applicant:** {app.get('applicant')}<br>
                            **Email:** {app.get('applicant_email')}<br>
                            **Phone:** {app.get('phone')}<br>
                            **Address:** {app.get('address')}<br>
                            **Housing:** {app.get('housing_type')}<br>
                            **Has Yard:** {'Yes ✅' if app.get('has_yard') else 'No ❌'}<br>
                            **Other Pets:** {app.get('other_pets')} {app.get('pets_details', '')}<br>
                            **Household Size:** {app.get('household_members')} people
                            """, unsafe_allow_html=True)

                        with col2:
                            st.markdown("**Experience:**")
                            st.text(app.get('experience', 'Not provided'))
                            st.markdown("**Reason for Adoption:**")
                            st.text(app.get('reason', 'Not provided'))

                        admin_notes = st.text_area("Admin Notes",
                                                   value=app.get("admin_notes", ""),
                                                   key=f"notes_{app['id']}")

                        col_a, col_b, col_c = st.columns(3)

                        with col_a:
                            if st.button("✅ Approve", key=f"approve_app_{app['id']}", type="primary"):
                                app["status"] = "approved"
                                app["admin_notes"] = admin_notes

                                # Update dog status
                                for dog in dogs:
                                    if dog["id"] == app["dog_id"]:
                                        dog["status"] = "Adopted"
                                        dog["adopted_by"] = app["applicant"]
                                        dog["adopted_at"] = str(dt.datetime.now())

                                storage.write("adoption_applications", applications)
                                storage.write("adoption_dogs", dogs)

                                create_notification("success",
                                                    f"Adoption approved: {app['dog_name']} → {app['applicant']}",
                                                    "high")
                                audit_log("ADOPTION_APPROVE", {"application": app['id']})

                                st.success("✅ Application approved!")
                                st.rerun()

                        with col_b:
                            if st.button("❌ Reject", key=f"reject_app_{app['id']}"):
                                app["status"] = "rejected"
                                app["admin_notes"] = admin_notes

                                storage.write("adoption_applications", applications)

                                create_notification("info",
                                                    f"Application rejected: {app['dog_name']} - {app['applicant']}",
                                                    "normal")
                                audit_log("ADOPTION_REJECT", {"application": app['id']})

                                st.warning("❌ Application rejected")
                                st.rerun()

                        with col_c:
                            if st.button("📧 Contact", key=f"contact_{app['id']}"):
                                st.info(f"📞 {app.get('phone')}\n📧 {app.get('applicant_email')}")

    # ============ TAB 4: ADMIN - VERIFY DOG SUBMISSIONS ============
    if user_role == "admin":
        with tabs[3]:
            st.markdown("### 🛡️ Verify Dog Submissions")

            pending_dogs = [d for d in dogs if d.get("status") == "Pending Approval"]

            if not pending_dogs:
                st.success("✅ No pending dog submissions")
            else:
                st.markdown(f"**{len(pending_dogs)} dogs awaiting verification**")

                for dog in pending_dogs:
                    with st.expander(f"🐶 {dog['name']} - Submitted by {dog.get('added_by')}"):
                        col1, col2 = st.columns([1, 1])

                        with col1:
                            if dog.get("image"):
                                try:
                                    st.image(decode_file(dog["image"]["data"]), width=300)
                                except:
                                    st.info("📷 Image could not be displayed")
                            else:
                                st.info("📷 No image uploaded")

                        with col2:
                            st.markdown(f"""
                            **Name:** {dog['name']}<br>
                            **Breed:** {dog['breed']}<br>
                            **Age:** {dog['age']}<br>
                            **Size:** {dog['size']}<br>
                            **Gender:** {dog['gender']}<br>
                            **Vaccinated:** {'Yes ✅' if dog.get('vaccinated') else 'No ❌'}<br>
                            **Neutered:** {'Yes ✅' if dog.get('neutered') else 'No ❌'}<br>
                            **Location:** {dog.get('location')}<br>
                            **Submitted by:** {dog.get('added_by')}<br>
                            **Submitted at:** {dog.get('added_at', 'N/A')[:19]}
                            """, unsafe_allow_html=True)

                        st.markdown("**Description:**")
                        st.text(dog.get('description', 'No description provided'))

                        col_approve, col_reject = st.columns(2)

                        with col_approve:
                            if st.button("✅ Approve & Publish", key=f"approve_dog_{dog['id']}",
                                         type="primary", use_container_width=True):
                                dog["status"] = "Available"
                                storage.write("adoption_dogs", dogs)

                                create_notification("success",
                                                    f"Dog approved: {dog['name']} is now available for adoption",
                                                    "normal")
                                audit_log("DOG_APPROVE", {"dog": dog['name'], "by": dog.get('added_by')})

                                # TODO: Send email notification to submitter
                                st.success(f"✅ {dog['name']} approved and published!")
                                st.rerun()

                        with col_reject:
                            if st.button("❌ Reject", key=f"reject_dog_{dog['id']}",
                                         use_container_width=True):
                                dog["status"] = "Rejected"
                                storage.write("adoption_dogs", dogs)

                                audit_log("DOG_REJECT", {"dog": dog['name'], "by": dog.get('added_by')})

                                # TODO: Send email notification to submitter
                                st.warning(f"❌ {dog['name']} rejected")
                                st.rerun()

    # ============ TAB: SUBMIT A DOG (ALL USERS) ============
    submit_tab_index = 4 if user_role == "admin" else 2
    with tabs[submit_tab_index]:
        st.markdown("### ➕ Submit a Dog for Adoption")
        st.info(
            "📝 Anyone can submit a dog! Admins will review your submission before it appears in the adoption listings.")

        with st.form("submit_dog_form"):
            st.markdown("#### Basic Information")
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Dog Name*")
                breed = st.text_input("Breed (if known)", placeholder="e.g., Labrador, Mixed")
                age = st.text_input("Age*", placeholder="e.g., 2 years, 6 months")
                gender = st.selectbox("Gender*", ["Male", "Female", "Unknown"])

            with col2:
                size = st.selectbox("Size*", ["Small", "Medium", "Large", "X-Large"])
                location = st.text_input("Location*", placeholder="City, State")
                vaccinated = st.checkbox("Vaccinated")
                neutered = st.checkbox("Neutered/Spayed")

            st.markdown("#### Additional Details")
            description = st.text_area("Description*",
                                       placeholder="Tell us about this dog's personality, behavior, health status, etc.",
                                       height=150)

            photo = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png"])

            st.markdown("---")
            col_submit, col_reset = st.columns([3, 1])

            with col_submit:
                submitted = st.form_submit_button("📤 Submit for Review",
                                                  type="primary",
                                                  use_container_width=True)

            with col_reset:
                st.form_submit_button("🔄 Reset", use_container_width=True)

            if submitted:
                if not all([name, age, gender, size, location, description]):
                    st.error("❌ Please fill in all required fields (*)")
                else:
                    photo_encoded = None
                    if photo:
                        photo_encoded = {
                            "name": photo.name,
                            "type": photo.type,
                            "data": encode_file(photo.getvalue())
                        }

                    new_dog = {
                        "id": f"DOG-{int(dt.datetime.now().timestamp())}",
                        "name": name,
                        "breed": breed or "Mixed",
                        "age": age,
                        "gender": gender,
                        "size": size,
                        "location": location,
                        "vaccinated": vaccinated,
                        "neutered": neutered,
                        "description": description,
                        "image": photo_encoded,
                        "status": "Pending Approval",  # All user submissions start as pending
                        "added_by": user_email,
                        "added_at": str(dt.datetime.now())
                    }

                    dogs.append(new_dog)
                    storage.write("adoption_dogs", dogs)

                    create_notification("info",
                                        f"New dog submission: {name} by {user_name}",
                                        "normal")
                    audit_log("DOG_SUBMIT", {"dog": name, "by": user_email})

                    st.success(f"✅ {name} submitted successfully! Admins will review it soon.")
                    st.balloons()
                    st.rerun()

    # ============ TAB: STATISTICS ============
    stats_tab_index = 5 if user_role == "admin" else 3
    with tabs[stats_tab_index]:
        st.markdown("### 📊 Adoption Statistics")

        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            adoption_rate = (adopted / len(dogs) * 100) if dogs else 0
            st.metric("Adoption Rate", f"{adoption_rate:.1f}%",
                      f"{adopted} of {len(dogs)}")

        with col2:
            approval_rate = (
                    sum(1 for a in applications if a.get("status") == "approved") /
                    len(applications) * 100
            ) if applications else 0
            st.metric("Application Approval", f"{approval_rate:.1f}%",
                      f"{sum(1 for a in applications if a.get('status') == 'approved')} approved")

        with col3:
            avg_time = 15  # Mock data - could be calculated
            st.metric("Avg. Time to Adopt", f"{avg_time} days", "📅")

        with col4:
            pending_review = sum(1 for d in dogs if d.get("status") == "Pending Approval")
            st.metric("Pending Review", pending_review, "⏳ Awaiting verification")

        st.markdown("---")

        # Charts Section
        if dogs or applications:
            col1, col2 = st.columns(2)

            # LEFT COLUMN - Dog Status Pie Chart
            with col1:
                st.markdown("#### 🐕 Dog Status Distribution")

                if dogs:
                    dog_status_counts = {}
                    for dog in dogs:
                        status = dog.get("status", "Unknown")
                        dog_status_counts[status] = dog_status_counts.get(status, 0) + 1

                    # Create simple visualization
                    status_data = pd.DataFrame(list(dog_status_counts.items()),
                                               columns=['Status', 'Count'])

                    # Color mapping and display
                    status_colors = {
                        "Available": "#10b981",
                        "Adopted": "#3b82f6",
                        "Pending Approval": "#f59e0b",
                        "Rejected": "#ef4444"
                    }

                    for idx, row in status_data.iterrows():
                        status = row['Status']
                        count = row['Count']
                        percentage = (count / len(dogs) * 100)
                        color = status_colors.get(status, "#64748b")

                        st.markdown(f"""
                        <div style="padding: 12px; background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; border-radius: 8px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="font-size: 16px; color: {color};">{status}</strong>
                                    <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">
                                        {count} dogs ({percentage:.1f}%)
                                    </p>
                                </div>
                                <div style="font-size: 28px; font-weight: bold; color: {color};">
                                    {count}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No dog data available")

            # RIGHT COLUMN - Application Status Breakdown
            with col2:
                st.markdown("#### 📋 Application Status")

                if applications:
                    status_counts = {}
                    for app in applications:
                        status = app.get("status", "unknown")
                        status_counts[status] = status_counts.get(status, 0) + 1

                    app_status_colors = {
                        "pending": "#f59e0b",
                        "approved": "#10b981",
                        "rejected": "#ef4444"
                    }

                    for status, count in status_counts.items():
                        percentage = (count / len(applications) * 100)
                        color = app_status_colors.get(status, "#64748b")

                        st.markdown(f"""
                        <div style="padding: 12px; background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border-left: 4px solid {color}; border-radius: 8px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="font-size: 16px; color: {color};">{status.title()}</strong>
                                    <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">
                                        {count} applications ({percentage:.1f}%)
                                    </p>
                                </div>
                                <div style="font-size: 28px; font-weight: bold; color: {color};">
                                    {count}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No application data available")

            st.markdown("---")

            # Additional Stats Section
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📈 Breed Distribution")
                if dogs:
                    breed_counts = {}
                    for dog in dogs:
                        breed = dog.get("breed", "Unknown")
                        breed_counts[breed] = breed_counts.get(breed, 0) + 1

                    # Sort and show top 5
                    sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)[:5]

                    for breed, count in sorted_breeds:
                        percentage = (count / len(dogs) * 100)
                        st.markdown(f"""
                        <div style="padding: 8px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 6px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span><strong>{breed}</strong></span>
                                <span style="color: #64748b;">{count} ({percentage:.1f}%)</span>
                            </div>
                            <div style="background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                                <div style="background: #6366f1; height: 100%; width: {percentage}%;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No breed data available")

            with col2:
                st.markdown("#### 📊 Size Distribution")
                if dogs:
                    size_counts = {}
                    for dog in dogs:
                        size = dog.get("size", "Unknown")
                        size_counts[size] = size_counts.get(size, 0) + 1

                    size_order = ["Small", "Medium", "Large", "X-Large"]
                    size_colors = {
                        "Small": "#10b981",
                        "Medium": "#3b82f6",
                        "Large": "#8b5cf6",
                        "X-Large": "#ef4444"
                    }

                    for size in size_order:
                        if size in size_counts:
                            count = size_counts[size]
                            percentage = (count / len(dogs) * 100)
                            color = size_colors.get(size, "#64748b")

                            st.markdown(f"""
                            <div style="padding: 8px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 6px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span><strong>{size}</strong></span>
                                    <span style="color: #64748b;">{count} ({percentage:.1f}%)</span>
                                </div>
                                <div style="background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                                    <div style="background: {color}; height: 100%; width: {percentage}%;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No size data available")

            st.markdown("---")

            # Success Stories
            st.markdown("#### 🏠 Recent Adoptions")
            adopted_dogs = [d for d in dogs if d.get("status") == "Adopted"]

            if adopted_dogs:
                # Show last 5 adopted dogs
                recent_adoptions = sorted(adopted_dogs,
                                          key=lambda x: x.get("adopted_at", ""),
                                          reverse=True)[:5]

                for dog in recent_adoptions:
                    st.markdown(f"""
                    <div style="padding: 12px; background: linear-gradient(135deg, #10b98122 0%, #10b98111 100%); 
                                border-left: 4px solid #10b981; border-radius: 8px; margin-bottom: 8px;">
                        <strong style="color: #10b981;">🎉 {dog['name']}</strong>
                        <span style="color: #64748b; font-size: 13px;"> adopted by {dog.get('adopted_by', 'Unknown')}</span><br>
                        <span style="color: #94a3b8; font-size: 12px;">📅 {dog.get('adopted_at', 'Unknown')[:10]}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No adoptions yet. Be the first to give a dog a forever home! 🏠")

        else:
            st.info("📊 No data available yet. Start by adding dogs or submitting applications!")

        # Admin-only export feature
        if user_role == "admin":
            st.markdown("---")
            st.markdown("### 📥 Export Data")

            col1, col2, col3 = st.columns(3)

            with col1:
                if applications:
                    df_apps = pd.DataFrame(applications)
                    csv_apps = df_apps.to_csv(index=False)
                    st.download_button(
                        "📥 Download Applications CSV",
                        csv_apps,
                        f"applications_{int(dt.datetime.now().timestamp())}.csv",
                        "text/csv",
                        use_container_width=True
                    )

            with col2:
                if dogs:
                    df_dogs = pd.DataFrame(dogs)
                    csv_dogs = df_dogs.to_csv(index=False)
                    st.download_button(
                        "📥 Download Dogs CSV",
                        csv_dogs,
                        f"dogs_{int(dt.datetime.now().timestamp())}.csv",
                        "text/csv",
                        use_container_width=True
                    )

            with col3:
                # Combined report
                if dogs and applications:
                    combined_report = {
                        "total_dogs": len(dogs),
                        "available": sum(1 for d in dogs if d.get("status") == "Available"),
                        "adopted": sum(1 for d in dogs if d.get("status") == "Adopted"),
                        "pending_approval": sum(1 for d in dogs if d.get("status") == "Pending Approval"),
                        "total_applications": len(applications),
                        "pending_apps": sum(1 for a in applications if a.get("status") == "pending"),
                        "approved_apps": sum(1 for a in applications if a.get("status") == "approved"),
                        "adoption_rate": f"{(sum(1 for d in dogs if d.get('status') == 'Adopted') / len(dogs) * 100):.1f}%" if dogs else "0%",
                        "generated_at": str(dt.datetime.now())
                    }

                    import json
                    report_json = json.dumps(combined_report, indent=2)

                    st.download_button(
                        "📥 Download Summary Report (JSON)",
                        report_json,
                        f"adoption_summary_{int(dt.datetime.now().timestamp())}.json",
                        "application/json",
                        use_container_width=True
                    )
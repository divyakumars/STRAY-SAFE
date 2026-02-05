# pages/ai_detection.py - COMPLETE VERSION WITH ALL FEATURES + NULL FIX

import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import random
from PIL import Image
from utils import storage
from components import page_header, has_role, audit_log
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# ---------------------------------------------------------------------
# CACHED REVERSE GEOCODER
# ---------------------------------------------------------------------
@st.cache_resource
def get_reverse_geocoder():
    geoloc = Nominatim(user_agent="safepaws_app")
    return RateLimiter(geoloc.reverse, min_delay_seconds=1, max_retries=2, error_wait_seconds=5)


# ---------------------------------------------------------------------
# MODEL LOADING - WITH CORRECT PATH
# ---------------------------------------------------------------------
@st.cache_resource
def load_pytorch_model():
    """Load the PyTorch disease detection model"""
    try:
        import torch
        import torch.nn as nn
        from torchvision import transforms, models

        # ✅ CORRECT MODEL PATH: outputs/best_model.pt
        MODEL_PATH = "outputs/best_model.pt"
        ckpt = torch.load(MODEL_PATH, map_location="cpu")

        idx_to_class = {v: k for k, v in ckpt["class_to_idx"].items()}

        def build_model(backbone: str, num_classes: int):
            if backbone == "resnet50":
                m = models.resnet50(weights=None)
                in_f = m.fc.in_features
                m.fc = nn.Sequential(
                    nn.Linear(in_f, 512),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.3),
                    nn.Linear(512, num_classes)
                )
            elif backbone == "efficientnet_b0":
                m = models.efficientnet_b0(weights=None)
                in_f = m.classifier[-1].in_features
                m.classifier[-1] = nn.Linear(in_f, num_classes)
            elif backbone == "convnext_tiny":
                m = models.convnext_tiny(weights=None)
                in_f = m.classifier[-1].in_features
                m.classifier[-1] = nn.Linear(in_f, num_classes)
            else:
                raise ValueError(f"Unknown backbone: {backbone}")
            return m

        model = build_model(ckpt["backbone"], num_classes=len(idx_to_class))
        model.load_state_dict(ckpt["model_state"])
        model.eval()

        tfms = transforms.Compose([
            transforms.Resize(int(ckpt["img_size"] * 1.14)),
            transforms.CenterCrop(ckpt["img_size"]),
            transforms.ToTensor(),
            transforms.Normalize(ckpt["mean"], ckpt["std"]),
        ])

        device = __import__("torch").device("cuda" if __import__("torch").cuda.is_available() else "cpu")
        model.to(device)

        return model, tfms, idx_to_class, device

    except Exception as e:
        st.error(f"❌ Model loading failed: {e}")
        return None, None, None, None


# ---------------------------------------------------------------------
# PREDICTION FUNCTION
# ---------------------------------------------------------------------
def predict_disease(img: Image.Image, disease_model, disease_tfms, idx_to_class, device):
    """Predict disease from image"""
    if disease_model is None:
        st.warning("⚠️ Model not loaded, using mock predictions")
        diseases = ["demodicosis", "dermatitis", "fungal_infections",
                    "hypersensitivity", "ringworm", "healthy"]
        pred = random.choice(diseases)
        conf = round(random.uniform(0.65, 0.98), 3)
        all_probs = {d: (conf if d == pred else round(random.uniform(0.0, 0.3), 3)) for d in diseases}
        return pred, conf, all_probs, 50

    try:
        import torch
        x = disease_tfms(img).unsqueeze(0).to(device)
        with torch.no_grad(), torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
            logits = disease_model(x)
            probs = torch.softmax(logits, dim=1).squeeze(0)
            conf, pred_idx = torch.max(probs, dim=0)

        pred = idx_to_class[pred_idx.item()]
        confidence = float(conf.item())
        all_probs = {idx_to_class[i]: float(probs[i].item()) for i in range(len(idx_to_class))}

        severity_map = {
            "healthy": 0,
            "dermatitis": 40,
            "fungal_infections": 50,
            "hypersensitivity": 45,
            "ringworm": 55,
            "demodicosis": 70
        }
        base_sev = severity_map.get(pred.lower(), 50)
        sev_score = int(base_sev * confidence)

        return pred, confidence, all_probs, sev_score

    except Exception as e:
        st.error(f"❌ Prediction failed: {e}")
        return "unknown", 0.0, {}, 0


# ---------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------
def severity_from_score(score: int, pred_class: str):
    """Convert severity score to label and number"""
    if pred_class.lower() == "healthy":
        return "Mild", 1
    if score < 30:
        return "Mild", 2 if score >= 15 else 1
    if score < 60:
        return "Moderate", 3
    return "Severe", 4 if score < 85 else 5


def severity_badge(label: str) -> str:
    """HTML badge for severity display"""
    color = {"Mild": "#10b981", "Moderate": "#f59e0b", "Severe": "#ef4444"}.get(label, "#6366f1")
    return f"""
    <div style="display: inline-block; padding: 6px 16px; background: {color};
                color: white; border-radius: 20px; font-weight: 700; font-size: 14px;">
        {label} Severity
    </div>
    """


def confidence_bar(pct: float) -> str:
    """HTML confidence bar"""
    pct = max(0.0, min(100.0, pct))
    return f"""
    <div style="padding: 16px; background: rgba(51, 65, 85, 0.3);
                border-radius: 12px; margin-bottom: 16px;">
        <div style="font-size: 14px; margin-bottom: 8px;">
            Confidence: <strong>{pct:.1f}%</strong>
        </div>
        <div style="background: rgba(0,0,0,0.3); height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #10b981 0%, #3b82f6 50%, #ef4444 100%);
                        width: {pct}%; height: 100%;"></div>
        </div>
    </div>
    """


def risk_level_badge(level: str) -> str:
    """HTML badge for risk level display"""
    colors = {
        "Low Risk": "#10b981",
        "Moderate Risk": "#f59e0b",
        "High Risk": "#ef4444",
        "Critical Risk": "#dc2626"
    }
    color = colors.get(level, "#6366f1")
    return f"""
    <div style="display: inline-block; padding: 8px 20px; background: {color};
                color: white; border-radius: 20px; font-weight: 700; font-size: 16px; margin: 12px 0;">
        {level}
    </div>
    """


# ---------------------------------------------------------------------
# BITE RISK ASSESSMENT FUNCTIONS
# ---------------------------------------------------------------------
def calculate_bite_risk_score(responses):
    """Calculate bite risk score from questionnaire responses"""
    # Scoring weights for each question
    score_map = {
        "aggression": {"Friendly/Calm": 0, "Neutral/Cautious": 5, "Defensive": 10, "Aggressive/Growling": 20,
                       "Attacking/Lunging": 30},
        "body_language": {"Relaxed (wagging tail, soft ears)": 0, "Alert (ears up, attentive)": 5,
                          "Tense (stiff body, raised hackles)": 15, "Cowering/Fearful": 10,
                          "Showing teeth/Snarling": 25},
        "eye_contact": {"Soft/Avoidant": 0, "Normal": 3, "Direct stare": 10, "Fixed stare with tension": 20},
        "territorial": {"Not territorial": 0, "Mild (barking)": 5, "Moderate (blocking path)": 10,
                        "Highly territorial (charging)": 20},
        "past_behavior": {"Never aggressive": 0, "Rare incidents": 10, "Multiple incidents": 20,
                          "Frequent attacks": 30},
        "approach": {"Friendly approach": 0, "Cautious but friendly": 3, "Avoidant/Backing away": 8,
                     "Warning signs (barking/growling)": 15, "Charging/Lunging": 25},
        "food_guarding": {"No guarding": 0, "Mild (tense when eating)": 5, "Moderate (growls near food)": 12,
                          "Severe (snaps/bites near food)": 20},
        "space": {"Comfortable with proximity": 0, "Prefers distance": 3, "Shows discomfort when approached": 10,
                  "Actively defends space": 18},
        "health": {"Appears healthy": 0, "Minor issues (limping)": 5, "Visible injuries": 10,
                   "Signs of rabies/severe illness": 25},
        "pack": {"Alone": 5, "With one other dog": 3, "In small pack (2-3)": 8, "Large pack (4+)": 15}
    }

    total_score = sum(score_map.get(key, {}).get(value, 0) for key, value in responses.items())

    # Determine risk level
    if total_score <= 20:
        risk_level = "Low Risk"
    elif total_score <= 50:
        risk_level = "Moderate Risk"
    elif total_score <= 80:
        risk_level = "High Risk"
    else:
        risk_level = "Critical Risk"

    return total_score, risk_level


def generate_safety_recommendations(responses):
    """Generate safety recommendations based on responses"""
    recommendations = []

    if responses.get("aggression") in ["Aggressive/Growling", "Attacking/Lunging"]:
        recommendations.append("🚨 Maintain safe distance - Do not approach")

    if responses.get("territorial") in ["Moderate (blocking path)", "Highly territorial (charging)"]:
        recommendations.append("🚶 Avoid entering the dog's territory - Choose alternate route")

    if responses.get("approach") in ["Warning signs (barking/growling)", "Charging/Lunging"]:
        recommendations.append("⛔ Do not attempt to pet or interact")

    if responses.get("health") == "Signs of rabies/severe illness":
        recommendations.append("⚠️ RABIES RISK - Contact health department immediately")

    if responses.get("pack") in ["In small pack (2-3)", "Large pack (4+)"]:
        recommendations.append("👥 Pack behavior increases unpredictability - Extra caution needed")

    if responses.get("food_guarding") in ["Moderate (growls near food)", "Severe (snaps/bites near food)"]:
        recommendations.append("🍖 Never approach when dog is eating or near food")

    return recommendations


# ---------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------
def render():
    """Main AI Detection page with tabs"""
    user_role = st.session_state.user.get("role")
    page_header("🧪", "AI Disease Detection & Bite Risk",
                "Advanced diagnostics powered by deep learning", user_role)

    # Create tabs
    tabs = st.tabs(["🔬 Disease Detection", "⚠️ Bite Risk Assessment", "📊 Analysis History"])

    reverse = get_reverse_geocoder()

    # ========== TAB 1: DISEASE DETECTION ==========
    with tabs[0]:
        left, right = st.columns([1, 1])

        with left:
            # Load model
            disease_model, disease_tfms, idx_to_class, device = load_pytorch_model()

            st.markdown("### Upload & Analyze")
            if disease_model is not None:
                st.success("✅ AI Model loaded successfully")
                st.caption(f"🎯 Model classes: {len(idx_to_class)}")
            else:
                st.error("❌ AI Model not loaded - using mock predictions")

            # Upload mode selection
            mode = st.radio("Upload Mode", ["Single Image", "Batch Upload (Multiple Dogs)"], horizontal=True)
            if mode == "Single Image":
                img_file = st.file_uploader("Upload Dog Image", type=["jpg", "jpeg", "png"], key="single_img")
                img_files = [img_file] if img_file else []
            else:
                img_files = st.file_uploader("Upload Multiple Images", type=["jpg", "jpeg", "png"],
                                             accept_multiple_files=True, key="batch_img")

            # ========== LOCATION INPUT SECTION ==========
            st.markdown("#### 📍 Location")

            # Load map utilities
            from utils.map_picker import create_location_picker, get_clicked_location
            from utils.free_maps import reverse_geocode

            col_loc1, col_loc2 = st.columns([2, 1])
            with col_loc1:
                location_mode = st.radio(
                    "Choose Location Input Mode",
                    ["Enter Manually", "Pick on Map / Use My GPS"],
                    horizontal=True
                )

            # Initialize session state for location
            if "last_geocoded_location" not in st.session_state:
                st.session_state.last_geocoded_location = None
            if "location_mode" not in st.session_state:
                st.session_state.location_mode = location_mode

            # Reset location if mode changes
            if st.session_state.location_mode != location_mode:
                st.session_state.location_mode = location_mode
                st.session_state.last_geocoded_location = None

            if location_mode == "Enter Manually":
                # Manual text input
                place_input = st.text_input("Enter location (address, landmark, area)",
                                            placeholder="e.g., Marina Beach, Chennai")

                if st.button("📍 Confirm Location", type="primary"):
                    if place_input.strip():
                        try:
                            with st.spinner("🌍 Geocoding location..."):
                                from utils.geo import geocode_place
                                coords = geocode_place(place_input)
                                if coords:
                                    st.session_state.last_geocoded_location = {
                                        "address": place_input,
                                        "coords": coords
                                    }
                                    st.success(f"✅ Location confirmed: {place_input}")
                                else:
                                    st.error("❌ Could not find location. Please try a different address.")
                        except Exception as e:
                            st.error(f"❌ Geocoding error: {e}")
                    else:
                        st.warning("⚠️ Please enter a location")

            else:  # Pick on Map / Use GPS
                st.info("👆 Click on the map to select a location, or click 'Use My Location' button")

                # Show location picker map
                clicked = create_location_picker(
                    default_lat=13.0827,
                    default_lon=80.2707,
                    zoom=11,
                    height=400,
                    label="Click to mark location",
                    enable_search=True,
                    enable_locate=True
                )

                # Get clicked location
                picked_loc = get_clicked_location(clicked)

                if picked_loc:
                    lat, lon = picked_loc
                    with st.spinner("📍 Getting address..."):
                        try:
                            addr = reverse_geocode(lat, lon)
                            st.session_state.last_geocoded_location = {
                                "address": addr or f"Location ({lat:.4f}, {lon:.4f})",
                                "coords": (lat, lon)
                            }
                        except:
                            st.session_state.last_geocoded_location = {
                                "address": f"Location ({lat:.4f}, {lon:.4f})",
                                "coords": (lat, lon)
                            }

            # Display confirmed location (✅ FIX: Added null check)
            if st.session_state.last_geocoded_location is not None:
                loc = st.session_state.last_geocoded_location
                st.markdown(f"""
                <div style="padding: 12px; background: rgba(51,65,85,0.3);
                            border-radius: 8px; margin-top: 8px;">
                    <div><strong>📍 Place:</strong> {loc.get('address', 'Unknown')}</div>
                    <div><strong>🧭 Coordinates:</strong> {loc.get('coords', [0, 0])[0]:.6f}, {loc.get('coords', [0, 0])[1]:.6f}</div>
                </div>
                """, unsafe_allow_html=True)

            # Symptom checklist
            with st.expander("📋 Symptom Checklist"):
                _ = st.selectbox("Visible Symptoms",
                                 ["Normal", "Red patches", "Hair loss", "Sores", "Scratching", "Lethargy"])
                ca, cb = st.columns(2)
                with ca:
                    appetite = st.checkbox("Reduced appetite")
                    scratching = st.checkbox("Excessive scratching")
                with cb:
                    spreading = st.checkbox("Infection spreading")
                    lethargy = st.checkbox("Lethargy/weakness")

            # Additional notes
            notes = st.text_area("📝 Additional Observations")

            # Validation
            can_analyze = bool(img_files and st.session_state.last_geocoded_location)
            if not img_files:
                st.warning("⚠️ Please upload at least one image")
            if not st.session_state.last_geocoded_location:
                st.warning("⚠️ Please enter a valid location")

            # Action buttons
            c1, c2 = st.columns(2)
            with c1:
                btn = st.button("🔬 Run AI Analysis", type="primary", use_container_width=True, disabled=not can_analyze)
            with c2:
                if st.button("🧹 Clear Results", type="secondary", use_container_width=True):
                    st.session_state.analysis_results = []
                    st.session_state.analyze_triggered = False
                    st.success("✅ Results cleared")

            # Initialize session state
            if "analysis_results" not in st.session_state:
                st.session_state.analysis_results = []
            if "analyze_triggered" not in st.session_state:
                st.session_state.analyze_triggered = False

            if btn:
                st.session_state.analyze_triggered = True
                st.session_state.analysis_results = []

        # ========== RIGHT COLUMN: RESULTS ==========
        with right:
            st.markdown("### Analysis Results")

            # Run analysis if triggered (✅ FIX: Added null check)
            if (st.session_state.get("analyze_triggered") and
                    img_files and
                    st.session_state.last_geocoded_location is not None):

                results = []
                loc = st.session_state.last_geocoded_location
                latlon = loc.get("coords", (0, 0))
                location_display = loc.get("address", "Unknown Location")

                pb = st.progress(0)
                status = st.empty()
                total = len(img_files)

                with st.spinner("🧠 AI Model analyzing..."):
                    for i, f in enumerate(img_files):
                        pb.progress((i + 1) / total)
                        status.text(f"Analyzing image {i + 1} of {total}...")

                        try:
                            img = Image.open(f).convert("RGB")
                        except Exception:
                            st.error(f"❌ Could not read image {getattr(f, 'name', i + 1)}. Skipping.")
                            continue

                        st.image(img, caption=f"Image {i + 1}: {getattr(f, 'name', 'Uploaded')}",
                                 use_container_width=True)
                        pred, conf, all_probs, base_sev = predict_disease(img, disease_model, disease_tfms,
                                                                          idx_to_class, device)

                        # Calculate severity with symptoms
                        sev_score = base_sev
                        if appetite:
                            sev_score += 5
                        if scratching:
                            sev_score += 5
                        if spreading:
                            sev_score += 10
                        if lethargy:
                            sev_score += 8

                        sev_label, sev_num = severity_from_score(sev_score, pred)

                        results.append({
                            "image_name": getattr(f, 'name', f"Image {i + 1}"),
                            "prediction": pred,
                            "confidence": conf,
                            "severity": sev_label,
                            "severity_num": sev_num,
                            "all_probabilities": all_probs,
                            "severity_score": sev_score
                        })

                pb.empty()
                status.empty()

                st.session_state.analysis_results = results

                # ========== SAVE TO DATABASE WITH FIXED FIELD NAMES ==========
                cases = storage.read("cases", [])
                if not isinstance(cases, list):
                    cases = []

                hotspots = storage.read("hotspots", [])
                if not isinstance(hotspots, list):
                    hotspots = []

                # ✅ Disease colors for hotspot mapping
                disease_colors = {
                    "ringworm": "#ef4444",  # Red
                    "demodicosis": "#dc2626",  # Dark Red
                    "fungal_infections": "#eab308",  # Yellow
                    "dermatitis": "#3b82f6",  # Blue
                    "hypersensitivity": "#10b981",  # Green
                    "healthy": "#64748b"  # Gray
                }

                created_c = 0
                created_h = 0

                for r in results:
                    # Create case ID
                    cid = f"CS-{int(dt.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}"

                    # Build case record
                    case = {
                        "id": cid,
                        "disease": r["prediction"],  # ✅ FIXED: Using "disease" for consistency
                        "analyzed_by": st.session_state.user.get("name"),
                        "confidence": r["confidence"],
                        "severity": r["severity"],
                        "severity_num": r["severity_num"],
                        "place": location_display,
                        "coords": latlon,
                        "time": str(dt.datetime.now()),
                        "notes": notes
                    }
                    cases.append(case)
                    created_c += 1

                    # Create hotspot if not healthy
                    if r["prediction"] != "healthy":
                        hid = f"HS-{int(dt.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}"
                        color = disease_colors.get(r["prediction"], "#64748b")

                        hotspot = {
                            "id": hid,
                            "disease_type": r["prediction"],  # Hotspots use disease_type
                            "lat": latlon[0],
                            "lon": latlon[1],
                            "risk": min(100, int(r["confidence"] * 100)),
                            "confidence": r["confidence"],
                            "cases": 1,
                            "color": color,
                            "place": location_display,
                            "severity": r["severity"],
                            "severity_num": r["severity_num"],
                            "time": str(dt.datetime.now()),
                            "created_at": str(dt.datetime.now()),
                            "reported_by": st.session_state.user.get("name"),
                            "category": "Disease",
                            "label": f"{r['prediction'].replace('_', ' ').title()}"
                        }
                        hotspots.append(hotspot)
                        created_h += 1

                # Save to storage
                storage.write("cases", cases)
                storage.write("hotspots", hotspots)

                # ✅ CRITICAL FIX: Set analyze_triggered to False AFTER saving to database
                # This prevents the analysis from running multiple times and creating duplicates
                st.session_state.analyze_triggered = False

            # ========== DISPLAY RESULTS (SEPARATE FROM ANALYSIS TRIGGER) ==========
            # This section runs independently and checks if results exist
            if st.session_state.analysis_results:
                results = st.session_state.analysis_results

                # ✅ FIX: Added null check for location address
                location_address = "Unknown"
                if st.session_state.last_geocoded_location is not None:
                    location_address = st.session_state.last_geocoded_location.get('address', 'Unknown')

                st.success(f"""
                ✅ **Analysis Complete!**
                - Created {len(results)} case(s)
                - Created {len([r for r in results if r['prediction'] != 'healthy'])} hotspot(s)
                - Location: {location_address}

                ➡️ View on **Hotspot Mapping** page
                """)

                # Display detailed results
                for idx, r in enumerate(results, 1):
                    st.markdown(f"---\n**Result {idx}: {r['prediction'].upper()}**")
                    st.markdown(confidence_bar(r['confidence'] * 100), unsafe_allow_html=True)
                    st.markdown(severity_badge(r['severity']), unsafe_allow_html=True)

                    with st.expander("View Probabilities"):
                        for disease, prob in sorted(r['all_probabilities'].items(), key=lambda x: x[1], reverse=True):
                            st.write(f"{disease}: {prob * 100:.1f}%")
            else:
                st.info("📤 Upload images and click 'Run AI Analysis' to see results")

    # ========== TAB 2: BITE RISK ASSESSMENT - FULLY FUNCTIONAL ==========
    with tabs[1]:
        st.markdown("### ⚠️ Bite Risk Assessment")
        st.info("📋 Complete the behavioral assessment questionnaire below to evaluate bite risk")

        # Initialize session state for bite risk assessment
        if "bite_risk_results" not in st.session_state:
            st.session_state.bite_risk_results = None

        # ========== LOCATION INPUT SECTION (SAME AS DISEASE DETECTION) ==========
        st.markdown("#### 📍 Location")

        # Load map utilities
        from utils.map_picker import create_location_picker, get_clicked_location
        from utils.free_maps import reverse_geocode

        col_loc1, col_loc2 = st.columns([2, 1])
        with col_loc1:
            bite_location_mode = st.radio(
                "Choose Location Input Mode",
                ["Enter Manually", "Pick on Map / Use My GPS"],
                horizontal=True,
                key="bite_location_mode"
            )

        # Initialize session state for bite risk location
        if "bite_last_geocoded_location" not in st.session_state:
            st.session_state.bite_last_geocoded_location = None
        if "bite_location_mode_state" not in st.session_state:
            st.session_state.bite_location_mode_state = bite_location_mode

        # Reset location if mode changes
        if st.session_state.bite_location_mode_state != bite_location_mode:
            st.session_state.bite_location_mode_state = bite_location_mode
            st.session_state.bite_last_geocoded_location = None

        if bite_location_mode == "Enter Manually":
            # Manual text input
            bite_place_input = st.text_input("Enter location (address, landmark, area)",
                                             placeholder="e.g., Park Street, Near School",
                                             key="bite_place_input")

            if st.button("📍 Confirm Bite Risk Location", type="primary", key="confirm_bite_location"):
                if bite_place_input.strip():
                    try:
                        with st.spinner("🌍 Geocoding location..."):
                            from utils.geo import geocode_place
                            coords = geocode_place(bite_place_input)
                            if coords:
                                st.session_state.bite_last_geocoded_location = {
                                    "address": bite_place_input,
                                    "coords": coords
                                }
                                st.success(f"✅ Location confirmed: {bite_place_input}")
                            else:
                                st.error("❌ Could not find location. Please try a different address.")
                    except Exception as e:
                        st.error(f"❌ Geocoding error: {e}")
                else:
                    st.warning("⚠️ Please enter a location")

        else:  # Pick on Map / Use GPS
            st.info("👆 Click on the map to select a location, or click 'Use My Location' button")

            # Show location picker map
            bite_clicked = create_location_picker(
                default_lat=13.0827,
                default_lon=80.2707,
                zoom=11,
                height=400,
                label="Click to mark bite risk location",
                enable_search=True,
                enable_locate=True
            )

            # Get clicked location
            bite_picked_loc = get_clicked_location(bite_clicked)

            if bite_picked_loc:
                lat, lon = bite_picked_loc
                with st.spinner("📍 Getting address..."):
                    try:
                        addr = reverse_geocode(lat, lon)
                        st.session_state.bite_last_geocoded_location = {
                            "address": addr or f"Location ({lat:.4f}, {lon:.4f})",
                            "coords": (lat, lon)
                        }
                    except:
                        st.session_state.bite_last_geocoded_location = {
                            "address": f"Location ({lat:.4f}, {lon:.4f})",
                            "coords": (lat, lon)
                        }

        # Display confirmed location
        if st.session_state.bite_last_geocoded_location is not None:
            loc = st.session_state.bite_last_geocoded_location
            st.markdown(f"""
            <div style="padding: 12px; background: rgba(51,65,85,0.3);
                        border-radius: 8px; margin-top: 8px;">
                <div><strong>📍 Place:</strong> {loc.get('address', 'Unknown')}</div>
                <div><strong>🧭 Coordinates:</strong> {loc.get('coords', [0, 0])[0]:.6f}, {loc.get('coords', [0, 0])[1]:.6f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔍 Behavioral Assessment Questionnaire")
        st.caption("Answer the following questions based on your observation of the dog")

        # Create two columns for questions
        col1, col2 = st.columns(2)

        with col1:
            # Question 1: Aggression Level
            q1 = st.selectbox(
                "1️⃣ Overall Aggression Level",
                ["Friendly/Calm", "Neutral/Cautious", "Defensive", "Aggressive/Growling", "Attacking/Lunging"],
                help="How would you describe the dog's general demeanor?"
            )

            # Question 2: Body Language
            q2 = st.selectbox(
                "2️⃣ Body Language",
                ["Relaxed (wagging tail, soft ears)", "Alert (ears up, attentive)",
                 "Tense (stiff body, raised hackles)", "Cowering/Fearful", "Showing teeth/Snarling"],
                help="What is the dog's body posture?"
            )

            # Question 3: Eye Contact
            q3 = st.selectbox(
                "3️⃣ Eye Contact Pattern",
                ["Soft/Avoidant", "Normal", "Direct stare", "Fixed stare with tension"],
                help="How does the dog make eye contact?"
            )

            # Question 4: Territorial Behavior
            q4 = st.selectbox(
                "4️⃣ Territorial Behavior",
                ["Not territorial", "Mild (barking)", "Moderate (blocking path)", "Highly territorial (charging)"],
                help="How does the dog respond to people entering its area?"
            )

            # Question 5: Past Behavior
            q5 = st.selectbox(
                "5️⃣ Past Aggressive Incidents",
                ["Never aggressive", "Rare incidents", "Multiple incidents", "Frequent attacks"],
                help="History of aggression (if known)"
            )

        with col2:
            # Question 6: Approach Response
            q6 = st.selectbox(
                "6️⃣ Response to Human Approach",
                ["Friendly approach", "Cautious but friendly", "Avoidant/Backing away",
                 "Warning signs (barking/growling)", "Charging/Lunging"],
                help="How does the dog react when people approach?"
            )

            # Question 7: Food Guarding
            q7 = st.selectbox(
                "7️⃣ Food Guarding Behavior",
                ["No guarding", "Mild (tense when eating)", "Moderate (growls near food)",
                 "Severe (snaps/bites near food)"],
                help="Does the dog guard food or resources?"
            )

            # Question 8: Personal Space
            q8 = st.selectbox(
                "8️⃣ Personal Space Preference",
                ["Comfortable with proximity", "Prefers distance", "Shows discomfort when approached",
                 "Actively defends space"],
                help="How does the dog feel about personal space?"
            )

            # Question 9: Health Status
            q9 = st.selectbox(
                "9️⃣ Health Status",
                ["Appears healthy", "Minor issues (limping)", "Visible injuries",
                 "Signs of rabies/severe illness"],
                help="Visible health conditions?"
            )

            # Question 10: Pack Behavior
            q10 = st.selectbox(
                "🔟 Pack Status",
                ["Alone", "With one other dog", "In small pack (2-3)", "Large pack (4+)"],
                help="Is the dog alone or with other dogs?"
            )

        # Additional Notes
        st.markdown("---")
        bite_notes = st.text_area("📝 Additional Observations", placeholder="Any other relevant details...")

        # Validation
        can_assess = bool(st.session_state.bite_last_geocoded_location)
        if not st.session_state.bite_last_geocoded_location:
            st.warning("⚠️ Please select/confirm a location before assessing risk")

        # Submit Assessment
        if st.button("📊 Calculate Bite Risk", type="primary", use_container_width=True, disabled=not can_assess):
            # Get location details
            bite_loc = st.session_state.bite_last_geocoded_location
            bite_location = bite_loc.get("address", "Unknown Location")
            bite_coords = bite_loc.get("coords", (0, 0))

            # Collect all responses
            responses = {
                "aggression": q1,
                "body_language": q2,
                "eye_contact": q3,
                "territorial": q4,
                "past_behavior": q5,
                "approach": q6,
                "food_guarding": q7,
                "space": q8,
                "health": q9,
                "pack": q10
            }

            # Calculate risk score
            risk_score, risk_level = calculate_bite_risk_score(responses)

            # Generate recommendations
            recommendations = generate_safety_recommendations(responses)

            # Store results
            st.session_state.bite_risk_results = {
                "score": risk_score,
                "level": risk_level,
                "responses": responses,
                "recommendations": recommendations,
                "location": bite_location,
                "coords": bite_coords,
                "notes": bite_notes,
                "timestamp": str(dt.datetime.now())
            }

            # Save to database
            bite_assessments = storage.read("bite_assessments", [])
            if not isinstance(bite_assessments, list):
                bite_assessments = []

            assessment_id = f"BR-{int(dt.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}"
            assessment = {
                "id": assessment_id,
                "location": bite_location,
                "coords": bite_coords,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "responses": responses,
                "notes": bite_notes,
                "assessed_by": st.session_state.user.get("name"),
                "timestamp": str(dt.datetime.now())
            }
            bite_assessments.append(assessment)
            storage.write("bite_assessments", bite_assessments)

            # ✅ CREATE HOTSPOT FOR ALL RISK LEVELS (with different colors)
            hotspots = storage.read("hotspots", [])
            if not isinstance(hotspots, list):
                hotspots = []

            # Determine hotspot color based on risk level
            hotspot_colors = {
                "Low Risk": "#10b981",  # Green
                "Moderate Risk": "#3b82f6",  # Blue
                "High Risk": "#f59e0b",  # Orange
                "Critical Risk": "#ef4444"  # Red
            }
            hotspot_color = hotspot_colors.get(risk_level, "#6b7280")

            # Create hotspot using the already geocoded coordinates
            hotspot_id = f"HS-{int(dt.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}"
            hotspot = {
                "id": hotspot_id,
                "lat": bite_coords[0],
                "lon": bite_coords[1],
                "risk": risk_score,
                "risk_score": risk_score,
                "cases": 1,
                "color": hotspot_color,
                "place": bite_location,
                "time": str(dt.datetime.now()),
                "created_at": str(dt.datetime.now()),
                "reported_by": st.session_state.user.get("name"),
                "category": "Bite Risk",
                "label": f"Bite Risk: {risk_level}"
            }
            hotspots.append(hotspot)
            storage.write("hotspots", hotspots)

            st.success("✅ Risk assessment complete and hotspot created! See results below.")

        # Display results if available
        if st.session_state.bite_risk_results:
            st.markdown("---")
            st.markdown("### 📊 Risk Assessment Results")

            result = st.session_state.bite_risk_results

            # Display risk level badge
            st.markdown(risk_level_badge(result["level"]), unsafe_allow_html=True)

            # Risk score visualization
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Score", f"{result['score']}/100")
            with col2:
                st.metric("Risk Level", result["level"])
            with col3:
                # Display location properly
                location_display = result.get("location", "Unknown")
                st.metric("Location", location_display if len(location_display) < 20 else location_display[:17] + "...")

            # Show full location if truncated
            if len(result.get("location", "")) >= 20:
                st.caption(f"📍 Full Location: {result.get('location', 'Unknown')}")

            # Show coordinates if available
            if result.get("coords"):
                coords = result["coords"]
                st.caption(f"🧭 Coordinates: {coords[0]:.6f}, {coords[1]:.6f}")

            # Risk score bar
            score_pct = min(100, result['score'])
            if score_pct <= 20:
                bar_color = "#10b981"
            elif score_pct <= 50:
                bar_color = "#f59e0b"
            else:
                bar_color = "#ef4444"

            st.markdown(f"""
            <div style="padding: 16px; background: rgba(51, 65, 85, 0.3);
                        border-radius: 12px; margin: 16px 0;">
                <div style="font-size: 14px; margin-bottom: 8px;">
                    Risk Score: <strong>{score_pct}/100</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: {bar_color}; width: {score_pct}%; height: 100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Recommendations
            st.markdown("### 💡 Safety Recommendations")
            for rec in result["recommendations"]:
                st.markdown(f"- {rec}")

            # Response summary
            with st.expander("📋 View Full Assessment Details"):
                st.markdown("**Assessment Responses:**")
                for key, value in result["responses"].items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")

                if result["notes"]:
                    st.markdown("**Additional Notes:**")
                    st.write(result["notes"])

                st.caption(f"Assessed at: {result['timestamp'][:19]}")

            # Clear button
            if st.button("🔄 New Assessment", use_container_width=True):
                st.session_state.bite_risk_results = None
                st.rerun()

    # ========== TAB 3: ANALYSIS HISTORY + CSV EXPORT ==========
    with tabs[2]:
        st.markdown("### 📊 Analysis History")

        # Tabs for disease and bite risk history
        history_tabs = st.tabs(["🔬 Disease Cases", "⚠️ Bite Risk Assessments"])

        with history_tabs[0]:
            cases = storage.read("cases", [])
            if not isinstance(cases, list):
                cases = []

            me = st.session_state.user.get("name")
            my_cases = [c for c in cases if c.get("analyzed_by") == me]

            if my_cases:
                st.success(f"You have analyzed {len(my_cases)} disease cases")

                recent = sorted(my_cases, key=lambda x: x.get("time", ""), reverse=True)[:20]

                for c in recent:
                    sev_color = {
                        "Mild": "#10b981",
                        "Moderate": "#f59e0b",
                        "Severe": "#ef4444"
                    }.get(c.get("severity", "Mild"), "#6366f1")

                    # ✅ FIX: Check both 'disease_type' (new) and 'disease' (old) for backwards compatibility
                    disease_name = c.get('disease_type') or c.get('disease', 'Unknown')

                    st.markdown(f"""
                       <div style="padding: 16px; background: rgba(51,65,85,0.3);
                                   border-left: 4px solid {sev_color}; border-radius: 8px; margin-bottom: 12px;">
                           <strong>{c.get('id', 'N/A')}</strong> — {disease_name.replace('_', ' ').title()}<br>
                           <span style="color: #94a3b8; font-size: 13px;">
                               📍 {c.get('place', 'Unknown')} • 🕐 {c.get('time', '')[:16]} • 
                               Confidence: {float(c.get('confidence', 0)) * 100:.1f}%
                           </span>
                       </div>
                       """, unsafe_allow_html=True)

                # CSV Export
                st.markdown("### 📥 Export Disease Cases")
                df = pd.DataFrame(my_cases)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Disease Cases as CSV",
                    csv,
                    file_name=f"{me.replace(' ', '_')}_disease_cases.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.info("No disease analysis history yet. Start by analyzing some images!")

        with history_tabs[1]:
            bite_assessments = storage.read("bite_assessments", [])
            if not isinstance(bite_assessments, list):
                bite_assessments = []

            me = st.session_state.user.get("name")
            my_assessments = [a for a in bite_assessments if a.get("assessed_by") == me]

            if my_assessments:
                st.success(f"You have completed {len(my_assessments)} bite risk assessments")

                recent = sorted(my_assessments, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]

                for a in recent:
                    risk_colors = {
                        "Low Risk": "#10b981",
                        "Moderate Risk": "#f59e0b",
                        "High Risk": "#ef4444",
                        "Critical Risk": "#dc2626"
                    }
                    risk_color = risk_colors.get(a.get("risk_level", "Low Risk"), "#6366f1")

                    st.markdown(f"""
                       <div style="padding: 16px; background: rgba(51,65,85,0.3);
                                   border-left: 4px solid {risk_color}; border-radius: 8px; margin-bottom: 12px;">
                           <strong>{a.get('id', 'N/A')}</strong> — {a.get('risk_level', 'Unknown')}<br>
                           <span style="color: #94a3b8; font-size: 13px;">
                               📍 {a.get('location', 'Unknown')} • 🕐 {a.get('timestamp', '')[:16]} • 
                               Score: {a.get('risk_score', 0)}/100
                           </span>
                       </div>
                       """, unsafe_allow_html=True)

                # CSV Export
                st.markdown("### 📥 Export Bite Risk Assessments")
                df = pd.DataFrame(my_assessments)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Bite Risk Assessments as CSV",
                    csv,
                    file_name=f"{me.replace(' ', '_')}_bite_risk_assessments.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.info("No bite risk assessment history yet. Complete an assessment to get started!")


if __name__ == "__main__":
    render()
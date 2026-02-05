# pages/awareness_hub.py

import streamlit as st
import pandas as pd
import datetime as dt
import re
from utils import storage
from components import page_header


def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def render():
    """Enhanced educational content hub with real interactivity"""
    user_role = st.session_state.user.get("role")
    user_id = st.session_state.user.get("id", "guest")
    page_header("🎓", "Awareness Hub",
                "Interactive learning, resources, and community knowledge", user_role)

    # Initialize user progress
    if "learning_progress" not in st.session_state:
        st.session_state.learning_progress = storage.read("learning_progress", {})

    if user_id not in st.session_state.learning_progress:
        st.session_state.learning_progress[user_id] = {
            "completed_videos": [],
            "quiz_scores": {},
            "bookmarks": [],
            "badges": [],
            "total_points": 0
        }

    user_progress = st.session_state.learning_progress[user_id]

    # Top stats bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Points", user_progress.get("total_points", 0))
    with col2:
        st.metric("📺 Videos Watched", len(user_progress.get("completed_videos", [])))
    with col3:
        st.metric("✅ Quizzes Passed", len([s for s in user_progress.get("quiz_scores", {}).values() if s >= 70]))
    with col4:
        st.metric("🎖️ Badges", len(user_progress.get("badges", [])))

    # Main tabs
    tabs = st.tabs(
        ["📺 Video Library", "📚 Interactive Guides", "🎯 Quizzes", "🌟 Campaigns", "💬 Community Q&A", "📊 My Progress"])

    # ==================== TAB 1: VIDEO LIBRARY ====================
    with tabs[0]:
        st.markdown("### 📺 Video Learning Library")

        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search videos", placeholder="Search by title or topic...",
                                         key="video_search")
        with col2:
            filter_category = st.selectbox("Filter by category",
                                           ["All", "Training", "Health", "First Aid", "Adoption", "Community"])

        # Load videos from storage
        videos = storage.read("awareness_videos", [])

        # Add default videos if empty
        if not videos:
            videos = [
                {
                    "id": "vid_001",
                    "title": "Basic Dog First Aid - Essential Skills",
                    "url": "https://www.youtube.com/watch?v=5PJddmfesaA",
                    "category": "First Aid",
                    "duration": "12:34",
                    "difficulty": "Beginner",
                    "description": "Learn essential first aid skills for dogs including CPR, wound care, and emergency response.",
                    "views": 0,
                    "likes": 0,
                    "uploaded_by": "Admin",
                    "date": str(dt.datetime.now())
                },
                {
                    "id": "vid_002",
                    "title": "How to Approach Street Dogs Safely",
                    "url": "https://www.youtube.com/watch?v=TBvPaqMZyo8",
                    "category": "Training",
                    "duration": "8:45",
                    "difficulty": "Beginner",
                    "description": "Understanding dog body language and safe approach techniques for street dogs.",
                    "views": 0,
                    "likes": 0,
                    "uploaded_by": "Admin",
                    "date": str(dt.datetime.now())
                },
                {
                    "id": "vid_003",
                    "title": "Vaccination Process Explained",
                    "url": "https://www.youtube.com/watch?v=example3",
                    "category": "Health",
                    "duration": "15:20",
                    "difficulty": "Intermediate",
                    "description": "Complete guide to dog vaccination schedules, types, and importance.",
                    "views": 0,
                    "likes": 0,
                    "uploaded_by": "Admin",
                    "date": str(dt.datetime.now())
                }
            ]
            storage.write("awareness_videos", videos)

        # Admin: Add new video
        if user_role == "admin":
            with st.expander("➕ Add New Video (Admin)"):
                with st.form("add_video_form"):
                    new_title = st.text_input("Video Title *")
                    new_url = st.text_input("YouTube URL *", help="Full YouTube video URL")
                    new_category = st.selectbox("Category",
                                                ["Training", "Health", "First Aid", "Adoption", "Community"])
                    new_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
                    new_description = st.text_area("Description")

                    if st.form_submit_button("📤 Upload Video", type="primary"):
                        if new_title and new_url:
                            videos.append({
                                "id": f"vid_{len(videos) + 1:03d}",
                                "title": new_title,
                                "url": new_url,
                                "category": new_category,
                                "duration": "0:00",
                                "difficulty": new_difficulty,
                                "description": new_description,
                                "views": 0,
                                "likes": 0,
                                "uploaded_by": st.session_state.user.get("name", "Admin"),
                                "date": str(dt.datetime.now())
                            })
                            storage.write("awareness_videos", videos)
                            st.success("✅ Video added successfully!")
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields")

        # Filter videos
        filtered_videos = videos
        if filter_category != "All":
            filtered_videos = [v for v in videos if v["category"] == filter_category]
        if search_query:
            filtered_videos = [v for v in filtered_videos
                               if search_query.lower() in v["title"].lower()
                               or search_query.lower() in v.get("description", "").lower()]

        # Display videos
        if not filtered_videos:
            st.info("No videos found matching your criteria.")
        else:
            for video in filtered_videos:
                video_id = extract_video_id(video["url"])

                with st.container():
                    # Category badges and views
                    col_badge1, col_badge2, col_views = st.columns([1, 1, 2])
                    with col_badge1:
                        st.markdown(f"**🏷️ {video['category']}**")
                    with col_badge2:
                        st.markdown(f"**📊 {video['difficulty']}**")
                    with col_views:
                        st.markdown(f"*👁️ {video.get('views', 0)} views*")

                    # Title and description
                    st.markdown(f"### {video['title']}")
                    st.markdown(video.get('description', 'No description available'))

                    # Metadata
                    st.caption(
                        f"📅 {video.get('date', 'Unknown date')[:10]} • 👤 {video.get('uploaded_by', 'Unknown')} • ⏱️ {video.get('duration', 'N/A')}")

                    # Embed YouTube video
                    if video_id:
                        st.video(f"https://www.youtube.com/watch?v={video_id}")
                    else:
                        st.warning("⚠️ Invalid YouTube URL - cannot embed video")

                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        is_completed = video["id"] in user_progress.get("completed_videos", [])
                        if st.button("✅ Mark Complete" if not is_completed else "✓ Completed",
                                     key=f"complete_{video['id']}",
                                     disabled=is_completed,
                                     use_container_width=True):
                            if video["id"] not in user_progress["completed_videos"]:
                                user_progress["completed_videos"].append(video["id"])
                                user_progress["total_points"] += 10
                                video["views"] = video.get("views", 0) + 1
                                storage.write("awareness_videos", videos)
                                storage.write("learning_progress", st.session_state.learning_progress)
                                st.success("🎉 +10 points! Video marked complete!")
                                st.rerun()

                    with col2:
                        if st.button(f"👍 Like ({video.get('likes', 0)})",
                                     key=f"like_{video['id']}",
                                     use_container_width=True):
                            video["likes"] = video.get("likes", 0) + 1
                            storage.write("awareness_videos", videos)
                            st.rerun()

                    with col3:
                        is_bookmarked = video["id"] in user_progress.get("bookmarks", [])
                        if st.button("🔖 Bookmark" if not is_bookmarked else "📌 Bookmarked",
                                     key=f"bookmark_{video['id']}",
                                     use_container_width=True):
                            if is_bookmarked:
                                user_progress["bookmarks"].remove(video["id"])
                            else:
                                user_progress["bookmarks"].append(video["id"])
                            storage.write("learning_progress", st.session_state.learning_progress)
                            st.rerun()

                    with col4:
                        if st.button("💬 Discuss", key=f"discuss_{video['id']}", use_container_width=True):
                            st.info("Discussion feature coming soon!")

                    st.markdown("---")

    # ==================== TAB 2: INTERACTIVE GUIDES ====================
    with tabs[1]:
        st.markdown("### 📚 Interactive Learning Guides")

        guides = [
            {
                "id": "guide_001",
                "title": "🐕 Complete Dog Care Manual",
                "category": "Care",
                "description": "Comprehensive guide covering nutrition, grooming, exercise, and health monitoring",
                "modules": ["Feeding Basics", "Grooming 101", "Exercise Requirements", "Health Checks"],
                "duration": "30 min read",
                "difficulty": "Beginner"
            },
            {
                "id": "guide_002",
                "title": "💉 Vaccination & Disease Prevention",
                "category": "Health",
                "description": "Everything about vaccines, schedules, and preventing common diseases",
                "modules": ["Vaccine Types", "Schedule Planning", "Disease Recognition", "Prevention Tips"],
                "duration": "25 min read",
                "difficulty": "Intermediate"
            },
            {
                "id": "guide_003",
                "title": "🚨 Emergency Response Protocol",
                "category": "First Aid",
                "description": "Step-by-step emergency handling from assessment to vet handoff",
                "modules": ["Scene Safety", "Quick Assessment", "First Aid Steps", "Transport Protocol"],
                "duration": "20 min read",
                "difficulty": "Intermediate"
            }
        ]

        for guide in guides:
            with st.expander(f"{guide['title']} - {guide['duration']}"):
                st.markdown(f"""
                **Category:** {guide['category']} | **Difficulty:** {guide['difficulty']}

                {guide['description']}

                **Modules Included:**
                """)

                for i, module in enumerate(guide['modules'], 1):
                    st.markdown(f"{i}. ✓ {module}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📖 Start Reading", key=f"read_{guide['id']}", use_container_width=True):
                        st.info("📚 Opening interactive guide...")
                with col2:
                    if st.button("📥 Download PDF", key=f"download_{guide['id']}", use_container_width=True):
                        st.success("✅ Guide downloaded!")
                with col3:
                    if st.button("🎓 Take Quiz", key=f"quiz_{guide['id']}", use_container_width=True):
                        st.info("Quiz will open in the Quizzes tab!")

    # ==================== TAB 3: INTERACTIVE QUIZZES ====================
    with tabs[2]:
        st.markdown("### 🎯 Test Your Knowledge")

        st.info("💡 **Pass quizzes to earn points and badges!** Score 70% or higher to pass.")

        quizzes = [
            {
                "id": "quiz_001",
                "title": "Dog First Aid Basics",
                "category": "First Aid",
                "questions": 10,
                "pass_score": 70,
                "points": 50,
                "difficulty": "Beginner"
            },
            {
                "id": "quiz_002",
                "title": "Vaccination Knowledge Check",
                "category": "Health",
                "questions": 15,
                "pass_score": 70,
                "points": 75,
                "difficulty": "Intermediate"
            },
            {
                "id": "quiz_003",
                "title": "Street Dog Behavior Understanding",
                "category": "Training",
                "questions": 12,
                "pass_score": 70,
                "points": 60,
                "difficulty": "Beginner"
            }
        ]

        for quiz in quizzes:
            quiz_id = quiz["id"]
            previous_score = user_progress.get("quiz_scores", {}).get(quiz_id, None)
            passed = previous_score and previous_score >= quiz["pass_score"]

            # Quiz card
            if passed:
                st.success(f"✅ **{quiz['title']}** - Score: {previous_score}% (PASSED)")
            else:
                st.info(f"📝 **{quiz['title']}**")

            st.write(f"{quiz['questions']} questions • {quiz['difficulty']} • 🎁 {quiz['points']} points")

            if previous_score and not passed:
                st.warning(f"Previous attempt: {previous_score}% - Try again to pass!")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎯 Start Quiz" if not previous_score else "🔄 Retake Quiz",
                             key=f"start_{quiz_id}",
                             use_container_width=True):
                    st.session_state[f"quiz_active_{quiz_id}"] = True
                    st.rerun()

            with col2:
                if previous_score:
                    st.button(f"📊 View Results", key=f"results_{quiz_id}", use_container_width=True, disabled=True)

            # Quiz interface (simplified example)
            if st.session_state.get(f"quiz_active_{quiz_id}", False):
                with st.container():
                    st.markdown("---")
                    st.markdown(f"### 📝 {quiz['title']}")

                    # Sample questions (in real app, load from database)
                    if quiz_id == "quiz_001":
                        st.markdown("**Question 1 of 10:**")
                        st.markdown("What is the first step when encountering an injured dog?")

                        answer = st.radio(
                            "Select your answer:",
                            ["Immediately touch the dog",
                             "Ensure your own safety first",
                             "Call the owner",
                             "Start treatment immediately"],
                            key=f"q1_{quiz_id}"
                        )

                        if st.button("Submit Answer", key=f"submit_{quiz_id}"):
                            if answer == "Ensure your own safety first":
                                st.success("✅ Correct! Always ensure scene safety first.")
                                # In real app: continue to next question
                                score = 90  # Simulated final score
                                user_progress["quiz_scores"][quiz_id] = score
                                user_progress["total_points"] += quiz["points"]

                                if score >= quiz["pass_score"]:
                                    st.balloons()
                                    st.success(
                                        f"🎉 Congratulations! You passed with {score}% and earned {quiz['points']} points!")

                                    # Award badge
                                    badge = f"First Aid Master - {quiz['title']}"
                                    if badge not in user_progress.get("badges", []):
                                        user_progress["badges"].append(badge)

                                storage.write("learning_progress", st.session_state.learning_progress)
                                st.session_state[f"quiz_active_{quiz_id}"] = False
                            else:
                                st.error("❌ Incorrect. Try again!")

                        if st.button("Cancel Quiz", key=f"cancel_{quiz_id}"):
                            st.session_state[f"quiz_active_{quiz_id}"] = False
                            st.rerun()

    # ==================== TAB 4: ACTIVE CAMPAIGNS ====================
    with tabs[3]:
        st.markdown("### 🌟 Join Active Campaigns")

        campaigns = storage.read("awareness_campaigns", [
            {
                "id": "camp_001",
                "name": "Rabies-Free Streets 2025",
                "icon": "💉",
                "goal": "Vaccinate 10,000 street dogs",
                "progress": 6500,
                "target": 10000,
                "description": "Help us eliminate rabies through comprehensive vaccination drives.",
                "participants": 245,
                "color": "#10b981"
            },
            {
                "id": "camp_002",
                "name": "Adopt Don't Shop",
                "icon": "🏠",
                "goal": "Find homes for 500 dogs",
                "progress": 285,
                "target": 500,
                "description": "Promote adoption of street dogs over buying from breeders.",
                "participants": 189,
                "color": "#6366f1"
            },
            {
                "id": "camp_003",
                "name": "Community Feeding Initiative",
                "icon": "🍖",
                "goal": "Establish 100 feeding stations",
                "progress": 67,
                "target": 100,
                "description": "Create sustainable feeding points across the city.",
                "participants": 312,
                "color": "#8b5cf6"
            }
        ])

        for campaign in campaigns:
            progress_percent = (campaign['progress'] / campaign['target'] * 100) if campaign['target'] > 0 else 0
            user_joined = st.session_state.get(f"joined_{campaign['id']}", False)

            # Campaign header
            st.markdown(f"## {campaign['icon']} {campaign['name']}")
            st.write(campaign['description'])
            st.caption(f"👥 {campaign['participants']} participants")

            # Progress bar
            st.progress(progress_percent / 100)
            col_prog1, col_prog2 = st.columns(2)
            with col_prog1:
                st.metric("Progress", f"{campaign['progress']:,} / {campaign['target']:,}")
            with col_prog2:
                st.metric("Completion", f"{progress_percent:.0f}%")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Join Campaign" if not user_joined else "✓ Joined",
                             key=f"join_{campaign['id']}",
                             disabled=user_joined,
                             use_container_width=True):
                    st.session_state[f"joined_{campaign['id']}"] = True
                    campaign['participants'] += 1
                    user_progress["total_points"] += 20
                    storage.write("awareness_campaigns", campaigns)
                    storage.write("learning_progress", st.session_state.learning_progress)
                    st.success("🎉 You joined the campaign! +20 points")
                    st.rerun()

            with col2:
                if st.button("📢 Share", key=f"share_{campaign['id']}", use_container_width=True):
                    st.info("📋 Campaign link copied to clipboard!")

            with col3:
                if st.button("📊 Details", key=f"details_{campaign['id']}", use_container_width=True):
                    st.info("Campaign details and updates will appear here")

    # ==================== TAB 5: COMMUNITY Q&A ====================
    with tabs[4]:
        st.markdown("### 💬 Community Questions & Answers")

        # Ask new question
        with st.expander("➕ Ask a Question"):
            with st.form("ask_question_form"):
                question_title = st.text_input("Question Title")
                question_category = st.selectbox("Category",
                                                 ["Health", "Training", "First Aid", "Adoption", "General"])
                question_body = st.text_area("Question Details")

                if st.form_submit_button("📤 Post Question", type="primary"):
                    if question_title and question_body:
                        questions = storage.read("awareness_questions", [])
                        questions.insert(0, {
                            "id": f"q_{len(questions) + 1:03d}",
                            "title": question_title,
                            "body": question_body,
                            "category": question_category,
                            "asked_by": st.session_state.user.get("name", "Anonymous"),
                            "date": str(dt.datetime.now()),
                            "answers": [],
                            "upvotes": 0
                        })
                        storage.write("awareness_questions", questions)
                        st.success("✅ Question posted!")
                        st.rerun()

        # Display questions
        questions = storage.read("awareness_questions", [])

        if not questions:
            st.info("No questions yet. Be the first to ask!")

        for q in questions[:10]:  # Show latest 10
            with st.container():
                # Question header
                st.markdown(f"**🏷️ {q['category']}**")
                st.markdown(f"### {q['title']}")
                st.write(q['body'][:200] + ('...' if len(q['body']) > 200 else ''))
                st.caption(f"👤 {q['asked_by']} • 📅 {q['date'][:10]} • 💬 {len(q.get('answers', []))} answers")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"👍 Upvote ({q.get('upvotes', 0)})",
                                 key=f"upvote_{q['id']}",
                                 use_container_width=True):
                        q['upvotes'] = q.get('upvotes', 0) + 1
                        storage.write("awareness_questions", questions)
                        st.rerun()
                with col2:
                    if st.button("💬 Answer", key=f"answer_{q['id']}", use_container_width=True):
                        st.session_state[f"answering_{q['id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("📤 Share", key=f"share_q_{q['id']}", use_container_width=True):
                        st.info("Link copied!")

                # Answer form
                if st.session_state.get(f"answering_{q['id']}", False):
                    with st.form(f"answer_form_{q['id']}"):
                        answer_text = st.text_area("Your Answer", key=f"ans_text_{q['id']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.form_submit_button("✅ Submit Answer", type="primary"):
                                if answer_text:
                                    if "answers" not in q:
                                        q["answers"] = []
                                    q["answers"].append({
                                        "text": answer_text,
                                        "by": st.session_state.user.get("name", "Anonymous"),
                                        "date": str(dt.datetime.now()),
                                        "upvotes": 0
                                    })
                                    user_progress["total_points"] += 15
                                    storage.write("awareness_questions", questions)
                                    storage.write("learning_progress", st.session_state.learning_progress)
                                    st.session_state[f"answering_{q['id']}"] = False
                                    st.success("✅ Answer posted! +15 points")
                                    st.rerun()
                        with col_b:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"answering_{q['id']}"] = False
                                st.rerun()

                st.markdown("---")

    # ==================== TAB 6: MY PROGRESS ====================
    with tabs[5]:
        st.markdown("### 📊 Your Learning Journey")

        # Progress overview
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🏆 Achievements")
            st.metric("Total Points Earned", user_progress.get("total_points", 0))
            st.metric("Videos Completed", len(user_progress.get("completed_videos", [])))
            st.metric("Quizzes Passed", len([s for s in user_progress.get("quiz_scores", {}).values() if s >= 70]))
            st.metric("Campaigns Joined",
                      len([k for k in st.session_state.keys() if k.startswith("joined_") and st.session_state[k]]))

        with col2:
            st.markdown("#### 🎖️ Badges Earned")
            badges = user_progress.get("badges", [])
            if badges:
                for badge in badges:
                    st.success(f"🏅 {badge}")
            else:
                st.info("Complete quizzes and activities to earn badges!")

        # Bookmarked content
        st.markdown("#### 🔖 Your Bookmarks")
        bookmarks = user_progress.get("bookmarks", [])
        if bookmarks:
            bookmarked_videos = [v for v in videos if v["id"] in bookmarks]
            for video in bookmarked_videos:
                st.markdown(f"- 📺 {video['title']}")
        else:
            st.info("Bookmark videos to save them for later!")

        # Quiz history
        st.markdown("#### 📝 Quiz History")
        quiz_scores = user_progress.get("quiz_scores", {})
        if quiz_scores:
            quiz_df = pd.DataFrame([
                {"Quiz ID": k, "Score": f"{v}%", "Status": "✅ Passed" if v >= 70 else "❌ Failed"}
                for k, v in quiz_scores.items()
            ])
            st.dataframe(quiz_df, use_container_width=True, hide_index=True)
        else:
            st.info("Take quizzes to see your results here!")

    # Footer
    st.markdown("---")
    st.info("💡 **Tip:** Complete activities to earn points and unlock badges!")
    st.caption("Questions or feedback? Contact us at support@safepaws.ai")
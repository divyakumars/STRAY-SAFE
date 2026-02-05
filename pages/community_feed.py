# pages/community_feed.py

import streamlit as st
from utils import storage
from components import page_header, encode_file, create_notification, decode_file
import time
import uuid
import datetime as dt
import base64
from io import BytesIO
from PIL import Image


def sanitize_posts(posts):
    """
    Ensure every post has valid structure and unique ID.
    Removes corrupt or non-dict entries safely.
    """
    clean_posts = []
    seen_ids = set()

    for p in posts:
        try:
            # Skip anything that's not a dictionary
            if not isinstance(p, dict):
                print("⚠️ Skipping invalid post:", p)
                continue

            # --- Basic Fields ---
            p.setdefault("id", f"POST-{int(time.time())}-{uuid.uuid4().hex[:6]}")
            p.setdefault("author", "Anonymous")
            p.setdefault("author_email", "")
            p.setdefault("content", "")
            p.setdefault("time", str(dt.datetime.now()))
            p.setdefault("likes", 0)
            p.setdefault("liked_by", [])
            p.setdefault("comments", [])
            p.setdefault("image", None)
            p.setdefault("approved", True)
            p.setdefault("flagged", False)

            # --- Ensure unique IDs ---
            if p["id"] in seen_ids:
                p["id"] = f"POST-{int(time.time())}-{uuid.uuid4().hex[:6]}"
            seen_ids.add(p["id"])

            clean_posts.append(p)

        except Exception as e:
            print(f"❌ Error sanitizing post: {e}")
            continue

    return clean_posts


def get_user_profile_picture(author_name):
    """Get user's profile picture from storage"""
    users = storage.read("users", [])
    user = next((u for u in users if u.get("name") == author_name), None)
    return user.get("profile_picture") if user else None


def render():
    """Community discussion and updates feed"""
    user_role = st.session_state.user.get("role")
    page_header("💬", "Community Feed",
                "Share updates, stories, and connect with the community", user_role)

    # ✅ Load and sanitize posts immediately
    raw_posts = storage.read("posts", [])
    posts = sanitize_posts(raw_posts)

    # ✅ Save cleaned version
    storage.write("posts", posts)

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Posts", len(posts))
    with col2:
        st.metric("❤️ Total Likes", sum(p.get("likes", 0) for p in posts))
    with col3:
        st.metric("💬 Total Comments", sum(len(p.get("comments", [])) for p in posts))

    # --- Create Post ---
    with st.expander("✏️ Create New Post", expanded=False):
        post_content = st.text_area("What's on your mind?",
                                    placeholder="Share an update, story, or ask for help...",
                                    height=100,
                                    key="new_post_content")
        col1, col2 = st.columns([2, 1])
        with col1:
            post_image = st.file_uploader("📷 Add Photo (Optional)",
                                          type=["jpg", "jpeg", "png"],
                                          key="post_image")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📤 Post", type="primary", use_container_width=True, key="submit_post"):
                if post_content.strip():
                    post_id = f"POST-{int(time.time())}-{uuid.uuid4().hex[:6]}"
                    image_data = encode_file(post_image.getvalue()) if post_image else None
                    new_post = {
                        "id": post_id,
                        "author": st.session_state.user.get("name", "Anonymous"),
                        "author_email": st.session_state.user.get("email", ""),
                        "content": post_content,
                        "image": image_data,
                        "time": str(dt.datetime.now()),
                        "likes": 0,
                        "liked_by": [],
                        "comments": [],
                        "approved": True,
                        "flagged": False
                    }
                    posts.insert(0, new_post)
                    storage.write("posts", posts)
                    create_notification("post", f"New post by {new_post['author']}", "low")
                    st.success("✅ Post published!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter some content")

    # --- Filter/Sort ---
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sort_option = st.selectbox("📋 Sort by",
                                   ["Newest First", "Oldest First", "Most Liked", "Most Commented"],
                                   key="sort_posts")
    with col2:
        filter_option = st.selectbox("🔍 Filter",
                                     ["All Posts", "My Posts", "Following"],
                                     key="filter_posts")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="refresh_feed"):
            st.rerun()

    # Apply sorting
    if sort_option == "Newest First":
        sorted_posts = sorted(posts, key=lambda x: x.get("time", ""), reverse=True)
    elif sort_option == "Oldest First":
        sorted_posts = sorted(posts, key=lambda x: x.get("time", ""))
    elif sort_option == "Most Liked":
        sorted_posts = sorted(posts, key=lambda x: x.get("likes", 0), reverse=True)
    else:  # Most Commented
        sorted_posts = sorted(posts, key=lambda x: len(x.get("comments", [])), reverse=True)

    # Apply filtering
    if filter_option == "My Posts":
        sorted_posts = [p for p in sorted_posts
                        if p.get("author_email") == st.session_state.user.get("email")]

    # --- Display Posts ---
    st.markdown("### 📰 Community Posts")

    if not sorted_posts:
        st.info("📝 No posts yet. Be the first to share something!")
    else:
        for idx, post in enumerate(sorted_posts):
            display_post(post, posts, idx)


def display_post(post, all_posts, idx):
    """Display a single post with interactions - COMPLETE VERSION"""
    current_user_email = st.session_state.user.get("email", "")
    current_user_name = st.session_state.user.get("name", "Anonymous")
    author_name = post.get('author', 'Anonymous')
    profile_pic = get_user_profile_picture(author_name)

    # Main post container with better styling
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(51, 65, 85, 0.4) 0%, rgba(30, 41, 59, 0.4) 100%);
                border-radius: 16px; padding: 24px; margin-bottom: 24px; 
                border: 1px solid rgba(148, 163, 184, 0.1);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    </div>
    """, unsafe_allow_html=True)

    # Post header with profile picture
    col_avatar, col_info = st.columns([1, 20])

    with col_avatar:
        if profile_pic:
            st.markdown(f"""
            <img src="data:image/png;base64,{profile_pic}" 
                 style="width: 56px; height: 56px; border-radius: 50%; 
                        object-fit: cover; border: 3px solid rgba(99, 102, 241, 0.5);
                        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);"/>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="width: 56px; height: 56px; border-radius: 50%; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        display: flex; align-items: center; justify-content: center; 
                        font-weight: 800; color: white; font-size: 28px;
                        border: 3px solid rgba(118, 75, 162, 0.5);
                        box-shadow: 0 2px 8px rgba(118, 75, 162, 0.3);">
                {author_name[0].upper()}
            </div>
            """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div style="padding-left: 12px;">
            <div style="font-weight: 700; font-size: 18px; color: #e2e8f0; margin-bottom: 4px;">
                {author_name}
            </div>
            <div style="font-size: 13px; color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                <span>🕒</span>
                <span>{post.get('time', '')[:19] if post.get('time') else 'Just now'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

    # Post content with better styling
    st.markdown(f"""
    <div style="font-size: 16px; line-height: 1.8; color: #e2e8f0; 
                padding: 16px; background: rgba(30, 41, 59, 0.3); 
                border-radius: 12px; margin-bottom: 16px;">
        {post.get('content', '')}
    </div>
    """, unsafe_allow_html=True)

    # Display image if present with size constraint
    if post.get("image"):
        try:
            image_bytes = base64.b64decode(post["image"])
            image = Image.open(BytesIO(image_bytes))

            # Resize image if too large
            max_width = 600
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            st.image(image, use_container_width=False, width=max_width)
            st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error loading image: {e}")

    # Interaction buttons with better styling
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        # Like button
        user_liked = current_user_email in post.get("liked_by", [])
        like_emoji = "❤️" if user_liked else "🤍"
        like_count = post.get('likes', 0)

        if st.button(f"{like_emoji} {like_count} Like{'s' if like_count != 1 else ''}",
                     key=f"like_{post['id']}_{idx}",
                     use_container_width=True):
            if user_liked:
                post["likes"] = max(0, post.get("likes", 0) - 1)
                if current_user_email in post["liked_by"]:
                    post["liked_by"].remove(current_user_email)
            else:
                post["likes"] = post.get("likes", 0) + 1
                if "liked_by" not in post:
                    post["liked_by"] = []
                post["liked_by"].append(current_user_email)

            storage.write("posts", all_posts)
            st.rerun()

    with col2:
        # Comment button
        comment_count = len(post.get("comments", []))
        if st.button(f"💬 {comment_count} Comment{'s' if comment_count != 1 else ''}",
                     key=f"comment_toggle_{post['id']}_{idx}",
                     use_container_width=True):
            session_key = f"show_comments_{post['id']}"
            st.session_state[session_key] = not st.session_state.get(session_key, False)
            st.rerun()

    with col3:
        # Share button
        if st.button("🔗 Share",
                     key=f"share_{post['id']}_{idx}",
                     use_container_width=True):
            st.info(f"📋 Share link: /community_feed?post={post['id']}")
            st.success("✅ Link ready to share!")

    with col4:
        # Report button (only for others' posts)
        if post.get("author_email") != current_user_email:
            if st.button("🚩",
                         key=f"report_{post['id']}_{idx}",
                         use_container_width=True):
                post["flagged"] = True
                storage.write("posts", all_posts)
                create_notification("moderation", f"Post {post['id']} flagged by {current_user_name}", "high")
                st.warning("⚠️ Post reported for moderation")
                time.sleep(1)
                st.rerun()

    # Comments section - ALWAYS VISIBLE when toggled
    comments = post.get("comments", [])
    session_key = f"show_comments_{post['id']}"

    if st.session_state.get(session_key, False):
        st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)

        # Comments header
        st.markdown(f"""
        <div style="font-size: 18px; font-weight: 700; color: #e2e8f0; 
                    margin-bottom: 16px; padding-bottom: 12px; 
                    border-bottom: 2px solid rgba(148, 163, 184, 0.2);">
            💬 Comments ({len(comments)})
        </div>
        """, unsafe_allow_html=True)

        # Display existing comments with complete content
        if comments:
            for comment_idx, comment in enumerate(comments):
                commenter_name = comment.get('author', 'Anonymous')
                commenter_pic = get_user_profile_picture(commenter_name)
                comment_text = comment.get('text', '')
                comment_time = comment.get('time', '')

                # Comment container with better styling
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.5); 
                            border-radius: 12px; padding: 16px; margin-bottom: 12px;
                            border-left: 3px solid #6366f1;">
                </div>
                """, unsafe_allow_html=True)

                col_avatar, col_content = st.columns([1, 15])

                with col_avatar:
                    if commenter_pic:
                        st.markdown(f"""
                        <img src="data:image/png;base64,{commenter_pic}" 
                             style="width: 40px; height: 40px; border-radius: 50%; 
                                    object-fit: cover; border: 2px solid rgba(99, 102, 241, 0.5);"/>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="width: 40px; height: 40px; border-radius: 50%; 
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    display: flex; align-items: center; justify-content: center; 
                                    font-weight: 700; color: white; font-size: 18px;
                                    border: 2px solid rgba(118, 75, 162, 0.5);">
                            {commenter_name[0].upper()}
                        </div>
                        """, unsafe_allow_html=True)

                with col_content:
                    st.markdown(f"""
                    <div style="padding-left: 8px;">
                        <div style="font-weight: 600; font-size: 15px; color: #e2e8f0; margin-bottom: 8px;">
                            {commenter_name}
                        </div>
                        <div style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin-bottom: 8px;">
                            {comment_text}
                        </div>
                        <div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px;">
                            <span>🕒</span>
                            <span>{comment_time[:19] if comment_time else 'Just now'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
        else:
            st.info("💭 No comments yet. Be the first to comment!")

        # Add comment form - COMPLETE AND VISIBLE
        st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size: 16px; font-weight: 600; color: #e2e8f0; margin-bottom: 12px;">
            ✍️ Add a comment:
        </div>
        """, unsafe_allow_html=True)

        comment_key = f"comment_input_{post['id']}_{idx}"
        comment_text = st.text_area(
            "Your comment",
            key=comment_key,
            placeholder="Share your thoughts...",
            height=100,
            label_visibility="collapsed"
        )

        col_btn1, col_btn2, col_spacer = st.columns([2, 2, 8])

        with col_btn1:
            if st.button("📝 Post Comment",
                         key=f"submit_comment_{post['id']}_{idx}",
                         type="primary",
                         use_container_width=True):
                if comment_text.strip():
                    new_comment = {
                        "author": current_user_name,
                        "author_email": current_user_email,
                        "text": comment_text,
                        "time": str(dt.datetime.now())
                    }

                    if "comments" not in post:
                        post["comments"] = []
                    post["comments"].append(new_comment)

                    storage.write("posts", all_posts)
                    create_notification("comment", f"{current_user_name} commented on a post", "low")
                    st.success("✅ Comment posted!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter a comment")

        with col_btn2:
            if st.button("❌ Cancel",
                         key=f"cancel_comment_{post['id']}_{idx}",
                         use_container_width=True):
                st.session_state[session_key] = False
                st.rerun()

    # Visual separator between posts
    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<hr style='border: 0; height: 1px; background: linear-gradient(to right, transparent, rgba(148, 163, 184, 0.3), transparent); margin: 24px 0;'>",
        unsafe_allow_html=True)


# Main entry point
if __name__ == "__main__":
    render()
import streamlit as st
import json
from PIL import Image
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================

SCENE_JSON = "small_scenes.json"
SAVE_DIR = "saved_annotations"
Path(SAVE_DIR).mkdir(exist_ok=True)

# ==================================================
# LOAD DATA
# ==================================================

with open(SCENE_JSON, "r") as f:
    SCENES = json.load(f)

SCENE_IDS = list(SCENES.keys())
TOTAL_SCENES = len(SCENE_IDS)

# ==================================================
# SESSION STATE
# ==================================================

if "ldapid" not in st.session_state:
    st.session_state.ldapid = None

if "scene_idx" not in st.session_state:
    st.session_state.scene_idx = 0

if "scene_results" not in st.session_state:
    st.session_state.scene_results = []

if "submitted_movie" not in st.session_state:
    st.session_state.submitted_movie = False

# ==================================================
# HELPERS
# ==================================================

def save_progress(movie_level=None):
    """Save progress after every scene or final submission."""
    data = {
        "ldapid": st.session_state.ldapid,
        "progress": {
            "completed_scenes": st.session_state.scene_idx,
            "total_scenes": TOTAL_SCENES
        },
        "scene_level": st.session_state.scene_results
    }

    if movie_level is not None:
        data["movie_level"] = movie_level

    out_path = Path(SAVE_DIR) / f"annotations_{st.session_state.ldapid}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)


def load_images(paths):
    imgs = []
    for p in paths:
        try:
            imgs.append(Image.open(p))
        except:
            imgs.append(None)
    return imgs


def get_scene():
    if st.session_state.scene_idx >= TOTAL_SCENES:
        return None
    return SCENES[SCENE_IDS[st.session_state.scene_idx]]

# ==================================================
# PAGE HEADER
# ==================================================

st.title("🎬 Long-Form Movie Evaluation")

# ==================================================
# LDAP ID GATE (MANDATORY)
# ==================================================

if st.session_state.ldapid is None:
    st.markdown("### 🔐 Annotator Identification")

    ldap = st.text_input(
        "Enter your LDAP ID (required to begin):",
        placeholder="e.g., jdoe123"
    )

    if st.button("Start Annotation"):
        if ldap.strip() == "":
            st.error("LDAP ID is required.")
        else:
            st.session_state.ldapid = ldap.strip()
            save_progress()
            st.rerun()

    st.stop()

# ==================================================
# PROGRESS BAR
# ==================================================

progress = st.session_state.scene_idx / TOTAL_SCENES
st.progress(progress)
st.caption(
    f"Progress: {st.session_state.scene_idx} / {TOTAL_SCENES} scenes completed"
)

# ==================================================
# EVALUATION GUIDELINES
# ==================================================

st.markdown("## 📘 Evaluation Guidelines")

with st.expander("Background Continuity (1–5)"):
    st.markdown("""
- Stable location identity  
- Persistent background elements  
- Camera motion explains variation  
""")

with st.expander("Character Appearance Consistency (1–5)"):
    st.markdown("""
- Same facial identity  
- Consistent clothing / body  
- No unexplained identity drift  
""")

with st.expander("Cinematic Expressiveness (1–5)"):
    st.markdown("""
- Intentional framing  
- Shot scale variation  
- Story-supportive composition  
""")

st.divider()

# ==================================================
# SCENE-LEVEL UI
# ==================================================

scene = get_scene()

if scene is None:
    st.success("✅ All scenes completed.")
else:
    st.header(f"Scene: {scene['scene_id']}")

    shots = scene["shots"]
    imgsA = load_images(scene["movie_A_image_paths"])
    imgsB = load_images(scene["movie_B_image_paths"])

    st.subheader("Shot Descriptions")

    for i, s in enumerate(shots):
        with st.expander(f"▶ Shot {i+1} Description", expanded=False):
            st.markdown(s)

    st.divider()

    with st.expander("▶ Movie A – Scene Visuals", expanded=False):
        colsA = st.columns(len(imgsA))
        for i, col in enumerate(colsA):
            with col:
                if imgsA[i]:
                    st.image(imgsA[i], width="stretch")
                st.caption(f"Shot {i+1}")


    st.divider()

    with st.expander("▶ Movie B – Scene Visuals", expanded=False):
        colsB = st.columns(len(imgsB))
        for i, col in enumerate(colsB):
            with col:
                if imgsB[i]:
                    st.image(imgsB[i], width="stretch")
                st.caption(f"Shot {i+1}")


    st.divider()

    st.subheader("Scene-Level Ratings")

    colA, colB = st.columns(2)

    with colA:
        bgA = st.radio("Background Continuity (A)", [1,2,3,4,5])
        charA = st.radio("Character Consistency (A)", [1,2,3,4,5])
        cineA = st.radio("Cinematic Expressiveness (A)", [1,2,3,4,5])

    with colB:
        bgB = st.radio("Background Continuity (B)", [1,2,3,4,5])
        charB = st.radio("Character Consistency (B)", [1,2,3,4,5])
        cineB = st.radio("Cinematic Expressiveness (B)", [1,2,3,4,5])

    pair_bg = st.radio("Better Background?", ["Movie A", "Movie B", "Tie"])
    pair_char = st.radio("Better Character?", ["Movie A", "Movie B", "Tie"])
    pair_cine = st.radio("More Cinematic?", ["Movie A", "Movie B", "Tie"])

    comment = st.text_area("Optional comment")

    if st.button("Save Scene & Continue"):
        st.session_state.scene_results.append({
            "scene_id": scene["scene_id"],
            "movie_A": {
                "background": bgA,
                "character": charA,
                "cinematic": cineA
            },
            "movie_B": {
                "background": bgB,
                "character": charB,
                "cinematic": cineB
            },
            "pairwise": {
                "background": pair_bg,
                "character": pair_char,
                "cinematic": pair_cine
            },
            "comment": comment
        })

        st.session_state.scene_idx += 1
        save_progress()
        st.rerun()

# ==================================================
# MOVIE-LEVEL SAVE
# ==================================================

if scene is None and not st.session_state.submitted_movie:

    st.header("🎥 Movie-Level Evaluation")

    narA = st.radio("Narrative Causality (A)", [1,2,3,4,5])
    charA_m = st.radio("Character Identity Persistence (A)", [1,2,3,4,5])
    spaceA = st.radio("Spatial Consistency (A)", [1,2,3,4,5])

    narB = st.radio("Narrative Causality (B)", [1,2,3,4,5])
    charB_m = st.radio("Character Identity Persistence (B)", [1,2,3,4,5])
    spaceB = st.radio("Spatial Consistency (B)", [1,2,3,4,5])

    pair_nar = st.radio("Better Narrative?", ["Movie A", "Movie B", "Tie"])
    pair_char = st.radio("Better Character?", ["Movie A", "Movie B", "Tie"])
    pair_space = st.radio("Better Spatial?", ["Movie A", "Movie B", "Tie"])

    if st.button("Submit Final Evaluation"):
        save_progress(movie_level={
            "movie_A": {
                "narrative": narA,
                "character": charA_m,
                "spatial": spaceA
            },
            "movie_B": {
                "narrative": narB,
                "character": charB_m,
                "spatial": spaceB
            },
            "pairwise": {
                "narrative": pair_nar,
                "character": pair_char,
                "spatial": pair_space
            }
        })
        st.caption(
            f"Currently annotating: Scene {st.session_state.scene_idx + 1} / {TOTAL_SCENES}"
        )
        st.session_state.submitted_movie = True
        st.success("✅ All annotations saved successfully.")

import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 상세 시스템", layout="wide")

# CSS: 시각적 강조 스타일 유지
st.markdown("""
    <style>
    .elite-mare {
        color: #1E90FF !important;
        font-weight: bold;
        font-size: 1.2em;
    }
    .sire-title {
        font-weight: bold;
        font-size: 1.5em;
        margin-bottom: 5px;
        color: #333333;
    }
    /* 리스트 간격 조정 */
    .progeny-item {
        margin-left: 25px;
        margin-bottom: 3px;
        color: #555555;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, "파일을 찾을 수 없습니다."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, f"파일 파싱 오류: {e}"

    id_map = {}
    for node in root.iter('node'):
        nid = node.get('ID')
        if nid:
            id_map[nid] = node.get('TEXT', '이름 없음')

    year_pattern = re.compile(r'(\d{4})')
    elite_sire_map = defaultdict(list)

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if my_text and '@' in my_text:
            year_match = year_pattern.search(my_text)
            birth_year = int(year_match.group(1)) if year_match else 0
            
            progeny = []
            for arrow in node.findall('arrowlink'):
                dest_id = arrow.get('DESTINATION')
                if dest_id in id_map:
                    progeny.append(f"🔗 [연결] {id_map[dest_id]}")
            
            for child in node.findall('node'):
                c_text = child.get('TEXT', '')
                if c_text:
                    progeny.append(f"🌿 [가지] {c_text}")

            mare_info = {
                'name': my_text.strip(),
                'year': birth_year,
                'progeny': progeny
            }
            if parent_text != "Unknown":
                elite_sire_map[parent_text.strip()].append(mare_info)
        
        for child in node.findall('node'):
            traverse(child, my_text)

    traverse(root)
    return elite_sire_map, None

# --- UI 메인 ---
st.title("🐎 암말우성 씨수말 랭킹 (전체 펼침 모드)")

password = st.text_input("접속 암호", type="password")
if password != "3811":
    if password: st.error("암호 오류")
    st.stop()

elite_map, err = load_and_analyze_data()
if err:
    st.error(err)
    st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 설정", 1900, 2030, (1900, 2026))

results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

if not results:
    st.warning("선택한 연도 범위 내에 데이터가 없습니다.")
else:
    for i, (sire, daughters, total) in enumerate(results[:50], 1):
        # [핵심] expanded=True 옵션을 넣어 처음부터 모두 펼쳐지게 함
        expander_label = f"[{i}위] {sire} (기간내: {len(daughters)} / 누적: {total})"
        
        with st.expander(expander_label, expanded=True):
            st.markdown(f"<div class='sire-title'>{i}위. {sire}</div>", unsafe_allow_html=True)
            st.write("---")
            
            for d in daughters:
                st.markdown(f"<div class='elite-mare'>⭐ {d['name']} ({d['year']}년생)</div>", unsafe_allow_html=True)
                
                if d['progeny']:
                    for p in d['progeny']:
                        st.markdown(f"<div class='progeny-item'>{p}</div>", unsafe_allow_html=True)
                st.write("")

import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 상세 시스템", layout="wide")

# CSS를 이용해 파란색 텍스트 스타일 정의
st.markdown("""
    <style>
    .blue-bold-text {
        color: #1E90FF !important;
        font-weight: bold;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, "파일을 찾을 수 없습니다."

    tree = ET.parse(file_path)
    root = tree.getroot()

    # ID 맵핑 (화살표 추적용)
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
            # 화살표 연결 자마
            for arrow in node.findall('arrowlink'):
                dest_id = arrow.get('DESTINATION')
                if dest_id in id_map:
                    progeny.append(f"🔗 [연결] {id_map[dest_id]}")
            
            # 하위 가지 자마
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
st.title("🐎 암말우성 씨수말 랭킹 & 자마 상세 추적")

password = st.text_input("접속 암호", type="password")
if password != "3811":
    if password: st.error("암호 오류")
    st.stop()

elite_map, err = load_and_analyze_data()
if err: st.error(err); st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 설정", 1900, 2030, (1900, 2026))

# 결과 정렬
results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

# 리스트 출력
for i, (sire, daughters, total) in enumerate(results[:50], 1):
    # 씨수말 폰트 2단계 키우고 굵게 (HTML 사용)
    header_label = f"<h3 style='margin-bottom:0px;'>{i}위. {sire} (선택: {len(daughters)} / 누적: {total})</h3>"
    with st.expander(f"더보기 클릭"):
        st.markdown(header_label, unsafe_allow_html=True)
        st.write("---")
        for d in daughters:
            # 엘리트 종빈마: 파란색, 폰트 1단계 키우기, 굵게
            st.markdown(f"<span class='blue-bold-text'>⭐ {d['name']} ({d['year']}년생)</span>", unsafe_allow_html=True)
            
            if d['progeny']:
                for p in d['progeny']:
                    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{p}")
            st.write("") # 간격 조절

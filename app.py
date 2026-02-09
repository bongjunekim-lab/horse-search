import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 시스템", layout="wide")

# CSS 설정: 종빈마 파란색 강조 및 자마 스타일
st.markdown("""
    <style>
    .elite-mare {
        color: #1E90FF !important;
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 12px;
        margin-bottom: 5px;
    }
    .progeny-item {
        margin-left: 30px;
        margin-bottom: 3px;
        color: #444444;
        font-size: 1.05em;
    }
    .hr-line {
        margin: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    .star-rating {
        color: #FFD700; /* 금색 별 */
        font-size: 0.9em;
        margin-left: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, "파일을 찾을 수 없습니다."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        id_map = {}
        for node in root.iter('node'):
            nid = node.get('ID')
            if nid:
                id_map[nid] = node.get('TEXT', '')

        year_pattern = re.compile(r'(\d{4})')
        elite_sire_map = defaultdict(list)

        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            if my_text and '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                progeny = []
                # 화살표 연결(arrowlink)만 추출
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_map:
                        progeny.append(f"🔗 [연결] {id_map[dest_id]}")
                
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
    except Exception as e:
        return None, f"분석 오류: {str(e)}"

# --- UI 메인 ---
st.title("🐎 암말우성 씨수말 랭킹 시스템")

password = st.text_input("접속 암호를 입력하세요", type="password")
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

# --- 결과 출력 ---
if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    st.write(f"현재 총 **{len(results)}두**의 씨수말이 검색되었습니다.")
    
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        # [추가] 종빈마 두수만큼 별 생성 (최대 10개로 제한하여 레이아웃 깨짐 방지)
        num_stars = len(daughters)
        stars = "⭐" * num_stars
        
        # Expander 제목에 별 추가
        expander_title = f"[{i}위] {sire} (엘리트: {num_stars}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown(f"#### 🏆 {sire} (전체 누적: {total}두)")
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            for d in daughters:
                st.markdown(f"<div class='elite-mare'>⭐ {d['name']} ({d['year']}년생)</div>", unsafe_allow_html=True)
                
                if d['progeny']:
                    for p in d['progeny']:
                        st.markdown(f"<div class='progeny-item'>{p}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 없음</div>", unsafe_allow_html=True)

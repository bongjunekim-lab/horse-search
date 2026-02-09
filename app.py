import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 기본 파란색, 성적 우수 종빈마 보라색, 닉 적색
st.markdown("""
    <style>
    .elite-mare-blue {
        color: #1E90FF !important; /* 기본 파란색 */
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .elite-mare-purple {
        color: #9400D3 !important; /* 굵은 보라색 (DarkViolet) */
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .progeny-item {
        margin-left: 30px;
        margin-bottom: 2px;
        color: #000000;
        font-size: 1.05em;
    }
    .nick-red {
        color: #FF0000 !important;
        font-weight: bold;
    }
    .hr-line {
        margin: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, None, "파일을 찾을 수 없습니다."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        id_to_text = {}
        id_to_parent_text = {}
        
        for parent in root.iter('node'):
            p_text = parent.get('TEXT', 'Unknown')
            for child in parent.findall('node'):
                c_id = child.get('ID')
                if c_id:
                    id_to_text[c_id] = child.get('TEXT', '')
                    id_to_parent_text[c_id] = p_text

        year_pattern = re.compile(r'(\d{4})')
        elite_sire_map = defaultdict(list)

        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            if my_text and '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                progeny_info = [] 
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_to_text:
                        progeny_info.append(dest_id)
                
                mare_info = {
                    'name': my_text.strip(),
                    'year': birth_year,
                    'progeny_ids': progeny_info 
                }
                if parent_text != "Unknown":
                    elite_sire_map[parent_text.strip()].append(mare_info)
            
            for child in node.findall('node'):
                traverse(child, my_text)

        traverse(root)
        return elite_sire_map, id_to_text, id_to_parent_text, None
    except Exception as e:
        return None, None, None, f"분석 오류: {str(e)}"

# --- UI 메인 ---
st.title("🐎 암말우성 씨수말 랭킹 및 성적 기반 분석")

password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

results = []
g1_pattern = re.compile(r'G1-(\d+)')

for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            # 닉 분석용 데이터 사전 생성
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            
            for d in daughters:
                # [수정] 엘리트 종빈마 성적 체크 (G1-10 이상이면 보라색, 아니면 파란색)
                mare_class = "elite-mare-blue"
                g1_match = g1_pattern.search(d['name'])
                if g1_match and int(g1_match.group(1)) >= 10:
                    mare_class = "elite-mare-purple"
                
                st.markdown(f"<div class='{mare_class}'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        progeny_sire = id_to_parent_text.get(p_id, "정보 없음")
                        
                        # [유지] 닉 중복 체크 (적색)
                        if len(sire_to_mothers[progeny_sire]) >= 2:
                            display_sire = f"<span class='nick-red'>{progeny_sire}</span>"
                        else:
                            display_sire = f"<b>{progeny_sire}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_name} ({display_sire})</div>", unsafe_allow_html=True)

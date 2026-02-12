import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 눈부심 방지 전문가용 컬러 팔레트
st.markdown("""
    <style>
    .elite-mare {
        color: #0077CC !important; 
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .progeny-item {
        margin-left: 30px;
        margin-bottom: 2px;
        color: #333333; 
        font-size: 1.05em;
    }
    .top-progeny {
        color: #800080 !important; 
        font-weight: bold;
    }
    .elite-daughter {
        color: #003366 !important; 
        font-weight: bold;
    }
    .star-daughter {
        color: #000000 !important; 
        font-weight: 900 !important; 
    }
    .nick-red {
        color: #C0392B !important; 
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
        
        # 1차 순회: 모든 노드의 ID와 텍스트 매핑
        for parent in root.iter('node'):
            p_text = parent.get('TEXT', 'Unknown')
            for child in parent.findall('node'):
                c_id = child.get('ID')
                if c_id:
                    id_to_text[c_id] = child.get('TEXT', '')
                    id_to_parent_text[c_id] = p_text

        year_pattern = re.compile(r'(\d{4})')
        elite_sire_map = defaultdict(list)

        def normalize_name(text):
            clean = text.replace('@', '').replace('#', '').replace('*', '')
            clean = clean.replace('암)', '').replace('수)', '').replace('거)', '')
            clean = clean.replace('가.', '').replace('나.', '').replace('다.', '')
            clean = clean.split('(')[0]
            return clean.strip().lower()

        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            if my_text and '@' in my_text:
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                
                progeny_info = [] 
                seen_ids = set()
                mare_pure_name = normalize_name(my_text)

                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_to_text:
                        if dest_id in seen_ids:
                            continue
                        child_raw_text = id_to_text[dest_id]
                        child_pure_name = normalize_name(child_raw_text)
                        if mare_pure_name == child_pure_name:
                            continue
                        progeny_info.append(dest_id)
                        seen_ids.add(dest_id)
                
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
st.title("🐎 암말우성 씨수말 랭킹 및 분석 시스템")

password = st.sidebar.text_input("접속 암호", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.info("사이드바에 암호를 입력해주세요.")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

# 사이드바 필터 설정
st.sidebar.header("조회 필터")
start_y, end_y = st.sidebar.slider("종빈마 출생 연도", 1900, 2030, (1900, 2026))
search_query = st.sidebar.text_input("🔍 마명 검색 (종빈마/자마/씨수말)", "").strip().lower()

# --- 필터링 로직 병합 ---
results = []
for sire, daughters in elite_map.items():
    filtered_daughters = []
    
    for d in daughters:
        # 1. 연도 조건
        year_match = start_y <= d['year'] <= end_y
        
        # 2. 검색 조건
        text_match = True
        if search_query:
            mare_match = search_query in d['name'].lower()
            progeny_names = [id_to_text.get(p_id, "").lower() for p_id in d['progeny_ids']]
            progeny_match = any(search_query in p_name for p_name in progeny_names)
            sire_match = search_query in sire.lower()
            text_match = mare_match or progeny_match or sire_match
        
        if year_match and text_match:
            filtered_daughters.append(d)
    
    if filtered_daughters:
        # (씨수말 이름, 필터링된 종빈마 리스트, 원래 전체 데이터 기준 정렬을 위한 개수)
        results.append((sire, filtered_daughters, len(filtered_daughters)))

# 정렬: 검색/필터링된 엘리트 종빈마가 많은 순
results.sort(key=lambda x: x[2], reverse=True)

# G1 성적 추출용 정규식
g1_pattern = re.compile(r'G1-(\d+)')

# --- 결과 출력 ---
if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    if search_query:
        st.success(f"'{search_query}' 검색 결과: {len(results)} 그룹 발견")

    for i, (sire, daughters, count) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            
            for d in daughters:
                st.markdown(f"<div class='elite-mare'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        father_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        # 스타일 로직
                        child_display = child_name
                        g1_match = g1_pattern.search(child_name)
                        is_high_g1 = g1_match and int(g1_match.group(1)) >= 7
                        
                        is_elite_daughter = False
                        is_star_daughter = False
                        
                        if '암)' in child_name:
                            parts = child_name.split('암)')
                            prefix = parts[0]
                            if ('@' in prefix) or ('#' in prefix): is_elite_daughter = True
                            if '*' in prefix: is_star_daughter = True
                        
                        if is_high_g1:
                            child_display = f"<span class='top-progeny'>{child_name}</span>"
                        elif is_elite_daughter:
                            child_display = f"<span class='elite-daughter'>{child_name}</span>"
                        elif is_star_daughter:
                            child_display = f"<span class='star-daughter'>{child_name}</span>"
                        
                        # 닉 강조
                        if len(sire_to_mothers[father_name]) >= 2:
                            father_display = f"<span class='nick-red'>{father_name}</span>"
                        else:
                            father_display = f"<b>{father_name}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_display} ({father_display})</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 정보 없음</div>", unsafe_allow_html=True)

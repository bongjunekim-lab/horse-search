import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 종빈마 파란색, 닉(Nick) 성공 부마 적색 스타일
st.markdown("""
    <style>
    .elite-mare {
        color: #1E90FF !important;
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
        
        # 1. 전수 조사: 모든 노드와 부모 관계 매핑
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
                
                progeny_info = [] # 자마 ID 저장용
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
st.title("🐎 암말우성 씨수말 랭킹 및 닉(Nick) 분석 시스템")

# 접속 암호: 5500
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

# 사이드바 연도 필터
start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

# 랭킹순 정렬
results.sort(key=lambda x: len(x[1]), reverse=True)

if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    st.write(f"현재 검색 범위 내에서 총 **{len(results)}두**의 씨수말이 검색되었습니다.")
    
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            # [핵심 로직 변경] 
            # 단순히 횟수가 아니라 '서로 다른 엘리트 종빈마(모마)'가 몇 명인지 카운트
            sire_to_mothers = defaultdict(set) # {부마이름: set(종빈마이름들)}
            
            for d in daughters:
                for p_id in d['progeny_ids']:
                    progeny_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[progeny_sire_name].add(d['name']) # 부마별로 모마(Daughter) 이름을 세트에 추가
            
            for d in daughters:
                # 💎 종빈마 파란색 강조
                st.markdown(f"<div class='elite-mare'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        sire_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        # [조건] 해당 부마와 교배한 '서로 다른 엘리트 종빈마'가 2두 이상인 경우만 적색
                        if len(sire_to_mothers[sire_name]) >= 2:
                            sire_display = f"<span class='nick-red'>{sire_name}</span>"
                        else:
                            sire_display = f"<b>{sire_name}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_name} ({sire_display})</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 정보 없음</div>", unsafe_allow_html=True)

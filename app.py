import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 시각적 강조 및 간격 최적화
st.markdown("""
    <style>
    .elite-mare {
        color: #1E90FF !important;
        font-weight: bold;
        font-size: 1.3em;
        margin-top: 20px;
        margin-bottom: 8px;
    }
    .progeny-item {
        margin-left: 35px;
        margin-bottom: 5px;
        color: #444444;
        font-size: 1.1em;
    }
    .hr-line {
        margin: 15px 0;
        border-bottom: 2px solid #eee;
    }
    .spacer {
        margin-bottom: 30px; /* 빈 공간 확보 */
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
        
        # ID별 텍스트 및 부모 노드 텍스트 매핑
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
                
                progeny = []
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_to_text:
                        child_name = id_to_text[dest_id]
                        # 부마 정보 가져오기
                        sire_info = id_to_parent_text.get(dest_id, "정보 없음")
                        # [변경] 부마 정보 부분을 굵게(**) 처리
                        progeny.append(f"🔗 [연결] {child_name} (**{sire_info}**)")
                
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
st.title("🐎 암말우성 씨수말 랭킹 및 혈통 추적")

# [변경] 접속 암호 5500
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

# 사이드바 연도 필터
start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

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
    st.write(f"현재 검색 범위 내에서 총 **{len(results)}두**의 씨수말이 검색되었습니다.")
    
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            for d in daughters:
                # 다이아몬드 + 마명 (연도 삭제 상태 유지)
                st.markdown(f"<div class='elite-mare'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny']:
                    for p in d['progeny']:
                        # [변경] 마크다운 형식을 사용하여 부마 정보의 굵게 처리 반영
                        st.markdown(f"<div class='progeny-item'>{p}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 정보 없음</div>", unsafe_allow_html=True)
                
                # [추가] 종빈마 블록 사이 빈 공간 3개 (줄바꿈)
                st.markdown("<br><br><br>", unsafe_allow_html=True)

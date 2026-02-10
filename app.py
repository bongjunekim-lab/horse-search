import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정: 눈부심 방지를 위한 가독성 중심 컬러 팔레트 적용
# 종빈마: 차분한 오션 블루
# G1 우수마: 로얄 퍼플 (중후함)
# 엘리트 딸: 네이비 블루 (진하고 명확함)
# 닉(Nick): 크림슨 레드 (눈이 덜 아픈 적색)
st.markdown("""
    <style>
    .elite-mare {
        color: #0077CC !important; /* 차분한 오션 블루 */
        font-weight: bold;
        font-size: 1.25em;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .progeny-item {
        margin-left: 30px;
        margin-bottom: 2px;
        color: #333333; /* 기본 글자색을 완전 검정보다 살짝 연하게 하여 눈 피로 감소 */
        font-size: 1.05em;
    }
    .top-progeny {
        color: #800080 !important; /* 로얄 퍼플 (보라색) - G1 7승 이상 */
        font-weight: bold;
    }
    .elite-daughter {
        color: #003366 !important; /* 네이비 블루 (진한 파랑) - 번식 우수 딸 */
        font-weight: bold;
    }
    .star-daughter {
        color: #000000 !important; /* 검정색 */
        font-weight: 900 !important; /* 아주 진하게 (Bold) - 별표 딸 */
    }
    .nick-red {
        color: #C0392B !important; /* 크림슨 레드 (벽돌색) - 닉 중복 */
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
st.title("🐎 암말우성 씨수말 랭킹 및 1대 자마 성적 분석 (G1-7 기준)")

password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":
    if password: st.error("암호 오류")
    st.stop()

elite_map, id_to_text, id_to_parent_text, err = load_and_analyze_data()
if err:
    st.error(err); st.stop()

start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

results = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        results.append((sire, filtered, len(daughters)))

results.sort(key=lambda x: len(x[1]), reverse=True)

# G1 성적 추출용 정규식
g1_pattern = re.compile(r'G1-(\d+)')

if not results:
    st.warning("조건에 맞는 데이터가 없습니다.")
else:
    for i, (sire, daughters, total) in enumerate(results[:100], 1):
        num_mares = len(daughters)
        stars = "⭐" * num_mares
        expander_title = f"[{i}위] {sire} (엘리트 종빈마: {num_mares}두) {stars}"
        
        with st.expander(expander_title):
            st.markdown("<div class='hr-line'></div>", unsafe_allow_html=True)
            
            # 닉(Nick) 분석 로직
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            
            for d in daughters:
                # 💎 종빈마 (차분한 파란색)
                st.markdown(f"<div class='elite-mare'>💎 {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        father_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        # --- [자마 이름 표시 로직] ---
                        
                        child_display = child_name
                        
                        # 1. G1 성적 확인 (보라색 조건 - 최우선)
                        g1_match = g1_pattern.search(child_name)
                        is_high_g1 = g1_match and int(g1_match.group(1)) >= 7
                        
                        # 번식 딸 체크를 위한 준비
                        is_elite_daughter = False # @, #
                        is_star_daughter = False  # *
                        
                        if '암)' in child_name:
                            # '암)'을 기준으로 앞부분(prefix) 추출
                            parts = child_name.split('암)')
                            prefix = parts[0] 
                            
                            # 2. 번식 우수 딸 (@, #) 확인
                            if ('@' in prefix) or ('#' in prefix):
                                is_elite_daughter = True
                            
                            # 3. 별표 딸 (*) 확인
                            if '*' in prefix:
                                is_star_daughter = True
                        
                        # [우선순위 적용]
                        if is_high_g1:
                            # 1순위: G1 7승 이상 -> 로얄 퍼플
                            child_display = f"<span class='top-progeny'>{child_name}</span>"
                        elif is_elite_daughter:
                            # 2순위: @ 또는 # 이 있는 암말 -> 네이비 블루
                            child_display = f"<span class='elite-daughter'>{child_name}</span>"
                        elif is_star_daughter:
                            # 3순위: * 이 있는 암말 -> 아주 진한 검정 (Bold)
                            child_display = f"<span class='star-daughter'>{child_name}</span>"
                        
                        # --- [로직 끝] ---

                        # 아버지(Father) 정보: 닉(Nick) 중복 시 크림슨 레드 강조
                        if len(sire_to_mothers[father_name]) >= 2:
                            father_display = f"<span class='nick-red'>{father_name}</span>"
                        else:
                            father_display = f"<b>{father_name}</b>"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_display} ({father_display})</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='progeny-item' style='color:#999;'>- 연결된 화살표 자마 정보 없음</div>", unsafe_allow_html=True)

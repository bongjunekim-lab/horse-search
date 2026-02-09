import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 검색기", layout="wide")

# 2. 데이터 분석 (잘 나오던 그 로직 그대로!)
@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, f"파일을 찾을 수 없습니다."

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"파일 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    elite_sire_map = defaultdict(list)
    branch_map = {} # 가지로 연결된 자식들 저장소

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()

        # [핵심] 현재 노드 바로 아래 연결된 자식들 발췌
        direct_children = []
        for child in node:
            c_text = child.get('TEXT', '')
            if c_text:
                direct_children.append(c_text.strip())
        branch_map[my_clean] = direct_children

        # 엘리트(@) 및 연도 추출
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        if is_elite and parent_clean != "Unknown":
            elite_sire_map[parent_clean].append({'name': my_clean, 'year': birth_year})
        
        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_sire_map, branch_map, None

# --- 화면 구성 ---
st.title("📊 엘리트 씨수말 랭킹 및 자마 비교")

elite_map, branch_map, error = load_and_analyze_data()
if error:
    st.error(error)
    st.stop()

# 사이드바 연도 필터
start_y, end_y = st.sidebar.slider("연도 범위:", 1900, 2026, (1900, 2026))

# 랭킹 정렬
sorted_list = []
for sire, daughters in elite_map.items():
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        sorted_list.append((sire, filtered, len(daughters)))

sorted_list.sort(key=lambda x: len(x[1]), reverse=True)

# 결과 출력
for i, (sire, daughters, total) in enumerate(sorted_list[:50], 1):
    stars = "⭐" * min(len(daughters), 10)
    with st.expander(f"[{i}위] {sire} (기간 내 @: {len(daughters)}두) {stars}"):
        st.write("엘리트 딸 옆의 체크박스를 누르면 자마가 나타납니다.")
        for idx, d in enumerate(daughters):
            col1, col2 = st.columns([0.1, 0.9])
            # 체크박스 추가
            is_checked = col1.checkbox("", key=f"c_{i}_{idx}")
            col2.write(f"⭐ **{d['name']}** ({d['year']}년생)")
            
            # 체크 시 가지연결 자마 노출
            if is_checked:
                kids = branch_map.get(d['name'], [])
                if kids:
                    with st.container(border=True):
                        k_cols = st.columns(3)
                        for k_idx, k_name in enumerate(kids):
                            k_cols[k_idx % 3].write(f"- {k_name}")
                else:
                    st.caption("연결된 하부 데이터가 없습니다.")
    st.divider()

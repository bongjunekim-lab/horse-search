import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="엘리트 씨수말 랭킹", layout="wide")

# 2. 데이터 분석 함수 (안정성 최우선)
@st.cache_data
def load_data():
    # 파일명 확인 (업로드하신 파일명과 일치해야 합니다)
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"파일 읽기 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    elite_map = defaultdict(list)
    branch_map = {}

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # [가지연결] 현재 노드 바로 아래 자식들의 텍스트만 추출
        direct_children = []
        for child in node:
            c_text = child.get('TEXT', '')
            if c_text:
                direct_children.append(c_text.strip())
        branch_map[my_clean] = direct_children

        # 엘리트(@) 및 연도 추출
        is_elite = '@' in my_clean
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0

        # 씨수말 실적으로 엘리트 자마 기록
        if is_elite and parent_clean != "Unknown":
            elite_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_map, branch_map, None

# --- 화면 출력부 ---
st.title("📊 연도별 엘리트 씨수말 랭킹")

# 데이터 불러오기
elite_map, branch_map, error = load_data()

if error:
    st.error(f"❌ {error}")
    st.stop()

# 사이드바 필터 (연도 범위)
st.sidebar.header("🔍 설정")
start_y, end_y = st.sidebar.slider("연도 범위:", 1900, 2026, (1900, 2026))

# 랭킹 데이터 정렬 (1차 결과)
sorted_list = []
if elite_map:
    for sire, daughters in elite_map.items():
        filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
        if filtered:
            sorted_list.append((sire, filtered, len(daughters)))

    sorted_list.sort(key=lambda x: len(x[1]), reverse=True)

# 최종 화면 표시
if not sorted_list:
    st.warning("데이터가 없거나 분석 중입니다. 잠시만 기다려주세요.")
else:
    st.success(f"✅ 총 {len(sorted_list)}두의 씨수말 랭킹을 찾았습니다.")
    
    for i, (sire, daughters, total) in enumerate(sorted_list[:50], 1):
        # 체크박스(0.05) + 정보(0.95)
        c1, c2 = st.columns([0.05, 0.95])
        
        # 2차 결과(자세히 보기)를 위한 체크박스
        show_detail = c1.checkbox("", key=f"rank_box_{i}")
        
        with c2:
            stars = "⭐" * min(len(daughters), 10)
            st.markdown(f"**[{i}위] {sire}** (기간 내 @: {len(daughters)}두 / 전체 @: {total}두) {stars}")
            
            # 체크박스 선택 시에만 '선으로 연결된' 자식 데이터 노출
            if show_detail:
                with st.container(border=True):
                    st.write(f"📂 **{sire}** 배출 엘리트 자마(@)의 하부 연결 정보")
                    for elite_mare in daughters:
                        # branch_map에서 '선으로 연결된' 하부 가지만 발췌
                        kids = branch_map.get(elite_mare['name'], [])
                        st.markdown(f"👉 **엘리트 종빈마: {elite_mare['name']}**")
                        if kids:
                            cols = st.columns(3)
                            for idx, k_name in enumerate(kids):
                                cols[idx % 3].write(f"- 🐎 {k_name}")
                        else:
                            st.caption("연결된 하부 자마 데이터가 없습니다.")
        st.divider()

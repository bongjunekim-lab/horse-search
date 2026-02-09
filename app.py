importimport streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="엘리트 씨수말 랭킹", layout="wide")

# 2. 데이터 분석 함수 (에러 방지를 위해 구조 단순화)
@st.cache_data
def load_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, f"파일이 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, None, f"파일 로딩 오류: {e}"

    year_pattern = re.compile(r'(\d{4})')
    
    # elite_map: 씨수말 -> 자식들 중 @가 있는 엘리트 정보 리스트
    # branch_map: 말 이름 -> 그 아래 '가지'로 직접 연결된 자식들 텍스트 리스트
    elite_map = defaultdict(list)
    branch_map = {}

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        # [가지연결 데이터 수집] 현재 노드 바로 아래의 자식들 텍스트만 추출
        direct_children = []
        for child in node:
            c_text = child.get('TEXT', '')
            if c_text:
                direct_children.append(c_text.strip())
        branch_map[my_clean] = direct_children

        # 엘리트(@) 및 연도 정보 추출
        is_elite = '@' in my_clean
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0

        # 씨수말(부모)의 실적으로 엘리트 자마 등록
        if is_elite and parent_clean != "Unknown":
            elite_map[parent_clean].append({
                'name': my_clean,
                'year': birth_year
            })

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return elite_map, branch_map, None

# --- 화면 구성 시작 ---
st.title("📊 연도별 엘리트 씨수말 랭킹")
st.caption("접속 암호와 상단 검색란을 제거하여 랭킹을 즉시 확인하실 수 있습니다.")

# 데이터 불러오기 (함수 호출 결과 정확히 3개 변수로 받기)
elite_map, branch_map, error = load_data()

if error:
    st.error(f"❌ {error}")
    st.stop()

# 사이드바: 연도 필터
st.sidebar.header("🔍 설정")
start_y, end_y = st.sidebar.slider(
    "자마 태생 연도 범위:", 1900, 2030, (1900, 2026)
)

# 랭킹 정렬 로직
sorted_list = []
for sire, daughters in elite_map.items():
    # 선택한 연도 범위 내의 엘리트들만 필터링
    filtered = [d for d in daughters if start_y <= d['year'] <= end_y]
    if filtered:
        sorted_list.append((sire, filtered, len(daughters)))

# 엘리트 배출 수가 많은 순서로 정렬
sorted_list.sort(key=lambda x: len(x[1]), reverse=True)

# 결과 출력
if not sorted_list:
    st.warning("선택한 연도 범위 내에 엘리트 데이터가 없습니다.")
else:
    st.success(f"✅ 총 {len(sorted_list)}두의 씨수말이 검색되었습니다.")
    
    for i, (sire, daughters, total) in enumerate(sorted_list[:50], 1):
        # 레이아웃: 체크박스(0.05) + 정보(0.95)
        c1, c2 = st.columns([0.05, 0.95])
        
        # 고유 키 생성하여 체크박스 배치
        show_detail = c1.checkbox("", key=f"rank_{i}")
        
        with c2:
            stars = "⭐" * min(len(daughters), 10)
            st.markdown(f"**[{i}위] {sire}** (기간 내 @: {len(daughters)}두 / 전체 @: {total}두) {stars}")
            
            # 체크박스 선택 시에만 '실제로 선(가지)으로 연결된' 자식 데이터 노출
            if show_detail:
                with st.container(border=True):
                    st.write(f"📂 **{sire}**의 엘리트 자마(@) 및 하부 자식들")
                    for elite_mare in daughters:
                        # branch_map에서 엘리트 종빈마의 가지에 연결된 자식들 가져오기
                        kids = branch_map.get(elite_mare['name'], [])
                        
                        st.markdown(f"👉 **엘리트 종빈마: {elite_mare['name']}**")
                        if kids:
                            # 3열로 정렬하여 표시
                            sub_cols = st.columns(3)
                            for idx, k_name in enumerate(kids):
                                sub_cols[idx % 3].write(f"- 🐎 {k_name}")
                        else:
                            st.caption("연결된 하부 자식 데이터가 없습니다.")
        st.divider()

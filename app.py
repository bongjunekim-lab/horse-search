import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 비교 시스템", layout="wide")

# 2. 데이터 분석 함수 (가장 안전한 구조)
@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, f"파일을 찾을 수 없습니다: {file_path}"

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, f"데이터 분석 중 오류 발생: {e}"

    year_pattern = re.compile(r'(\d{4})')
    offspring_map = defaultdict(list)
    elite_list = []

    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        if not my_text: return
        
        my_clean = my_text.strip()
        parent_clean = parent_text.strip()
        
        year_match = year_pattern.search(my_clean)
        birth_year = int(year_match.group(1)) if year_match else 0
        is_elite = '@' in my_clean

        info = {'name': my_clean, 'year': birth_year, 'is_elite': is_elite}

        # 가지연결 저장: 부모 노드 아래에 현재 자식 정보 저장
        if parent_clean != "Unknown":
            offspring_map[parent_clean].append(info)
        
        # 이름에 @가 있는 엘리트 종빈마만 따로 모음
        if is_elite:
            info['sire'] = parent_clean
            elite_list.append(info)

        for child in node:
            traverse(child, parent_text=my_clean)

    traverse(root)
    return (offspring_map, elite_list), None

# --- 메인 화면 로직 ---
st.title("🐎 엘리트 종빈마 비교 및 자마 검색")

# [보안] 암호 입력
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "3811":
    if password: st.error("암호가 틀렸습니다.")
    st.stop()

# 데이터 로딩
data_package, error_message = load_and_analyze_data()
if error_message:
    st.error(error_message)
    st.stop()

offspring_map, elite_list = data_package

# 사이드바 설정
st.sidebar.header("🔍 필터링")
search_sire = st.sidebar.text_input("씨수말(Sire) 이름으로 찾기")
year_range = st.sidebar.slider("연도 범위", 1900, 2026, (1900, 2026))

# 데이터 필터링
filtered = [
    e for e in elite_list 
    if (not search_sire or search_sire.lower() in e['sire'].lower()) and
       (year_range[0] <= e['year'] <= year_range[1])
]

# 결과 화면
st.markdown(f"### 📊 검색된 엘리트 종빈마: {len(filtered)}두")
st.info("체크박스를 누르면 연결된 자마(가지연결)가 나타납니다.")

for i, elite in enumerate(filtered):
    # 한 줄에 체크박스와 정보 배치
    c1, c2 = st.columns([0.05, 0.95])
    
    # 고유 ID 생성 (에러 방지용)
    chk_key = f"chk_{i}_{elite['name']}"
    is_open = c1.checkbox("", key=chk_key)
    
    with c2:
        st.markdown(f"⭐ **{elite['name']}** (부친: {elite['sire']})")
        
        # 체크박스가 선택되었을 때만 자마 정보 노출
        if is_open:
            children = offspring_map.get(elite['name'], [])
            if children:
                sorted_kids = sorted(children, key=lambda x: x['year'])
                with st.container(border=True):
                    st.write(f"📂 **{elite['name']}**의 자마 목록 ({len(sorted_kids)}두)")
                    cols = st.columns(3) # 3열로 출력
                    for idx, kid in enumerate(sorted_kids):
                        icon = "⭐" if kid['is_elite'] else "🐎"
                        cols[idx % 3].write(f"{icon} {kid['name']} ({kid['year'] if kid['year'] > 0 else '미상'}년)")
            else:
                st.caption("연결된 자마 데이터가 없습니다.")
    st.divider()




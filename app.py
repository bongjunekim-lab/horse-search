import streamlit as st
# --- 비밀번호 기능 시작 ---
password = st.text_input("접속 암호를 입력하세요", type="password")
if password != "5500":  # "5500"를 원하는 비밀번호로 바꾸세요
    st.warning("암호가 틀렸습니다. 올바른 암호를 입력해야 보입니다.")
    st.stop()
# --- 비밀번호 기능 끝 ---
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

# 1. 페이지 기본 설정
st.set_page_config(page_title="엘리트 혈통 추적기", page_icon="🧬", layout="wide")

# 2. 제목 및 설명
st.title("🐎 암말우성 씨수말 (Broodmare Sire)")
st.markdown("""
### 💡 프로그램 소개
지정한 기간 내에 태어난 **엘리트 종빈마**를 찾아, 그들의 부친(Broodmare Sire)별로 묶어서 보여줍니다.

> **엘리트 종빈마란?** > G급(Grade) 자마를 줄줄이 배출한, 유전력이 검증된 **슈퍼 씨암말**을 지칭합니다.
""")

# 3. 데이터 로딩 및 분석 함수 (캐싱으로 속도 최적화)
@st.cache_data
def load_and_analyze_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    
    if not os.path.exists(file_path):
        return None, "파일을 찾을 수 없습니다."
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return None, f"파일 로딩 오류: {e}"

    # 정규표현식 (연도 추출)
    year_pattern = re.compile(r'(\d{4})')
    
    # 데이터 저장소 (씨수말 이름 -> 딸들의 정보 리스트)
    merged_sire_map = defaultdict(list)

    # 재귀함수로 모든 노드 탐색
    def traverse(node, parent_text="Unknown"):
        my_text = node.get('TEXT', '')
        parent_clean = parent_text.strip() # 공백 제거

        if my_text:
            # 연도 추출
            year_match = year_pattern.search(my_text)
            birth_year = int(year_match.group(1)) if year_match else 0
            
            # 엘리트(@) 여부 확인
            is_elite = '@' in my_text

            mare_info = {
                'name': my_text.strip(),
                'year': birth_year,
                'sire_key': parent_clean,
                'is_elite': is_elite
            }
            
            # 엘리트 암말이고, 아빠가 있는 경우에만 저장
            if is_elite and parent_clean and parent_clean != "Unknown":
                merged_sire_map[parent_clean].append(mare_info)
        
        # 자식 노드로 이동 (현재 말을 부모로 전달)
        for child in node:
            traverse(child, parent_text=my_text)

    traverse(root)
    return merged_sire_map, None

# --- 메인 화면 로직 ---

# 데이터 불러오기
sire_map, error_message = load_and_analyze_data()

if error_message:
    st.error(f"❌ {error_message}")
    st.stop() # 에러 나면 여기서 멈춤

# 사이드바: 검색 조건 설정
st.sidebar.header("🔍 검색 옵션")
# 슬라이더로 연도 선택 (1900 ~ 2030)
start_year, end_year = st.sidebar.slider(
    "검색할 기간을 선택하세요:",
    min_value=1900, max_value=2030,
    value=(1990, 2024) # 기본값
)

st.divider() # 구분선
# --- [엘리트 종빈마 자식 검색 기능] ---
st.divider()
st.markdown("### 🐎 엘리트 종빈마 자식(자마) 검색")
st.info("여기에 '암말(종빈마)' 이름을 넣으면, 그녀가 배출한 **엘리트 자식들**을 보여줍니다.")

# 1. 검색창
mom_name = st.text_input("검색할 종빈마(엄마) 이름을 입력하세요", placeholder="예: Urban Sea, Hasili 등")

if mom_name:
    st.markdown(f"#### 🔎 '{mom_name}'의 자마 검색 결과")
    found_mom = False
    
    # 2. 데이터(sire_map)에서 '엄마'로 등록된 이름 찾기
    for parent_key, children_list in sire_map.items():
        # 대소문자 상관없이 이름이 포함되어 있는지 확인
        if mom_name.lower() in parent_key.lower():
            found_mom = True
            
            # 3. 자식 목록 출력
            with st.container():
                st.success(f"✅ **[{parent_key}]** 종빈마가 배출한 엘리트 자마: 총 {len(children_list)}두")
                
                # 자식들을 태어난 연도순으로 정렬해서 보여주기
                sorted_children = sorted(children_list, key=lambda x: x['year'])
                
                for child in sorted_children:
                    # 화면에 깔끔하게 출력
                    st.write(f"- 🐎 **{child['name']}** ({child['year']}년생)")
            
            st.divider() # 구분선

    # 4. 검색 결과가 없을 때 (자식이 없는 경우)
    if not found_mom:
        st.error("검색된 종빈마가 없습니다.")
        st.warning(f"💡 힌트: '{mom_name}'이(가) 데이터 파일에 '부모(상위 폴더)'로 등록되어 있지 않거나, 배출한 자식 중 '엘리트(@)' 등급이 없을 수도 있습니다.")

# ----------------------------------------------------
    # 2. [참고] 이 말의 '아빠' 찾기 (Daughter Search)
    # ---------------------------------------------------------
    st.markdown("#### 2. 🧬 이 말의 부모 (혈통)")
    daughter_found = False
    
    for sire_name, daughters in sire_map.items():
        for mare in daughters:
            if search_keyword.lower() in mare['name'].lower():
                daughter_found = True
                st.info(f"✅ **{mare['name']}** ({mare['year']}년생)의 아버지는 **[{sire_name}]** 입니다.")

    if not daughter_found:
        st.write("이 말의 부모 정보는 검색되지 않았습니다.")
# ----------------------
# 결과 분석 로직
sorted_results = []
total_found_mares = 0

# 전체 데이터 중에서 기간에 맞는 것만 필터링
for sire_name, daughters in sire_map.items():
    # 이 씨수말의 딸들 중, 기간 내에 태어난 딸만 골라냄
    filtered_daughters = [
        d for d in daughters 
        if start_year <= d['year'] <= end_year
    ]
    
    if filtered_daughters:
        # (씨수말 이름, 기간 내 딸들, 평생 낳은 엘리트 딸 수)
        sorted_results.append((sire_name, filtered_daughters, len(daughters)))
        total_found_mares += len(filtered_daughters)

# 결과가 많은 순서대로 정렬 (랭킹)
sorted_results.sort(key=lambda x: len(x[1]), reverse=True)

# 화면 출력
if not sorted_results:
    st.warning(f"⚠️ {start_year}년 ~ {end_year}년 사이에 검색된 엘리트 자마가 없습니다.")
else:
    st.success(f"✅ 총 **{len(sorted_results)}두**의 씨수말이 배출한 **{total_found_mares}두**의 엘리트 자마를 찾았습니다.")
    
    # 랭킹별 출력
    for rank, (sire_name, daughters, life_time_count) in enumerate(sorted_results, 1):
        # 자마들을 연도순으로 정렬
        daughters.sort(key=lambda x: x['year'])
        
        # 별점 계산 (평생 업적)
        star_mark = "⭐" * life_time_count
        if life_time_count > 10:
            star_mark = f"⭐ x {life_time_count}"
        
        # 접었다 펴기 기능 (Expander) 사용
        # 제목: [랭킹] 씨수말이름 (기간 내 자마 수 / 평생 자마 수)
        expander_title = f"[{rank}위] {sire_name} (검색 기간 내: {len(daughters)}두) {star_mark}"
        
        with st.expander(expander_title):
            st.markdown(f"**📜 {sire_name}의 엘리트 자마 목록 ({start_year}~{end_year})**")
            for mare in daughters:
                # 리스트 형태로 출력

                st.text(f"  - [{mare['year']}년생] {mare['name']}")









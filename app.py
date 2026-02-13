import streamlit as st
import xml.etree.ElementTree as ET
import re
import os

# 스타일 설정: 선생님의 눈이 편안하시도록 전문가용 레이아웃 적용
st.set_page_config(page_title="혈통 닉(Nick) 분석 시스템", layout="wide")
st.markdown("""
    <style>
    .result-box { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 8px solid; }
    .male { background-color: #f1f8ff; border-color: #0077CC; }
    .female { background-color: #fff5f5; border-color: #C0392B; }
    .bms-final { color: #ff4b4b; font-weight: bold; font-size: 1.1em; text-decoration: underline; }
    .header { background-color: #e6fffa; padding: 20px; border-radius: 12px; border: 2px solid #38b2ac; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def analyze_nicks_by_arrow(query):
    file_path = '우수한 경주마(수말, 암말).mm' # 전수조사 대상 파일
    if not os.path.exists(file_path): return None, "데이터 파일을 찾을 수 없습니다."

    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # [핵심] 500개 전수조사 기반의 ID 및 부모 관계 매핑
    id_map = {n.get('ID'): n for n in root.iter('node') if n.get('ID')}
    parent_map = {c: p for p in root.iter() for c in p}

    # 1. 씨수말(부마) 검색
    target_sire = None
    for node in root.iter('node'):
        txt = node.get('TEXT', '').strip()
        if query.lower() in txt.lower() and node.findall('node'):
            target_sire = node
            break
    if not target_sire: return None, f"'{query}' 씨수말을 찾을 수 없습니다."

    males, females = [], []

    # 2. 자마 전수 조사 및 '가지(arrowlink)' 있는 것만 발췌
    for foal in target_sire.findall('node'):
        arrow = foal.find('arrowlink')
        if arrow is None: continue # 가지가 없는 자마는 과감히 버림

        f_text = foal.get('TEXT', '').strip()
        dest_id = arrow.get('DESTINATION')
        
        # 3. 화살표를 타고 모마(Dam)로 점프
        mom_node = id_map.get(dest_id)
        bms_info = "외조부 정보 없음"
        
        if mom_node is not None:
            # 4. 모마의 부모 노드에서 외조부(BMS) 정보 낚아채기
            gs_node = parent_map.get(mom_node)
            if gs_node is not None:
                bms_info = gs_node.get('TEXT', '').strip()

        # 결과 조립 및 성별 분류
        display = f"🐎 자마: {f_text}<br>↳ <span class='bms-final'>외조부: {bms_info}</span>"
        
        if "암)" in f_text or "@" in f_text:
            females.append(display)
        else:
            males.append(display)
            
    return (males, females, target_sire.get('TEXT')), None

# --- 화면 UI ---
st.markdown("<div class='header'><h2>🐎 혈통 닉(Nick) 분석 시스템</h2>"
            "<p>선생님의 지시사항: 가지(arrowlink)가 연결된 자마만 발췌하여 모마의 부마(외조부)를 즉시 추적합니다.</p></div>", unsafe_allow_html=True)

query_input = st.text_input("분석할 씨수말(부마) 이름을 입력하세요 (예: Bernardini):", "Bernardini").strip()

if query_input:
    res, err = analyze_nicks_by_arrow(query_input)
    if err:
        st.warning(err)
    else:
        m, f, s_name = res
        st.success(f"✅ {s_name} 분석 완료 (유효 데이터: {len(m)+len(f)}두)")
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"🟦 아들 자마 (닉 분석 대상: {len(m)})")
            for item in m: st.markdown(f'<div class="result-box male">{item}</div>', unsafe_allow_html=True)
        with col2:
            st.error(f"🟥 딸 자마 (닉 분석 대상: {len(f)})")
            for item in f: st.markdown(f'<div class="result-box female">{item}</div>', unsafe_allow_html=True)

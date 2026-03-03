import streamlit as st
import xml.etree.ElementTree as ET
import re
import os
from collections import defaultdict

def clean_name_symbols(text):
    """씨수말 이름 맨 앞의 숫자, 특수기호(도형, 기호 등), 공백을 모두 제거합니다."""
    cleaned = re.sub(r'^[\d\s\W_]+', '', text)
    return cleaned.strip()

# 1. 페이지 설정
st.set_page_config(page_title="엘리트 혈통 추적 시스템", layout="wide")

# CSS 설정
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
        margin-bottom: 3px;
        color: #333333;
        font-size: 1.05em;
    }
    /* G1-7 수말 및 @, # 암말 강조 (적색) */
    .premium-progeny {
        color: #D32F2F !important;
        font-weight: bold;
    }
    .star-daughter {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .sire-deep-blue-bold {
        color: #0000FF !important;
        font-weight: 900 !important;
    }
    .hr-line {
        margin: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    
    /* 아코디언(expander) 헤더 폰트 크기 및 굵기 조정 */
    div[data-testid="stExpander"] summary p {
        font-size: 1.2em !important; 
        font-weight: 400 !important; 
        color: #111111 !important;
    }
    
    /* 랭킹 타이틀 내 강조된 통산 점수를 부마와 동일한 진한 파란색(#0000FF)으로 강제 덮어쓰기 */
    div[data-testid="stExpander"] summary p span,
    div[data-testid="stExpander"] summary p strong {
        color: #0000FF !important;
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def parse_bloodline_data():
    file_path = '우수한 경주마(수말, 암말).mm'
    if not os.path.exists(file_path):
        return None, None, None, "파일을 찾을 수 없습니다."
    try:
        tree = ET.parse(file_path); root = tree.getroot()
        id_to_text = {}; id_to_parent_text = {}
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
            clean = clean.replace('＠', '').replace('＃', '')
            clean = clean.replace('암)', '').replace('수)', '').replace('거)', '')
            clean = clean.replace('가.', '').replace('나.', '').replace('다.', '')
            clean = clean.split('(')[0]
            return clean.strip().lower()
            
        def traverse(node, parent_text="Unknown"):
            my_text = node.get('TEXT', '')
            if my_text and ('@' in my_text or '#' in my_text or '＠' in my_text or '＃' in my_text):
                year_match = year_pattern.search(my_text)
                birth_year = int(year_match.group(1)) if year_match else 0
                progeny_info = []; seen_ids = set()
                mare_pure_name = normalize_name(my_text)
                for arrow in node.findall('arrowlink'):
                    dest_id = arrow.get('DESTINATION')
                    if dest_id in id_to_text:
                        if dest_id in seen_ids: continue
                        child_raw_text = id_to_text[dest_id]
                        child_pure_name = normalize_name(child_raw_text)
                        if mare_pure_name == child_pure_name: continue
                        progeny_info.append(dest_id)
                        seen_ids.add(dest_id)
                mare_info = {'name': my_text.strip(), 'year': birth_year, 'progeny_ids': progeny_info}
                if parent_text != "Unknown": elite_sire_map[parent_text.strip()].append(mare_info)
            for child in node.findall('node'): traverse(child, my_text)
        traverse(root); return elite_sire_map, id_to_text, id_to_parent_text, None
    except Exception as e: return None, None, None, f"분석 오류: {str(e)}"

# UI 메인
st.title("🐎 암말우성 씨수말 랭킹과 점수")

password = st.text_input("접속 암호를 입력하세요", type="password")

# --- 로그인 전 (대문) 공지사항 노출 ---
if password != "5500":
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #d32f2f; margin-top: 10px; margin-bottom: 20px;'>
        <h4 style='margin-top: 0; color: #333;'>📢 업데이트 소식 및 이용 안내</h4>
        <ul style='margin-bottom: 0; color: #555; line-height: 1.7; font-size: 1.05em;'>
            <li><b>[기능 추가]</b> BMS(외조부)의 유전력을 기준으로 점수화 시스템을 도입했습니다. 좌측 사이드바의 <b>현구간 최소 점수 필터(Cut-off)</b>를 통해 원하는 기준 이상의 씨수말만 필터링할 수 있습니다. (기본값 3.0점)</li>
            <li><b>[점수 안내]</b> 사용자가 지정한 출생 연도의 점수는 <b>'현구간 유전력'</b>을 뜻하며, 역대 총점은 <b>'통산 유전력'</b>으로 병기됩니다. 두 점수가 3점 이상 차이 날 경우 <span style='color: #0000FF; font-weight: 900;'>통산 점수</span>가 파란색으로 강조됩니다.</li>
            <li><b>[UI/UX]</b> 랭킹 타이틀 목록에서 씨수말 이름 앞의 특수기호 및 숫자가 제거되었습니다.</li>
            <li><b>[분석 팁]</b> 현구간 점수가 1~2점인 씨수말은 외조부로서의 유전력보다 교배된 부마(Sire)의 우연성에 기인했을 확률이 높아 필터링을 권장합니다.</li>
            <li><b>[검색 팁]</b> 보유한 말의 외조부가 획득한 별(⭐) 개수를 찾으려면, 최소 점수 필터를 <b>0</b>으로 설정한 후 <b>Ctrl + F</b>를 눌러 마명을 검색하십시오.</li>
            <li><b>[개발 목표]</b> 본 시스템의 최종 목적은 별이 1개인 외조부라도 그 딸들이 G급 자마를 몇 두나 배출하는지 일괄 확인하여, 외조부 간의 초기 잠재력 우열을 선제적으로 파악하는 데 있습니다.</li>
            <li><b>[문의처]</b> 사용 중 불편한 점이나 개선 사항은 <b>bongjunekim@gmail.com</b> 또는 <b>010-8982-3811</b>(문자 요망)로 남겨주시면 확인 후 연락드리겠습니다.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if password: 
        st.error("암호 오류")
    st.stop()

# --- 로그인 후 (데이터 뷰) 초슬림 공지사항 노출 ---
with st.expander("📢 업데이트 소식 및 이용 안내 (클릭하여 펴기)"):
    st.markdown("""
    <ul style='margin-bottom: 0; color: #555; line-height: 1.6; font-size: 0.95em;'>
        <li><b>[기능 추가]</b> BMS(외조부) 유전력 기준 점수화 및 현구간 최소 점수 필터(Cut-off) 적용</li>
        <li><b>[점수 안내]</b> 지정 연도 점수 = <b>현구간 유전력</b> / 역대 총점 = <b>통산 유전력</b> (3점 이상 차이 시 <span style='color: #0000FF; font-weight: 900;'>통산 점수</span> 파란색 강조)</li>
        <li><b>[UI/UX]</b> 랭킹 타이틀 내 씨수말 이름 특수기호/숫자 제거</li>
        <li><b>[분석 팁]</b> 현구간 1~2점은 우연성에 기인했을 확률이 높아 최소 3.0점 이상 필터링 권장</li>
        <li><b>[검색 팁]</b> 최소 점수 필터를 0으로 둔 후 <b>Ctrl + F</b>로 보유 말의 외조부 마명 검색 가능</li>
        <li><b>[개발 목표]</b> 별 1개 외조부의 G급 자마 배출량 일괄 확인 및 초기 잠재력 우열 선제 파악</li>
        <li><b>[문의처]</b> bongjunekim@gmail.com / 010-8982-3811(문자 요망)</li>
    </ul>
    """, unsafe_allow_html=True)

elite_map, id_to_text, id_to_parent_text, err = parse_bloodline_data()
if err: st.error(err); st.stop()

# 좌측 사이드바 필터 설정 영역
st.sidebar.markdown("### 🔍 검색 조건 설정")
start_y, end_y = st.sidebar.slider("종빈마 출생 연도 필터", 1900, 2030, (1900, 2026))

st.sidebar.markdown("---")
min_score = st.sidebar.slider("현구간 최소 점수 필터", 0.0, 30.0, 3.0, 0.5)

st.sidebar.markdown("---")
# 부마 BMS 보기 체크박스 추가
show_sire_bms = st.sidebar.checkbox("혈통상 모계 깊이(부마 BMS) 보기", value=False)

g1_pattern = re.compile(r'G1-(\d+)')

# 점수 계산을 위한 내부 함수
def calculate_score(daughters_list):
    n1 = len(daughters_list)
    s2 = 0
    n2 = 0
    productive_k = set()
    
    for d in daughters_list:
        for p_id in d['progeny_ids']:
            child_name = id_to_text.get(p_id, "")
            g1_match = g1_pattern.search(child_name)
            is_high_g1 = bool(g1_match and int(g1_match.group(1)) >= 7)
            is_daughter = '암)' in child_name
            
            is_n2 = ('@' in child_name or '#' in child_name or '＠' in child_name or '＃' in child_name) and is_daughter
            is_s2 = is_high_g1 and not is_daughter
            
            if is_n2:
                n2 += 1
                productive_k.add(d['name'])
            if is_s2:
                s2 += 1
                productive_k.add(d['name'])
                
    k = len(productive_k)
    score = (1.0 * n1) + (1.5 * s2) + (2.0 * n2) + (1.0 * k)
    return score

# 전체 씨수말의 BMS 점수 사전(Dictionary) 미리 생성
sire_all_bms_scores = {}
for sire, all_daughters in elite_map.items():
    sire_clean_key = sire.strip()
    filtered_d = [d for d in all_daughters if start_y <= d['year'] <= end_y]
    
    all_time_s = calculate_score(all_daughters)
    current_s = calculate_score(filtered_d) if filtered_d else 0.0
    
    # 점수가 0 이상인 경우에만 딕셔너리에 저장
    if all_time_s > 0:
        sire_all_bms_scores[sire_clean_key] = (current_s, all_time_s)

# 데이터 가공 및 점수 계산 (메인 랭킹용)
scored_results = []
for sire, all_daughters in elite_map.items():
    # 필터가 적용된 자마 목록 (한 줄로 작성하여 SyntaxError 방지)
    filtered_daughters = [d for d in all_daughters if start_y <= d['year'] <= end_y]
    
    if not filtered_daughters:
        continue
        
    # 통산 점수 계산 (전체 자마 기준)
    all_time_score = calculate_score(all_daughters)
    
    # 현구간 점수 계산 (필터링된 자마 기준)
    n1 = len(filtered_daughters)
    filtered_score = calculate_score(filtered_daughters)
    
    # 계산된 현구간 점수가 사이드바에서 설정한 최소 점수 이상일 때만 결과에 포함
    if filtered_score >= min_score:
        scored_results.append({
            'sire': sire,
            'daughters': filtered_daughters,
            'n1': n1,
            'score': filtered_score,
            'all_time_score': all_time_score
        })

# 합산 점수 기준 내림차순 정렬
scored_results.sort(key=lambda x: x['score'], reverse=True)

if not scored_results: 
    st.warning("조건에 맞는 데이터가 없습니다. 사이드바의 필터 조건을 조정해 보세요.")
else:
    for i, data in enumerate(scored_results[:500], 1):
        sire = data['sire']
        daughters = data['daughters']
        n1 = data['n1']
        score = data['score']
        all_time_score = data['all_time_score']
        stars = "⭐" * n1
        
        display_sire = clean_name_symbols(sire)
        
        if (all_time_score - score) >= 3.0:
            all_time_str = f":blue[**(통산: {all_time_score:.1f}점)**]"
        else:
            all_time_str = f"(통산: {all_time_score:.1f}점)"
        
        expander_title = f"[{i}위] {display_sire} (엘리트 종빈마: {n1}두) {stars} | 🏆 현구간: {score:.1f}점 {all_time_str}"
        
        with st.expander(expander_title):
            sire_to_mothers = defaultdict(set)
            for d in daughters:
                for p_id in d['progeny_ids']:
                    p_sire_name = id_to_parent_text.get(p_id, "정보 없음")
                    sire_to_mothers[p_sire_name].add(d['name'])
            nick_sires = [s for s, mothers in sire_to_mothers.items() if len(mothers) >= 2]
            bg_palette = ["#FFEBEE", "#E0F2F1", "#F3E5F5", "#E8F5E9", "#FBE9E7"]
            border_palette = ["#D32F2F", "#00796B", "#7B1FA2", "#388E3C", "#E64A19"]
            nick_style_map = {}
            color_idx = 0
            for ns in nick_sires:
                nick_style_map[ns] = (border_palette[color_idx % 5], bg_palette[color_idx % 5])
                color_idx += 1

            for d in daughters:
                st.markdown(f"<div class='elite-mare'>&#128142; {d['name']}</div>", unsafe_allow_html=True)
                
                if d['progeny_ids']:
                    for p_id in d['progeny_ids']:
                        child_name = id_to_text.get(p_id, "")
                        father_name = id_to_parent_text.get(p_id, "정보 없음")
                        
                        g1_match = g1_pattern.search(child_name)
                        is_high_g1 = bool(g1_match and int(g1_match.group(1)) >= 7)
                        is_daughter = '암)' in child_name
                        is_elite_daughter = ('@' in child_name or '#' in child_name or '＠' in child_name or '＃' in child_name) and is_daughter
                        is_high_g1_son = is_high_g1 and not is_daughter
                        
                        if is_high_g1_son or is_elite_daughter:
                            child_display = f"<span class='premium-progeny'>{child_name}</span>"
                        elif '*' in child_name and is_daughter:
                            child_display = f"<span class='star-daughter'>{child_name}</span>"
                        else: 
                            child_display = child_name
                        
                        # 체크박스 활성화 시, 부마의 BMS 점수를 검은색으로 3칸 띄워서 추가
                        bms_depth_text = ""
                        clean_father_name = father_name.strip()
                        if show_sire_bms and clean_father_name in sire_all_bms_scores:
                            cur_s, all_s = sire_all_bms_scores[clean_father_name]
                            bms_depth_text = f"&nbsp;&nbsp;&nbsp;<span style='color:#000000; font-weight:bold; font-size:0.95em;'>[BMS 현구간: {cur_s:.1f}점, 통산 점수: {all_s:.1f}점]</span>"

                        if is_high_g1_son or is_elite_daughter:
                            if father_name in nick_style_map:
                                b_c, bg_c = nick_style_map[father_name]
                                father_display = f"<span style='color:#0000FF; background-color:{bg_c}; font-weight:900; padding:2px 6px; border-radius:4px; border: 1px solid {b_c}60;'>{father_name}</span>{bms_depth_text}"
                            else:
                                father_display = f"<span class='sire-deep-blue-bold'>{father_name}</span>{bms_depth_text}"
                        else:
                            if father_name in nick_style_map:
                                b_c, bg_c = nick_style_map[father_name]
                                father_display = f"<span style='color:{b_c}; background-color:{bg_c}; font-weight:400; padding:2px 6px; border-radius:4px; border: 1px solid {b_c}60;'>{father_name}</span>{bms_depth_text}"
                            else: 
                                father_display = f"<b>{father_name}</b>{bms_depth_text}"
                        
                        st.markdown(f"<div class='progeny-item'>🔗 [연결] {child_display} ({father_display})</div>", unsafe_allow_html=True) 

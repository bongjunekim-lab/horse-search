import pandas as pd
import os

def generate_filter_report():
    # 1. 경로 설정 (C:\engineering)
    folder_path = r'C:\engineering'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_name = 'Filter_Impedance_Design_Report.xlsx'
    full_path = os.path.join(folder_path, file_name)

    # 2. 설계 데이터 구성 (사용자 최적 설계안 반영)
    # 150(Flash) -> 120(Bridge) -> 45+PB(Concentration)
    layers = [
        {
            "Layer": "1st (Front)",
            "Particle_Size_um": 150,
            "Thickness_mm": 0.438,
            "PB_Coating": "No",
            "Rel_Resistance": 1.0,
            "Functional_Role": "Flash (Initial Absorption)"
        },
        {
            "Layer": "2nd (Middle)",
            "Particle_Size_um": 120,
            "Thickness_mm": 0.562,
            "PB_Coating": "No",
            "Rel_Resistance": 2.25,
            "Functional_Role": "Bridge (Transition Zone)"
        },
        {
            "Layer": "3rd (Rear)",
            "Particle_Size_um": 45,
            "Thickness_mm": 0.500,
            "PB_Coating": "Yes (3μm)",
            "Rel_Resistance": 4.85,
            "Functional_Role": "Concentration (Final Trapping)"
        }
    ]
    df_layers = pd.DataFrame(layers)

    # 3. 공학적 성능 지표 계산
    # 저항 합계를 기반으로 한 시뮬레이션 수치
    total_r = df_layers['Rel_Resistance'].sum()
    
    summary = {
        "Metric_Indicator": [
            "Sequential Stability Index",
            "Expected Capture Capacity (mg)",
            "Trap Duration (min)",
            "Discharge Duration (min)",
            "Total Process Time (min)"
        ],
        "Value": [
            round(total_r / 3, 2), # 안정성 지수
            120.0,                 # 예상 포집량
            106.1,                 # 포집 시간
            99.5,                  # 배출 시간
            205.6                  # 총 시간
        ],
        "Unit": ["Index", "mg", "min", "min", "min"]
    }
    df_summary = pd.DataFrame(summary)

    # 4. 엑셀 파일로 저장
    try:
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            df_layers.to_excel(writer, sheet_name='Layer_Spec', index=False)
            df_summary.to_excel(writer, sheet_name='Performance_Analysis', index=False)
        print(f"성공: 파일이 생성되었습니다 -> {full_path}")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    generate_filter_report()
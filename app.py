import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as html
from PIL import Image
import random
from datetime import datetime, timedelta
import plotly.express as px

plt.rc('font', family='MalGun Gothic')
plt.rcParams['axes.unicode_minus'] = False

## 데이터프레임 일부 행 표시 함수 - head는 style 메소드 지원 안해서 따로적용
def display_dataframe(df, n=10, styled=False):
    random_rows = df.sample(n=n)
    if styled:
        st.dataframe(random_rows.style.applymap(highlight_counts, subset=['횟수']))
    else:
        st.dataframe(random_rows)


## 횟수 8이상 강조표시 함수생성
def highlight_counts(val):
    color = ''
    if val >= 6:
        color = 'background-color: red'
    elif 3 <= val <= 5:
        color = 'background-color: yellow'
    return color

## 카드식별번호 포맷함수생성
def format_card_number(num):
    num_str = f'{num:016d}'  # 16자리로 패딩
    return f'{num_str[:4]}-{num_str[4:8]}-{num_str[8:12]}-{num_str[12:]}'


df = pd.read_csv("data/app_df.csv")
의심리스트_데이터 = pd.read_csv("data/의심리스트_df.csv", encoding='cp949')
카드태그_데이터 = pd.read_csv("data/카드태그_df.csv", encoding='cp949')
카드태그_데이터['일시'] = pd.to_datetime(카드태그_데이터['일시'])


#블랙리스트 세션 관리
if '블랙리스트' not in st.session_state:
    st.session_state.블랙리스트 = pd.DataFrame(columns=의심리스트_데이터.columns)

if 'removed_cards' not in st.session_state:
    st.session_state.removed_cards = pd.DataFrame(columns=의심리스트_데이터.columns)

with st.sidebar:
    choose = option_menu('서울교통공사',['통합-대시보드', '영상', '블랙리스트'],
        icons=['bi bi-check-square' , 'bi bi-caret-right', 'bi bi-cart-x-fill'],
        menu_icon='bi bi-bank',
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#fafafa"},
            "icon": {"color": "blue", "font-size": "25px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "10px", "--hover-color": "#eee"},
        }
    )

if choose == '통합-대시보드':
    st.title('통합')
    station = list(df['역명'].unique())
    selected_station = st.sidebar.selectbox('역을 선택하세요', station)
    selected_date = st.sidebar.date_input(
        "날짜를 선택하세요:",
        min_value=pd.to_datetime('2024-07-01'),
        max_value=pd.to_datetime('2024-07-31'),
        value=pd.to_datetime('2024-07-01')
    )

#메인 레이아웃
    col1, col2 = st.columns(2)

#왼쪽컬럼 - 한달 달력 및 의심 리스트 데이터
    with col1:    
    #의심리스트 데이터
        st.subheader('의심리스트')
        display_dataframe(의심리스트_데이터, n=10, styled=True)

        #의심리스트에서 선택한 카드 블랙리스트로 이동
        suspicious_cards = st.multiselect(
            '블랙리스트로 보낼 카드식별번호를 선택하세요.',
            options = 의심리스트_데이터['카드식별번호'].unique()
        )

        if st.button('블랙리스트로 이동'):
            if suspicious_cards:
                selected_cards = 의심리스트_데이터[의심리스트_데이터['카드식별번호'].isin(suspicious_cards)]
                st.session_state.블랙리스트 = pd.concat([st.session_state.블랙리스트, selected_cards]).drop_duplicates()
                st.success(f'{len(suspicious_cards)}개의 카드가 블랙리스트로 이동되었습니다.')
            else:
                st.warning('이동할 카드를 선택하세요.')

                

#오른쪽 컬럼 - 카드 태그 테이블

    with col2:
        show_card_log = st.checkbox('의심카드 태그로그 보기', value=True)
        if show_card_log:
            st.subheader('카드태그로그 데이터')
            filtered_df = 카드태그_데이터[카드태그_데이터['일시'] <= pd.to_datetime(selected_date)]
            st.dataframe(filtered_df)
        
#시각화        
    station_data = df[df['역명'] == selected_station]
    
    ## 데이터 필터링
    g_boarding = station_data[(station_data['할인'] == '일반') & (station_data['구분'] == '승차')]
    g_alighting = station_data[(station_data['할인'] == '일반') & (station_data['구분'] == '하차')]
    
    old_boarding = station_data[(station_data['할인'] == '우대권') & (station_data['구분'] == '승차')]
    old_alighting = station_data[(station_data['할인'] == '우대권') & (station_data['구분'] == '하차')]
# Plotly Express를 사용하여 그래프를 생성합니다.
    fig = px.line()

    fig.add_scatter(x=g_boarding['시간대'], y=g_boarding['이용량'], mode='lines', name='일반 승차')
    fig.add_scatter(x=g_alighting['시간대'], y=g_alighting['이용량'], mode='lines', name='일반 하차')
    fig.add_scatter(x=old_boarding['시간대'], y=old_boarding['이용량'], mode='lines', name='우대권 승차')
    fig.add_scatter(x=old_alighting['시간대'], y=old_alighting['이용량'], mode='lines', name='우대권 하차')

    fig.update_layout(
        title=f'{selected_station} 시간대 별 일반 및 우대권 이용량',
        xaxis_title='시간대',
        yaxis_title='이용량',
        legend_title='구분'
    )
    st.plotly_chart(fig)
    
elif choose == '영상':
    st.title('개찰구 CV')
    station = list(df['역명'].unique())
    selected_station = st.sidebar.selectbox('역을 선택하세요', station)
    st.subheader(f'{selected_station} 영상')


elif choose == '블랙리스트': 
    station = list(df['역명'].unique())
    selected_station = st.sidebar.selectbox('역을 선택하세요', station)
    
    selected_date = st.sidebar.date_input(
        "날짜를 선택하세요:",
        min_value=pd.to_datetime('2024-07-01'),
        max_value=pd.to_datetime('2024-07-31'),
        value=pd.to_datetime('2024-07-01')
    )
    try:
        if '일시' in st.session_state.블랙리스트.columns:
            st.session_state.블랙리스트['일시'] = pd.to_datetime(st.session_state.블랙리스트['일시'])
            blacklist_df = st.session_state.블랙리스트[st.session_state.블랙리스트['일시'] <= pd.to_datetime(selected_date)]
        else:
            blacklist_df = st.session_state.블랙리스트
            #예외처리
    except Exception as e:
        st.error(f"Error processing blacklist data: {e}")
        blacklist_df = pd.DataFrame(columns=st.session_state.블랙리스트.columns)

    st.sidebar.subheader(f'{selected_station}의 블랙리스트 ({selected_date})')
    st.sidebar.dataframe(blacklist_df)
    
    st.title(f'{selected_station} 블랙리스트 관리')
    st.subheader('블랙리스트에서 제거할 카드 선택')

# 블랙리스트에서 제거할 카드식별번호 선택
    cards_to_remove = st.multiselect(
        '제거할 카드식별번호를 선택하세요',
        options=blacklist_df['카드식별번호'].unique()
    )

    # 제거 버튼
    if st.button('제거'):
        if cards_to_remove:
        # 블랙리스트 데이터에서 선택한 카드 제거
            removed_cards = blacklist_df[blacklist_df['카드식별번호'].isin(cards_to_remove)]
            st.session_state.블랙리스트.drop(st.session_state.블랙리스트[st.session_state.블랙리스트['카드식별번호'].isin(cards_to_remove)].index, inplace=True)
        
            st.session_state.removed_cards = pd.concat([st.session_state.removed_cards, removed_cards])
            st.success(f'{len(cards_to_remove)}개의 카드가 블랙리스트에서 제거되었습니다.')
        else:
            st.warning('제거할 카드를 선택하세요.')

    st.subheader('제거된 블랙리스트')
    st.dataframe(st.session_state.removed_cards)
    
# 복원할 카드식별번호 선택
# 복원할 카드 식별 번호를 체크박스 리스트로 표시
    restore_cards = st.multiselect(
        '복원할 카드식별번호를 선택하세요',
        options=st.session_state.removed_cards['카드식별번호'].values
    )

# 복원 버튼
    if st.button('복원'):
        if restore_cards:
        # 제거된 카드에서 선택한 카드를 블랙리스트로 복원
            restored_cards = st.session_state.removed_cards[st.session_state.removed_cards['카드식별번호'].isin(restore_cards)]
            st.session_state.removed_cards = st.session_state.removed_cards[~st.session_state.removed_cards['카드식별번호'].isin(restore_cards)]
        
        # 블랙리스트 데이터에 복원된 카드 추가
            st.session_state.블랙리스트 = pd.concat([st.session_state.블랙리스트, restored_cards])
            st.success(f'{len(restore_cards)}개의 카드가 블랙리스트에 복원되었습니다.')
        else:
            st.warning('복원할 카드를 선택하세요.')
# 업데이트된 블랙리스트 데이터와 제거된 카드 목록을 표시
    st.subheader('업데이트된 블랙리스트')
    st.dataframe(st.session_state.블랙리스트)
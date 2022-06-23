# Create your views here.
# from __future__ import unicode_literals
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views import View
from django.shortcuts import redirect, render
from .forms import startForm
import pymysql
import pandas as pd
import numpy as np
import json
from fiona.crs import from_epsg
import geopandas as gpd
from keplergl import KeplerGl
from sqlalchemy import create_engine
from shapely.geometry.polygon import Polygon,LineString
from datetime import datetime, timedelta, timezone
import os
import warnings
from haversine import haversine
warnings.filterwarnings('ignore')

# 실행용 경로 drive/MyDrive/"팀 프로젝트"/"3차 프로젝트"/작업물/조남현/SkyRoad_for_Drone

# mountain_path = '/content/drive/MyDrive/"팀 프로젝트"/"3차 프로젝트"/작업물/조남현/SkyRoad_for_Drone/dataset'
mountain_path = 'dataset'
# array_path = '/content/drive/MyDrive/"팀 프로젝트"/"3차 프로젝트"/작업물/조남현/SkyRoad_for_Drone/dataset'
array_path = 'dataset'

global trip_count
global trip_multi
trip_count = 0
trip_multi = dict(type="FeatureCollection", features=[])

class service_window:
  #데이터 베이스에서 해당이름의 데이터 가져오기
  @staticmethod
  def load_db_data(name):
    conn = pymysql.connect(host='34.64.132.212', user='root', password='ASewetsvc124~1242#%1wsdeWXV', db='source')
    sql_state=f'SELECT * FROM `{name}`'
    name=pd.read_sql_query(sql_state, conn)
    return name

  #경계값을 지나는 장애물 검출하기
  @staticmethod
  def check_intersects(df,df1,poly):
    #pandas의 경우 데이터 타입을 geometry로 변경
    df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
    df = gpd.GeoDataFrame(df, geometry=df['geometry'])
    df['within']=df[['geometry']].intersects(poly)
    df=df.loc[df['within']==True]

    #geometry 타입은 그대로 검출에 사용
    df1['within']=df1[['geometry']].intersects(poly)
    df1=df1.loc[df1['within']==True]
    return df, df1

  # 병원,빌딩,드론 공항 불러오기
  @staticmethod
  def load_data():
    hospital=service_window.load_db_data("군집화된병원6")
    building=service_window.load_db_data("building_final")
    blood=service_window.load_db_data("드론공항위치")

    #산의 데이터 불러오기
    mountain = gpd.read_file(f'{mountain_path}/11.shp', encoding='euc-kr')
    mountain=mountain[['geometry']]
    mountain=mountain.to_crs(epsg=4326)
    mountain=mountain.drop(697)

    return hospital, building, blood, mountain

  # 고도를 고려한 경로의 추가
  @staticmethod
  def set_path(data_):
    data=[]
    for i in range(len(data_)):
      if i==0:
        data.append(data_[i])
        data.append(data_[i])
      elif i == len(data_)-1:
        data.append(data_[i])
        data.append(data_[i])
        data.append(data_[i])
      else:
        data.append(data_[i])

      path=pd.DataFrame(columns=['s_x','s_y','e_x','e_y'],data=data)

      #고도를 고려한 경로한 시작좌표와 도착좌표 변경
      path['e_x'][0] = path['s_x'][0]
      path['e_y'][0] = path['s_y'][0]
      # path['e_x'][1] = path['s_x'][1]
      # path['e_y'][1] = path['s_y'][1]

      path['s_x'][len(path)-2] = path['e_x'][len(path)-2]
      path['s_y'][len(path)-2] = path['e_y'][len(path)-2]
      path['s_x'][len(path)-1] = path['e_x'][len(path)-1]
      path['s_y'][len(path)-1] = path['e_y'][len(path)-1]

    return path

  # (line)경로 만들기
  @staticmethod
  def get_path(start,target):
    data = service_window.load_array(start,target)
    data = service_window.set_path(data)

    return data

  # 시간의 흐름에 따른 경로 만들기
  @staticmethod
  def get_path_trip(path):

    global trip_count 
    global trip_multi
   
    # 시작좌표와 도착좌표를 Point로 변경
    path['start'] = list(zip(path['s_y'], path['s_x']))
    path['end'] = list(zip(path['e_y'], path['e_x']))

    # 위에서 구한 Point를 Line으로 변경
    path['line'] = path.apply(lambda row : LineString([row['start'], row['end']]), axis=1)

    # 좌표간의 거리 추가를 위한 초기값 생성
    path['length']=0

    # 단위를 M로한 시작좌표와 도착좌표의 실제 거리
    for i in range(2,len(path)-2):
      path['length'][i] = haversine(path['start'][i], path['end'][i], unit = 'm')

    path = path[['s_x','s_y','length']]

    # 지표면에서 50미터 위로 다니기에 해당 길이는 50미터로 설정
    path['length'][1] = 50
    path['length'][len(path)-2] = 50 

    # 드론 속도를 고려한 초속 속도 
    speed = 70000 #70000m/h
    second_speed = speed/3600 

    # 길이를 초속으로 나누어 걸리는 시간을 구함
    # 상승과 하강은 1m/s 이므로 임의로 변경
    path['time'] = path['length'] / second_speed
    path['time'][0]=50
    path['time'].iloc[-2]=50

    # google colab에서 시간차이가 9시간 걸림
    now = datetime.now()+timedelta(hours=9)
    current = now.timestamp()
    
    # 현재시간을 구함
    path['datetime']=0
    path['datetime'][0]=current

    # 현재시간을 기준으로 해서 해당 좌표에서의 시간을 계산
    for i in range(1,len(path)):
      path['datetime'][i]=path['datetime'][i-1]+path['time'][i-1]

    path['trip_id'] = trip_count
    trip_count = trip_count+1
    print(trip_count)

    # 효과적인 시각화를 위해 높이는 300으로 설정 -> 실제 값은 해당 고도값 (50) 
    path['altitude']=300
    path['altitude'][0]=0
    path['altitude'].iloc[-1]=0

    #시작 도착 좌표 오차주기 -> 시각화 툴에서 같은 좌표에서의 높이 변경은 오차가 있어야 표현됨
    path['s_x'][0] = path['s_x'][0]-0.0001
    path['s_y'][0] = path['s_y'][0]-0.0001
    path['s_x'][len(path)-1] = path['s_x'][len(path)-1]-0.0001
    path['s_y'][len(path)-1] = path['s_y'][len(path)-1]-0.0001

    # 걸리는 시간과 도착시 시간을 구함
    elapsed_time = path['datetime'][len(path)-1]-path['datetime'][0]
    arrival_time = path['datetime'][len(path)-1]

    d = datetime.fromtimestamp(arrival_time)
    arrival_time=d.strftime("%X")

    # 데이터 삽입을 위한 그룹 타입으로 데이터 변경
    geo_json = dict(type="FeatureCollection", features=[])
    geo_json["features"]
    for trip in path.trip_id.unique():
      feature = dict(type="Feature", geometry=None, properties=dict(trip_id=str(trip)))
      feature["geometry"] = dict(type="LineString", coordinates=path.loc[path.trip_id==trip, ["s_x", "s_y", "altitude", "datetime"]].to_records(index=False).tolist())
      geo_json["features"].append(feature)
    trip_multi["features"].append(feature)

    return geo_json, elapsed_time, arrival_time

  #카카오 api
  @staticmethod
  def knavi(rest_api_key, origin, destination, priority = 'RECOMMEND'):
    import json
    import requests
    
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    url = f"https://apis-navi.kakaomobility.com/v1/directions?origin={origin}&destination={destination}&waypoints=&priority={priority}&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"
    
    res = requests.get(url, headers=headers)
    document = json.loads(res.text)

    return document

  # 시각화 시간을 단축을 위한 카카오 api를 활용한 바운더리 얻기
  @staticmethod
  def kakao_boundary(blood,hospital):

    rest_api_key = '41239f1ad95324b1d51bf118d1e84251'

    origin = str(blood['경도'][0])+ ', '+str(blood['위도'][0])
    destination = str(hospital['경도'][0])+ ', '+str(hospital['위도'][0])

    temp = service_window.knavi(rest_api_key, origin, destination)
    max_x,max_y,min_x,min_y = list(temp['routes'][0]['summary']['bound'].values())
    new_boundary =[[min_x,min_y],[max_x,min_y],[max_x,max_y],[min_x,max_y],[min_x,min_y]]
    polygon = Polygon(new_boundary)
    return polygon, temp

  # DQN과 RRT를 활용한 좌표값 가져오기
  @staticmethod
  def load_array(start,target):
    import numpy as np
    
    if start == "서울동부혈액원":
      start = 'clu0'
    elif start == "재단법인아산사회복지재단서울아산병원":
      start = 'clu1'
    elif start == "서울특별시보라매병원":
      start = 'clu2'
    elif start == "학교법인연세대학교의과대학세브란스병원":
      start = 'clu3'
    elif start == "서울남부혈액원":
      start = 'clu4'
    elif start == "서울중앙혈액원":
      start = 'clu5'
    
    path = f"{array_path}/{start}_{target}.npy"
    array = np.load(path)
    return array

  # 지도 생성
  @staticmethod
  def create_map(start_, target_):
    # 데이터 불러오기
    hospital, building, blood, mountain = service_window.load_data()

    #시작지와 도착지 이름
    start = start_
    target = target_

    #해당되는 영역의 데이터
    blood = blood.loc[blood['기관명']==start].reset_index()
    hospital = hospital.loc[hospital['기관명']==target].reset_index()
    polygon,temp = service_window.kakao_boundary(blood,hospital)
    building, mountain = service_window.check_intersects(building,mountain, polygon)

    # 경로와 필요한 변수 산출
    path = service_window.get_path(start,target)
    trip, elapsed_time, arrival_time = service_window.get_path_trip(path)

    path = path[['s_x','s_y','e_x','e_y']]
    setting = service_window.kepler_set(start,target)

    # 지도에 데이터 삽입
    map = KeplerGl(height=600, width=500)
    map.add_data(data=hospital, name= "hospital")
    map.add_data(data=building, name= "building")
    map.add_data(data=blood, name= "blood")
    map.add_data(data=mountain, name='mountain')
    map.add_data(data=path, name= "path")
    map.add_data(data=trip, name='trip')
    map.config = setting

    arrival_time = datetime.strptime(arrival_time, '%H:%M:%S')
    arrival_time -= timedelta(hours=9)
    arrival_time = arrival_time.strftime('%H:%M:%S')
    
    return map, elapsed_time, arrival_time

  # 카카오 api에서 얻을수 있는 자동차 경로 좌표
  @staticmethod
  def kakao_path(temp):
    path_list=[]
    for i in range(0,len(temp['routes'][0]['sections'][0]['guides'])-1):
      s_x = temp['routes'][0]['sections'][0]['guides'][i]['x']
      s_y = temp['routes'][0]['sections'][0]['guides'][i]['y']
      t_x = temp['routes'][0]['sections'][0]['guides'][i+1]['x']
      t_y = temp['routes'][0]['sections'][0]['guides'][i+1]['y']
      path_list.append([s_x,s_y,t_x,t_y])
    
    path = get_path(path_list)
    path = path[['s_x','s_y','e_x','e_y']]
    return path

  #시작점과 도착점의 좌표
  @staticmethod
  def get_corrdinate(start_,target_):
    hospital, building, blood, mountain = service_window.load_data()
    start = start_
    target = target_

    blood = blood.loc[blood['기관명']==start].reset_index()
    hospital = hospital.loc[hospital['기관명']==target].reset_index()
    
    b_x = blood['경도'][0]
    b_y = blood['위도'][0]

    h_x = hospital['경도'][0]
    h_y = hospital['위도'][0]

    return b_x,b_y,h_x,h_y

  # 시각화시 좌표값을 고려한 세팅값을 가져옴
  @staticmethod
  def kepler_set(start_,target_):

    b_x,b_y,h_x,h_y = service_window.get_corrdinate(start_,target_)
    setting = {'config': {'mapState': {'bearing': 24,
    'dragRotate': True,
    'isSplit': False,
    'latitude': (b_y+h_y)/2,
    'longitude': (b_x+h_x)/2,
    'pitch': 50,
    'zoom': 12},
    'mapStyle': {'mapStyles': {},
    'styleType': 'dark',
    'threeDBuildingColor': [218.82023004728686,
      223.47597962276103,
      223.47597962276103],
    'topLayerGroups': {},
    'visibleLayerGroups': {'3d building': False,
      'border': False,
      'building': False,
      'label': False,
      'land': True,
      'road': True,
      'water': True}},
    'visState': {'animationConfig': {
      'speed': 0.5},
    'filters': [],
    'interactionConfig': {'brush': {'enabled': False, 'size': 0.5},
      'coordinate': {'enabled': False},
      'geocoder': {'enabled': False},
      'tooltip': {'compareMode': False,
      'compareType': 'absolute',
      'enabled': True,
      'fieldsToShow': {'blood': [{'format': None, 'name': 'index'},
        {'format': None, 'name': '기관명'},
        {'format': None, 'name': '경도'},
        {'format': None, 'name': '위도'},
        {'format': None, 'name': 'agglo_cluster'}],
        'building': [{'format': None, 'name': 'BLD_NM'},
        {'format': None, 'name': 'GRND_FLR'},
        {'format': None, 'name': 'HEIGHT'},
        {'format': None, 'name': 'height2'},
        {'format': None, 'name': 'within'}],
        'hospital': [{'format': None, 'name': 'index'},
        {'format': None, 'name': '기관ID'},
        {'format': None, 'name': '기관명'},
        {'format': None, 'name': '경도'},
        {'format': None, 'name': '위도'}],
        'mountain': [{'format': None, 'name': 'within'}],
        'path': [{'format': None, 'name': 's_x'},
        {'format': None, 'name': 's_y'},
        {'format': None, 'name': 'e_x'},
        {'format': None, 'name': 'e_y'}],
        'trip': [{'format': None, 'name': 'trip_id'}]}}},
    'layerBlending': 'normal',
    'layers': [{'config': {'color': [255, 254, 230],
        'columns': {'geojson': '_geojson'},
        'dataId': 'trip',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'trip',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [255, 255, 255],
          'field': None,
          'offset': [0, 0],
          'size': 18}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'opacity': 0.8,
        'sizeRange': [0, 10],
        'thickness': 4.7,
        'trailLength': 180}},
      'id': '2ilnoih',
      'type': 'trip',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'sizeField': None,
        'sizeScale': 'linear'}},
      {'config': {'color': [137, 218, 193],
        'columns': {'altitude': None, 'lat': '위도', 'lng': '경도'},
        'dataId': 'hospital',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'new layer',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [248, 248, 249],
          'field': {'name': '기관명', 'type': 'string'},
          'offset': [0, 0],
          'size': 30}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'filled': True,
        'fixedRadius': False,
        'opacity': 0.8,
        'outline': False,
        'radius': 30,
        'radiusRange': [0, 50],
        'strokeColor': None,
        'strokeColorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'thickness': 2}},
      'id': 'vybky1s',
      'type': 'point',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'sizeField': None,
        'sizeScale': 'linear',
        'strokeColorField': None,
        'strokeColorScale': 'quantile'}},
      {'config': {'color': [227, 26, 26],
        'columns': {'altitude': None, 'lat': '위도', 'lng': '경도'},
        'dataId': 'blood',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'new layer',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [248, 248, 249],
          'field': {'name': '기관명', 'type': 'string'},
          'offset': [0, 0],
          'size': 30}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'filled': True,
        'fixedRadius': False,
        'opacity': 1,
        'outline': False,
        'radius': 26.7,
        'radiusRange': [0, 50],
        'strokeColor': None,
        'strokeColorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'thickness': 2}},
      'id': 'nun2t19',
      'type': 'point',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'sizeField': None,
        'sizeScale': 'linear',
        'strokeColorField': None,
        'strokeColorScale': 'quantile'}},
      {'config': {'color': [227, 26, 26],
        'columns': {'alt0': None,
        'alt1': None,
        'lat0': 's_y',
        'lat1': 'e_y',
        'lng0': 's_x',
        'lng1': 'e_x'},
        'dataId': 'path',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'new layer',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [255, 255, 255],
          'field': None,
          'offset': [0, 0],
          'size': 18}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'elevationScale': 1,
        'opacity': 0.8,
        'sizeRange': [0, 10],
        'targetColor': None,
        'thickness': 2}},
      'id': 'hzhw0uc',
      'type': 'line',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'sizeField': None,
        'sizeScale': 'linear'}},
      {'config': {'color': [18, 147, 154],
        'columns': {'geojson': 'geometry'},
        'dataId': 'building',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'building',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [255, 255, 255],
          'field': None,
          'offset': [0, 0],
          'size': 18}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'elevationScale': 1,
        'enable3d': True,
        'enableElevationZoomFactor': True,
        'filled': True,
        'heightRange': [0, 500],
        'opacity': 0.8,
        'radius': 10,
        'radiusRange': [0, 50],
        'sizeRange': [0, 10],
        'strokeColor': [221, 178, 124],
        'strokeColorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'strokeOpacity': 0.8,
        'stroked': False,
        'thickness': 0.5,
        'wireframe': False}},
      'id': 'amlhxsb',
      'type': 'geojson',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'heightField': {'name': 'height2', 'type': 'real'},
        'heightScale': 'linear',
        'radiusField': None,
        'radiusScale': 'linear',
        'sizeField': None,
        'sizeScale': 'linear',
        'strokeColorField': None,
        'strokeColorScale': 'quantile'}},
      {'config': {'color': [37, 67, 37],
        'columns': {'geojson': 'geometry'},
        'dataId': 'mountain',
        'hidden': False,
        'highlightColor': [252, 242, 26, 255],
        'isVisible': True,
        'label': 'mountain',
        'textLabel': [{'alignment': 'center',
          'anchor': 'start',
          'color': [255, 255, 255],
          'field': None,
          'offset': [0, 0],
          'size': 18}],
        'visConfig': {'colorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'elevationScale': 5,
        'enable3d': False,
        'enableElevationZoomFactor': True,
        'filled': True,
        'heightRange': [0, 500],
        'opacity': 1,
        'radius': 10,
        'radiusRange': [0, 50],
        'sizeRange': [0, 10],
        'strokeColor': [255, 153, 31],
        'strokeColorRange': {'category': 'Uber',
          'colors': ['#5A1846',
          '#900C3F',
          '#C70039',
          '#E3611C',
          '#F1920E',
          '#FFC300'],
          'name': 'Global Warming',
          'type': 'sequential'},
        'strokeOpacity': 0.8,
        'stroked': False,
        'thickness': 0.5,
        'wireframe': False}},
      'id': '7k9uu7',
      'type': 'geojson',
      'visualChannels': {'colorField': None,
        'colorScale': 'quantile',
        'heightField': None,
        'heightScale': 'linear',
        'radiusField': None,
        'radiusScale': 'linear',
        'sizeField': None,
        'sizeScale': 'linear',
        'strokeColorField': None,
        'strokeColorScale': 'quantile'}}],
    'splitMaps': []}},
  'version': 'v1'}
    
    return setting

# 서비스 메인 화면 서비스 화면
class main_service: 
  # 메인 서비스 화면에서 사용할 데이터 불러오기
  @staticmethod
  def load_data():
    hospital=service_window.load_db_data("군집화된병원6")
    building=service_window.load_db_data("building_final")
    blood=service_window.load_db_data("드론공항위치")

    mountain = gpd.read_file(f'{mountain_path}/11.shp', encoding='euc-kr')
    mountain=mountain[['geometry']]
    mountain=mountain.to_crs(epsg=4326)
    mountain=mountain.drop(697)

    return hospital, building, blood, mountain
  # 메인서비스에서 사용할 지도 상태
  @staticmethod
  def create_map():
    global trip_count
    hospital, building, blood, mountain = main_service.load_data()
    map = KeplerGl(height=600, width=500)
    map.add_data(data=hospital, name= "hospital")
    map.add_data(data=blood, name= "blood")
    map.add_data(data=building, name= "building")
    map.add_data(data=mountain, name= "mountain")
   
    if trip_count > 0:
      trip = main_service.select_trip()
      map.add_data(data=trip, name= "multi_trip")
      
    map.config = main_service.setting()
    
    return map
  
  @staticmethod
  def select_trip():
    global trip_multi
    global trip_count

    temp_trip = dict(type="FeatureCollection", features=[])

    now = datetime.now()+timedelta(hours=9)
    current = now.timestamp()

    # 현재 시간을 고려해서 이미 지나간 경로는 제거
    for i in range(0,trip_count):
      if trip_multi["features"][i]["geometry"]["coordinates"][-1][3] > current:
        temp_trip["features"].append(trip_multi["features"][i])

    return temp_trip

  @staticmethod
  def setting():
    
    now = datetime.now()+timedelta(hours=9)
    current = now.timestamp()

    setting = {'config': {'mapState': {'bearing': 24,
   'dragRotate': True,
   'isSplit': False,
   'latitude': 37.525983497580704,
   'longitude': 126.97269802564206,
   'pitch': 50,
   'zoom': 11.273004176173325},
  'mapStyle': {'mapStyles': {},
   'styleType': 'dark',
   'threeDBuildingColor': [9.665468314072013,
    17.18305478057247,
    31.1442867897876],
   'topLayerGroups': {},
   'visibleLayerGroups': {'3d building': False, 
    'border': False,
    'building': True,
    'label': True,
    'land': True,
    'road': True,
    'water': True}},
  'visState': {'animationConfig': {'currentTime': current, 'speed': 1},
   'filters': [],
   'interactionConfig': {'brush': {'enabled': False, 'size': 0.5},
    'coordinate': {'enabled': False},
    'geocoder': {'enabled': False},
    'tooltip': {'compareMode': False,
     'compareType': 'absolute',
     'enabled': True,
     'fieldsToShow': {'blood': [{'format': None, 'name': '기관명'},
       {'format': None, 'name': '경도'},
       {'format': None, 'name': '위도'},
       {'format': None, 'name': 'agglo_cluster'}],
      'building': [{'format': None, 'name': 'BLD_NM'},
       {'format': None, 'name': 'GRND_FLR'},
       {'format': None, 'name': 'HEIGHT'},
       {'format': None, 'name': 'height2'}],
      'hospital': [{'format': None, 'name': '기관ID'},
       {'format': None, 'name': '기관명'},
       {'format': None, 'name': '경도'},
       {'format': None, 'name': '위도'},
       {'format': None, 'name': '응급실'}],
      'mountain': [],
      'multi_trip': [{'format': None, 'name': 'trip_id'}]}}},
   'layerBlending': 'normal',
   'layers': [{'config': {'color': [255, 254, 230],
      'columns': {'geojson': '_geojson'},
      'dataId': 'multi_trip',
      'hidden': False,
      'highlightColor': [252, 242, 26, 255],
      'isVisible': True,
      'label': 'multi_trip',
      'textLabel': [{'alignment': 'center',
        'anchor': 'start',
        'color': [255, 255, 255],
        'field': None,
        'offset': [0, 0],
        'size': 18}],
      'visConfig': {'colorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'opacity': 0.8,
       'sizeRange': [0, 10],
       'thickness': 3,
       'trailLength': 180}},
     'id': 'sduie3',
     'type': 'trip',
     'visualChannels': {'colorField': None,
      'colorScale': 'quantile',
      'sizeField': None,
      'sizeScale': 'linear'}},
    {'config': {'color': [18, 147, 154],
      'columns': {'geojson': 'geometry'},
      'dataId': 'building',
      'hidden': False,
      'highlightColor': [252, 242, 26, 255],
      'isVisible': True,
      'label': 'building',
      'textLabel': [{'alignment': 'center',
        'anchor': 'start',
        'color': [255, 255, 255],
        'field': None,
        'offset': [0, 0],
        'size': 18}],
      'visConfig': {'colorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'elevationScale': 1,
       'enable3d': True,
       'enableElevationZoomFactor': True,
       'filled': True,
       'heightRange': [0, 500],
       'opacity': 0.8,
       'radius': 10,
       'radiusRange': [0, 50],
       'sizeRange': [0, 10],
       'strokeColor': [221, 178, 124],
       'strokeColorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'strokeOpacity': 1,
       'stroked': False,
       'thickness': 0.5,
       'wireframe': False}},
     'id': 'hntoj5g',
     'type': 'geojson',
     'visualChannels': {'colorField': None,
      'colorScale': 'quantile',
      'heightField': {'name': 'height2', 'type': 'real'},
      'heightScale': 'linear',
      'radiusField': None,
      'radiusScale': 'linear',
      'sizeField': None,
      'sizeScale': 'linear',
      'strokeColorField': None,
      'strokeColorScale': 'quantile'}},
    {'config': {'color': [39, 79, 40],
      'columns': {'geojson': 'geometry'},
      'dataId': 'mountain',
      'hidden': False,
      'highlightColor': [252, 242, 26, 255],
      'isVisible': True,
      'label': 'mountain',
      'textLabel': [{'alignment': 'center',
        'anchor': 'start',
        'color': [255, 255, 255],
        'field': None,
        'offset': [0, 0],
        'size': 18}],
      'visConfig': {'colorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'elevationScale': 5,
       'enable3d': False,
       'enableElevationZoomFactor': True,
       'filled': True,
       'heightRange': [0, 500],
       'opacity': 0.8,
       'radius': 10,
       'radiusRange': [0, 50],
       'sizeRange': [0, 10],
       'strokeColor': [255, 153, 31],
       'strokeColorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'strokeOpacity': 0.8,
       'stroked': False,
       'thickness': 0.5,
       'wireframe': False}},
     'id': '27j87j',
     'type': 'geojson',
     'visualChannels': {'colorField': None,
      'colorScale': 'quantile',
      'heightField': None,
      'heightScale': 'linear',
      'radiusField': None,
      'radiusScale': 'linear',
      'sizeField': None,
      'sizeScale': 'linear',
      'strokeColorField': None,
      'strokeColorScale': 'quantile'}},
    {'config': {'color': [136, 87, 44],
      'columns': {'altitude': None, 'lat': '위도', 'lng': '경도'},
      'dataId': 'hospital',
      'hidden': False,
      'highlightColor': [252, 242, 26, 255],
      'isVisible': True,
      'label': 'hospital',
      'textLabel': [{'alignment': 'center',
        'anchor': 'start',
        'color': [255, 255, 255],
        'field': None,
        'offset': [0, 0],
        'size': 18}],
      'visConfig': {'colorRange': {'category': 'ColorBrewer',
        'colors': ['#1b9e77',
         '#d95f02',
         '#7570b3',
         '#e7298a',
         '#66a61e',
         '#e6ab02'],
        'name': 'ColorBrewer Dark2-6',
        'type': 'qualitative'},
       'filled': True,
       'fixedRadius': False,
       'opacity': 0.8,
       'outline': False,
       'radius': 15,
       'radiusRange': [0, 50],
       'strokeColor': None,
       'strokeColorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'thickness': 2}},
     'id': 'a6rc0b',
     'type': 'point',
     'visualChannels': {'colorField': {'name': 'agglo_cluster',
       'type': 'integer'},
      'colorScale': 'quantile',
      'sizeField': None,
      'sizeScale': 'linear',
      'strokeColorField': None,
      'strokeColorScale': 'quantile'}},
    {'config': {'color': [210, 0, 0],
      'columns': {'altitude': None, 'lat': '위도', 'lng': '경도'},
      'dataId': 'blood',
      'hidden': False,
      'highlightColor': [252, 242, 26, 255],
      'isVisible': True,
      'label': 'blood',
      'textLabel': [{'alignment': 'center',
        'anchor': 'start',
        'color': [255, 255, 255],
        'field': {'name': '기관명', 'type': 'string'},
        'offset': [0, 0],
        'size': 18}],
      'visConfig': {'colorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'filled': True,
       'fixedRadius': False,
       'opacity': 0.8,
       'outline': False,
       'radius': 25,
       'radiusRange': [0, 50],
       'strokeColor': None,
       'strokeColorRange': {'category': 'Uber',
        'colors': ['#5A1846',
         '#900C3F',
         '#C70039',
         '#E3611C',
         '#F1920E',
         '#FFC300'],
        'name': 'Global Warming',
        'type': 'sequential'},
       'thickness': 2}},
     'id': '80rx5gj',
     'type': 'point',
     'visualChannels': {'colorField': None,
      'colorScale': 'quantile',
      'sizeField': None,
      'sizeScale': 'linear',
      'strokeColorField': None,
      'strokeColorScale': 'quantile'}}],
   'splitMaps': []}},
 'version': 'v1'}
    return setting



# 템플릿에 딕셔너리를 넘겨주기 위한 json 만들기.
conn = pymysql.connect(host='34.64.132.212', user='root', password='ASewetsvc124~1242#%1wsdeWXV', db='source')
sql_state='SELECT * FROM `군집화된병원6`'
hospital = pd.read_sql_query(sql_state, conn)
sql_state='SELECT * FROM `드론공항위치`'
hub = pd.read_sql_query(sql_state, conn)
hub_list = hub.기관명.tolist()
dic = {}
for i in hub_list:
    cluster_temp = hospital.loc[hospital.기관명 == i, 'agglo_cluster'].values[0]
    dic[i] = hospital.loc[(hospital.agglo_cluster == cluster_temp)&(hospital.기관명 != i), '기관명'].tolist()
# print(dic)
goals = json.dumps(dic)

# @xframe_options_exempt
def path_planning(request):
    context = {}
    form = startForm()
    context['form'] = form
    context['goals'] = goals
    if request.POST:
      start = request.POST['start_field']
      goal = request.POST['goal_field']
      print(start)
      print(goal)
      if start == "None" or goal == "None":
          return render(request,f'single_pages/base_origin.html',context)
      else:
          map, elapsed_time, arrival_time = service_window.create_map(start, goal)
          map.save_to_html(file_name=f'single_pages/templates/single_pages/path_new.html')
          temp_min = round(elapsed_time // 60)
          temp_sec = round(elapsed_time % 60)
          elapsed_time = f"{temp_min}분 {temp_sec}초"
          context['elapsed_time'] = elapsed_time
          context['arrival_time'] = arrival_time
          return render(request,f'single_pages/path.html',context)
    else:
        return render(request,'single_pages/base_origin.html',context)

def control_drone(request):
    context = {}
    map = main_service.create_map()
    map.save_to_html(file_name=f'single_pages/templates/single_pages/base_main.html')
    return render(request,'single_pages/base.html',context)


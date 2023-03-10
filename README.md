# 드론 신속 배송을 위한 AI기반 최적 하늘길 구축 시스템

<img src = "https://user-images.githubusercontent.com/96767467/197766534-1d1c197f-8a47-4b73-849c-64f546aff05c.png" align = 'center' width = "95%" height = "53%">

### 들어가기 전에
- 본 프로젝트는 2022년 8월에 "국토교통부 빅데이터 활용 경진대회"에서 우수상을 수상하였습니다 🎉
- 발표 영상: https://youtu.be/TZF6tO4_9ro (경진대회용 영상)
- 코드 설명 참고 영상: https://youtu.be/DveW9Zwkjw4
- 드론 응급배송 인프라를 위한 AI기반 최적 하늘길 구축 프로젝트입니다.
- 국토교통부, 중앙의료원, 기상청, 산림청 등의 공공데이터를 활용하였습니다.
- 자세한 내용은 [소스코드](https://github.com/MiddleJo/SkyRoad_for_Drone/tree/main/%EC%BD%94%EB%93%9C) 혹은 pdf를 참고해 주시기 바랍니다.
- 저작권에 유의하시기 바랍니다.


### 목차
[1. 기획 및 과제 정의](#1-기획)</br>
[2. 모델링](#2-모델링)</br>
[3. 시스템 개발](#3-시스템-개발)</br>
[4. 데모 시연](#4-데모-시연)</br>
[5. 발전 가능성과 기대가치](#5-발전-가능성과-기대가치)</br>
[6. 부가 설명](#부가-설명)</br>
[7. 팀원소개](#팀원-소개)
</br>

---

## 1. 기획

### 1-1 주제 선정 배경
<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224073781-944046c0-a0d0-4b92-94a0-af5de24f044f.PNG" width = "48%" height = "27%">
<img src = "https://user-images.githubusercontent.com/96767467/224073912-9b0485ee-f96d-4ee7-bd7d-267a8f7ecedc.PNG" width = "48%" height = "27%">
</p>
<p> 
응급환자는 1시간안에 수혈받지 못하면 사망율이 99%에 육박합니다. 이에 르완다 등에서는 드론으로 응급물품을 배송하는 시도가 이어지고 있습니다.  
다만 우리나라는 건물이 밀집한 특성으로 인해 드론 배송이 쉽지는 않습니다. 이것을 고려하여 하늘길을 구축한다면 우리나라에서도 시도해볼 수 있을 것입니다.
<p>
</br>

### 1-2 프로젝트 개요

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224081093-15d23491-6084-4277-a604-493c43003b7e.PNG" align = 'center' width = "95%" height = "53%">
</p>
</br>


## 2. 모델링

### 2-1 시스템 요약도

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224225177-8931a8ec-a01f-466a-9347-0fb6d8cfa1c0.PNG" align = 'center' width = "95%" height = "53%">
</p>
</br>

### 2-2 DB 구축

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224225507-fcf5007f-c23c-4908-a0e7-ce3522b91fb8.PNG" align = 'center' width = "95%" height = "53%">
</p>
</br>


## 3. 시스템 개발
<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224228034-e8d2cbe7-faca-4cb6-9108-da6cc532c874.PNG" align = 'center' width = "95%" height = "53%">
</p>
시스템 개발은 두 단계로 이루어집니다. 드론 배송 인프라를 구축하기 위해 드론 공항이 설치될 곳을 정하는 단계,</br>
설치된 공항들을 기준으로 하늘길을 구축하는 단계로 나뉘어 있습니다.
</br>
</br>

### 3-1 드론 공항 설치

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224228080-ba51dd2c-64cb-4533-b747-94fe43359ac6.PNG" align = 'center' width = "95%" height = "53%">
</p>
<p>
현재 혈액원은 담당구역이 너무 방대해 배송 시간, 경로상의 변수, 배터리 등을 고려할 때 문제점이 있습니다.</br>
따라서 군집분석을 통해 적절한 범위로 재구성하고, 총 3곳의 대표 병원을 "임시 혈액원"으로 선정하여 운영합니다.
</p>

[부록1](#부록1-드론-공항-설치)

</br>

### 3-2 하늘길 구축

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224228688-dc83388c-d873-416f-bcf7-4b874417d2d1.PNG" align = 'center' width = "95%" height = "53%">
</p>
<p>
좌측 그림은 위치상의 최단 경로가 최적의 경로가 되지는 않다는 것을 보여주고 있습니다. 붉은 영역을 지나는 드론은 장애요소로 인해 오히려 늦게 도착하는 것을 볼 수 있습니다.</br>
따라서 배터리, 환경 요소를 고려한 거시적 경로와 실제 장애물을 피해가는 미시적 경로를 따로 구성해야 합니다.
</p>
</br>

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224229218-5038ab79-c29b-40f6-99d7-7172823b332e.PNG" align = 'center' width = "90%" height = "50%">
</p>
<p>
거시적 경로는 미로찾기 강화학습 알고리즘인 DQN을, 미시적 경로는 최단경로 알고리즘인 Informed RRT* 알고리즘을 활용합니다.</br>
실제 공간을 1km 단위로 격자화 하여 드론 비행에 영향을 주는 요소를 비용함수화 한 뒤, 보상체계를 세워 위험한 곳을 피해가도록 합니다.</br>
큰 경로 공간이 결정되었다면 골격화된 지도 안에서 장애물을 회피해 갈 수 있도록 합니다.
</p>
</br>

<p align = 'center'>
<img src = "https://user-images.githubusercontent.com/96767467/224229727-78dea9cf-ff33-4b16-b656-d234789979eb.PNG" align = 'center' width = "90%" height = "50%">
</p>
<p>
비용함수는 드론 도메인 지식을 바탕으로 건물, 산, 바람, 강수를 변수로 사용합니다.</br>
해당 지수들은 게임 엔진인 Unreal Engine4에서 드론 시뮬레이터로 실험한 데이터를 바탕으로 설정하였습니다.
</p>

[부록2](#부록2-거시적-경로)

</br>


## 4. 데모 시연

https://user-images.githubusercontent.com/96767467/224230498-2ce59f64-db73-4a5a-8590-56f01767194c.mp4

</br>

데모 시연에 대한 설명은 [발표영상](https://youtu.be/TZF6tO4_9ro) 뒷부분을 참고해주시기 바랍니다.
시뮬레이션에 사용된 드론 스펙은 부록3을 참고해주시기 바랍니다.

## 5. 발전 가능성과 기대가치

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224231760-3bd0d0df-848a-4604-917a-2d0f445a368b.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
현재는 데이터가 제한적이나, S-Map 등의 실제 3d 데이터와 드론 전문가와 협업한다면 더 고도화된 모델을 실현할 수 있습니다.
</p>
</br>

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224232258-f28c456f-db51-47f9-a55e-eb509e78ec58.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
앞서 말씀드린 것들이 개선되고 이 인프라가 실현된다면 응급상황시 골든타임을 맞추지 못해 사망하던 20%의 응급환자를 살릴 수 있고,</br>
이 프로젝트는 UAM으로의 확장 가능성도 가지고 있기에 가치가 있습니다.
</p>
</br>
</br>

## #부가 설명

### 부록1. 드론 공항 설치

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224233517-a0fe3cca-a247-4ee0-a832-69030a4e5c94.PNG" align = 'center' width = 95% height = "53%">
</p>
</br>

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224233621-d3bac9b4-18ad-4ab2-9690-aa32070a6956.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
실루엣 계수를 확인하여 군집 개수를 결정하였고, 임시 혈액원이 될 대표 병원들은 위와 같은 기준으로 결정되었습니다.
</p>
</br>
</br>

### 부록2. 거시적 경로

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224234064-206f539b-6ae4-4433-92c7-2547203d071e.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
DQN은 보상체계를 학습하며 최상의 경로를 선택하므로, 보상체계에 사용될 비용 함수가 필요합니다.
</p>
</br>
</br>

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224234326-a8208a29-3aaf-4340-a431-786770f85485.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
드론 도메인 지식에 따라, 이와 같은 가정을 하고 실험하였습니다.
</p>
</br>
</br>

<p>
<img src = "https://user-images.githubusercontent.com/96767467/224234499-799c049c-200d-4253-9faf-12e90745ae0c.PNG" align = 'center' width = 95% height = "53%">
</p>
<p>
대략적인 영향도만 있다면 보상체계를 설립할 수 있기 때문에, 우선 polifit 라이브러리를 통해 일차함수로 분석하였습니다.</br>
강수는 기상청이 제공하는 등급으로 지수화 하였습니다.
</p>
</br>

</br>
</br>

## 팀원 소개
----
<img align="left" width="180" height="180" src="https://user-images.githubusercontent.com/96767467/175253262-f4614359-abd2-4839-b8d3-0f7b8dd32f53.jpg" />

- 조남현(CHO NAM HYEON)</br>
- 기획, 군집분석, 미시적 경로(최단경로 알고리즘), 지도 골격화 및 DQN 설계, 비용함수, 웹 구현</br></br></br>
MAIL : chonh0531@gmail.com</br>
Github : https://github.com/MiddleJo </br></br>

----
<img align="left" width="180" height="180"  src="https://user-images.githubusercontent.com/102858692/161480452-fc8d952a-b964-4b44-8a9b-b5eab3652f89.png"/>

- 박광민(PARK KWAMG MIN)</br>
- DB구축, 시뮬레이션(UE4), 지리데이터 가공 및 시각화(Kepler.gl)</br></br></br>
MAIL : qkrrhk@gmail.com</br>
Github : https://github.com/KMP94</br></br>

----
<img align="left" width="180" height="180" src="https://user-images.githubusercontent.com/102858692/161481002-6c4f9f96-5ae6-4ea6-b2d0-d0a665b158fa.png"/>

- 김기현(KIM GI HYUN)</br>
- 팀장, 지도 골격화, 거시적 경로(강화학습 알고리즘), 보상체계 설정</br></br></br>
MAIL : luckyboy3214@naver.com</br>
Github : https://github.com/spiner321</br></br>

----

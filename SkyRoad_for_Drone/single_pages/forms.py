from django import forms
import pymysql
import pandas as pd
# from models import startModel


# cluster = None

conn = pymysql.connect(host='34.64.132.212', user='root', password='ASewetsvc124~1242#%1wsdeWXV', db='source')
sql_state='SELECT * FROM `군집화된병원6`'
hospital = pd.read_sql_query(sql_state, conn)

START_CHOICES = [
    ('None','===출발지선택==='),
	('서울동부혈액원', '서울동부혈액원'),
    ('서울남부혈액원', '서울남부혈액원'),
    ('서울중앙혈액원', '서울중앙혈액원'),
    ('서울특별시보라매병원', '보라매병원'),
    ('재단법인아산사회복지재단서울아산병원', '서울아산병원'),
    ('학교법인연세대학교의과대학세브란스병원', '연세대학교세브란스병원'),
]

GOAL_CHOICES = [
        ('None','===도착지선택===')]
# targets = hospital.기관명.tolist()
# for i in targets:
#     GOAL_CHOICES.append((i,i))
 

class startForm(forms.Form):
    # class Meta:
    start_field = forms.ChoiceField( label="출발지", choices=START_CHOICES, widget = forms.Select(attrs = {'onchange':'selectgoals(this.value);','required':True,'class':'bootstrap-select'}))
    goal_field = forms.ChoiceField( label="도착지", choices=GOAL_CHOICES, widget = forms.Select(attrs = {'required':True,'class':'bootstrap-select'}))
#import dash_core_components as dcc
#import dash_html_components as html
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import warnings
import os
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
import configparser
import config as cf
import getPrices
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

TGSites = pd.read_csv("TotalGasSites.csv")
CompetenciaSites = pd.read_csv("CompetenciaSites.csv")
Prices = getPrices.preciosCompetencia
PrecioHistorico = getPrices.preciosHistoricos


Prices["place_id"] = pd.to_numeric(Prices["place_id"])
PrecioHistorico["place_id"] = pd.to_numeric(PrecioHistorico["place_id"])

workTable = pd.merge(CompetenciaSites,Prices,left_on='place_id',right_on='place_id')
workTable02 = pd.merge(workTable,Prices,left_on=['compite_a','product'],right_on=['place_id','product'])
workTable02['dif'] =  workTable02['prices_x'] - workTable02['prices_y']
wt01 = workTable02[['place_id_x', 'cre_id', 'Marca', 'distancia', 'x', 'y', 'compite_a', 'prices_x', 'product', 'dif']]
wt01.columns = ['place_id', 'cre_id', 'Marca', 'distancia', 'x', 'y', 'compite_a', 'prices', 'product', 'dif']

tableGraphs = pd.merge(CompetenciaSites,PrecioHistorico,left_on='place_id',right_on='place_id')
tableGraphs = tableGraphs[['place_id','prices','product','date','cre_id','Marca','compite_a']]

descargarTabla = pd.DataFrame()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

warnings.filterwarnings("ignore")
conn_string = cf.urlDB
engine = create_engine(conn_string)
db = SQLAlchemy()
config = configparser.ConfigParser()
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable = False)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
Users_tbl = Table('users', Users.metadata)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets) #app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
app.config.suppress_callback_exceptions = True
# config
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI=conn_string,
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(server)
# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'
#User as base
# Create User class with UserMixin
class Users(UserMixin, Users):
    pass
#variables
mapbox_access_token = cf.mapbox_access_token

def generate_table(dataframe, max_rows=20):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    ) 

def generate_map(dataframe,citylat,citylon):
    fig = go.Figure(go.Scattermapbox(
            lon = dataframe['x'],
            lat = dataframe['y'],
            text = dataframe['text'],
            mode = 'markers'
            ))

    fig.update_layout(
            title = 'Mapa de Precios',
            autosize=True,
            hovermode='closest',
            mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=citylat,
                lon=citylon
            ),
            pitch=0,
            zoom=10
    ),
        )
    return html.Div([
    dcc.Graph(figure=fig)
    ])

def generate_graphs(dataframe):
    df = dataframe.pivot_table(values='prices', index=['date','Marca'], aggfunc=[np.mean])
    df.columns = df.columns.droplevel(0)
    df = df.reset_index()
    df = df.round(2)
    fig = px.line(df, 
        x="date",y='prices', color='Marca',title='Precios por Marca')
    return html.Div([
    dcc.Graph(figure=fig)
    ])

tab1 = html.Div([
            html.H4(children='Estaciones de Servicio Total Gas'),
                dcc.Checklist(
                    id='mychecklist',
                    options = ['regular', 'premium', 'diesel'],
                    value = ['regular'],
                    inline=True
                ),
                dcc.Dropdown(id='dropdown', options=[
                    {'label': i, 'value': i} for i in TGSites.cre_id.unique()
                ], multi=True, placeholder='Filter by Permiso CRE...'),
                html.Div(id='table-container'),
                html.Button("Download CSV", id="btn_csv"),
                dcc.Download(id="download-dataframe-csv"),
            ])

tab2 = html.Div([
            html.H4(children='Mapa de Estaciones de Servicio'),
                dcc.Dropdown(['Juarez', 'Aguascalientes', 'Delicias', 'Parral', 'Ahumada'], 'Juarez', id='dropdownMapa'),
                dcc.RadioItems(
                    ['regular', 'premium','diesel'], 'regular',
                    id='productType',
                    inline=True
                ),
                html.Div(id='dd-output-container')
])    

tab3 = html.Div([
            html.H4(children='Gráficas precios últimos 21 días'),
                dcc.Dropdown(id='dropdownGraphs', options=[
                    {'label': i, 'value': i} for i in TGSites.cre_id.unique()
                ], multi=True, placeholder='Filter by Permiso CRE...'),
                dcc.RadioItems(
                    ['regular', 'premium','diesel'], 'regular',
                    id='productTypeGraphs',
                    inline=True
                ),
                html.Div(id='container_graphs')
])
# create = html.Div([ html.H1('Create User Account')
#         , dcc.Location(id='create_user', refresh=True)
#         , dcc.Input(id="username"
#             , type="text"
#             , placeholder="user name"
#             , maxLength =15)
#         , dcc.Input(id="password"
#             , type="password"
#             , placeholder="password")
#         , dcc.Input(id="email"
#             , type="email"
#             , placeholder="email"
#             , maxLength = 50)
#         , html.Button('Create User', id='submit-val', n_clicks=0)
#         , html.Div(id='container-button-basic')
#     ])#end div
image_path = 'assets/jojuma.png'

login =  html.Div([dcc.Location(id='url_login', refresh=True)
            , html.Img(src=image_path)
            , html.H1('Bienvenido a Jojuma BI - Fuel Pricing Tool')
            , html.H2('''Ingresa tu usuario y contraseña''', id='h1')
            , dcc.Input(placeholder='Usuario',
                    type='text',
                    id='uname-box')
            , dcc.Input(placeholder='Contraseña',
                    type='password',
                    id='pwd-box')
            , html.Button(children='Ingresa',
                    n_clicks=0,
                    type='submit',
                    id='login-button')
            , html.Div(children='', id='output-state')
        ]) #end div
# success = html.Div([dcc.Location(id='url_login_success', refresh=True)
#             , html.Div([html.H2('Login successful.')
#                     , html.Br()
#                     , html.P('Select a Dataset')
#                     , dcc.Link('Data', href = '/data')
#                 ]) #end div
#             , html.Div([html.Br()
#                     , html.Button(id='back-button', children='Go back', n_clicks=0)
#                 ]) #end div
#         ]) #end div
data = html.Div([
    html.H1('Reporte de precios estaciones de servicio TotalGas'),
    dcc.Tabs(id="tabs-example", value='tab-1', children=[
        dcc.Tab(id="tab-1", label='Precios', value='tab-1'),
        dcc.Tab(id="tab-2", label='Mapa', value='tab-2'),
        dcc.Tab(id="tab-3", label='Graficas', value='tab-3')
    ]),
    html.Div(id='tabs-content',
             children = [tab1,tab2,tab3]),
    
    # html.Div([dcc.Dropdown(
    #                 id='dropdown',
    #                 options=[{'label': i, 'value': i} for i in ['Day 1', 'Day 2']],
    #                 value='Day 1')
    #             , html.Br()
    #             , html.Div([dcc.Graph(id='graph')])
    #         ]) #end div
     html.Div([html.Br()
             , html.Button(id='back-button', children='Go back', n_clicks=0)
              ]) #end div
])
failed = html.Div([ dcc.Location(id='url_login_df', refresh=True)
            , html.Div([html.H2('Log in Failed. Please try again.')
                    , html.Br()
                    , html.Div([login])
                    , html.Br()
                    , html.Button(id='back-button', children='Go back', n_clicks=0)
                ]) #end div
        ]) #end div
logout = html.Div([dcc.Location(id='logout', refresh=True)
        , html.Br()
        , html.Div(html.H2('You have been logged out - Please login'))
        , html.Br()
        , html.Div([login])
        , html.Button(id='back-button', children='Go back', n_clicks=0)
    ])#end div
app.layout= html.Div([
            html.Div(id='page-content', className='content')
            ,  dcc.Location(id='url', refresh=False)
        ])
# callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
@app.callback(
    Output('page-content', 'children')
    , [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return login
    elif pathname == '/login':
        return login
    # elif pathname == '/success':
    #     if current_user.is_authenticated:
    #         return success
    #     else:
    #         return failed
    elif pathname =='/data':
        if current_user.is_authenticated:
            return data
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return logout
        else:
            return logout
    else:
        return '404'
@app.callback(Output('tabs-content', 'children'),
             [Input('tabs-example', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return tab1
    elif tab == 'tab-2':
        return tab2
    elif tab == 'tab-3':
        return tab3
@app.callback(
    Output('table-container', 'children'),
    Input('dropdown', 'value'),
    Input('mychecklist','value'))
def display_table(dropdown, mychecklist):
    global table
    if dropdown is None:
        placeIDTG = TGSites['place_id'].to_list()
    else:
        placeIDTG = TGSites['place_id'][TGSites.cre_id.str.contains('|'.join(dropdown))]
    dff = wt01
    dff = dff[dff['compite_a'].isin(placeIDTG)]
    table = pd.pivot_table(dff[['cre_id','Marca','prices','dif','product']], values=['prices','dif'], index=['cre_id', 'Marca'],
                    columns=['product'], aggfunc=np.mean, fill_value="-")
    #coculs = ['cre_id','Marca'] + mychecklist
    table = table.reindex(columns=['prices','dif'], level=0)
    print(mychecklist)
    table = table.reindex(columns=mychecklist, level=1)
    table.columns = table.columns.map('|'.join).str.strip('|')
    table = table.round(2)
    table = table.reset_index()
    return generate_table(table)

@app.callback(
    Output('dd-output-container', 'children'),
    Input('dropdownMapa', 'value'),
    Input('productType','value'))
def make_map(dropdownMapa, productType):
   
    df0 = workTable[workTable['product']==productType] 
    placeIDTG = TGSites['place_id'][TGSites['Municipio']==dropdownMapa]
    df = df0[df0['compite_a'].isin(placeIDTG)]
    df['text'] = df['Marca'] + ' ' + df['cre_id'] + ', Precio: ' + df['prices'].astype(str)

    if dropdownMapa == 'Juarez':
        citylat = 31.71947
        citylon = -106.4514
    elif dropdownMapa == "Aguascalientes":
        citylat = 21.91797
        citylon = -102.2973
    elif dropdownMapa == "Delicias":
        citylat = 28.184184
        citylon = -105.463511
    elif dropdownMapa == "Parral":
        citylat = 26.933387
        citylon = -105.669176
    elif dropdownMapa == "Ahumada":
        citylat = 30.574909
        citylon = -106.510286
    else:
        citylat = 31.71947
        citylon = -106.4514

    return generate_map(df,citylat,citylon)

@app.callback(
    Output('container_graphs', 'children'),
    Input('dropdownGraphs', 'value'),
    Input('productTypeGraphs','value'))
def display_table(dropdownGraphs, productTypeGraphs):

    if dropdownGraphs is None:
        placeIDTG = TGSites['place_id'][TGSites.cre_id.str.contains('PL/10059/EXP/ES/2015')]
    else:
        placeIDTG = TGSites['place_id'][TGSites.cre_id.str.contains('|'.join(dropdownGraphs))]

    graphTable = tableGraphs[tableGraphs['compite_a'].isin(placeIDTG)]
    graphTable = graphTable[graphTable['product']==productTypeGraphs] 
    return generate_graphs(graphTable)

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_data_frame(table.to_csv, "tabla.csv")
@app.callback(
    Output('url_login', 'pathname')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def successful(n_clicks, input1, input2):
    user = Users.query.filter_by(username=input1).first()
    if user:
        if check_password_hash(user.password, input2):
            login_user(user)
            return '/data'
        else:
            pass
    else:
        pass
@app.callback(
    Output('output-state', 'children')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def update_output(n_clicks, input1, input2):
    if n_clicks > 0:
        user = Users.query.filter_by(username=input1).first()
        if user:
            if check_password_hash(user.password, input2):
                return ''
            else:
                return 'Incorrect username or password'
        else:
            return 'Incorrect username or password'
    else:
        return ''
@app.callback(
    Output('url_login_success', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
    else:
        return '/logout'
@app.callback(
    Output('url_login_df', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
    else:
        return '/logout'
# Create callbacks
@app.callback(
    Output('url_logout', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'
    else:
        return '/logout'
if __name__ == '__main__':
    app.run_server(debug=True)
"""_summary_
This file is for an interactive dashboard to visualize the guesses that people have made to date.
"""

from msilib.schema import Component
from select import select
import pandas as pd
import plotly.express as px
import json
from tinydb import TinyDB, Query
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import requests


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    
db = requests.get('https://raw.githubusercontent.com/doomercreatine/MasterCasketBot/main/updated_db.json').json()

casket_data = pd.DataFrame()
guesses = [item for item in iter(db['_default'])]
guesses = [db['_default'][i] for i in guesses]
df = pd.DataFrame(guesses,
                  columns=['date', 'time', 'name', 'guess', 'casket', 'win'])
df['date'] = pd.to_datetime(df['date'])
df['date'] = [d.date() for d in df['date']]
df['time'] = pd.to_datetime(df['time'], format="%H%M%S")
df['time'] = [t.time() for t in df['time']]
df['difference'] = abs(df['guess'] - df['casket'])

winners = {}

for _, item in df.iterrows():
    if item['win'] == 'yes':
        if item['name'] in winners.keys():
            winners[item['name']] += 1
        else:
            winners[item['name']] = 1

winners = dict(sorted(winners.items(), key=lambda item: item[1], reverse=True))

leaderboard = []

for key, value in winners.items():
    n_guesses = df.loc[df['name'] == key]['name'].value_counts().tolist()[0]
    closest_guess = df.loc[(df['name'] == key) & (df['win'] == 'yes')]
    closest_guess = min(closest_guess['difference'].tolist())
    leaderboard.append(
        {
            'User': key,
            'Num. Guesses': n_guesses,
            'Closest Guess': closest_guess,
            'Wins': value,
        }
    )
    
leaderboard = pd.DataFrame(leaderboard)


# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Set up the app layout
app.layout = html.Div([
    html.H1("Hey_Jase Master Casket Tracker", style={'textAlign': 'center'}),
    html.H3("Leaderboard", style={
            'textAlign': 'center'
        }),
    dash_table.DataTable(
        id='leaderboard',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in leaderboard.columns
        ],
        data=leaderboard.head(n=10).to_dict('records'),
        editable=False,
        filter_action="none",
        sort_action="none",
        sort_mode="single",
        column_selectable=False,
        row_selectable=False,
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 100,
        filter_options={'case': 'insensitive'},
        style_cell={'textAlign': 'center'}
    ),
    html.Br(),
    html.H3("All Data", style={
            'textAlign': 'center'
        }),
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns if i != 'id'
        ],
        data=df.to_dict('records'),
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="single",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 20,
        filter_options={'case': 'insensitive'},
        style_cell={'textAlign': 'center'},
    ),

])







# Run local server
if __name__ == '__main__':
    app.run_server(debug=False)

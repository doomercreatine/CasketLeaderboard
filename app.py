"""_summary_
This file is for an interactive dashboard to visualize the guesses that people have made to date.
"""
from dash import Dash, html, dcc, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import requests
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy import stats


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Casket Dashboard"
app._favicon = ("./favicon.ico")
server = app.server

def default_plot():
    fig = go.FigureWidget(data=[
    go.Histogram(x=[])
    ])
    fig.layout.update(template="plotly_dark")
    return fig


# Set up the app layout
app.layout = html.Div([
    html.H1("Hey_Jase Master Casket Tracker", style={'textAlign': 'center'}), 
    # Leaderboard header and datatable formatting
    html.H3("Leaderboard", style={
            'textAlign': 'center'
        }),
    dcc.Store(id="store"),  # store that holds the data reference
    dcc.Store(id="sha", data=""),
    dcc.Interval(
            id='interval',
            interval=300*1000,
            n_intervals=0),
    dash_table.DataTable(
        id="leaderboard",
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="single",
        column_selectable=False,
        row_selectable=False,
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        cell_selectable=False,
        page_action="native",
        page_current= 0,
        page_size= 10,
        filter_options={'case': 'insensitive'},
        style_cell={'textAlign': 'center', 'background': '#222'}
    ),
    html.Div(id="stats"),
    html.Div([
        dcc.Graph(
            id='guess-graph',
            figure=default_plot(),
            style={'width': '49%', 'display': 'inline-block'}
        ),
        # Column 2 plot
        dcc.Graph(id='guess-line', figure=default_plot(), style={'width': '49%', 'display': 'inline-block'}),
    ], style={'padding': '0 20'}),
    html.Div([
        # Column 1
        dcc.Graph(id='guess-series', figure=default_plot(), style={'width': '49%', 'display': 'inline-block'}),
        # Column 2
        dcc.Graph(id='guess-series-x', figure=default_plot(), style={'width': '49%', 'display': 'inline-block'}),
    ]),
    html.Br(),
    # Raw datatable
    html.H3("All Data", style={
            'textAlign': 'center'
        }),
    dash_table.DataTable(
        id='datatable-interactivity',
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="single",
        column_selectable=False,
        row_selectable=False,
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        cell_selectable=False,
        page_action="native",
        page_current= 0,
        page_size= 20,
        filter_options={'case': 'insensitive'},
        style_cell={'textAlign': 'center', 'background': '#222'},
    ),  
])


@app.callback([Output("store", "data"),
               Output("stats", "children")],
              Input('interval', 'n_intervals'),
              State("sha", "data"),
              State("store", "data"))
def update_data(n_clicks, sha_data, data):
    resp = json.loads(requests.get("https://api.github.com/repos/doomercreatine/casketleaderboard/contents/updated_db.json").content)
    if resp['sha'] == sha_data:
        df = pd.read_json(data)
    else:
        db = requests.get("https://raw.githubusercontent.com/doomercreatine/MasterCasketBot/main/updated_db.json").json()
        sha_data = resp['sha']
        # Build a pandas dataframe from the JSON
        guesses = [item for item in iter(db['_default'])]
        guesses = [db['_default'][i] for i in guesses]
        df = pd.DataFrame(guesses,
                        columns=['date', 'time', 'name', 'guess', 'casket', 'win'])
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = [d.date() for d in df['date']]
        df['time'] = pd.to_datetime(df['time'], format="%H%M%S")
        df['time'] = [t.time() for t in df['time']]
        df['difference'] = abs(df['guess'] - df['casket'])
    caskets = sorted(set(df['casket']))
    total_caskets = len(caskets)
    return [
        df.to_json(),
        [    # Stats on casket values and guesses
            html.H4(f"Total caskets: {total_caskets} | Mean casket value: {'{:,}'.format(int(np.mean(caskets)))} (\u00B1 {'{:,}'.format(int(np.std(caskets)))}gp) sd) | Median casket value: {'{:,}'.format(int(np.median(caskets)))}gp", style={
                    'textAlign': 'center'
            }),
            # Count of how many caskets and how many guesses have been logged
            html.H4(f"Guesses logged: {'{:,}'.format(df['guess'].count())} | Mean guess value: {'{:,}'.format(int(np.mean(df['guess'])))} (\u00B1 {'{:,}'.format(int(np.std(df['guess'])))}gp) sd | Median guess value: {'{:,}'.format(int(np.median(df['guess'])))}gp", style={
                'textAlign': 'center'
            })]
    ]


@app.callback(
    [Output("leaderboard", "columns"),
    Output("leaderboard", "data"),
    Output("datatable-interactivity", "columns"),
    Output("datatable-interactivity", "data")], 
    Input("store", "data"))
def show_data(data):
    df = pd.read_json(data)
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
                'Rate (1 in )': round(( n_guesses/value ), 2)
            }
        )
        
    leaderboard = pd.DataFrame(leaderboard)
    return(
        [
            [{"name": i, "id": i, "deletable": False, "selectable": True} for i in leaderboard.columns],
            leaderboard.to_dict('records'),
            [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns if i != 'id'],
            df.to_dict('records'),
        ]
    )
    
@app.callback(
    Output("guess-graph", "figure"),
    Input("store", "data")
)
# Creates the top left graph for guesses per stream
def update_graph(data):
    df = pd.read_json(data)
    fig = go.FigureWidget(data=[
        go.Histogram(x=df['date'].tolist())
    ])
    fig.update_xaxes(
    tickformat="%d %b %Y")
    fig.layout.update(title="Guesses per Stream", template="plotly_dark")
    return fig
@app.callback(
    Output("guess-line", "figure"),
    Input("store", "data")
)
# Line graph creation to plot the distribution of casket values versus guesses
def line_graph(data):
    df = pd.read_json(data)
    casket_data = df['casket'].tolist()
    guess_data = df['guess'].tolist()
    guess_lower = df['guess'].quantile(0.025)

    guess_upper = df['guess'].quantile(0.975)
    guess_data = np.where(guess_data < guess_lower, guess_lower, guess_data)

    guess_data = np.where(guess_data > guess_upper, guess_upper, guess_data)
    group_labels = ['casket', 'guess'] # name of the dataset
    fig = ff.create_distplot([casket_data, guess_data], group_labels, show_hist=False, curve_type='kde', show_rug=False)
    fig.layout.update(title='Guess and Casket Distributions', template="plotly_dark")
    return fig


# Updates the Row 2 Column 1 graph
@app.callback(
    Output('guess-series', 'figure'),
    State('store', 'data'),
    Input('guess-graph', 'clickData'))
def update_x_timeseries(data, clickData):
    df = pd.read_json(data)
    idx = clickData['points'][0]['pointNumbers']
    new_df = df.iloc[idx]
    fig = go.FigureWidget(data=[
        go.Histogram(x=new_df['time'].tolist())
    ])
    fig.update_xaxes(
    tickformat="%H:%M")
    fig.layout.update(title='Guesses per Casket', template="plotly_dark")
    return fig
    
# Updates the Row 2 Column 2 graph
@app.callback(
    Output('guess-series-x', 'figure'),
    State('store', 'data'),
    Input('guess-series', 'clickData')
    )
def update_xx_timeseries(data, clickData):
    df = pd.read_json(data)
    idx = clickData['points'][0]['pointNumbers']
    new_df = df.iloc[idx]
    fig = go.FigureWidget(data=[
        go.Histogram(x=new_df['guess'].tolist())
    ])
    fig.update_traces(xbins=dict( # bins used for histogram
        start=0,
        end=max(new_df['guess'])+100000,
        size=100000
    ))
    fig.layout.update(title="Guesses Distribution", template="plotly_dark")
    return fig


# Run local server
if __name__ == '__main__':
    app.run_server(debug=False)

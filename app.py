"""_summary_
This file is for an interactive dashboard to visualize the guesses that people have made to date.
"""

import pandas as pd
import plotly.express as px
from dash import Dash, html, dash_table
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

def update_graph():
    fig = px.histogram(df, x = "date", title="Guesses per Stream")
    fig.update_xaxes(

    tickformat="%d %b %Y")
    return fig

def line_graph():
    casket_data = df['casket'].tolist()
    guess_data = df['guess'].tolist()
    guess_lower = df['guess'].quantile(0.10)

    guess_upper = df['guess'].quantile(0.90)
    guess_data = np.where(guess_data < guess_lower, guess_lower, guess_data)

    guess_data = np.where(guess_data > guess_upper, guess_upper, guess_data)
    group_labels = ['casket', 'guess'] # name of the dataset
    fig = ff.create_distplot([casket_data, guess_data], group_labels, show_hist=False, curve_type='normal', show_rug=False)
    fig.layout.update(title='Guess and Casket Distributions')
    return fig

# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
    
    html.Div([
        dcc.Graph(
            id='guess-graph',
            figure=update_graph(), style={'width': '49%', 'display': 'inline-block'}
        ),
        dcc.Graph(id='guess-line', figure=line_graph(), style={'width': '49%', 'display': 'inline-block'}),
    ], style={'padding': '0 20'}),
    html.Div([
        dcc.Graph(id='guess-series', style={'width': '49%', 'display': 'inline-block'}),
        dcc.Graph(id='guess-series-x', style={'width': '49%', 'display': 'inline-block'}),
    ]),
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




@app.callback(
    Output('guess-series', 'figure'),
    Input('guess-graph', 'clickData'))
def update_x_timeseries(clickData):
    idx = clickData['points'][0]['pointNumbers']
    new_df = df.iloc[idx]
    fig = px.histogram(new_df, x = "time", title="Guesses per Casket")
    fig.update_xaxes(
    tickformat="%H:%M")
    return fig
'''
@app.callback(
    Output('guess-line', 'figure'),
    Input('guess-graph', 'clickData'))
def update_line_timeseries(clickData):
    idx = clickData['points'][0]['pointNumbers']
    new_df = df.iloc[idx]
    hist_data = new_df['casket'].tolist()
    hist_data2 = new_df['guess'].tolist()
    mean = np.median(np.array(hist_data), axis=0)
    sd = np.std(np.array(hist_data), axis=0)

    final_list = [x for x in hist_data if (x > mean - 2 * sd)]
    final_list = [x for x in final_list if (x < mean + 2 * sd)]
    group_labels = ['casket', 'guess'] # name of the dataset

    fig = ff.create_distplot([final_list, hist_data2], group_labels, show_hist=False, curve_type='kde')
    return fig
    '''
    

@app.callback(
    Output('guess-series-x', 'figure'),
    Input('guess-series', 'clickData'))
def update_xx_timeseries(clickData):
    idx = clickData['points'][0]['pointNumbers']
    new_df = df.iloc[idx]
    fig = px.histogram(new_df, x = "guess", title = "Guesses Distribution")
    fig.update_traces(xbins=dict( # bins used for histogram
        start=0,
        end=max(new_df['guess'])+100000,
        size=100000
    ))
    return fig




# Run local server
if __name__ == '__main__':
    app.title = "Hey_Jase Master Casket Dashboard"
    app.run_server(debug=False)

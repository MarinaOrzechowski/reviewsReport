# import updateDB
import dash
import dash_table
import dash_core_components as dcc
import dash_daq as daq
#import dash_bootstrap_components as dbc
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import re
from datetime import date, timedelta
import pymongo
import pandas as pd
from pymongo import MongoClient

import numpy as np
import pandas as pd

#your MongoDb password here
mypassw = 
# prevent triggering of pandas chained assignment warning
pd.options.mode.chained_assignment = None
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, meta_tags=[
    {"content": "width=device-width, initial-scale=1.0"}
])

#connect to boaReviews database
client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
db = client["boaReviews"]
collection = db["reviews"]
df = pd.DataFrame(collection.find())
del df['_id']
df = df.sort_values(by=['date'], ascending=False)

# add missing columns which are necessary for visualization
df['count'] = 1
df.insert(0, 'geoid', range(0, len(df)))
columns = df.columns
#df = df.dropna()
df['rating'] = pd.to_numeric(df['rating'])
df['date'] = df['date'].astype(str).str.slice(0,10)
df['month'] = df['date'].str[5:7]
print(df.date)
df['day'] = df['date'].str[8:]

table_columns = ['date', 'name','rating','product', 'source', 'text', 'responded']
table_df = df[table_columns]

# fixme
colors = {
    'background': '#F5F5F5',
    'background2': '#d3d3d3',
    'text': '#000000',
    'text2': '#000000',
    'border': '#000000',
    'chart': ['#27496d', '#00909e', '#4d4c7d']
}

##############################################################################
# parallel coordinates graph
new_columns = ['weekday','rating','product', 'gender']
filtered_data = df[new_columns]

# array of attributes
arr1 = [str(r) for r in new_columns if r not in ['rating']]
arr1 = sorted(arr1)
arr = ['rating']
arr.extend(arr1)

fig = go.Figure(data=px.parallel_categories(
    filtered_data, dimensions=new_columns, title = "Parallel Categories Plot",
    color = 'rating', color_continuous_scale = px.colors.sequential.Viridis
    ))

fig.update_layout(
    height=800,
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],

)
##############################################################################################
# page layout
##############################################################################################
app.layout = html.Div(
    html.Div([

        # Hidden divs inside the app that stores the selected areas on the map and passes it into
        # the map callback so those areas are colored
        html.Div(id='selectedReviews', style={'display': 'none'}),
        html.Div(id='scrapedData', style={'display': 'none'}),

        # row1 with the header 
        html.Div([
            html.H1(
                children='DoubleIA Analytics Tool',
                className='row')
        ], style={
            'textAlign': 'center',
            'color': colors['text'],
            'paddingTop':'1%',
            'paddingBottom': '1%'
        }, className='row'),

    # row2: button 'request reviews'
    html.Div([
            html.Button('Scrape New Reviews', id='scrape_btn', n_clicks=0, style={'backgroundColor':'#32B2B2'})
            ], 
            style={
            'textAlign': 'center',
            'color': colors['text'],
            'paddingTop':'1%',
            'paddingBottom': '1%'
        }, className='row'),
    # row3 with a date range input 
        html.Div([

            # row2: date range
            html.Div([
                dcc.DatePickerRange(
                    id = 'datePicker',
                    start_date_placeholder_text="Start Period",
                    end_date_placeholder_text="End Period",
                    calendar_orientation='vertical',
                    style={'float': 'left', 
                            'backgroundColor': colors['background'],
                            'paddingTop':'1%',
                            'paddingBottom': '2%'
                    }
                )  
            ],
                className='three columns'
            ),
            
        #     dbc.Modal(
        #     [
        #         dbc.ModalHeader("Retrieving Reviews"),
        #         dbc.ModalBody("Please wait."),
        #         dbc.ModalFooter(
        #             dbc.Button("Close", id="close_btn", className="ml-auto")
        #         ),
        #     ],
        #     id="modal",
        #     size="lg",
        #     backdrop = False,
        #     centered=True
        # )
        ],
            className='row'),



        # row3 with a table 
        html.Div([
            # row3:  table
            html.Div([
                dash_table.DataTable(
                    id='table',
                    columns=[{"id":i, "name": i.capitalize(), "deletable": True} for i in table_df.columns],
                    page_size=10,
                    filter_action='native',
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="multi",
                    style_header={
                        'backgroundColor': '#bae2e4',
                        'fontWeight': 'bold',
                        'font_size': '18px'
                    },
                    style_cell={'padding': '10px'},
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'text'},
                            'textAlign': 'left',
                            'maxWidth': '300px'
                            
                        }
                    ],
                    style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                tooltip_data=[
                    {
                        column: {'value': str(value), 'type': 'markdown'}
                        for column, value in row.items()
                    } for row in df.to_dict('rows')
                ],
                tooltip_duration=None,
                data=table_df.to_dict('records'),
                )
            ],
                className='row')

        ],
            className='row'),

        # row 4 with monthly and daily avg.reviews
        html.Div([
            # row4: montly avg. reviews line chart
            html.Div([
                dcc.Graph(
                    id='monthly_rating'
                )], className='six columns'),

            # row4 daily avg. reviews line chart
            html.Div([
                dcc.Graph(
                    id='daily_rating'
                )
            ], className='six columns')

        ],
            className='row'),

        # row5 with parallel coord
        html.Div([
            dcc.Graph(
                id='para_coor',
                figure = fig
            )
        ],
            className='row'),

    ],
        style={'backgroundColor': colors['background']})
)


####################################################################################
# callbacks
####################################################################################
# @app.callback(
#     Output('scrapedData', 'children'),
#     [
#         Input("scrape_btn", "n_clicks")
#     ])
# def scrape_data(n_clicks):
#     if n_clicks>0:
#         updateDB.updateDB()
#     client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
#     db = client["boaReviews"]
#     collection = db["reviews"]
#     df = pd.DataFrame(collection.find())
#     del df['_id']
#     df = df.sort_values(by=['date'], ascending=False)

    # # add missing columns which are necessary for visualization
    # df['count'] = 1
    # df.insert(0, 'geoid', range(0, len(df)))
    # columns = df.columns
    # #df = df.dropna()
    # df['rating'] = pd.to_numeric(df['rating'])
    # df['date'] = df['date'].astype(str).str.slice(0,10)
    # df['month'] = df['date'].str[5:7]
    # df['day'] = df['date'].str[8:]
    # return df.to_dict('records')

@app.callback(
        Output('table', 'data'),
    [
        Input("selectedReviews", "children")
    ])
def filter_table(review_ids):

    df_table = df
    df_filtered_table = df_table[df_table['geoid'].isin(review_ids)]
    return df_filtered_table.to_dict('records')

@app.callback(
        Output('selectedReviews', 'children'),
    [
        Input('datePicker','start_date'),
        Input('datePicker', 'end_date')
    ])
def toggle_modal(start_date, end_date):

    df_range = df

    if start_date:
        df_range = df_range[df_range['date'] >= start_date]
    if end_date:
        df_range = df_range[df['date'] <= end_date]
    
    selected_ids = df_range['geoid']
    return selected_ids



# update monthly representation of avg. ratings based on selected reviews
@app.callback(
    Output('monthly_rating', 'figure'),
    [Input('selectedReviews', 'children')]
    )
def display_selected_data(selected_reviews):

    months_data = df
    if len(selected_reviews)>0:
        months_data = months_data[months_data['geoid'].isin(selected_reviews)]


    df_selected = months_data.groupby(['month']).agg(
        {'count': 'sum', 'rating':'mean'}).reset_index()

    fig = go.Figure()
    months = [month for month in range(1, 13)]
    months_str = ['Jan', 'Feb', 'Mar', 'Apr', "May",
                  'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    title = "<b>Average Rating By Month</b>"

    # some months didn't have reviews, so fill it with zeros
    for i in range(12):
        if i+1 not in df_selected['month']:
            df_selected = df_selected.append(
                {'month': i+1, 'rating': 0}, ignore_index=True)

    ratings = [df_selected.iloc[i]['rating']
                    for i in range(12)]

    fig.add_trace(go.Scatter(x=months_str, y=ratings,
                                line=dict(width=0.5),
                                mode='lines+markers',
                                name=str('avg. rating')))

    fig.update_layout(xaxis_title='Month',
                      yaxis_title='avg. rating',
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      title={
                          'text': title,
                          'x': 0.5,
                          'xanchor': 'center'}
                      )
    return fig
    

# update daily representation of avg. ratings based on selected reviews
@app.callback(
    Output('daily_rating', 'figure'),
    [Input('selectedReviews', 'children')]
    )
def display_selected_data(selected_reviews):

    daily_data = df
    if len(selected_reviews)>0:
        daily_data = daily_data[daily_data['geoid'].isin(selected_reviews)]


    df_selected = daily_data.groupby(['weekday']).agg(
        {'count': 'sum', 'rating':'mean'}).reset_index()

    fig = go.Figure()
    days = [day for day in range(1, 8)]
    months_str = ['Mon', 'Tue', 'Wed', 'Thu', "Fri", 'Sat', 'Sun']

    title = "<b>Average Rating By Weekday</b>"

    # some days didn't have reviews, so fill it with zeros
    for i in range(7):
        if i not in df_selected['weekday']:
            df_selected = df_selected.append(
                {'weekday': i, 'rating': 0}, ignore_index=True)

    ratings = [df_selected.iloc[i]['rating']
                    for i in range(7)]

    fig.add_trace(go.Scatter(x=months_str, y=ratings,
                                line=dict(width=0.5),
                                mode='lines+markers',
                                name=str('avg. rating')))

    fig.update_layout(xaxis_title='Week Day',
                      yaxis_title='avg. rating',
                      plot_bgcolor=colors['background'],
                      paper_bgcolor=colors['background'],
                      title={
                          'text': title,
                          'x': 0.5,
                          'xanchor': 'center'}
                      )
    return fig


if __name__ == '__main__':
   # app.config['suppress_callback_exceptions'] = True
    app.run_server(debug=True)
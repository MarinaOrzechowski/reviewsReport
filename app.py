import updateDB
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
import base64

import numpy as np
import pandas as pd

#your MongoDb password here
mypassw = 
# prevent triggering of pandas chained assignment warning
pd.options.mode.chained_assignment = None
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,  meta_tags=[
    {"content": "width=device-width, initial-scale=1.0"}
])

#connect to boaReviews database
client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
db = client["boaReviews"]
collection = db["reviews"]
df = pd.DataFrame(collection.find())
del df['_id']
df['date'] = df['date'].astype(str).str.slice(0,10)
df = df.sort_values(by=['date'], ascending=False)

# add missing columns which are necessary for visualization
df['count'] = 1
df.insert(0, 'geoid', range(0, len(df)))
columns = df.columns
#df = df.dropna()
df['rating'] = pd.to_numeric(df['rating'])
df['date'] = df['date'].astype(str).str.slice(0,10)
df['month'] = df['date'].str[5:7]
df['day'] = df['date'].str[8:]

table_columns = ['date', 'name','rating','product', 'source', 'text', 'responded']
table_df = df[table_columns]

image_filename = 'assets\WordCount.jpeg' 
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

# fixme
colors = {
    'background': '#F5F5F5',
    'background2': '#d3d3d3',
    'text': '#000000',
    'text2': '#000000',
    'border': '#000000',
    'chart': ['#27496d', '#00909e', '#4d4c7d']
}


##############################################################################################
# page layout
##############################################################################################
app.layout = html.Div(
    html.Div([

        # Hidden divs (to store data)
        html.Div(id='selectedReviews', style={'display': 'none'}),
        html.Div(id='intermediate-value', style={'display': 'none'}),
        html.Div(id='isScraping', style={'display': 'none'}),

        # row1 with the header 
        html.Div([
            html.H1(
                children='DoubleAI Analytics Tool',
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

    #row 3 with label "This will take a few minutes. Please wait..."
    html.Div([
            html.H5(
                id='wait_text',
                children='This might take a few minutes. Please wait...',
                className='row')
        ], style={
            'display': 'block',
            'textAlign': 'center',
            'color': colors['text'],
            # 'paddingTop':'1%',
            # 'paddingBottom': '1%'
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
                    clearable=True,
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

        html.Div([
            html.Img(src='data:image/png;base64,{}'.format(encoded_image))
        ]),

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
                id='para_coor'
            )
        ],
            className='row'),

    ],
        style={'backgroundColor': colors['background']})
)


####################################################################################
# callbacks
####################################################################################

# show "please wait" text
@app.callback(
    Output('wait_text', 'style'),
    [
        Input("scrape_btn", "n_clicks"),
        Input('intermediate-value', 'children')])
def makeLabelVisible(n_clicks, updated):

    if updated:
        print('!!!done updating ')
        return {'display': 'none'}
    elif n_clicks>0:
        print('!!!! updating now')
        return {'display': 'block'}
    else:
        print('!!! didnt press btn yet')
        return {'display': 'none'}

    

# update dataset after scraping request
@app.callback(
    
    Output('intermediate-value', 'children'),
    [
        Input("scrape_btn", "n_clicks")
    ])
def get_recently_scraped_data(n_clicks):
    if n_clicks>0:
        updateDB.updateDB()
        client = MongoClient("mongodb+srv://mishkice:"+mypassw+"@cluster0.t6imm.mongodb.net/boaReviews?retryWrites=true&w=majority")
        db = client["boaReviews"]
        collection = db["reviews"]
        df_new = pd.DataFrame(collection.find())
        del df_new['_id']
        df_new['date'] = df_new['date'].astype(str).str.slice(0,10)
        df_new = df_new.sort_values(by=['date'], ascending=False)

        # add missing columns which are necessary for visualization
        df_new['count'] = 1
        df_new.insert(0, 'geoid', range(0, len(df_new)))
        columns = df_new.columns
        #df_new = df_new.dropna()
        df_new['rating'] = pd.to_numeric(df_new['rating'])
        df_new['date'] = df_new['date'].astype(str).str.slice(0,10)
        df_new['month'] = df_new['date'].str[5:7]
        df_new['day'] = df_new['date'].str[8:]

        return df_new.to_json(orient='split')
    else:
        return None

@app.callback(
        Output('table', 'data'),
    [
        Input("selectedReviews", "children"),
        Input('intermediate-value', 'children')
    ])
def filter_table(review_ids, updated_df):
    if updated_df:
        df_table = pd.read_json(updated_df, orient='split')
        df_table['date'] = df_table['date'].astype(str).str.slice(0,10)
        df_table['month'] = df_table['date'].str[5:7]
        df_table['day'] = df_table['date'].str[8:]
    else:
        df_table = df
    df_filtered_table = df_table[df_table['geoid'].isin(review_ids)]
    return df_filtered_table.to_dict('records')

@app.callback(
        Output('selectedReviews', 'children'),
    [
        Input('datePicker','start_date'),
        Input('datePicker', 'end_date'),
        Input('intermediate-value', 'children')
    ])
def toggle_modal(start_date, end_date, updated_df):
    if updated_df:
        df_range = pd.read_json(updated_df, orient='split')
        df_range['date'] = df_range['date'].astype(str).str.slice(0,10)
        df_range['month'] = df_range['date'].str[5:7]
        df_range['day'] = df_range['date'].str[8:]
    else:
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
    [Input('selectedReviews', 'children'),
    Input('intermediate-value', 'children')]
    )
def display_selected_data(selected_reviews, updated_df):
    if updated_df:
        months_data = pd.read_json(updated_df, orient='split')
        months_data['date'] = months_data['date'].astype(str).str.slice(0,10)
        months_data['month'] = months_data['date'].str[5:7]
        months_data['day'] = months_data['date'].str[8:]
    else:
        months_data = df

    if selected_reviews and len(selected_reviews)>0:
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
    [Input('selectedReviews', 'children'),
    Input('intermediate-value', 'children')]
    )
def display_selected_data(selected_reviews, updated_df):
    if updated_df:
        daily_data = pd.read_json(updated_df, orient='split')
        daily_data['date'] = daily_data['date'].astype(str).str.slice(0,10)
        daily_data['month'] = daily_data['date'].str[5:7]
        daily_data['day'] = daily_data['date'].str[8:]
    else:
        daily_data = df

    if selected_reviews and len(selected_reviews)>0:
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


    # update para_coord based on selected areas, outliers limit, and selected date
@app.callback(
        Output('para_coor', 'figure'),
    [
        Input('selectedReviews', 'children'),
        Input('intermediate-value', 'children')
    ])

def build_parallel_coord(selected_reviews, updated_df):

    if updated_df:
        para_data = pd.read_json(updated_df, orient='split')
        para_data['date'] = para_data['date'].astype(str).str.slice(0,10)
        para_data['month'] = para_data['date'].str[5:7]
        para_data['day'] = para_data['date'].str[8:]
    else:
        para_data = df

    if selected_reviews and len(selected_reviews)>0:
        para_data = para_data[para_data['geoid'].isin(selected_reviews)]


    df_selected = para_data.groupby(['weekday']).agg(
        {'count': 'sum', 'rating':'mean'}).reset_index()

    new_columns = ['weekday','rating','product', 'gender']
    filtered_data = para_data[new_columns]

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


    return fig


if __name__ == '__main__':
   # app.config['suppress_callback_exceptions'] = True
    app.run_server(debug=True)
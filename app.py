
# press request - > open window "In progress" and run it until requestReviews returns True
# retrieve data from MongoDB into dataframe
# filter out by date and product

import dash
import dash_table
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import re
from datetime import date


import numpy as np
import pandas as pd


# prevent triggering of pandas chained assignment warning
pd.options.mode.chained_assignment = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, meta_tags=[
    {"content": "width=device-width, initial-scale=1.0"}
])


# mapbox access info (not for boa project yet)
mapbox_access_token = 'pk.eyJ1IjoibWlzaGtpY2UiLCJhIjoiY2s5MG94bWRoMDQxdjNmcHI1aWI1YnFkYyJ9.eFsHqEMYY7qxa0Pb9USCtQ'
mapbox_style = "mapbox://styles/mishkice/ckbjhq6w50hlc1io4cnqg7svc"


# map 
# Load and prepare data for map:
# - merge each of them with geo data (centers_df) to get coordinates of tract centers to use in map;
base = "https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/geolayers/"
base2 = "https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/ct_geolayers/"

centers_df = pd.read_csv(
    'https://raw.githubusercontent.com/MarinaOrzechowski/GasLeakConEd/timeline_branch/data/processed/important_(used_in_app)/geoid_with_centers.csv')


# read data
df = pd.read_csv('data\wallethub_processed.csv')

columns = df.columns
df = df.dropna()
df['rating'] = pd.to_numeric(df['rating'])

table_columns = ['date', 'name','rating','product', 'source', 'text']
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

colorscale_by_boro = ['#e41a1c',
                      '#377eb8',
                      '#4daf4a',
                      '#984ea3',
                      '#ff7f00']

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
        html.Div(id='selected_reviews', style={'display':'none'}),
        html.Div(id='par_coord_range', style={'display': 'none'}),
        html.Div(id='selected_reviews_map', style={'display': 'none'}),


        # row1 with the header and reset button
        html.Div([
            html.H1(
                children='DoubleIA Analytics Tool',
                className='eleven columns'),
            html.Button('Reset', id='reset_btn', n_clicks=0, style={'backgroundColor':'#f59999'}),

        ], style={
            'textAlign': 'center',
            'color': colors['text'],
            'paddingTop':'1%',
            'paddingBottom': '1%'
        }, className='row'),

    
    # row2 with a date range input and button 'request reviews'
        html.Div([

            # row2: date range
            html.Div([
                dcc.DatePickerRange(
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text=date.today(),
                calendar_orientation='vertical',
                style={'float': 'left', 'backgroundColor': colors['background']}
            )  
            ],
                className='three columns'
            ),
            # row2: button 'request reviews'
            html.Button('Request Reviews', id='request_btn', n_clicks=0, style={'backgroundColor':'#32B2B2'})
        ],
            className='row'),



        # row3 with a table and line graphs (need to move down)
        html.Div([
            # row3:  table
            html.Div([
                dash_table.DataTable(
                    id='table',
                    columns=[{"id":i, "name": i, "id": i} for i in table_df.columns],
                    page_size=15,
                    style_cell={'padding': '2px'},
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
                className='six columns',
                style={'display': 'inline-block'}),

            html.Div([
                # row3: montly avg. reviews line chart
                html.Div([
                    dcc.Graph(
                        id='monthly_rating'
                    )], className='row'),

                # row3 daily avg. reviews line chart
                html.Div([
                    dcc.Graph(
                        id='daily_rating'
                    )
                ],
                className='row')

            ],
                className='six columns',
                style={'display': 'inline-block'})
        ],
            className='row'),

        # row4 with parallel coord
        html.Div([
            dcc.Graph(
                id='para_coor',
                figure = fig
            )
        ],
            className='row'),

        # not for boa project
        # # row7: dropdown to choose attributes
        # html.Div([

        #     html.Label([
        #             "Attributes for scatter plot: ",
        #             dcc.Dropdown(
        #                 id="dropdown_attr",
        #                 options=[
        #                     {
        #                         'label': i.replace('_', ' ').capitalize(), 'value': i
        #                     } for i in columns if i not in ['gas_leaks','gas_leaks_per_person','geoid', 'incident_year','Unnamed: 0']
        #                 ],
        #                 value=['lonely_housholder%', 'not_us_citizen%'],
        #                 multi=True,
        #                 placeholder="Select attributes",
        #                 style={'display': 'inline-block', 'width': '100%'}
        #             )
        #         ],
        #             className='six columns',
        #             style={'display': 'inline-block'})
        #     ],
        # className='row'),

        # # row8 with the scatterplots
        # html.Div([
        #     dcc.Graph(
        #         id='scatter_matrix'
        #     )
        # ],
        #     className='row')

        # select nbr for map (not used for boa yet )
        html.Div([
                dcc.Dropdown(
                    id='dropdown_nta',
                    options=[
                        {'label': i, 'value': i} for i in np.append('all', centers_df['nta'].unique())
                    ],
                    multi=True,
                    placeholder='Choose neighborhoods')
            ],
                className='six columns',
                style={'display': 'inline-block'}),

        # map
        html.Div([
                dcc.Graph(
                    id='map_graph',
                    figure=dict(

                        layout=dict(
                            mapbox=dict(
                                layers=[],
                                accesstoken=mapbox_access_token,
                                style=mapbox_style,
                                center=dict(
                                    lat=40.7342,
                                    lon=-73.91251
                                ),
                                pitch=0,
                                zoom=10,
                                maxzoom = 15,
                                minzoom = 5
                            ),
                            autosize=False,
                        ),
                    ),
                )
            ],
                className='row')


    ],
        style={'backgroundColor': colors['background']})
)


# takes a hex representation of a color (string) and returns an RGB (tuple)
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = hex_color * 2
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


####################################################################################
# callbacks
####################################################################################

# update monthly representation of avg. ratings based on selected reviews
@app.callback(
    Output('monthly_rating', 'figure'),
    [Input('selected_reviews', 'children')]
    )
def display_selected_data(selected_reviews):

    months_data = df
    if len(selected_reviews)>0:
        months_data = months_data[months_data['geoid'].isin(selected_reviews)]


    df_selected = months_data.groupby(['incident_month']).agg(
        {'count': 'sum', 'rating':'mean'}).reset_index()

    fig = go.Figure()
    months = [month for month in range(1, 13)]
    months_str = ['Jan', 'Feb', 'Mar', 'Apr', "May",
                  'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    title = "<b>Average Rating By Month</b>"

    # some months didn't have reviews, so fill it with zeros
    for i in range(12):
        if i+1 not in df_selected['incident_month']:
            df_selected = df_selected.append(
                {'incident_month': i+1, 'rating': 0}, ignore_index=True)

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
    [Input('selected_reviews', 'children')]
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

    title = "<b>Average Rating By Weekay</b>"

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

# filter data by selected location:
# - inputs: map, dropdown, scatterplot, par.coordinates;
# - recognize which input triggered the callback;
# - filter by that input;
# - return list of selected geoids
@app.callback(
    Output('selected_reviews', 'children'),
    [Input('par_coord_range', 'children')]
    )

def selected_areas(selected_pc):

    ctx = dash.callback_context
    if not ctx.triggered:
        return []
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'par_coord_range':
        return selected_pc
    else:
        return []


# @app.callback(
#     Output('selected_review_ids', 'children'),
#     [
#         Input('map_graph', 'selectedData'),
#         Input('dropdown_nta', 'value'),
#         Input('scatter_matrix', 'selectedData')
#     ])

# def selected_areas(selected_map, selected_dd, selected_scatter):

#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return []
#     trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

#     if trigger_id == 'dropdown_nta':
#         if (selected_dd and'all' in selected_dd) or not selected_dd:
#             return []
#         else:
#             return df[df['nta'].isin(selected_dd)]['geoid'].to_list()

#     if trigger_id == 'scatter_matrix':
#         points = selected_scatter["points"]
#         return np.unique([str(point["text"].split("<br>")[2]) for point in points])

#     if trigger_id == 'map_graph':
#         points = selected_map['points']
#         return np.unique([str(point["text"].split("<br>")[2]) for point in points])

# # retrieve selected lines (geoids) on the parallel coordinates graph
# @app.callback(
#     Output('par_coord_range', 'children'),
#     [
#         Input('para_coor', 'restyleData'),
#         Input('para_coor', 'figure'),
#         Input('selected_review_ids', 'children'),
#         Input('timeline', 'value'),
#         Input('outliers_toggle', 'on'),
#         Input('limit_outliers_field', 'value')
#     ]
# )

# def get_selected_parcoord(restyleData, figure, geoids, year, toggle, limit):
#     ranges = []
#     all_geoids = []

#     if year != 2019:
#         dff = df[df['incident_year']==year]
#     else:
#         dff = df_all_years

#     if toggle:
#         dff = dff[dff['gas_leaks_per_person'] < limit]

#     if len(geoids)>0:
#         dff = dff[dff['geoid'].isin(geoids)]

#     dim = 0
#     split = []
#     if restyleData:
#         for key, val in restyleData[0].items():
#             split = re.split(r'\[|\]', key)


#     if restyleData and len(split)>2:
#         dim = int(split[1])
#         label = figure['data'][0]['dimensions'][dim]['label']

#         # list of lists
#         if 'constraintrange' in figure['data'][0]['dimensions'][dim]:
#             ranges = figure['data'][0]['dimensions'][dim]['constraintrange']
#             all_geoids = []
#             # select geoids with gas_leaks in the selected intervals
#             if isinstance(ranges[0], list):
#                 for range in ranges:
#                     selected_dff = dff[dff[label.replace(' ', '_')].between(
#                         range[0], range[1], inclusive=True)]
#                     geoids = selected_dff['geoid']
#                     all_geoids.extend(geoids)
#             else:
#                 selected_dff = dff[dff[label.replace(' ', '_')].between(
#                     ranges[0], ranges[1], inclusive=True)]
#                 geoids = selected_dff['geoid']
#                 all_geoids.extend(geoids)

#     return all_geoids


#########################################################################################
# map - not for boa project

# update map depending on chosen year;
# red color areas selected on par.coord/scatterplot/dropdown/map
@app.callback(
    [
        Output("map_graph", "figure"),
        Output("selected_reviews_map", 'children')
    ],
    [
        Input('selected_reviews', 'children')
    ],
    [
        State("map_graph", "figure")
    ]
)
def display_map(selected_reviews, figure):

    text_ann = 'Average Rating per Office'

    annotations = [
        dict(
            showarrow=False,
            align="right",
            text=text_ann,
            font=dict(color="#000000"),
            bgcolor=colors['background'],
            x=0.95,
            y=0.95,
        )
    ]


    #colorscale = DEFAULT_COLORSCALE
    # latitude = data_["centerLat"]
    # longitude = data_["centerLong"]
    # hover_text = data_["hover"]
    latitude = (40.7342,)
    longitude = (-73.91251,)

    #cm = dict(zip(bins, colorscale))
    data = [
        dict(
            lat=latitude,
            lon=longitude,
            #text=hover_text,
            type="scattermapbox",
            hoverinfo="text",
            marker=dict(size=5, color="black", opacity=0),
        )
    ]

    if "layout" in figure:
        lat = figure["layout"]["mapbox"]["center"]["lat"]
        lon = figure["layout"]["mapbox"]["center"]["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]
        maxzoom = 15,
        minzoom = 5
    else:
        lat = (40.7342,)
        lon = (-73.91251,)
        zoom = 10
        maxzoom = 15,
        minzoom = 5

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
            maxzoom = 15,
            minzoom = 5
        ),
        height=900,
        transition={'duration': 500},
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode="lasso"
    )

    for geoid in selected_reviews:
        geo_layer = dict(
            sourcetype="geojson",
            source=base2 + str(geoid) + ".geojson",
            type="fill",

            color='#F74DFF',
            opacity=0.4,
            # CHANGE THIS
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    fig = dict(data=data, layout=layout)

    return fig, []

# # update para_coord based on selected areas, outliers limit, and selected date
# @app.callback(
#         Output('para_coor', 'figure'),
#     [
#         Input("selected_reviews_map", "children")
#     ])

# def build_parallel_coord(selected_reviews_map):
#     new_columns = ['incident_month', 'weekday','rating','product', 'gender']
#     filtered_data = df[new_columns]

#     if len(selected_reviews_map)>0:
#         filtered_data = filtered_data[filtered_data['geoid'].isin(selected_reviews_map)]
    
#     # array of attributes
#     arr1 = [str(r) for r in new_columns if r not in ['rating']]
#     arr1 = sorted(arr1)
#     arr = ['rating']
#     arr.extend(arr1)


#     dim = [dict(label=attr.replace('_', ' '), values=filtered_data[attr]) for attr in arr]

#     fig = go.Figure(data=go.Parcoords(
#         line=dict(
#             color=filtered_data['rating'],
#             colorscale=px.colors.sequential.Viridis,
#             showscale=True
#             ),
#         meta=dict(colorbar=dict(title="Avg. rating")),
#         dimensions=dim,
#         #labelangle=10
#         ))

#     fig.update_layout(
#         height=500,
#         plot_bgcolor=colors['background'],
#         paper_bgcolor=colors['background2'],

#     )
#     return fig





if __name__ == '__main__':
   # app.config['suppress_callback_exceptions'] = True
    app.run_server(debug=True)

from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
import seaborn as sns
import numpy as np
from model import ThermalState

######################################################################################################
### APP

app = Dash(__name__,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}])
app.css.append_css({'external_url': 'reset.css'})


# App layout
app.layout = html.Div([
    html.H1("Thermal State Master Equations"),
    html.Div([
        dcc.Graph(id='state-chart'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Div([
        dcc.Graph(id='dist-chart'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Div([
        html.H1("Thermal Inputs"),
        html.Div([
            html.H3("Outdoor Air Temperature (Ta)"),
            dcc.Slider(
                id='Ta-slider',
                min=0,
                max=30,
                value=10,
                step=1
            )
        ]),

        html.Div([
            html.H3("Set-point Temperature"),
            dcc.Slider(
                id='Tset-slider',
                min=10,
                max=30,
                value=20,
                step=1
            ),
        ]),

        html.Div([
            html.H3("Initial Indoor Temperature"),
            dcc.Slider(
                id='Tstart-slider',
                min=10,
                max=30,
                value=15,
                step=1
            ),
        ]),
    ]),
])


@app.callback(

    Output('state-chart', 'figure'),
    Output('dist-chart', 'figure'),
    [Input('Ta-slider', 'value'),
     Input('Tset-slider', 'value'),
     Input('Tstart-slider', 'value')]
)

def update_chart(Ta,Tset,Tstart):
    state = ThermalState(Ta, Tset, Tstart)
    x_path = state.runIt()

    # CONVERT TO TERRIBLE DASH PLOTTER...
    x1 = [0, 1, 2, 3]
    s_list = sns.color_palette("magma_r", 6)
    d_list = sns.color_palette("magma_r", 7)

    s_line_colors_rgba = ['rgba({}, {}, {}, 1)'.format(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in
                        s_list]
    d_line_colors_rgba = ['rgba({}, {}, {}, 1)'.format(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in
                          d_list]


    state_fig = go.Figure()
    dist_fig = go.Figure()

    for idx, t in enumerate(np.arange(0, 25, 4)):
        if t > 0:
            state = np.sum(x_path[t], axis=0)[0].tolist() + np.sum(x_path[t], axis=0)[1].tolist()
            dist = np.sum(np.sum(x_path[t], axis=2), axis=1)

            state_fig.add_trace(go.Scatter(x=x1, y=state, mode='lines+markers', line=dict(dash='dash',color=s_line_colors_rgba[idx-1]), name=f't = {t}'))
            dist_fig.add_trace(go.Scatter(x=list(range(0, 50)), y=dist, mode='lines', line=dict(dash='dash',color=d_line_colors_rgba[idx-1]), name=f't = {t}'))

    # Update layout
    state_fig.update_layout(title='Thermal State Distribution',
                      xaxis=dict(title="States", tickvals=x1, ticktext=['S[0,0]', 'S[0,1]','S[1,0]','S[1,1]']),
                      yaxis_title='Occupation number')

    dist_fig.update_layout(title='Indoor Air Temperature (Ti) Distribution',
                      xaxis_title='Indoor Temperature Ti (C)',
                      yaxis_title='Density')

    # sizing
    state_fig.update_layout(height=350)
    dist_fig.update_layout(height=350)

    return state_fig, dist_fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8071)
    # app.run_server(debug=True)
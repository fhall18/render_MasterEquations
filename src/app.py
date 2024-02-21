
from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import seaborn as sns
import numpy as np
from model import ThermalState

######################################################################################################
### APP

app = Dash(__name__)
server = app.server

# App layout
app.layout = html.Div([
    html.H1("Thermal State Master Equations"),
    html.Div([
        dcc.Graph(id='main-chart'),
    ],
    ),

    html.Div([
        html.H1("Thermal Inputs"),
        html.Div([
            html.H3("Outdoor Air Temperature (Ta)"),
            dcc.Slider(
                id='Ta-slider',
                min=-15,
                max=15,
                value=0,
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
Output('main-chart', 'figure'),
    [Input('Ta-slider', 'value'),
     Input('Tset-slider', 'value'),
     Input('Tstart-slider', 'value')]
)

def update_chart(Ta,Tset,Tstart):
    state = ThermalState(Ta, Tset, Tstart)
    x_path = state.runIt()

    # CONVERT TO TERRIBLE DASH PLOTTER...
    x1 = [0, 1, 2, 3] # placeholder state x-values
    s_list = sns.color_palette("magma_r", 6)
    d_list = sns.color_palette("magma_r", 7)

    s_line_colors_rgba = ['rgba({}, {}, {}, 1)'.format(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in
                        s_list]
    d_line_colors_rgba = ['rgba({}, {}, {}, 1)'.format(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in
                          d_list]

    fig = make_subplots(rows=1, cols=2, shared_yaxes=False,shared_xaxes=False, vertical_spacing=0.1)

    for idx, t in enumerate(np.arange(0, 25, 4)):
        if t > 0:
            state = np.sum(x_path[t], axis=0)[0].tolist() + np.sum(x_path[t], axis=0)[1].tolist()
            dist = np.sum(np.sum(x_path[t], axis=2), axis=1)

            fig.add_trace(go.Scatter(x=x1, y=state, mode='lines+markers', line=dict(dash='dash',color=s_line_colors_rgba[idx-1]), name=f't = {t}',showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=list(range(0, 50)), y=dist, mode='lines', line=dict(dash='dash',color=d_line_colors_rgba[idx-1]), name=f't = {t}'), row=1, col=2)

    # Update layout
    fig.update_yaxes(title_text="Occupation Number", row=1, col=1)
    fig.update_xaxes(title_text="Thermal State",tickvals=x1, ticktext=['S[0,0]', 'S[0,1]','S[1,0]','S[1,1]'], row=1, col=1)

    fig.update_xaxes(title_text="Indoor Air Temperature (℃)", row=1, col=2)
    fig.update_yaxes(title_text="", row=1, col=2)

    return fig


if __name__ == "__main__":
    # app.run_server(debug=True, port=8071)
    app.run_server(debug=True)
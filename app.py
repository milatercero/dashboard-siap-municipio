# =====================================
# TABLERO INTERACTIVO DE AGUACATE (versión para Render)
# =====================================
# Lee aguacate.csv, que se exporta desde Colab con los registros de aguacate

import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

# =====================================
# 1. DATOS
# =====================================

# El archivo ya viene filtrado a aguacate y toneladas desde Colab
df = pd.read_csv("aguacate.csv")

columnas_tabla = ["Anio", "Nomestado", "Nommunicipio", "Nomcicloproductivo",
                  "Nommodalidad", "Sembrada", "Cosechada", "Siniestrada",
                  "Volumenproduccion", "Rendimiento", "precio_por_unidad",
                  "Valorproduccion"]
df = df[columnas_tabla]

estados = sorted(df["Nomestado"].unique())
modalidades = sorted(df["Nommodalidad"].unique())
ciclos = sorted(df["Nomcicloproductivo"].unique())
anio_min = int(df["Anio"].min())
anio_max = int(df["Anio"].max())

# Nombres para mostrar en las gráficas y la tabla
etiquetas = {
    "Anio": "Año",
    "Nomestado": "Estado",
    "Nommunicipio": "Municipio",
    "Nomcicloproductivo": "Ciclo",
    "Nommodalidad": "Modalidad",
    "Sembrada": "Superficie sembrada (ha)",
    "Cosechada": "Superficie cosechada (ha)",
    "Siniestrada": "Superficie siniestrada (ha)",
    "Volumenproduccion": "Volumen de producción (ton)",
    "Rendimiento": "Rendimiento (ton/ha)",
    "precio_por_unidad": "Precio medio rural ($/ton)",
    "Valorproduccion": "Valor de la producción ($)"
}

variables = ["precio_por_unidad", "Volumenproduccion", "Rendimiento",
             "Cosechada", "Valorproduccion"]


# Función para filtrar los datos con los controles del panel
def filtrar_datos(estados_sel, municipios_sel, modalidades_sel, ciclos_sel,
                  periodo, busqueda):

    datos = df[
        (df["Anio"] >= periodo[0]) &
        (df["Anio"] <= periodo[1])
    ]

    if estados_sel:
        datos = datos[datos["Nomestado"].isin(estados_sel)]

    if municipios_sel:
        datos = datos[datos["Nommunicipio"].isin(municipios_sel)]

    datos = datos[datos["Nommodalidad"].isin(modalidades_sel)]
    datos = datos[datos["Nomcicloproductivo"].isin(ciclos_sel)]

    if busqueda:
        datos = datos[datos["Nommunicipio"].str.contains(busqueda, case=False, na=False)]

    return datos


# Función para agrupar: suma superficies, volumen y valor, y recalcula
# precio (valor / volumen) y rendimiento (volumen / cosechada)
def agrupar(datos, columnas):

    g = datos.groupby(columnas, as_index=False)[
        ["Sembrada", "Cosechada", "Siniestrada",
         "Volumenproduccion", "Valorproduccion"]
    ].sum()

    g["precio_por_unidad"] = g["Valorproduccion"] / g["Volumenproduccion"]
    g["Rendimiento"] = g["Volumenproduccion"] / g["Cosechada"]
    g = g.replace([np.inf, -np.inf], np.nan)

    return g


# Función para crear una tarjeta KPI
def tarjeta(titulo, id_valor):
    return dbc.Card(
        dbc.CardBody([
            html.H6(titulo),
            html.H4("-", id=id_valor)
        ]),
        className="text-center"
    )


# =====================================
# 2. APLICACIÓN
# =====================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Render usa esta variable para levantar el tablero con gunicorn
server = app.server

# =====================================
# 3. PANEL LATERAL DE CONTROLES
# =====================================

sidebar = html.Div([

    html.H4("AGUACATE", className="text-success"),
    html.Hr(),

    # Control 1: Dropdown de estados
    html.Label("Estado"),
    dcc.Dropdown(
        id="estado",
        options=[{"label": e, "value": e} for e in estados],
        value=[],
        multi=True,
        placeholder="Todos los estados"
    ),

    html.Br(),

    # Control 2: Dropdown de municipios (depende del estado)
    html.Label("Municipio"),
    dcc.Dropdown(
        id="municipio",
        options=[],
        value=[],
        multi=True,
        placeholder="Todos los municipios"
    ),

    html.Br(),

    # Control 3: RadioItems para la variable de análisis
    html.Label("Variable a analizar"),
    dcc.RadioItems(
        id="variable",
        options=[{"label": etiquetas[v], "value": v} for v in variables],
        value="precio_por_unidad"
    ),

    html.Br(),

    # Control 4: Checklist de modalidad
    html.Label("Modalidad"),
    dcc.Checklist(
        id="modalidad",
        options=[{"label": m, "value": m} for m in modalidades],
        value=modalidades,
        inline=True
    ),

    html.Br(),

    # Control 5: Checklist de ciclo productivo
    html.Label("Ciclo productivo"),
    dcc.Checklist(
        id="ciclo",
        options=[{"label": c, "value": c} for c in ciclos],
        value=ciclos
    ),

    html.Br(),

    # Control 6: RangeSlider de años
    html.Label("Periodo de análisis"),
    dcc.RangeSlider(
        id="periodo",
        min=anio_min,
        max=anio_max,
        step=1,
        value=[anio_min, anio_max],
        marks={a: str(a) for a in range(anio_min, anio_max + 1, 5)}
    ),

    html.Br(),

    # Control 7: Input para buscar municipio por texto
    html.Label("Buscar municipio"),
    dcc.Input(
        id="busqueda",
        type="text",
        value="",
        placeholder="Ej. Uruapan",
        className="form-control"
    ),

    html.Br(),

    # Control 8: RadioItems para cambiar el tipo de gráfica de tendencia
    html.Label("Tipo de gráfica de tendencia"),
    dcc.RadioItems(
        id="tipo_grafica",
        options=[
            {"label": "Líneas", "value": "lineas"},
            {"label": "Barras", "value": "barras"}
        ],
        value="lineas",
        inline=True
    ),

    html.Br(),

    # Control 9: Checklist para desglosar la tendencia por estado
    dcc.Checklist(
        id="desglose",
        options=[{"label": "Desglosar tendencia por estado", "value": "si"}],
        value=[]
    ),

    html.Hr(),

    # Control 10: Botón de actualización (aplica la búsqueda de texto)
    dbc.Button("Actualizar", id="actualizar", color="success",
               className="me-2"),

    # Control 11: Botón de reinicio
    dbc.Button("Reiniciar filtros", id="reiniciar", color="secondary")

], style={
    "padding": "20px",
    "backgroundColor": "#f1f3f5",
    "minHeight": "100vh"
})

# =====================================
# 4. CONTENIDO PRINCIPAL
# =====================================

kpis = dbc.Row([
    dbc.Col(tarjeta("Registros", "kpi_registros"), md=3),
    dbc.Col(tarjeta("Volumen total (ton)", "kpi_volumen"), md=3),
    dbc.Col(tarjeta("Precio medio ($/ton)", "kpi_precio"), md=3),
    dbc.Col(tarjeta("Rendimiento medio (ton/ha)", "kpi_rendimiento"), md=3)
], className="mb-3")

# Control 12: Tabs para cambiar de vista
pestanas = dcc.Tabs(id="pestanas", value="general", children=[

    # Vista 1: tendencia y comparación entre estados
    dcc.Tab(label="Resumen general", value="general", children=[
        dcc.Graph(id="grafica_tendencia"),
        dcc.Graph(id="grafica_barras")
    ]),

    # Vista 2: relaciones y distribuciones
    dcc.Tab(label="Relaciones y distribución", value="distribucion", children=[
        dcc.Graph(id="grafica_dispersion"),
        dbc.Row([
            dbc.Col(dcc.Graph(id="grafica_histograma"), md=6),
            dbc.Col(dcc.Graph(id="grafica_caja"), md=6)
        ])
    ]),

    # Vista 3: comparación de dos estados
    dcc.Tab(label="Comparar estados", value="comparar", children=[
        html.Br(),
        dbc.Row([
            dbc.Col([
                html.Label("Estado A"),
                # Control 13: Dropdown del estado A
                dcc.Dropdown(
                    id="estado_a",
                    options=[{"label": e, "value": e} for e in estados],
                    value=estados[0],
                    clearable=False
                )
            ], md=6),
            dbc.Col([
                html.Label("Estado B"),
                # Control 14: Dropdown del estado B
                dcc.Dropdown(
                    id="estado_b",
                    options=[{"label": e, "value": e} for e in estados],
                    value=estados[1],
                    clearable=False
                )
            ], md=6)
        ]),
        dcc.Graph(id="grafica_comparar"),
        html.Div(id="resumen_comparar", className="mt-2")
    ]),

    # Vista 4: tabla de registros
    dcc.Tab(label="Tabla de registros", value="tabla", children=[
        html.Br(),
        # Control 15: DataTable
        dash_table.DataTable(
            id="tabla",
            columns=[{"name": etiquetas[c], "id": c} for c in columnas_tabla],
            data=[],
            page_size=10,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#D9EAF7"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f2f2f2"}
            ]
        ),
        html.Br(),
        # Control 16: Download de los datos filtrados
        dbc.Button("Descargar CSV", id="descargar", color="success"),
        dcc.Download(id="archivo")
    ])
])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(sidebar, width=3),
        dbc.Col([
            html.H2("Producción y precio del aguacate en México",
                    className="mt-3"),
            html.P("Fuente: SIAP, cierre agrícola municipal"),
            html.Div(id="mensaje", className="text-danger"),
            kpis,
            pestanas
        ], width=9)
    ], className="g-0")
], fluid=True)

# =====================================
# 5. CALLBACK: MUNICIPIOS SEGÚN ESTADO
# =====================================

@app.callback(
    Output("municipio", "options"),
    Input("estado", "value")
)
def actualizar_municipios(estados_sel):

    datos = df
    if estados_sel:
        datos = df[df["Nomestado"].isin(estados_sel)]

    return [{"label": m, "value": m}
            for m in sorted(datos["Nommunicipio"].unique())]

# =====================================
# 6. CALLBACK: BOTÓN DE REINICIO
# =====================================

@app.callback(
    Output("estado", "value"),
    Output("municipio", "value"),
    Output("variable", "value"),
    Output("modalidad", "value"),
    Output("ciclo", "value"),
    Output("periodo", "value"),
    Output("busqueda", "value"),
    Output("tipo_grafica", "value"),
    Output("desglose", "value"),
    Input("reiniciar", "n_clicks"),
    prevent_initial_call=True
)
def reiniciar_filtros(n_clicks):
    return ([], [], "precio_por_unidad", modalidades, ciclos,
            [anio_min, anio_max], "", "lineas", [])

# =====================================
# 7. CALLBACK: GRÁFICAS, KPIs Y TABLA
# =====================================

@app.callback(
    Output("grafica_tendencia", "figure"),
    Output("grafica_barras", "figure"),
    Output("grafica_dispersion", "figure"),
    Output("grafica_histograma", "figure"),
    Output("grafica_caja", "figure"),
    Output("tabla", "data"),
    Output("kpi_registros", "children"),
    Output("kpi_volumen", "children"),
    Output("kpi_precio", "children"),
    Output("kpi_rendimiento", "children"),
    Output("mensaje", "children"),

    Input("estado", "value"),
    Input("municipio", "value"),
    Input("variable", "value"),
    Input("modalidad", "value"),
    Input("ciclo", "value"),
    Input("periodo", "value"),
    Input("tipo_grafica", "value"),
    Input("desglose", "value"),
    Input("actualizar", "n_clicks"),
    Input("reiniciar", "n_clicks"),
    # La búsqueda de texto se aplica al presionar "Actualizar"
    State("busqueda", "value")
)
def actualizar_tablero(estados_sel, municipios_sel, variable, modalidades_sel,
                       ciclos_sel, periodo, tipo, desglose, n1, n2, busqueda):

    # Si se presionó "Reiniciar filtros" se ignora la búsqueda de texto
    if ctx.triggered_id == "reiniciar":
        busqueda = ""

    datos = filtrar_datos(estados_sel, municipios_sel, modalidades_sel,
                          ciclos_sel, periodo, busqueda)

    # Si no hay registros se avisa y se regresan gráficas vacías
    if datos.empty:
        vacia = px.scatter(title="No hay registros con estos filtros")
        return (vacia, vacia, vacia, vacia, vacia, [], "0", "-", "-", "-",
                "No se encontraron registros. Revisa los filtros o la búsqueda.")

    # ---------- Gráfica 1: tendencia por año ----------
    if "si" in desglose:
        tendencia = agrupar(datos, ["Anio", "Nomestado"])
        color = "Nomestado"
    else:
        tendencia = agrupar(datos, ["Anio"])
        color = None

    if tipo == "lineas":
        fig1 = px.line(tendencia, x="Anio", y=variable, color=color,
                       markers=True, labels=etiquetas,
                       title=f"Tendencia anual: {etiquetas[variable]}")
    else:
        fig1 = px.bar(tendencia, x="Anio", y=variable, color=color,
                      labels=etiquetas,
                      title=f"Tendencia anual: {etiquetas[variable]}")
    fig1.update_layout(template="plotly_white")

    # ---------- Gráfica 2: barras por estado o municipio ----------
    # Si se eligió un solo estado, se comparan sus municipios
    if estados_sel and len(estados_sel) == 1:
        grupo = "Nommunicipio"
    else:
        grupo = "Nomestado"

    ranking = agrupar(datos, [grupo])
    ranking = ranking.sort_values(variable, ascending=False).head(15)

    fig2 = px.bar(ranking, x=grupo, y=variable, color=variable,
                  color_continuous_scale="Greens", labels=etiquetas,
                  title=f"Top 15 por {etiquetas[grupo].lower()}: "
                        f"{etiquetas[variable]} ({periodo[0]}-{periodo[1]})")
    fig2.update_layout(template="plotly_white")

    # ---------- Gráfica 3: dispersión superficie vs volumen ----------
    fig3 = px.scatter(datos, x="Cosechada", y="Volumenproduccion",
                      color="Nommodalidad", hover_name="Nommunicipio",
                      hover_data=["Nomestado", "Anio"], opacity=0.6,
                      labels=etiquetas,
                      title="Superficie cosechada vs volumen de producción "
                            "(cada punto es un municipio en un año)")
    fig3.update_layout(template="plotly_white")

    # ---------- Gráfica 4: histograma de la variable ----------
    fig4 = px.histogram(datos, x=variable, nbins=40, labels=etiquetas,
                        title=f"Distribución: {etiquetas[variable]}")
    fig4.update_layout(template="plotly_white")

    # ---------- Gráfica 5: boxplot por modalidad ----------
    fig5 = px.box(datos, x="Nommodalidad", y=variable, color="Nommodalidad",
                  labels=etiquetas,
                  title=f"Valores atípicos por modalidad: {etiquetas[variable]}")
    fig5.update_layout(template="plotly_white", showlegend=False)

    # ---------- KPIs ----------
    volumen = datos["Volumenproduccion"].sum()
    precio = datos["Valorproduccion"].sum() / volumen if volumen > 0 else np.nan
    cosechada = datos["Cosechada"].sum()
    rendimiento = volumen / cosechada if cosechada > 0 else np.nan

    kpi1 = f"{len(datos):,}"
    kpi2 = f"{volumen:,.0f}"
    kpi3 = f"${precio:,.2f}" if not np.isnan(precio) else "-"
    kpi4 = f"{rendimiento:,.2f}" if not np.isnan(rendimiento) else "-"

    return (fig1, fig2, fig3, fig4, fig5, datos.to_dict("records"),
            kpi1, kpi2, kpi3, kpi4, "")

# =====================================
# 8. CALLBACK: COMPARACIÓN DE ESTADOS
# =====================================

@app.callback(
    Output("grafica_comparar", "figure"),
    Output("resumen_comparar", "children"),
    Input("estado_a", "value"),
    Input("estado_b", "value"),
    Input("variable", "value"),
    Input("periodo", "value")
)
def comparar_estados(estado_a, estado_b, variable, periodo):

    datos = df[
        (df["Nomestado"].isin([estado_a, estado_b])) &
        (df["Anio"] >= periodo[0]) &
        (df["Anio"] <= periodo[1])
    ]

    comparacion = agrupar(datos, ["Anio", "Nomestado"])

    fig = px.line(comparacion, x="Anio", y=variable, color="Nomestado",
                  markers=True, labels=etiquetas,
                  title=f"{estado_a} vs {estado_b}: {etiquetas[variable]}")
    fig.update_layout(template="plotly_white")

    # Valor del periodo completo para cada estado
    total = agrupar(datos, ["Nomestado"]).set_index("Nomestado")

    textos = []
    for e in [estado_a, estado_b]:
        if e in total.index:
            textos.append(f"{e}: {total.loc[e, variable]:,.2f}")
        else:
            textos.append(f"{e}: sin registros en el periodo")

    resumen = html.H5(f"{etiquetas[variable]} ({periodo[0]}-{periodo[1]}) → "
                      + "  |  ".join(textos))

    return fig, resumen

# =====================================
# 9. CALLBACK: DESCARGA DE CSV
# =====================================

@app.callback(
    Output("archivo", "data"),
    Input("descargar", "n_clicks"),
    # Se descarga lo que muestra la tabla, incluyendo sus filtros y orden
    State("tabla", "derived_virtual_data"),
    prevent_initial_call=True
)
def descargar_reporte(n_clicks, datos_tabla):

    datos = pd.DataFrame(datos_tabla)

    return dcc.send_data_frame(
        datos.to_csv,
        "aguacate_filtrado.csv",
        index=False,
        encoding="utf-8-sig"
    )

# =====================================
# 10. EJECUTAR
# =====================================
# En Render no se usa esta parte (gunicorn arranca "server");
# sirve para probarlo en una computadora con: python app.py

if __name__ == "__main__":
    app.run(debug=False)

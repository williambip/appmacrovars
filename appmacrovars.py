import streamlit as st
from datetime import datetime
import numpy as np
import sgs
import pandas as pd
from slugify import slugify
import plotly.express as px

# Set page configuration to wide mode
st.set_page_config(page_title='Seleção de Variáveis Econômicas', layout='wide')

st.title('Seleção de Variáveis Econômicas')
### variaveis default
variables_dict = {
    'selic': 4390,
    'valor-compra-dolar': 3695,
    'valor-venda-dolar': 3696,
    'inpc': 188,
    'ipca': 433,
    'tx-selic': 4189,
    'pib': 4380,
    'ipca12': 13522,
    'endividamento-sfn': 19882,
    'endividamento-sfn-exceto-credito-habitacional': 20400,
    'atraso': 21082,
    'inadimplencia-pf': 21084,
    'inadimplencia-pj': 21083,
    'desocupacao': 24369,
    'cc': 4393,
    'ipa': 7459,
#    'it': 25241,
#    'ice': 1859
}
class CollectDataBacen:
    def __init__(self, dict_vars=None, start_date="01/05/2016", end_date="30/09/2024"):
        if dict_vars is None or not dict_vars:
            raise ValueError('Dados de variáveis não podem ser nulos.')
        self.dict_vars = dict_vars
        self.start_date = start_date
        self.end_date = end_date

    def request_macro_vars(self):
        df = sgs.dataframe(
            list(self.dict_vars.values()),
            start=self.start_date,
            end=self.end_date,
        )
        inverted_dict_codes = {v: k for k, v in self.dict_vars.items()}
        df.rename(columns=inverted_dict_codes, inplace=True)
        return df

# Initialize session state variables
if 'dict_vars' not in st.session_state:
    st.session_state['dict_vars'] = variables_dict
if 'var_name' not in st.session_state:
    st.session_state['var_name'] = ''
if 'var_value' not in st.session_state:
    st.session_state['var_value'] = 0
if 'data_collected' not in st.session_state:
    st.session_state['data_collected'] = False
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()


# Section to select start and end dates
st.header('Selecione os Períodos de início e fim da captação dos dados.')

data_inicio = st.date_input('Data Início', value=datetime(2016, 5, 1))
data_fim = st.date_input('Data Fim', value=datetime(2024, 4, 30))

# Section to add economic variables
st.header('Adicionar Variáveis Econômicas')

def add_variable():
    var_name = st.session_state['var_name']
    var_value = st.session_state['var_value']
    if var_name and var_value:
        slugified_var_name = slugify(var_name)
        if slugified_var_name in st.session_state['dict_vars']:
            st.warning(f'A variável "{slugified_var_name}" já existe.')
        else:
            st.session_state['dict_vars'][slugified_var_name] = int(var_value)
            st.success(f'Variável "{var_name}" com valor {var_value} adicionada.')
        # Reset input fields
        st.session_state['var_name'] = ''
        st.session_state['var_value'] = 0
    else:
        st.error('Por favor, insira tanto o nome da variável quanto o valor.')

# Input fields for variable name and value
var_name = st.text_input('Nome da Variável (string)', key='var_name')
var_value = st.number_input('Valor da Variável (int)', step=1, format='%d', key='var_value')

# Button to add the variable
st.button('Adicionar Variável', on_click=add_variable)

# Option to remove variables
st.subheader('Remover Variáveis Econômicas')
if st.session_state['dict_vars']:
    vars_to_remove = st.multiselect('Selecione as variáveis que deseja remover:', list(st.session_state['dict_vars'].keys()))
    if st.button('Remover Variáveis Selecionadas'):
        for var in vars_to_remove:
            del st.session_state['dict_vars'][var]
        st.success('Variáveis removidas com sucesso.')
else:
    st.write('Nenhuma variável para remover.')

# Display the current variables
st.subheader('Variáveis Econômicas Selecionadas')
st.write(st.session_state['dict_vars'])

# Option to reset variables to default
if st.button('Redefinir Variáveis para Padrão'):
    st.session_state['dict_vars'] = variables_dict.copy()
    st.success('Variáveis redefinidas para o padrão.')
    st.session_state['data_collected'] = False

# Proceed with data collection
if st.button('Prosseguir com Coleta de Dados'):
    if not st.session_state['dict_vars']:
        st.error('Nenhuma variável selecionada. Por favor, selecione pelo menos uma variável.')
    else:
        try:
            data_collector = CollectDataBacen(
                dict_vars=st.session_state['dict_vars'],
                start_date=data_inicio.strftime('%d/%m/%Y'),
                end_date=data_fim.strftime('%d/%m/%Y')
            )
            df = data_collector.request_macro_vars()
            st.session_state['df'] = df
            st.session_state['data_collected'] = True
        except Exception as e:
            st.error(f'Ocorreu um erro: {e}')
            st.session_state['data_collected'] = False

# Display the data and plots if data has been collected
if st.session_state['data_collected']:
    import plotly.graph_objects as go
    st.subheader('Gráfico de Linhas das Variáveis Econômicas')
#    st.line_chart(st.session_state['df'], height=600, use_container_width=True)
    df = st.session_state['df'].reset_index()
    df_melted = df.melt(id_vars='index', var_name='Variável', value_name='Valor')
    df_melted.rename(columns={'index': 'Data'}, inplace=True)

    # Create an empty figure
    fig = go.Figure()

    # Loop through each variable and add a separate trace for each
    for variable_name, group_data in df_melted.groupby('Variável'):
        fig.add_trace(go.Scatter(
            x=group_data['Data'],
            y=group_data['Valor'],
            mode='lines',
            name=variable_name,  # This will set the name in the legend and hover tooltip
            hovertemplate=f'Variável: {variable_name}<br>Data: %{{x}}<br>Valor: %{{y}}<extra></extra>'
        ))

    # Update layout of the figure
    fig.update_layout(
        title='Evolução das Variáveis Econômicas',
        xaxis_title='Data',
        yaxis_title='Valor',
        height=800,
        width=1200
    )

    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    # Download options
    st.subheader('Download dos Dados')
    download_format = st.selectbox('Selecione o formato para download:', ['CSV', 'Parquet'])

    if download_format == 'CSV':
        csv = st.session_state['df'].to_csv(index=True).encode('utf-8')
        st.download_button(
            label='Baixar Dados em CSV',
            data=csv,
            file_name='dados_economicos.csv',
            mime='text/csv'
        )
    elif download_format == 'Parquet':
        parquet = st.session_state['df'].to_parquet(index=True)
        st.download_button(
            label='Baixar Dados em Parquet',
            data=parquet,
            file_name='dados_economicos.parquet',
            mime='application/octet-stream'
        )

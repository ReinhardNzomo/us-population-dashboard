import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import openpyxl

# set page configs
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# load data
df_us = pd.read_excel(r'US Population.xlsx')

# transform data
## unpivot data
df_us_unpivoted = pd.melt(df_us,id_vars=[df_us.columns[0], df_us.columns[1]],var_name="Year", value_name="Population")


######### add a sidebar
## The selected_year (from the available years from 2010-2019) will then be used to
## subset the data for that year, which is then displayed in-app.

##The selected_color_theme will allow the choropleth map and heatmap to be
## colored according to the selected color specified by the aforementioned widget.

with st.sidebar:
    st.title('🏂 US Population Dashboard')

    year_list = list(df_us_unpivoted.Year.unique())[::-1]

    selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    df_selected_year = df_us_unpivoted[df_us_unpivoted.Year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by ="Population", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)


######### define custom functions to create the various plots displayed in the dashboard.
#### A heatmap will allow us to see the population growth over the years from 2010-2019 for the 52 states.
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'max({input_color}):Q',
                            legend=None,
                            scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        )
    #height=300
    return heatmap

#### A colored map of the 52 US states for the selected year is depicted by the choropleth map.
# input_df: The DataFrame that provides the data for the map.
# locations=input_id: The column in the DataFrame that contains the geographic locations (e.g., state abbreviations like 'CA', 'NY').
# color=input_column: The column with data values that will determine the color intensity on the map.
# locationmode="USA-states": Specifies that the geographic locations are US states.
# color_continuous_scale=input_color_theme: Sets the color scale for the map based on the input_color_theme.
# range_color=(0, max(df_selected_year.Population)): Defines the range of values for the color scale. The max function should be applied to the column in the DataFrame that holds the data values.
# scope="usa": Limits the map view to the USA.
# labels={'Population': 'Population'}: Customizes the label for the color scale in the map legend.
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column, locationmode="USA-states",
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_year.Population)),
                               scope="usa",
                               labels={'Population':'Population'}
                               )
    ### update_layout: A method used to update the layout of the Plotly figure.
    # template='plotly_dark': Applies the 'plotly_dark' template to the map, giving it a dark theme.
    # plot_bgcolor='rgba(0,0,0,0)': Sets the background color of the plotting area to be fully transparent.
    # paper_bgcolor='rgba(0,0,0,0)': Sets the background color of the entire figure (including margins) to be fully transparent.
    # margin=dict(l=0, r=0, t=0, b=0): Sets the margins around the plot to zero, making the plot fill the entire available space.
    # height=350: Sets the height of the map to 350 pixels.
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0,r=0,t=0,b=0),
        height=350
    )
    return choropleth

#### create a donut chart for the states migration in percentage.
# Particularly, this represents the percentage of states with annual inbound or outbound migration > 50,000 people.
# For instance, in 2019, there were 12 out of 52 states and this corresponds to 23%.
# First, calculate the year-over-year population migrations.
def calculate_population_difference(input_df, input_year):
  selected_year_data = input_df[input_df['Year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['Year'] == input_year - 1].reset_index()
  selected_year_data['population_difference'] = selected_year_data.Population.sub(previous_year_data.Population, fill_value=0)
  return pd.concat([selected_year_data.States, selected_year_data.StateCode, selected_year_data.Population, selected_year_data.population_difference], axis=1).sort_values(by="population_difference", ascending=False)

####
#donut chart is then created from the aforementioned percentage value for states migration
def make_donut(input_response, input_text, input_color):
    # Define colors based on the input_color
    if input_color == 'blue':
        chart_color = ['#29b5e8', '#155F7A']
    elif input_color == 'green':
        chart_color = ['#27AE60', '#12783D']
    elif input_color == 'orange':
        chart_color = ['#F39C12', '#875A12']
    elif input_color == 'red':
        chart_color = ['#E74C3C', '#781F16']
    # Data for the donut chart
    #    source DataFrame contains the data for the chart, where input_response is the percentage value to be visualized.
    source = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100-input_response, input_response]
    })
    #   source_bg provides background data for the donut chart.
    source_bg = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100, 0]
    })
    
    # Create the donut chart
    # The theta encoding maps the % value to the arc length, and color is mapped to different sections based on Topic
    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta="% value",
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=130, height=130)
    
    # Add text to the center of the donut chart
    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
    
    # Create background for the donut chart
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="% value",
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=130, height=130)
    
    # Combines the background chart, the donut chart, and the text label into a single visualization.
    return plot_bg + plot + text

#### create a custom function for making population values more concise as well as improving the aesthetics
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

#################################### App layout
# Finally, it’s time to put everything together in the app.
# Define the layout
# Begin by creating 3 columns:
col = st.columns((1.5, 4.5, 2), gap='medium')


################################# Column 1
with col[0]:
    st.markdown('#### Gains/Losses')

    df_population_difference_sorted = calculate_population_difference(df_us_unpivoted, selected_year)
    # top state metric
    if selected_year > 2010:
        first_state_name = df_population_difference_sorted.States.iloc[0]
        first_state_population = format_number(df_population_difference_sorted.Population.iloc[0])
        first_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = ''
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)
    # last state metric
    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.States.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.Population.iloc[-1])   
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])   
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)

    st.markdown('#### States Migration')

    if selected_year > 2010:
        # Filter states with population difference > 50000
        # df_greater_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference_absolute > 50000]
        df_greater_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference > 50000]
        df_less_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference < -50000]
        
        # % of States with population difference > 50000
        states_migration_greater = round((len(df_greater_50000)/df_population_difference_sorted.States.nunique())*100)
        states_migration_less = round((len(df_less_50000)/df_population_difference_sorted.States.nunique())*100)
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')
    else:
        states_migration_greater = 0
        states_migration_less = 0
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')
    migrations_col = st.columns((0.2,1,0.2))
    with migrations_col[1]:
        st.write('Inbound')
        st.altair_chart(donut_chart_greater)
        st.write('Outbound')
        st.altair_chart(donut_chart_less)

################################# Column 2
# Next, the second column displays the choropleth map and heatmap using custom functions created earlier.
with col[1]:
    st.markdown('#### Total Population')

    choropleth = make_choropleth(df_selected_year, 'StateCode', 'Population', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)

    heatmap = make_heatmap(df_us_unpivoted, 'Year', 'States', 'Population', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)

# ################################# Column 3
# shows the top states via a dataframe whereby the population are shown
# as a colored progress bar via the column_config parameter of st.dataframe.
with col[2]:
    st.markdown('#### Top States')

    st.dataframe(df_selected_year_sorted,
                 column_order=("States", "Population"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "States": st.column_config.TextColumn(
                        "States",
                    ),
                    "Population": st.column_config.ProgressColumn(
                        "Population",
                        format="%f",
                        min_value=0,
                        max_value=max(df_selected_year_sorted.Population),
                     )}
                 )
    
    with st.expander('About', expanded=True):
        st.write('''
            - Data: [U.S. Census Bureau](<https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html>).
            - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
            - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
            ''')
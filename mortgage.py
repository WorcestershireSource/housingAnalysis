import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime


# SIDEBAR 
region_choice = st.sidebar.selectbox("Select region:", ['United Kingdom', 'England', 'Scotland', 'Wales', 'Northern Ireland', 'London'])
year_start, year_end = [datetime(i, 1, 1) for i in st.sidebar.slider("Years covered:", 1975, 2022, (1975, 2022))]


# READ INPUT FILES AND CLEAN DATA
# BoE interest rate data
bankRate_df = pd.read_csv('datasources//BankRateHistoryBoE.csv', parse_dates=['Date'])
bankRate_df = bankRate_df.groupby(pd.Grouper(key='Date', freq='YS')).mean()
bankRate_df.reset_index(inplace=True)

# HM Land Registry house price data
housePrice_df = pd.read_csv('datasources//HPI-Average-prices-2022-08.csv', parse_dates=['Date'])
housePrice_df = housePrice_df[['Date', 'Average_Price']][housePrice_df['Region_Name'] == region_choice]
housePrice_df = housePrice_df.groupby(pd.Grouper(key='Date', freq='YS')).mean()
housePrice_df.reset_index(inplace=True)

# ONS CPIH inflation data
inflation_df = pd.read_csv('datasources//CPIH-series-301022.csv', header=8, parse_dates=['Date']).stack()

# ONS population estimates
pop_df = pd.read_csv('datasources//ONS_population_estimates_UK.csv', header=7)
pop_df = pd.melt(pop_df, id_vars=['Code','Name', 'Geography'], var_name='Date', value_name='Population')
pop_df = pop_df.replace('Mid-', '', regex=True)
pop_df['Date'] = pd.to_datetime(pop_df['Date'])
pop_df = pop_df[['Date', 'Name', 'Population']][pop_df['Name'] == region_choice.upper()]
pop_df['Index'] = [i / pop_df['Population'][pop_df['Date'].idxmin()] for i in pop_df['Population'] * 100]

# ONS housing stock data
houseNo_df = pd.concat([
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='1', header=4, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='3', header=5, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='4', header=4, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='5', header=4, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='6', header=5, na_values='..'),
], keys=['United Kingdom', 'England', 'Wales', 'Scotland', 'Northern Ireland'], names=['Region', 'Index']
)
houseNo_df.reset_index(inplace=True)
houseNo_df = houseNo_df[['Date', 'All dwellings']][houseNo_df['Region'] == region_choice]
houseNo_df = houseNo_df.replace('As at ', '', regex=True)
houseNo_df['Date'] = pd.to_datetime(houseNo_df['Date'])
houseNo_df = houseNo_df.groupby(pd.Grouper(key='Date', freq='YS')).mean()
houseNo_df['All dwellings'] = houseNo_df['All dwellings'].mul(1000)
houseNo_df.reset_index(inplace=True)
houseNo_df['Index'] = [i / houseNo_df['All dwellings'][houseNo_df['Date'].idxmin()] for i in houseNo_df['All dwellings'] * 100]



# HEADINGS
st.write("""
    # UK Housing Market Analysis
    A web application to analyse data on the UK housing market using Streamlit, Pandas and Altair. 
""")


# PAGE CONTENT
# Chart showing relationship between BoE base rate and housing prices
st.subheader('House prices have risen as interest rates have fallen')
br_chart = alt.Chart(
        bankRate_df[(bankRate_df['Date'] <= year_end) & (bankRate_df['Date'] >= year_start)]
    ).mark_line(color='#5276A7').encode(
    x = alt.X ('Date', axis = alt.Axis(grid=False)),
    y = alt.Y ('Bank Rate', axis = alt.Axis(title = 'Bank rate %'))
)
hpi_chart = alt.Chart(
        housePrice_df[(housePrice_df['Date'] <= year_end) & (housePrice_df['Date'] >= year_start)]
    ).mark_line(color='#57A44C').encode(
    x = alt.X ('Date', axis = alt.Axis(grid=False)),
    y = alt.Y ('Average_Price', axis = alt.Axis(title = 'Average house price £'))
)
chartalt = alt.layer(br_chart, hpi_chart).resolve_scale(
    y = 'independent'
).configure_axisLeft(labelColor='#5276A7', titleColor='#5276A7').configure_axisRight(labelColor='#57A44C', titleColor='#57A44C')
st.altair_chart(chartalt, use_container_width=True)
st.write('Note: prices are not adjusted for inflation.')
st.caption('Sources: Bank of England and HM Land Registry UK House Price Index')


# Chart showing UK population vs housing supply indexed as 2001 = 100
st.subheader('UK population and housing supply have grown at similar rates (Index: 2001 = 100)')
supplydemand = pd.merge(
    pop_df[['Date', 'Index']],
    houseNo_df[['Date', 'Index']],
    on='Date', 
    how='outer',
    suffixes=[': population', ': no. dwellings']
)
supplydemand = pd.melt(supplydemand, id_vars=['Date'], var_name='Index', value_name='Value')
supplydemand_chart = alt.Chart(
    supplydemand[(supplydemand['Date'] <= year_end) & (supplydemand['Date'] >= year_start)]
).mark_line(color='#5276A7').encode(
    y = alt.Y('Value', scale = alt.Scale(domain = (95, 120), clamp=True), axis = alt.Axis(tickCount=5)),
    x = alt.X ('Date', axis = alt.Axis(grid=False)),
    color = 'Index'
)
st.altair_chart(supplydemand_chart, use_container_width=True)
st.caption('Source: ONS UK population estimates and dwelling stock by tenure')
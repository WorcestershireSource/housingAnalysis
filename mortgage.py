import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
from functools import reduce



# SIDEBAR 
region_choice = st.sidebar.selectbox("Select region:", ['United Kingdom', 'England', 'Scotland', 'Wales', 'Northern Ireland', 'London'])
year_start, year_end = [datetime(i, 1, 1) for i in st.sidebar.slider("Years covered (where data available):", 1980, 2022, (1980, 2022))]
year_start_data = datetime(2001 if year_start.year < 2001 else year_start.year, 1, 1)
year_start_UK = datetime(2001 if region_choice != 'United Kingdom' and year_start.year < 2001 else year_start.year, 1, 1)



# READ INPUT FILES AND CLEAN DATA
# BoE interest rate data
bankRate_df = pd.read_csv('datasources//BankRateHistoryBoE.csv', parse_dates=['Date'])
bankRate_df = bankRate_df.groupby(pd.Grouper(key='Date', freq='YS')).mean(numeric_only=True)
bankRate_df.reset_index(inplace=True)

# HM Land Registry house price data
housePrice_df = pd.read_csv('datasources//HPI-Average-prices-2022-08.csv', parse_dates=['Date'])
housePrice_df = housePrice_df[housePrice_df['Region_Name'] == region_choice]
housePrice_df = housePrice_df.groupby(pd.Grouper(key='Date', freq='YS')).mean(numeric_only=True)
housePrice_df.reset_index(inplace=True)

# ONS CPIH inflation data
inflation_df = pd.read_csv('datasources//CPIH-series-301022.csv', header=8, parse_dates=['Date']).stack()

# ONS population estimates
pop_df = pd.read_excel('datasources//ONS_UK_population_time_series.xls', header=7, parse_dates=['Date'])
pop_df = pop_df[pop_df['Region'] == region_choice]
pop_df = pop_df[pop_df['Date'] > datetime(1979, 12, 31)]

# ONS housing stock data
houseNo_df = pd.concat([
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='1', header=4, na_values='..', parse_dates=['Date']),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='3', header=5, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='4', header=4, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='5', header=4, na_values='..'),
    pd.read_excel('datasources//ukdwellingdataset2020.xlsx', sheet_name='6', header=5, na_values='..'),
], keys=['United Kingdom', 'England', 'Wales', 'Scotland', 'Northern Ireland'], names=['Region', 'Index']
)
houseNo_df.reset_index(inplace=True)
houseNo_df = houseNo_df.replace('As at ', '', regex=True)
houseNo_df.loc[:,'Date'] = pd.to_datetime(houseNo_df['Date'])
houseNo_df = houseNo_df[houseNo_df['Region'] == region_choice]
houseNo_df = houseNo_df[houseNo_df['Date'] > datetime(1979, 12, 31)]
houseNo_df = houseNo_df.groupby(pd.Grouper(key='Date', freq='YS')).mean(numeric_only=True)
houseNo_df['All dwellings'] = houseNo_df['All dwellings'].mul(1000)
houseNo_df.reset_index(inplace=True)

# OBR GDP deflators
gdp_deflators_df = pd.read_excel('datasources//GDP_Deflators_Spring_Statement_March_2022_update.xlsx', header=5, na_values='-', parse_dates=['Date'])
gdp_deflators_df = gdp_deflators_df[gdp_deflators_df['Date'] > datetime(1979, 12, 31)]

# ONS wages
wages_df = pd.read_excel('datasources//ONS_earn01oct2022.xls', header=6, na_values='-', parse_dates=['Date']) 
wages_df = wages_df.groupby(pd.Grouper(key='Date', freq='YS')).mean(numeric_only=True)
wages_df.reset_index(inplace=True)



# PAGE CONTENT
# Heading
st.write("""
    # UK Housing Market Analysis
    A web application to analyse data on the UK housing market using Streamlit, Pandas and Altair. 

    ### Key points:
    - House prices have followed a long upward trend. This appears to be driven by the availability of cheap credit, movement within the UK and a trend toward smaller households. 
    - Smaller households could be a result of an aging population and a long-term shift away from multi-generation family households. 
    - There are strong regional disparities in prices. 
    - While the UK population has grown, the number of dwellings has kept pace with this chnage, although data does not show changes in sizes of dwellings or sub-national regions. 
""")


# Chart showing relationship between BoE base rate and housing prices
st.subheader('House prices have risen as interest rates have fallen')
st.write("Regional filter available.".format(year_start_UK.year))
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


# Chart showing UK population vs housing supply indexed against start year
st.subheader('At a national level housing supply has kept pace with population growth')
st.write("Index: {} = 100. Regional filter available. No data for dwellings by region before 2001.".format(year_start_UK.year))
houseNo_df['No. dwellings'] = [i / houseNo_df['All dwellings'][houseNo_df.index[houseNo_df['Date'] == year_start_UK].tolist()[0]] for i in houseNo_df['All dwellings'] * 100]
pop_df['Pop\'ation'] = [i / pop_df['Population'][pop_df.index[pop_df['Date'] == year_start_UK].tolist()[0]] for i in pop_df['Population'] * 100]
supplydemand = pd.merge(
    pop_df[['Date', 'Pop\'ation']],
    houseNo_df[['Date', 'No. dwellings']],
    on='Date', 
    how='outer',
)
supplydemand = pd.melt(supplydemand, id_vars=['Date'], var_name='Key', value_name='Index')
supplydemand_chart = alt.Chart(
    supplydemand[(supplydemand['Date'] <= year_end) & (supplydemand['Date'] >= year_start)]
).mark_line(color='#5276A7').encode(
    y = alt.Y('Index', scale = alt.Scale(domain = (95, 140), clamp=True), axis = alt.Axis(tickCount=5)),
    x = alt.X ('Date', axis = alt.Axis(grid=False)),
    color = 'Key'
)
st.altair_chart(supplydemand_chart, use_container_width=True)
st.caption('Source: ONS UK population estimates and dwelling stock (all dwelling types)')


# Chart showing change in house prices compared to GDP deflator and average wages
st.subheader('House prices have increased faster than wages and inflation')
st.write("Index: {} = 10. National data only. Data not available before 2001 for all measures.".format(year_start_data.year))
housePrice_df['House prices'] = [i / housePrice_df['Average_Price'][housePrice_df.index[housePrice_df['Date'] == year_start_data].tolist()[0]] for i in housePrice_df['Average_Price'] * 100]
wages_df['Wages'] = [i / wages_df['Weekly Earnings'][wages_df.index[wages_df['Date'] == year_start_data].tolist()[0]] for i in wages_df['Weekly Earnings'] * 100]
gdp_deflators_df['Inflation'] = [i / gdp_deflators_df['Index 20/21'][gdp_deflators_df.index[gdp_deflators_df['Date'] == year_start_data].tolist()[0]] for i in gdp_deflators_df['Index 20/21'] * 100]
df_to_merge = [wages_df, gdp_deflators_df, housePrice_df]
pricechanges = reduce(lambda  left,right: pd.merge(left,right,on=['Date'],how='outer'), df_to_merge)
pricechanges = pricechanges[['Inflation', 'House prices', 'Wages', 'Date']]
pricechanges = pricechanges[pricechanges['Date'] > datetime(2000, 12, 31)]
pricechanges = pd.melt(pricechanges, id_vars=['Date'], var_name='Key', value_name='Index')
pricechanges_chart = alt.Chart(
    pricechanges[(pricechanges['Date'] <= year_end) & (pricechanges['Date'] >= year_start)]
).mark_line(color='#5276A7').encode(
    y = alt.Y('Index', scale = alt.Scale(domain = (95, 300), clamp=True), axis = alt.Axis(tickCount=5)),
    x = alt.X ('Date', axis = alt.Axis(grid=False)),
    color = 'Key'
)
st.altair_chart(pricechanges_chart, use_container_width=True)
st.caption('Source: OBR GDP deflator estimates, HM Land Registry UK House Price Index and ONS average weekly earnings estimates')







# NO LONGER NEEEDED

# Original code for importing population data, but found a better time series - kept here for example of melt function

# pop_df = pd.read_csv('datasources//ONS_population_estimates_UK.csv', header=7)
# pop_df = pd.melt(pop_df, id_vars=['Code','Name', 'Geography'], var_name='Date', value_name='Population')
# pop_df = pop_df.replace('Mid-', '', regex=True)
# pop_df['Date'] = pd.to_datetime(pop_df['Date'])
# pop_df = pop_df[['Date', 'Name', 'Population']][pop_df['Name'] == region_choice.upper()]
# pop_df['Index'] = [i / pop_df['Population'][pop_df['Date'].idxmin()] for i in pop_df['Population'] * 100]
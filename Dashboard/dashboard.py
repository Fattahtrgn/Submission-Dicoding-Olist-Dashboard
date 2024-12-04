import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import io

import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

st.set_page_config(layout="wide", page_icon=":bar_chart:", page_title="Olist Dashboard")

# 
def create_daily_orders(df):
    if df.empty:
        return pd.DataFrame(columns=['order_purchase_timestamp', 'order_count', 'product_value', 'freigh_value', 'total_value'])

    daily_orders = df.resample(rule='D', on='order_purchase_timestamp').agg(
        order_count=('order_id', 'nunique'),
        product_value=('total_price', 'sum'),
        freigh_value=('freight_value', 'sum'),
        total_value=('total_value', 'sum')
    ).reset_index()

    return daily_orders

# def create_review_score(df):
#     review_score = df.groupby('review_score').agg(
#         frequency = ('review_id','nunique')
#     ).reset_index()
    
#     return review_score


def create_orders_category(df):
    orders_category = df.groupby('product_category_name').agg(
        Quantity = ('quantity', 'sum'),
        Value = ('total_price','sum')
    ).reset_index()

    return orders_category

def create_sellers_performance(df):
    sellers_performance = df.groupby('seller_id').agg(
        order_count = ('order_id', 'nunique'),
        total_value = ('total_price', 'sum'),
        average_score = ('review_score', 'mean')
    ).reset_index()

    return sellers_performance

def create_cust_city(df):
    cust_city = df.groupby('customer_city').agg(
        customer_count = ('customer_unique_id', 'nunique')
    ).sort_values('customer_count', ascending=False).reset_index()
    
    return cust_city

def create_cust_state(df):
    cust_state = df.groupby('customer_state').agg(
        customer_count=('customer_unique_id', 'nunique')
    ).sort_values('customer_count', ascending=False).reset_index()

    return cust_state

def create_create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg(
        max_order_timestamp = ("order_purchase_timestamp", "max"),
        frequency = ("order_id", "nunique"),
        monetary = ("total_price", "sum")
    ).reset_index()

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

def create_star(df):

    avg_score = df['review_score'].mean() if not df['review_score'].isna().all() else 0

    fig = make_subplots(
        rows=1, 
        cols=2, 
        horizontal_spacing=0, 
        column_widths=[avg_score / 5, (5 - avg_score) / 5]
)

    x = [5, 15, 25, 35, 45]
    y = [25, 25, 25, 25, 25]

    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', 
                             marker=dict(symbol='star', color='gold', size=50, line=dict(width=2))),
                  row=1, col=1)

    if avg_score < 5:
        fig.add_trace(go.Scatter(x=x, y=y, mode='markers', 
                                marker=dict(symbol='star', color='grey', size=50, line=dict(width=2))),
                    row=1, col=2)

    fig.update_layout(
        showlegend=False,
        width=350,
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showticklabels=False, range=[0, avg_score * 10]),
        yaxis=dict(showticklabels=False, showgrid=False),
        xaxis2=dict(showticklabels=False, range=[avg_score * 10, 50]),
        yaxis2=dict(showticklabels=False, showgrid=False)
    )

    return fig

#
all_df = pd.read_csv("Dashboard/all_data.csv")


all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)    

all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])
all_df['order_date'] = all_df['order_purchase_timestamp'].dt.date



min_date = all_df["order_date"].min()
max_date = all_df["order_date"].max()

with st.sidebar:

    st.image("Dashboard/logo.svg")
    
    start_date = st.date_input("Pilih tanggal mulai", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Pilih tanggal akhir", min_value=min_date, max_value=max_date, value=max_date)

    if end_date < start_date:
        st.warning("Tanggal akhir lebih awal dari tanggal mulai. Tanggal akhir otomatis disamakan dengan tanggal mulai.")
        end_date = start_date
    elif start_date > end_date:
        st.warning("Tanggal mulai lebih besar dari tanggal akhir. Tanggal mulai otomatis disamakan dengan tanggal akhir.")
        start_date = end_date

main_df = all_df[(all_df["order_date"] >= start_date) &
                 (all_df["order_date"] <= end_date)]

if main_df.empty:
        st.warning("Warning: Tidak ada data pada rentang waktu ini.")



daily_orders1 = create_daily_orders(main_df)
daily_orders2 = create_daily_orders(all_df)
# review_score = create_review_score(main_df)
orders_category = create_orders_category(main_df)
sellers_performance = create_sellers_performance(main_df)
cust_city = create_cust_city(main_df)
cust_state = create_cust_state(main_df)
rfm_df = create_create_rfm_df(main_df)



st.header('Olist Dashboard :sparkles:')

st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders1.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_value = format_currency(daily_orders1.total_value.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", total_value)

col1, col2 = st.columns(2)

with col1:
    mean_score = str(round(main_df['review_score'].mean(), 1))
    st.metric("Average Score", mean_score + "/5.0")

with col2:
    fig = create_star(main_df)
    
    st.plotly_chart(fig, config={"displayModeBar": False, "staticPlot": True}, )


fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily_orders2['order_purchase_timestamp'],
    y=daily_orders2['order_count'],
    mode='lines',
    name='Orders per Day',
    hovertemplate='<b>Tanggal:</b> %{x}<br><b>Jumlah Order:</b> %{y}',
))

fig.update_layout(
    title='Total Orders per Day',
    xaxis=dict(
        range=[start_date - pd.Timedelta(days=3), end_date + pd.Timedelta(days=3)],
        rangeslider=dict(visible = True),
    ),
    template='plotly_dark',
    
)

st.plotly_chart(fig, use_container_width=False)


trace1 = go.Scatter(
    x=daily_orders2['order_purchase_timestamp'],
    y=daily_orders2['product_value'],
    mode='lines',
    name='Product Value'
)

trace2 = go.Scatter(
    x=daily_orders2['order_purchase_timestamp'],
    y=daily_orders2['freigh_value'],
    mode='lines',
    name='Freight Value'
)

layout = go.Layout(
    title='Product and Freight Value vs Total Orders per Day',
    xaxis=dict(
        range=[start_date - pd.Timedelta(days=3), end_date + pd.Timedelta(days=3)],
        rangeslider=dict(visible = True),
    ),
 
    legend=dict(
        x=1,
        y=1,
        orientation="h",  
        xanchor="right",  
        yanchor="bottom"  
    ),
    margin=dict(r=30),
    # paper_bgcolor='white',
)

fig = go.Figure(data=[trace1, trace2], layout=layout)

st.plotly_chart(fig)

st.subheader("Best  Product Category")

col1, col2 = st.columns(2)

with col1:
    fig= plt.figure(figsize=(20, 15))
    colors=["#72BCD4"] + ["#D3D3D3"]*9
    sns.barplot(
        y="product_category_name", 
        x="Quantity",
        data=orders_category.sort_values(by='Quantity', ascending=False).head(10),
        palette=colors,
    )
    plt.title("Total orders by category", fontsize=50)
    plt.ylabel(None)
    plt.xlabel(None)
    plt.tick_params(axis='x', labelsize=30)
    plt.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

with col2:
    fig= plt.figure(figsize=(20, 15))
    sns.barplot(
        y="product_category_name", 
        x="Value",
        data=orders_category.sort_values(by='Value', ascending=False).head(10),
        palette=colors,    
    )
    plt.title("Total values by category", fontsize=50)
    plt.ylabel(None)
    plt.xlabel(None)
    plt.tick_params(axis='x', labelsize=30)
    plt.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

st.subheader("Customer Demographics")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 10))

sns.barplot(
    data=cust_city.head(5),
    y="customer_count", 
    x="customer_city",
    palette=colors,
    ax=ax[0]
)
ax[0].set_title("Number of Customer by cities", fontsize=40)
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].tick_params(axis='x', labelsize=35, rotation=45)
ax[0].tick_params(axis='y', labelsize=25)

sns.barplot(
    data=cust_state.head(5),
    y="customer_count", 
    x="customer_state",
    palette=colors,
    ax=ax[1]
)
ax[1].set_title("Number of Customer by states", fontsize=40)
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].tick_params(axis='x', labelsize=35, rotation=45)
ax[1].tick_params(axis='y', labelsize=25)

plt.suptitle("Customer Demographics by City and State", fontsize=50, y=1.05)

st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(),1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(),2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR')
    st.metric("Average Monetary", value=avg_monetary)

fig = make_subplots(
    rows=1, cols=3,
    subplot_titles=("By Recency (days)", "By Frequency", "By Monetary"),
    column_widths=[0.33, 0.33, 0.33],
)

top_customers_recency = rfm_df.sort_values("recency", ascending=True).head(10)
fig.add_trace(
    go.Bar(
        x=top_customers_recency["customer_unique_id"],
        y=top_customers_recency["recency"],
        marker_color="#90CAF9",
        name="Recency",
    ),
    row=1, col=1
)

top_customers_frequency = rfm_df.sort_values("frequency", ascending=False).head(10)
fig.add_trace(
    go.Bar(
        x=top_customers_frequency["customer_unique_id"],
        y=top_customers_frequency["frequency"],
        marker_color="#90CAF9",
        name="Frequency",
    ),
    row=1, col=2
)

top_customers_monetary = rfm_df.sort_values("monetary", ascending=False).head(10)
fig.add_trace(
    go.Bar(
        x=top_customers_monetary["customer_unique_id"],
        y=top_customers_monetary["monetary"],
        marker_color="#90CAF9",
        name="Monetary",
    ),
    row=1, col=3
)

fig.update_layout(
    # title_text=None,
    # title_x=0,
    height=600,
    showlegend=False, 
    xaxis_title=None,
    yaxis_title=None,
    xaxis=dict(tickangle=90, tickfont=dict(size=15)),
    yaxis=dict(tickfont=dict(size=20)),
    xaxis2=dict(tickangle=90, tickfont=dict(size=15)),
    yaxis2=dict(tickfont=dict(size=20)),
    xaxis3=dict(tickangle=90, tickfont=dict(size=15)),
    yaxis3=dict(tickfont=dict(size=20)),
)

st.plotly_chart(fig)

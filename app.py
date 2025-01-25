import streamlit as st
import pandas as pd
import plotly.express as px

# Title of the app
st.title("CMS Synthetic vs. LDS Claims Datasets")

st.header("Introduction")

# Add some text
st.write("""
In May 2023, CMS released a [new synthetic claims dataset](https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event).  This dataset is significantly more realistic than prior synthetic claims datasets released by CMS (namely, [DE-SynPUF](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf)) in two ways:

1. **Data Format:** The tables and columns contained in this dataset closely approximate real data CMS provides to researchers and ACOs
2. **Data Values:** The actual values of the data appear realistic, at least from a high-level

Synthetic datasets are increasingly being used to build out data platforms and analytics workflows, and there is an ongoing debate as to whether they can be used to generate scientific evidence.  CMS claims "the synthetic data approximates the mathematical and statistical properties of real data."  However, as any researcher knows, how closely this approximation holds depends largely on the use cases it's being tested against.

CMS provides really fantastic documentation on the dataset, including a very detailed description of every data element.  They also provide analysis comparing the synthetic data to real data.  However, we found these comparisons to be somewhat limited in scope and wondered how well the synthetic dataset approximated real data on more advanced use cases.

In this post we explore how realistic the new synthetic claims dataset from CMS is, by comparing it to the [CMS LDS](https://www.cms.gov/data-research/files-for-order/limited-data-set-lds-files) claims dataset, specifically the 5% sample from 2020.  We use Tuva to transform both datasets into analytics-ready datasets.  As a result, the analyses computed on both datasets follow identical methodologies.
""")

st.info("💡 You can use this [repo](https://github.com/tuva-health/cms_synthetic_connector) to load the CMS Synthetic dataset into to your data warehouse and transform it with Tuva, allowing you to easily recreate any analysis in this post in your data warehouse.")

st.write("""
In this post we explore how the two datasets compare on a variety of fundamental analytics aspects, including:

- Claim Type
- Service Category
- Encounters
- Enrollment
- Financials
- Demographics
- Chronic Disease
- Emergency Department Visits
- Acute Inpatient Stays
- Readmissions
""")




## ---- Load Data ---- ##
@st.cache_data
def load_data(file):
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"An error occurred while loading the CSV file: {e}")
        return pd.DataFrame()




## ---- Claim Type ---- ##
st.markdown("## Claim Type")

# Load the data
file = "data/claim_count_by_type.csv"
df = load_data(file)
df.columns = df.columns.str.lower()

summary_table = (
    df.groupby(["data_source", "claim_type"])["claim_count"]
    .sum()
    # .groupby(level=0)
    # .apply(lambda x: (x / x.sum() * 100).round(2))
    .unstack(fill_value=0)  # Pivot the table, filling missing values with 0
)

# # Add Total column as the sum of Professional and Institutional
summary_table["total"] = summary_table.professional+summary_table.institutional

summary_percent = summary_table.div(summary_table["total"], axis=0) * 100

summary_percent = summary_percent.rename(columns={
    "professional": "Professional",
    "institutional": "Institutional",
    "total": "Total"
})  # Rename the columns

# Replace and rename columns
summary_percent.index = summary_percent.index.map({
    "cms_synthetic": "Synthetic",
    "medicare_lds": "LDS"
})  # Rename the index values

formatted_table = summary_percent.style.format({
    "Professional": "{:.2f}%",
    "Institutional": "{:.2f}%",
    "Total": "{:.2f}%"
})

st.write("""
Medical claims in health insurance claims data are either one of two types: institutional or professional.  Institutional claims are billed on a UB-04 claim form by facilities (e.g. hospitals) whereas professional claims are billed on a CMS-1500 claim form by physicians (e.g. your primary care doctor) and for medical supplies (e.g. durable medical equipment).  You can find a detailed overview of claim types and forms [here](https://thetuvaproject.com/knowledge/claims-data-fundamentals/intro-to-claims).

In most claims datasets you'll see professional claims account for ~80% of total medical claim volume and institutional claims making up the remaining share.  The table below shows this is approximately true in the LDS dataset, however, in the synthetic dataset this proportion is flipped.  
""")

st.table(formatted_table)

st.write("""
It can be instructive to look at how these proportions, as well as overall claim volume, change over time.  Generally we expect claim volume to be relatively stable over time.  Dramatic changes or spikes can indicate data quality problems.  The synthetic dataset shows a significant increase in institutional claim volume occurred in Q1 2021.  This is an unusual pattern with no clear explanation.  

On the other hand, the LDS dataset shows a decrease in claim volume in the first half of 2020.  This, however, does have a natural explanation, namely, COVID-19.  This decrease in claim volume was similar for both institutional and professional claims, whereas the 2021 increase in the synthetic dataset is driven entirely by institutional claims.
""")

# Add a toggle to select the data source
df["data_source"] = df["data_source"].replace({
    "cms_synthetic": "Synthetic",
    "medicare_lds": "LDS"
})

data_source = st.radio(
    "Select Data Source:",
    options=df["data_source"].unique(),
    index=0,
)

# Convert `year_month` to datetime for better visualization
df["year_month"] = pd.to_datetime(df["year_month"], format="%Y%m")

# Filter data based on the selected data source
filtered_df = df[df["data_source"] == data_source]

# Plotly Stacked Bar Chart
fig = px.bar(
    filtered_df,
    x="year_month",
    y="claim_count",
    color="claim_type",
    text="claim_count",
    labels={"year_month": "Year-Month", "claim_count": "Count of Claims", "claim_type": "Claim Type"},
)

# Customize layout
fig.update_layout(
    xaxis=dict(title="Year Month", tickformat="%b %Y"),  # Format x-axis as month-year
    yaxis=dict(title="Count of Claims"),
    barmode="stack",  # Ensure stacking of bars
    legend_title="Claim Type",
    # title_x=0.5,  # Center the title
)

# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)




## ---- Service Category ---- ##
st.markdown("## Service Category")

st.write ("""
Claim type tells us nothing about the type of services being rendered.  To understand this we need to look at service categories.  The Tuva [Service Category Grouper](https://thetuvaproject.com/data-marts/service-categories) assigns every claim line to a 3-tier mutually exclusive and exhaustive hierarchy.  The table below shows how claim volume is distributed at the highest level of the service category grouper.  The distribution of claims in the LDS dataset is approximately what we see with most real claims datasets.  Unfortunately the distribution of claims in the synthetic dataset is nowhere close to this.
""")

file = "data/claim_count_by_service_category_1.csv"
df_2 = load_data(file)
df_2.columns = df_2.columns.str.lower()

# Create the summary table
summary_table = (
    df_2.groupby(["data_source", "service_category_1"])["claim_count"]
    .sum()
    .unstack(fill_value=0)  # Pivot the table, filling missing values with 0
)

# Add Total column as the sum of all service categories
summary_table["total"] = summary_table.sum(axis=1)

# Convert values to percentages
summary_percent = summary_table.div(summary_table["total"], axis=0) * 100

# Rename columns for better readability
summary_percent = summary_percent.rename(columns={
    "inpatient": "Inpatient",
    "outpatient": "Outpatient",
    "office-based": "Office-based",
    "ancillary": "Ancillary",
    "other": "Other",
    "total": "Total"
})

# Replace and rename index for better readability
summary_percent.index = summary_percent.index.map({
    "cms_synthetic": "Synthetic",
    "medicare_lds": "LDS"
})

# Transpose the table so columns become rows
pivoted_table = summary_percent.transpose()

# Format the table for display in Streamlit
formatted_table = pivoted_table.style.format(
    {col: "{:.2f}%" for col in pivoted_table.columns}
)

# Display the table in Streamlit
st.table(formatted_table)





## ---- Encounters ---- ##
st.header("Encounters")
st.write ("""
While it's interesting to look at claim volume and dissect it by service categories, this tells us nothing about how many distinct healthcare encounters (i.e. visits) are happening.  Measuring encounters from claims is complex.  A single claim can represent multiple encounters, as typically happens with office-based physical therapy, or a single encounter can be made up of multiple claims, as is almost always the case with care delivered inside a hospital.  

We need to group claims into encounters in order to accurately measure the number of encounters in a claims dataset.  To do this we use the Tuva [Encounter Grouper](https://thetuvaproject.com/data-marts/encounter-types).  In a nutshell, the Encounter Grouper builds on the Service Category to categorize claims and then combine them into encounters.

The table below shows that dialysis encounters comprise nearly 40% of all encounters in the synthetic dataset, whereas they make up only 1.3% of encounters in LDS.  About the only encounter types that are approximately similar between the two datasets are Outpatient Hospital or Clinic, Emergency Department, and Ambulatory Surgery Center.
""")

file = "data/encounters.csv"
df_3 = load_data(file)
df_3.columns = df_3.columns.str.lower()

# Create the summary table
summary_table = (
    df_3.groupby(["data_source", "encounter_group", "encounter_type"])["claim_count"]
    .sum()
    .reset_index()  # Ensure all groupers are explicit columns
)

# Pivot the table to create columns for data sources (Synthetic and LDS)
pivoted_table = summary_table.pivot_table(
    index=["encounter_group", "encounter_type"],
    columns="data_source",
    values="claim_count",
    fill_value=0
).reset_index()

# Rename columns for clarity
pivoted_table.columns.name = None
pivoted_table = pivoted_table.rename(columns={
    "cms_synthetic": "Synthetic",
    "medicare_lds": "LDS",
    "encounter_group": "Encounter Group",
    "encounter_type": "Encounter Type"
})

# Calculate percentages for Synthetic and LDS
synthetic_total = pivoted_table["Synthetic"].sum()
lds_total = pivoted_table["LDS"].sum()

pivoted_table["Synthetic"] = (pivoted_table["Synthetic"] / synthetic_total * 100)
pivoted_table["LDS"] = (pivoted_table["LDS"] / lds_total * 100)

# Add a total row at the bottom using pd.concat
total_row = pd.DataFrame({
    "Encounter Group": ["Total"],
    "Encounter Type": [""],
    "Synthetic": [pivoted_table["Synthetic"].sum()],
    "LDS": [pivoted_table["LDS"].sum()]
})

pivoted_table = pd.concat([pivoted_table, total_row], ignore_index=True)

# Format the table for display in Streamlit with percentages for Synthetic and LDS
formatted_table = pivoted_table.style.format(
    {
        "Synthetic": "{:.2f}%",
        "LDS": "{:.2f}%"
    }
)

# Display the table in Streamlit
st.table(formatted_table)



file = "data/encounters.csv"
df_3 = load_data(file)
df_3.columns = df_3.columns.str.lower()

# Create the summary table
summary_table = (
    df_3.groupby(["data_source", "encounter_group", "encounter_type", "year_month"])["claim_count"]
    .sum()
    .reset_index()  # Ensure all groupers are explicit columns
)

# Ensure the 'year_month' column is in the correct datetime format
summary_table["year_month"] = pd.to_datetime(summary_table["year_month"], format="%Y%m")

# Add toggles for the data source and encounter type
data_source = st.radio(
    "Select Data Source:",
    options=summary_table["data_source"].unique(),
    index=0,
)

encounter_type = st.selectbox(
    "Select Encounter Type:",
    options=summary_table["encounter_type"].unique(),
    index=0,
)

# Filter data based on user selection
filtered_df = summary_table[
    (summary_table["data_source"] == data_source) &
    (summary_table["encounter_type"] == encounter_type)
]

# Plot the time series chart
fig = px.bar(
    filtered_df,
    x="year_month",
    y="claim_count",
    color="encounter_group",
    text="claim_count",
    labels={
        "year_month": "Year-Month",
        "claim_count": "Count of Claims",
        "encounter_group": "Encounter Group",
    },
    title=f"Time Series for {encounter_type} ({data_source})",
)

# Customize chart layout
fig.update_layout(
    xaxis=dict(title="Year-Month", tickformat="%b %Y"),
    yaxis=dict(title="Count of Claims"),
    barmode="stack",
    legend_title="Encounter Group",
)

# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)

# Pivot the table to create columns for data sources (Synthetic and LDS)
pivoted_table = summary_table.pivot_table(
    index=["encounter_group", "encounter_type"],
    columns="data_source",
    values="claim_count",
    fill_value=0
).reset_index()

# Rename columns for clarity
pivoted_table.columns.name = None
pivoted_table = pivoted_table.rename(columns={
    "cms_synthetic": "Synthetic",
    "medicare_lds": "LDS",
    "encounter_group": "Encounter Group",
    "encounter_type": "Encounter Type"
})

# Calculate percentages for Synthetic and LDS
synthetic_total = pivoted_table["Synthetic"].sum()
lds_total = pivoted_table["LDS"].sum()

pivoted_table["Synthetic"] = (pivoted_table["Synthetic"] / synthetic_total * 100)
pivoted_table["LDS"] = (pivoted_table["LDS"] / lds_total * 100)

# Add a total row at the bottom using pd.concat
total_row = pd.DataFrame({
    "Encounter Group": ["Total"],
    "Encounter Type": [""],
    "Synthetic": [pivoted_table["Synthetic"].sum()],
    "LDS": [pivoted_table["LDS"].sum()]
})

pivoted_table = pd.concat([pivoted_table, total_row], ignore_index=True)

# Format the table for display in Streamlit with percentages for Synthetic and LDS
formatted_table = pivoted_table.style.format(
    {
        "Synthetic": "{:.2f}%%",
        "LDS": "{:.2f}%%"
    }
)

# Display the table in Streamlit
st.table(formatted_table)














## ---- Enrollment ---- ##
st.header("Enrollment")

st.header("Demographics")

st.header("Chronic Disease")

st.header("ED Visits")

st.header("Acute Inpatient Stays")

st.header("Readmissions")







# ## ---- Claim Volume Over Time by Claim Type ----




